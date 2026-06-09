"""회복 게이트(content_unlocked) 로직 단위 테스트.

실제 Redis / MongoDB 없이 순수 계산 로직만 검증합니다.
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.services.emotion import get_recovery


def _make_records(scores: list[int], risks: list[int]) -> list[dict]:
    """테스트용 감정 기록 생성. 최신 기록이 인덱스 0."""
    return [
        {"score": s, "risk_level": r, "created_at": "2026-06-09T00:00:00+00:00"}
        for s, r in zip(scores, risks)
    ]


@pytest.mark.asyncio
async def test_gate_unlocked_when_conditions_met():
    """3회 이상 + 평균 5점 이상 + risk 1 이하 + 회복 추세 → 언락."""
    records = _make_records(
        scores=[8, 7, 6, 5, 6],
        risks=[0, 0, 0, 1, 0],
    )
    with patch(
        "app.services.emotion.get_recent_emotions", new=AsyncMock(return_value=records)
    ):
        result = await get_recovery("pet_test_1")

    assert result.content_unlocked is True


@pytest.mark.asyncio
async def test_gate_locked_when_checkins_too_few():
    """체크인 2회 이하면 잠금 유지."""
    records = _make_records(scores=[9, 8], risks=[0, 0])
    with patch(
        "app.services.emotion.get_recent_emotions", new=AsyncMock(return_value=records)
    ):
        result = await get_recovery("pet_test_2")

    assert result.content_unlocked is False


@pytest.mark.asyncio
async def test_gate_locked_when_avg_score_low():
    """평균 점수 5점 미만이면 잠금 유지."""
    records = _make_records(scores=[3, 4, 2, 3, 4], risks=[0, 0, 0, 0, 0])
    with patch(
        "app.services.emotion.get_recent_emotions", new=AsyncMock(return_value=records)
    ):
        result = await get_recovery("pet_test_3")

    assert result.content_unlocked is False


@pytest.mark.asyncio
async def test_gate_locked_when_crisis():
    """최근 risk_level 2 이상이면 잠금 유지."""
    records = _make_records(
        scores=[8, 7, 6, 5, 7],
        risks=[2, 0, 0, 0, 0],  # 최신 기록 risk=2
    )
    with patch(
        "app.services.emotion.get_recent_emotions", new=AsyncMock(return_value=records)
    ):
        result = await get_recovery("pet_test_4")

    assert result.content_unlocked is False


@pytest.mark.asyncio
async def test_gate_locked_when_worsening_trend():
    """주의 필요 추세이면 잠금 유지."""
    # 최근이 더 낮아지는 패턴 → "주의 필요"
    records = _make_records(
        scores=[3, 3, 7, 8, 9],  # 최신(인덱스0)이 낮음
        risks=[0, 0, 0, 0, 0],
    )
    with patch(
        "app.services.emotion.get_recent_emotions", new=AsyncMock(return_value=records)
    ):
        result = await get_recovery("pet_test_5")

    assert result.content_unlocked is False


@pytest.mark.asyncio
async def test_gate_no_data():
    """데이터 없으면 잠금 유지."""
    with patch(
        "app.services.emotion.get_recent_emotions", new=AsyncMock(return_value=[])
    ):
        result = await get_recovery("pet_test_empty")

    assert result.content_unlocked is False
