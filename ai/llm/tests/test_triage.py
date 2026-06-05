"""1단계 증상 진료 안내 로직·프롬프트 테스트.

LLM 없이도 검증 가능한 것만 다룹니다:
  1. 프롬프트 조립 — 입력값이 정확히 채워지고 금지 항목이 박혀 있는가.
  2. 심각도 추론 — 키워드별로 emergency·urgent·soon·monitor 가 맞게 나오는가.
  3. 흐름 — 가짜 generate 를 주입해 generate_triage 단계가 맞는가.
  4. 안전 — 보호자 note 에 위기 신호가 있으면 1393 우선, LLM 호출 안 함.
"""

from __future__ import annotations

import pytest

from ..prompts import triage as triage_prompt
from ..safety import CRISIS_HOTLINE
from ..triage import generate_triage

PET = {"name": "콩이", "species": "강아지", "age": "3살"}


# --------------------------------------------------------------------------- #
# 1. 프롬프트 조립
# --------------------------------------------------------------------------- #


def test_prompt_fills_pet_info():
    messages = triage_prompt.build_messages(
        "구토를 반복해요", name="콩이", species="강아지", age="3살"
    )
    user_content = messages[1]["content"]
    assert "콩이" in user_content
    assert "강아지" in user_content
    assert "3살" in user_content
    assert "구토를 반복해요" in user_content


def test_prompt_uses_missing_when_no_pet_info():
    messages = triage_prompt.build_messages("기침을 해요")
    user_content = messages[1]["content"]
    assert "미입력" in user_content


def test_prompt_closing_matches_severity():
    """심각도에 맞는 마지막 안내 문장이 프롬프트에 들어가는지."""
    messages = triage_prompt.build_messages("경련을 일으켜요", severity="emergency")
    user_content = messages[1]["content"]
    assert triage_prompt.SEVERITY_CLOSINGS["emergency"] in user_content


def test_system_prompt_forbids_diagnosis():
    """시스템 프롬프트에 단정 금지가 명시돼 있어야 한다."""
    assert "단정" in triage_prompt.SYSTEM_PROMPT
    assert "약" in triage_prompt.SYSTEM_PROMPT


def test_build_messages_has_system_and_user():
    messages = triage_prompt.build_messages("밥을 안 먹어요", name="콩이", species="강아지")
    assert [m["role"] for m in messages] == ["system", "user"]


# --------------------------------------------------------------------------- #
# 2. 심각도 추론
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "symptoms, expected",
    [
        ("경련을 일으켜요", "emergency"),
        ("발작이 왔어요", "emergency"),
        ("호흡곤란이 있어요", "emergency"),
        ("구토를반복해요", "urgent"),
        ("설사를반복해요", "urgent"),
        ("아무것도안먹어요", "urgent"),
        ("혈변이 있어요", "urgent"),
        ("기침을 해요", "soon"),
        ("눈곱이 껴요", "soon"),
        ("다리를절어요", "soon"),
        ("평소보다 좀 처져요", "monitor"),  # 매칭 키워드 없음
    ],
)
def test_assess_severity(symptoms, expected):
    assert triage_prompt._assess_severity(symptoms) == expected


# --------------------------------------------------------------------------- #
# 3. 흐름 (가짜 generate 주입)
# --------------------------------------------------------------------------- #


def test_generate_triage_returns_advice_and_severity():
    """generate_triage 가 advice·severity·source 를 반환하는지."""
    fake_output = "구토 반복은 소화기 문제일 수 있습니다. 오늘 안에 동물병원에 방문해 보세요."

    def fake_generate(prompt, *, max_tokens=300, temperature=0.4, json_mode=False):
        return fake_output

    result = generate_triage("구토를반복해요", PET, generate=fake_generate)

    assert result["advice"] == fake_output
    assert result["severity"] == "urgent"
    assert result["source"] == "local"


def test_generate_triage_passes_symptoms_in_prompt():
    """symptoms 텍스트가 실제로 LLM 에 전달되는지."""
    captured = {}

    def fake_generate(prompt, *, max_tokens=300, temperature=0.4, json_mode=False):
        captured["prompt"] = prompt
        return "안내 텍스트"

    generate_triage("경련을 일으켰어요", PET, generate=fake_generate)
    assert "경련을 일으켰어요" in captured["prompt"]


def test_generate_triage_custom_source():
    def fake_generate(prompt, *, max_tokens=300, temperature=0.4, json_mode=False):
        return "안내"

    result = generate_triage("기침해요", PET, generate=fake_generate, source="perso")
    assert result["source"] == "perso"


# --------------------------------------------------------------------------- #
# 4. 안전: 보호자 위기 신호 → 1393 우선
# --------------------------------------------------------------------------- #


def test_crisis_note_skips_llm_and_returns_hotline():
    """보호자 메모에 위기 신호(L2↑)가 있으면 LLM 을 호출하지 않는다."""
    called = False

    def fake_generate(prompt, *, max_tokens=300, temperature=0.4, json_mode=False):
        nonlocal called
        called = True
        return "이 문장은 나오면 안 됩니다."

    result = generate_triage(
        "밥을 안 먹어요",
        PET,
        note="콩이 곁으로 나도 따라가고 싶어요",
        generate=fake_generate,
    )

    assert called is False
    assert CRISIS_HOTLINE in result["crisis_message"]
    assert result["severity"] == "crisis"
    assert result["source"] == "safety"


def test_no_note_does_not_trigger_crisis_check():
    """note 가 없으면 위기 체크를 건너뛰고 정상적으로 LLM 을 호출한다."""
    called = False

    def fake_generate(prompt, *, max_tokens=300, temperature=0.4, json_mode=False):
        nonlocal called
        called = True
        return "안내 텍스트"

    generate_triage("기침해요", PET, generate=fake_generate)
    assert called is True
