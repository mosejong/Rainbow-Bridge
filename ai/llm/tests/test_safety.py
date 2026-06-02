"""⑦ 위기 감지 규칙 레이어 테스트.

핵심 보장:
  1. 심각 등급(L2·L3) **미탐(놓침) 0** — 감지 등급이 기대치보다 낮으면 실패.
  2. 함정 케이스(반려동물 죽음)는 위기로 올라가지 않음(오탐 0 at 심각 등급).
  3. 1393 안내는 L2 이상에서만 필수.
"""

from __future__ import annotations

import pytest

from ..safety import (
    CRISIS_HOTLINE,
    HOTLINE_REQUIRED_FROM,
    RiskLevel,
    Subject,
    detect_crisis,
)
from .golden_crisis import GOLDEN_CASES


def test_crisis_hotline_is_1393():
    """🚨 안내 번호는 1393 으로 고정 — 변경/누락 금지."""
    assert CRISIS_HOTLINE == "1393"


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=lambda c: c.id)
def test_no_missed_detection(case):
    """미탐 0: 감지 등급이 기대 등급보다 낮으면 안 된다(보수적).

    심각 케이스를 놓치는 것이 가장 위험하므로, '같거나 더 높게'를 허용하고
    '더 낮음'만 실패로 둔다.
    """
    result = detect_crisis(case.text)
    assert result.risk_level >= case.expected_level, (
        f"[미탐] {case.id}: '{case.text}' → "
        f"감지 {result.risk_level.name}, 기대 최소 {case.expected_level.name}"
    )


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=lambda c: c.id)
def test_exact_level_matches_golden(case):
    """규칙 레이어 회귀: 등급이 골든셋과 정확히 일치(사전 변경 감지용)."""
    result = detect_crisis(case.text)
    assert result.risk_level == case.expected_level, (
        f"[등급변동] {case.id}: '{case.text}' → "
        f"감지 {result.risk_level.name}, 골든 {case.expected_level.name}"
    )


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=lambda c: c.id)
def test_subject_matches_golden(case):
    """표현 대상(subject) 구분이 골든셋과 일치."""
    result = detect_crisis(case.text)
    assert result.subject == case.expected_subject, (
        f"[대상오류] {case.id}: '{case.text}' → "
        f"감지 {result.subject}, 골든 {case.expected_subject}"
    )


def test_pet_death_is_not_crisis():
    """함정 직접 검증: '봄이가 죽었어요' 는 L0(정상)·대상 pet."""
    result = detect_crisis("봄이가 죽었어요")
    assert result.risk_level == RiskLevel.L0_NORMAL
    assert result.subject == Subject.PET
    assert result.hotline_required is False


def test_hotline_required_from_l2():
    """1393 안내는 L2(경고) 이상에서만 필수."""
    assert HOTLINE_REQUIRED_FROM == RiskLevel.L2_WARNING

    warning = detect_crisis("봄이 곁으로 따라가고 싶어요")
    assert warning.risk_level >= RiskLevel.L2_WARNING
    assert warning.hotline_required is True
    assert warning.as_dict()["hotline"] == CRISIS_HOTLINE

    normal = detect_crisis("산책하던 길을 지나니 봄이 생각이 나요")
    assert normal.hotline_required is False
    assert normal.as_dict()["hotline"] is None


def test_self_desire_overrides_pet_mention():
    """반려동물 언급이 있어도 본인 사망 욕구가 있으면 self·경고 이상."""
    result = detect_crisis("봄이 따라 나도 죽고 싶어요")
    assert result.subject == Subject.SELF
    assert result.risk_level >= RiskLevel.L2_WARNING
