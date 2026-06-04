"""⑦ 위기 감지 LLM 레이어(L1) + 융합 테스트 — 네트워크 없이 검증.

가짜 generate 로 결정적으로 확인:
  1. generate 미주입 → 규칙 결과 그대로(백엔드 호환)
  2. 보수적 융합 — L1이 올리면 따라 오름, 내리려 해도 안 내려감(미탐 0)
  3. graceful — L1 실패/JSON 깨짐이면 규칙 결과로 폴백
  4. classify_with_llm JSON 파싱
"""

from __future__ import annotations

import json

from ..safety import (
    HOTLINE_REQUIRED_FROM,
    RiskLevel,
    Subject,
    assess_crisis,
    classify_with_llm,
    detect_crisis,
)


def _fake(level: int, subject: str = Subject.SELF, reason: str = "테스트"):
    """주어진 등급을 JSON 으로 돌려주는 가짜 generate."""
    payload = json.dumps(
        {"risk_level": level, "subject": subject, "reason": reason},
        ensure_ascii=False,
    )

    def gen(prompt, *, max_tokens=256, temperature=0.0, json_mode=False):
        assert json_mode is True  # L1은 JSON 강제
        return payload

    return gen


# --- 1. generate 미주입 → 규칙과 동일 (백엔드 호환) ------------------------- #


def test_no_generate_equals_rule():
    text = "봄이 따라 나도 죽고 싶어요"
    assert assess_crisis(text).risk_level == detect_crisis(text).risk_level
    # 정상 문장도 동일
    assert assess_crisis("봄이가 죽었어요").risk_level == RiskLevel.L0_NORMAL


# --- 2. 보수적 융합 --------------------------------------------------------- #


def test_llm_escalates_rule_miss():
    """규칙이 L0(놓침)인데 L1이 L2로 보면 → 융합 L2, 1393 필요."""
    text = "요즘 모든 게 손에서 놓여버린 기분이에요"  # 규칙 사전에 없는 완곡 표현
    assert detect_crisis(text).risk_level == RiskLevel.L0_NORMAL  # 규칙은 놓침
    result = assess_crisis(text, generate=_fake(2))
    assert result.risk_level == RiskLevel.L2_WARNING
    assert result.hotline_required is True
    assert result.risk_level >= HOTLINE_REQUIRED_FROM


def test_llm_cannot_deescalate():
    """규칙이 L2인데 L1이 L0로 내리려 해도 → 융합은 L2 유지(미탐 방지)."""
    text = "봄이 따라 나도 죽고 싶어요"
    assert detect_crisis(text).risk_level == RiskLevel.L2_WARNING
    result = assess_crisis(text, generate=_fake(0, subject=Subject.PET))
    assert result.risk_level == RiskLevel.L2_WARNING
    assert result.hotline_required is True


def test_llm_can_raise_to_emergency():
    text = "그냥 다 끝내고 싶어"
    result = assess_crisis(text, generate=_fake(3))
    assert result.risk_level == RiskLevel.L3_EMERGENCY


def test_trap_stays_l0_when_llm_agrees():
    """함정(반려동물 죽음)은 L1도 L0로 보면 융합 L0 유지(과탐 없음)."""
    result = assess_crisis("봄이가 죽었어요", generate=_fake(0, subject=Subject.PET))
    assert result.risk_level == RiskLevel.L0_NORMAL
    assert result.hotline_required is False


# --- 3. graceful 폴백 ------------------------------------------------------- #


def test_bad_json_falls_back_to_rule():
    def bad(prompt, *, max_tokens=256, temperature=0.0, json_mode=False):
        return "이건 JSON 이 아닙니다"

    text = "봄이 따라 나도 죽고 싶어요"
    result = assess_crisis(text, generate=bad)
    assert result.risk_level == detect_crisis(text).risk_level  # 규칙 폴백


def test_exception_falls_back_to_rule():
    def boom(prompt, *, max_tokens=256, temperature=0.0, json_mode=False):
        raise RuntimeError("LLM 다운")

    result = assess_crisis("봄이가 죽었어요", generate=boom)
    assert result.risk_level == RiskLevel.L0_NORMAL


# --- 4. classify_with_llm 파싱 ---------------------------------------------- #


def test_classify_parses_verdict():
    verdict = classify_with_llm(
        "아무 문장", _fake(2, subject=Subject.SELF, reason="근거")
    )
    assert verdict is not None
    assert verdict.risk_level == RiskLevel.L2_WARNING
    assert verdict.subject == Subject.SELF
    assert verdict.reason == "근거"


def test_classify_clamps_and_sanitizes():
    """범위 밖 등급·이상한 subject 는 안전하게 보정."""
    verdict = classify_with_llm("문장", _fake(9, subject="garbage"))
    assert verdict is not None
    assert verdict.risk_level == RiskLevel.L3_EMERGENCY  # 9 → 3 클램프
    assert verdict.subject == Subject.NONE  # 잘못된 subject → none


def test_classify_returns_none_on_failure():
    def boom(prompt, *, max_tokens=256, temperature=0.0, json_mode=False):
        raise RuntimeError("x")

    assert classify_with_llm("문장", boom) is None
