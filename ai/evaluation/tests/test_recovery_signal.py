"""일상복귀 신호 — 순수함수 검증 (DB/LLM 없이)."""

from __future__ import annotations

from ..recovery_signal import (
    SIGNAL_AT_RISK,
    SIGNAL_INSUFFICIENT,
    SIGNAL_RECOVERING,
    SIGNAL_STABLE,
    compute_recovery_signal,
)


def _checkins(scores: list[float]) -> list[dict]:
    """오래된→최근 순 점수 리스트를 체크인 목록으로(created_at 부여)."""
    return [{"score": s, "created_at": f"2026-06-{i + 1:02d}"} for i, s in enumerate(scores)]


def test_insufficient_data():
    out = compute_recovery_signal(_checkins([4, 5]))
    assert out["signal"] == SIGNAL_INSUFFICIENT
    assert out["recovery_index"] is None


def test_recovering_when_scores_rise():
    out = compute_recovery_signal(_checkins([3, 3, 4, 7, 8, 8]))
    assert out["signal"] == SIGNAL_RECOVERING
    assert out["emotion"]["direction"] == "상승"


def test_at_risk_when_scores_fall():
    out = compute_recovery_signal(_checkins([8, 7, 7, 4, 3, 3]))
    assert out["signal"] == SIGNAL_AT_RISK
    assert out["emotion"]["direction"] == "하락"


def test_stable_when_flat():
    out = compute_recovery_signal(_checkins([5, 5, 5, 5, 5]))
    assert out["signal"] == SIGNAL_STABLE


def test_unordered_checkins_sorted_by_date():
    """입력 순서가 뒤섞여도 created_at 기준으로 정렬해 추세를 낸다."""
    rows = [
        {"score": 8, "created_at": "2026-06-06"},
        {"score": 3, "created_at": "2026-06-01"},
        {"score": 7, "created_at": "2026-06-05"},
        {"score": 3, "created_at": "2026-06-02"},
        {"score": 4, "created_at": "2026-06-03"},
        {"score": 6, "created_at": "2026-06-04"},
    ]
    out = compute_recovery_signal(rows)
    assert out["signal"] == SIGNAL_RECOVERING


def test_mission_completion_rate():
    missions = [{"done": True}, {"done": True}, {"done": False}, {"done": False}]
    out = compute_recovery_signal(_checkins([5, 5, 6, 6]), missions)
    assert out["mission_completion_rate"] == 0.5
    assert any("미션 완료율 50%" in e for e in out["evidence"])


def test_access_decrease_reads_as_recovery_evidence():
    """감정이 오르는 중 + 접속이 줄면 '의존이 줄어드는 회복 신호'로 근거에 잡힌다."""
    out = compute_recovery_signal(
        _checkins([3, 3, 4, 7, 8, 8]), access_counts=[10, 9, 7, 4, 2, 1]
    )
    assert out["access_trend"]["direction"] == "감소"
    assert any("회복 신호" in e for e in out["evidence"])


def test_graceful_without_engagement_or_missions():
    """접속/재생/미션 없이 감정만으로도 동작(자리만 비어 있음)."""
    out = compute_recovery_signal(_checkins([4, 5, 6, 7]))
    assert out["signal"] in {SIGNAL_RECOVERING, SIGNAL_STABLE}
    assert out["access_trend"] is None
    assert out["play_trend"] is None
    assert out["mission_completion_rate"] is None
