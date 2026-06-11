"""일상복귀 신호 — 순수함수 검증 (DB/LLM 없이)."""

from __future__ import annotations

from ..recovery_signal import (
    SIGNAL_AT_RISK,
    SIGNAL_INSUFFICIENT,
    SIGNAL_RECOVERING,
    SIGNAL_STABLE,
    compute_recovery_signal,
    recovery_score,
)


def _checkins(scores: list[float]) -> list[dict]:
    """오래된→최근 순 점수 리스트를 체크인 목록으로(created_at 부여)."""
    return [
        {"score": s, "created_at": f"2026-06-{i + 1:02d}"} for i, s in enumerate(scores)
    ]


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
    assert out["mission_completion_rate"] == 2
    assert any("미션 누적 2개 완료" in e for e in out["evidence"])


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
    assert out["mission_completion_rate"] == 0


# --- 회복 점수 (RECOVERY_GATE 40/35/25) ------------------------------------- #


def test_recovery_score_weighted_40_35_25():
    """감정40·미션누적35(sticky)·꾸준25 가중합. 모두 만점이면 100, 모두 절반이면 50."""
    assert recovery_score(10, 35, 100) == 100  # E=100·M=35·C=25
    assert recovery_score(5.5, 17, 50) == 50  # E=50·M=17·C=12.5


def test_recovery_score_clamped_0_100():
    """범위 밖 입력이어도 0~100 보장(음수/초과 클램프)."""
    assert recovery_score(1, 0, 0) == 0  # E=0
    assert recovery_score(0, 0, 0) == 0  # 음수 입력 → 0
    assert recovery_score(11, 35, 100) == 100  # 초과 입력 → 100


# --- 불변식 (예시가 아닌 '어떤 입력이든' 보장) ------------------------------ #


def test_recovery_score_always_in_0_100():
    """어떤 입력(범위 밖 포함)이어도 점수는 0~100."""
    for emo in (0, 1, 5.5, 10, 11, -3):
        for comp in (0, 1, 17, 35, 50):
            for cons in (-10, 0, 50, 100, 150):
                s = recovery_score(emo, comp, cons)
                assert 0 <= s <= 100, (emo, comp, cons, s)


def test_recovery_score_monotonic_in_emotion():
    """미션·꾸준함 고정 시 감정만 올리면 점수는 줄지 않는다(단조)."""
    prev = -1
    for emo in (1, 3, 5, 7, 10):
        s = recovery_score(emo, 17, 50)
        assert s >= prev
        prev = s


def test_consistency_detects_dropout_with_as_of():
    """as_of(오늘) 주면 장기 잠수가 꾸준함 0%로 잡힌다(이탈 탐지)."""
    from datetime import date

    rows = _checkins([5, 6, 7, 5, 6, 7])  # 6/1~6/6 체크인
    # 기본(as_of 없음) = 최근 체크인 기준 → 꾸준함 있음
    assert compute_recovery_signal(rows)["checkin_consistency"] > 0
    # 한 달 뒤 기준 → 14일 창에 0일 → 0%
    out = compute_recovery_signal(rows, as_of=date(2026, 7, 10))
    assert out["checkin_consistency"] == 0.0


def test_recovery_index_uses_composite_not_avg10():
    """recovery_index 가 단순 avg*10 이 아니라 40/35/25 산식(꾸준함 포함)으로 나온다."""
    missions = [{"done": True}, {"done": False}]  # 완료 1개
    out = compute_recovery_signal(_checkins([5, 5, 6, 6]), missions)
    c = out["checkin_consistency"]
    assert c is not None
    # index == recovery_score(평균, 완료 미션 수, 꾸준함)
    assert out["recovery_index"] == recovery_score(5.5, 1, c)
    # 과거 단순 척도(avg*10=55)와는 다르다(미션·꾸준함 반영).
    assert out["recovery_index"] != round(5.5 * 10)


def test_checkin_consistency_in_output_and_evidence():
    """꾸준함이 출력·근거 문장에 실린다(최근 14일 중 체크인 날 수)."""
    out = compute_recovery_signal(_checkins([3, 3, 4, 7, 8, 8]))  # 연속 6일
    assert out["checkin_consistency"] == round(6 / 14 * 100, 1)
    assert any("체크인 꾸준함" in e for e in out["evidence"])
