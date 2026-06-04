"""③ 추모 메시지 로직·프롬프트 테스트.

LLM 없이도 검증 가능한 것만 다룹니다(실제 모델 품질은 provider 확정 후 단계):
  1. 프롬프트 조립 — 입력값이 정확히 채워지고 가드 문구가 박혀 있는가.
  2. 흐름 — 가짜 generate 를 주입해 generate_message 의 단계가 맞는가.
  3. 안전 — 위기 입력은 메시지보다 1393 안내가 우선인가.
  4. 가드 — 부활/1인칭 출력은 차단되는가.
"""

from __future__ import annotations

import pytest

from ..memorial import GuardrailViolation, generate_message
from ..prompts import memorial as memorial_prompt
from ..safety import CRISIS_HOTLINE

PET = {
    "name": "봄이",
    "species": "강아지",
    "period": "12년",
    "memories": ["아침마다 현관에서 기다림", "노란 공놀이"],
}


# --- 1. 프롬프트 조립 -------------------------------------------------------- #


def test_prompt_fills_inputs():
    prompt = memorial_prompt.build_user_prompt(
        name="봄이", species="강아지", period="12년", score=3, note="산책을 좋아했어요"
    )
    assert "봄이" in prompt
    assert "강아지" in prompt
    assert "12년" in prompt
    assert "3/10" in prompt
    assert "산책을 좋아했어요" in prompt


def test_prompt_includes_memories_when_given():
    prompt = memorial_prompt.build_user_prompt(
        name="봄이", species="강아지", period="12년", score=5, memories=["노란 공놀이"]
    )
    assert "노란 공놀이" in prompt


def test_prompt_omits_memory_block_when_empty():
    prompt = memorial_prompt.build_user_prompt(
        name="봄이", species="강아지", period="12년", score=5, memories=[]
    )
    assert "함께한 추억" not in prompt


def test_unknown_tone_falls_back_to_default():
    prompt = memorial_prompt.build_user_prompt(
        name="봄이", species="강아지", period="12년", score=5, tone="존재하지않는톤"
    )
    assert memorial_prompt.TONE_GUIDE[memorial_prompt.DEFAULT_TONE] in prompt


def test_system_prompt_has_ethics_guardrails():
    """🚨 시스템 프롬프트에 1인칭·부활 금지가 실제로 박혀 있어야 한다."""
    system = memorial_prompt.SYSTEM_PROMPT
    assert "1인칭" in system
    assert "살아나" in system or "돌아온다" in system


def test_build_messages_has_system_and_user():
    messages = memorial_prompt.build_messages(
        name="봄이", species="강아지", period="12년", score=5
    )
    assert [m["role"] for m in messages] == ["system", "user"]


# --- 2. 흐름 (가짜 generate 주입) ------------------------------------------- #


def test_generate_message_uses_injected_generate():
    """generate_message 가 주입된 generate 의 출력을 그대로 감싸는지."""
    fake_output = "봄이와 함께한 아침 산책의 온기가 당신 곁에 오래 머물기를 바랍니다."

    def fake_generate(prompt, *, max_tokens=400, temperature=0.7, json_mode=False):
        assert "봄이" in prompt  # 프롬프트가 실제로 전달됐는지
        return fake_output

    result = generate_message(
        PET, {"emotion_score": 3, "note": "너무 보고 싶어요"}, generate=fake_generate
    )
    assert result["content"] == fake_output
    assert result["source"] == "local"
    assert result["tone"] == memorial_prompt.DEFAULT_TONE


# --- 3. 안전: 위기 입력은 1393 우선 ----------------------------------------- #


def test_crisis_input_returns_hotline_not_message():
    """위기 신호(L2↑)면 LLM 을 호출하지 않고 1393 안내를 우선한다."""
    called = False

    def fake_generate(prompt, *, max_tokens=400, temperature=0.7, json_mode=False):
        nonlocal called
        called = True
        return "이 문장은 나오면 안 됩니다."

    result = generate_message(
        PET,
        {"emotion_score": 1, "note": "봄이 곁으로 나도 따라가고 싶어요"},
        generate=fake_generate,
    )
    assert called is False  # 위기 시 생성 자체를 건너뜀
    assert CRISIS_HOTLINE in result["crisis_message"]
    assert CRISIS_HOTLINE in result["content"]


# --- 4. 가드: 부활/1인칭 출력 차단 ------------------------------------------ #


def test_resurrection_output_is_blocked():
    def bad_generate(prompt, *, max_tokens=400, temperature=0.7, json_mode=False):
        return "걱정 마세요, 봄이는 곧 다시 살아서 돌아올 거예요."

    with pytest.raises(GuardrailViolation):
        generate_message(
            PET, {"emotion_score": 5, "note": "보고 싶어요"}, generate=bad_generate
        )


def test_guard_retries_then_succeeds():
    """첫 출력이 위반이면 재생성, 다음이 정상이면 통과."""
    outputs = iter(
        [
            "봄이가 부활해서 돌아온다.",  # 위반
            "봄이와 나눈 시간이 당신을 따뜻하게 지켜줄 거예요.",  # 정상
        ]
    )

    def flaky_generate(prompt, *, max_tokens=400, temperature=0.7, json_mode=False):
        return next(outputs)

    result = generate_message(
        PET, {"emotion_score": 4, "note": "보고 싶어요"}, generate=flaky_generate
    )
    assert "부활" not in result["content"].replace(" ", "")
