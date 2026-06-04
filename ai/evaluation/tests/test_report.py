"""⑧ build_report 집계 테스트."""

from __future__ import annotations

from ..report import build_report


def test_empty_report():
    r = build_report("pet1")
    assert r["usage"]["total_calls"] == 0
    assert r["mission_completion_rate"] is None


def test_usage_and_completion():
    logs = [{"kind": "message"}, {"kind": "message"}, {"kind": "crisis"}]
    missions = [{"done": True}, {"done": False}, {"done": True}, {"done": False}]
    r = build_report("pet1", "2026-06", llm_logs=logs, missions=missions)
    assert r["usage"]["total_calls"] == 3
    assert r["usage"]["by_kind"]["message"] == 2
    assert r["mission_completion_rate"] == 0.5


def test_emotion_trend_sorted():
    checkins = [
        {"created_at": "2026-06-02", "mood": 3},
        {"created_at": "2026-06-01", "mood": 1},
    ]
    r = build_report("pet1", emotion_checkins=checkins)
    moods = [row["mood"] for row in r["emotion_trend"]]
    assert moods == [1, 3]  # created_at 오름차순 정렬
