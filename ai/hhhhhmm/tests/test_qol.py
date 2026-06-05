"""HHHHHMM 삶의 질 척도 순수 함수 테스트 — 외부 의존 없음."""

from __future__ import annotations

import pytest

from ..qol import QOL_CRITERIA, score_qol


def _scores(value: int = 7) -> dict[str, int]:
    """모든 항목을 같은 값으로 채운 입력."""
    return {k: value for k in QOL_CRITERIA}


def test_all_seven_total_and_tier():
    """7점씩 → 총점 49, 유지 가능 등급."""
    r = score_qol(_scores(7))
    assert r["total"] == 49
    assert r["max"] == 70
    assert r["tier"] == "maintainable"


def test_low_scores_declining():
    """전부 2점 → 총점 14, 저하 등급."""
    r = score_qol(_scores(2))
    assert r["total"] == 14
    assert r["tier"] == "declining"


def test_boundary_35_is_maintainable():
    """경계값: 총점 정확히 35는 유지 가능(>=35)."""
    s = _scores(5)  # 5*7 = 35
    r = score_qol(s)
    assert r["total"] == 35
    assert r["tier"] == "maintainable"


def test_just_below_boundary_is_declining():
    """총점 34는 저하 등급."""
    s = _scores(5)
    s["hurt"] = 4  # 35 - 1 = 34
    r = score_qol(s)
    assert r["total"] == 34
    assert r["tier"] == "declining"


def test_low_items_flagged():
    """5점 미만 항목은 low_items에 잡혀야 함."""
    s = _scores(8)
    s["mobility"] = 2
    r = score_qol(s)
    assert "mobility" in r["low_items"]
    assert "hunger" not in r["low_items"]


def test_always_has_vet_referral_and_disclaimer():
    """등급과 무관하게 수의사 안내·면책 문구가 항상 들어가야 함."""
    for value in (1, 9):
        r = score_qol(_scores(value))
        assert r["vet_referral"]
        assert "수의사" in r["vet_referral"]
        assert "안락사를 결정하지 않습니다" in r["disclaimer"]


def test_missing_criterion_raises():
    s = _scores(7)
    del s["happiness"]
    with pytest.raises(ValueError):
        score_qol(s)


def test_unknown_criterion_raises():
    s = _scores(7)
    s["zoomies"] = 10
    with pytest.raises(ValueError):
        score_qol(s)


def test_out_of_range_raises():
    s = _scores(7)
    s["hunger"] = 11
    with pytest.raises(ValueError):
        score_qol(s)


def test_non_integer_raises():
    s = _scores(7)
    s["hydration"] = 7.5  # type: ignore[assignment]
    with pytest.raises(ValueError):
        score_qol(s)


def test_bool_rejected():
    """bool은 int 서브클래스라 명시적으로 거부해야 함."""
    s = _scores(7)
    s["hurt"] = True  # type: ignore[assignment]
    with pytest.raises(ValueError):
        score_qol(s)
