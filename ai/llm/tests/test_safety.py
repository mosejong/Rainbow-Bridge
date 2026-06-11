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
    assess_crisis,
    detect_crisis,
)
from .golden_crisis import GOLDEN_CASES


def test_crisis_hotline_is_1393():
    """🚨 안내 번호는 1393 으로 고정 — 변경/누락 금지."""
    assert CRISIS_HOTLINE == "1393"


_L0_DETECTION_CASES = [c for c in GOLDEN_CASES if "L0 미탐 허용" not in c.note]


@pytest.mark.parametrize("case", _L0_DETECTION_CASES, ids=lambda c: c.id)
def test_no_missed_detection(case):
    """미탐 0: 규칙(L0) 감지 등급이 기대 등급보다 낮으면 안 된다(보수적).

    심각 케이스를 놓치는 것이 가장 위험하므로, '같거나 더 높게'를 허용하고
    '더 낮음'만 실패로 둔다. 'L0 미탐 허용' 케이스는 L1(LLM)이 보완.
    """
    result = detect_crisis(case.text)
    assert result.risk_level >= case.expected_level, (
        f"[미탐] {case.id}: '{case.text}' → "
        f"감지 {result.risk_level.name}, 기대 최소 {case.expected_level.name}"
    )


_L0_EXACT_CASES = [c for c in GOLDEN_CASES if "L0 미탐 허용" not in c.note]


@pytest.mark.parametrize("case", _L0_EXACT_CASES, ids=lambda c: c.id)
def test_exact_level_matches_golden(case):
    """규칙 레이어 회귀: 등급이 골든셋과 정확히 일치(사전 변경 감지용).

    note에 'L0 미탐 허용'이 있는 케이스는 L1(LLM)이 보완하는 항목으로 제외.
    """
    result = detect_crisis(case.text)
    assert result.risk_level == case.expected_level, (
        f"[등급변동] {case.id}: '{case.text}' → "
        f"감지 {result.risk_level.name}, 골든 {case.expected_level.name}"
    )


@pytest.mark.parametrize("case", _L0_EXACT_CASES, ids=lambda c: c.id)
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


@pytest.mark.parametrize("case", GOLDEN_CASES, ids=lambda c: c.id)
def test_assess_crisis_matches_detect_for_now(case):
    """창구 함수 계약: 현재(LLM 융합 전)는 detect_crisis 와 동일 결과.

    백엔드는 assess_crisis 만 호출합니다. 향후 이 함수에 LLM 융합이 붙으면
    결과가 달라질 수 있으나, 그때 이 테스트를 함께 갱신합니다(계약 변경 신호).
    """
    assert assess_crisis(case.text).risk_level == detect_crisis(case.text).risk_level


def test_assess_crisis_returns_crisis_result():
    """백엔드 연동 계약: CrisisResult 타입·as_dict 키를 보장."""
    result = assess_crisis("봄이 곁으로 따라가고 싶어요")
    assert result.risk_level >= RiskLevel.L2_WARNING
    assert result.as_dict()["hotline"] == CRISIS_HOTLINE


# --- 자책감(guilt) → 조합 상향 + 공감 톤 플래그 --------------------------- #


def test_guilt_with_passive_escalates_to_l2():
    """자책감 + 수동적 위기신호(L1) → L2 로 상향(조합 룰), 1393 필수."""
    result = detect_crisis("사는 의미가 없어요. 다 내 탓이에요.")
    assert result.guilt is True
    assert result.risk_level == RiskLevel.L2_WARNING
    assert result.hotline_required is True


def test_guilt_alone_stays_l0():
    """자책감만(일반 애도)으론 등급을 올리지 않는다 — 오탐 방지(공감 톤은 memorial 몫)."""
    result = detect_crisis("미안해 봄아. 내가 더 잘했어야 했는데, 다 내 탓이야.")
    assert result.guilt is True
    assert result.risk_level == RiskLevel.L0_NORMAL


def test_guilt_does_not_lower_means_l3():
    """means(구체적 수단)는 자책감과 무관하게 L3 유지(상한 L2가 끌어내리지 않음)."""
    result = detect_crisis("다 내 탓이야. 유서도 써뒀어.")
    assert result.risk_level == RiskLevel.L3_EMERGENCY


def test_normal_grief_has_no_guilt_flag():
    """자책 표현이 없는 일반 애도는 guilt=False, L0."""
    result = detect_crisis("봄이가 무지개다리를 건넜어요. 너무 보고 싶어요.")
    assert result.guilt is False
    assert result.risk_level == RiskLevel.L0_NORMAL
