"""시한부 케어 고정 안내 — 콘텐츠 로드·구조·안전장치 검증.

LLM 호출이 없는 고정 콘텐츠라, 구조가 깨지지 않고 위기 안내(1393)가
상수에서 제대로 주입되는지를 점검합니다.
"""

from __future__ import annotations

from ai.llm.safety import CRISIS_HOTLINE
from ai.llm.terminal_care import get_terminal_care_info


def test_returns_required_top_level_keys():
    info = get_terminal_care_info()
    for key in ("title", "disclaimer", "stages", "care", "support_note", "crisis_hotline"):
        assert key in info, f"누락 키: {key}"


def test_has_two_stages_with_groups():
    info = get_terminal_care_info()
    stage_ids = [s["id"] for s in info["stages"]]
    assert stage_ids == ["early_mid", "late"]
    for stage in info["stages"]:
        assert stage["groups"], f"{stage['id']} 단계에 증상 그룹이 비어 있음"
        for group in stage["groups"]:
            assert group["name"]
            assert group["items"], f"{group['name']} 항목이 비어 있음"


def test_care_section_has_items():
    info = get_terminal_care_info()
    assert info["care"]["items"], "보호자 케어 항목이 비어 있음"


def test_crisis_hotline_injected_from_constant():
    """🚨 1393 은 JSON 에 박지 않고 CRISIS_HOTLINE 상수에서 주입돼야 함."""
    info = get_terminal_care_info()
    assert info["crisis_hotline"] == CRISIS_HOTLINE
    assert CRISIS_HOTLINE in info["support_note"]


def test_hotline_not_hardcoded_in_json():
    """원본 JSON 본문(콘텐츠)에는 번호가 하드코딩돼 있지 않아야 함."""
    import json
    from pathlib import Path

    raw = Path(__file__).parents[1].joinpath("data", "terminal_care.json").read_text(
        encoding="utf-8"
    )
    data = json.loads(raw)
    # 콘텐츠 영역(stages/care/closing/disclaimer)에 번호가 직접 들어가지 않았는지
    blob = json.dumps(
        {k: data[k] for k in ("disclaimer", "stages", "care", "closing")},
        ensure_ascii=False,
    )
    assert CRISIS_HOTLINE not in blob


def test_disclaimer_mentions_vet_and_no_diagnosis():
    """진단·예측이 아님을 명시(윤리)."""
    info = get_terminal_care_info()
    disclaimer = info["disclaimer"]
    assert "수의사" in disclaimer
    assert "진단" in disclaimer or "예측" in disclaimer
