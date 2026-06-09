"""리포트 집계 보조 로직 단위 테스트 — DB 없이 순수 함수만 검증."""

from __future__ import annotations

from datetime import datetime, timezone

from app.services.report import _bucket_access_counts


def _dt(day: int) -> datetime:
    return datetime(2026, 6, day, 9, 0, tzinfo=timezone.utc)


def test_bucket_groups_by_day_oldest_first():
    """같은 날 접속은 합산, 날짜 오름차순(오래된→최근)으로 반환."""
    ts = [_dt(1), _dt(1), _dt(2), _dt(4), _dt(4), _dt(4)]
    assert _bucket_access_counts(ts) == [2, 1, 3]


def test_bucket_handles_iso_strings():
    """datetime 아닌 ISO 문자열도 앞 10자(날짜)로 버킷팅."""
    ts = [
        "2026-06-01T08:00:00+00:00",
        "2026-06-01T20:00:00+00:00",
        "2026-06-03T00:00:00",
    ]
    assert _bucket_access_counts(ts) == [2, 1]


def test_bucket_empty():
    assert _bucket_access_counts([]) == []


def test_bucket_unordered_input_sorted_by_date():
    """입력 순서가 뒤섞여도 날짜순 정렬."""
    ts = [_dt(5), _dt(1), _dt(3)]
    assert _bucket_access_counts(ts) == [1, 1, 1]
