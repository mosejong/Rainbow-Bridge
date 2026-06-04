from typing import Any, Optional

from pydantic import BaseModel, Field


class EmotionTrend(BaseModel):
    created_at: str
    score: int


class ReportResponse(BaseModel):
    pet_id: str
    period: Optional[str] = Field(None, description="집계 기간 (예: 2026-06)")
    usage: dict[str, Any] = Field(default_factory=dict, description="LLM 사용 횟수")
    emotion_trend: list[EmotionTrend] = Field(
        default_factory=list, description="감정 추이"
    )
    mission_completion_rate: Optional[float] = Field(
        None, description="미션 완료율 0~1"
    )
    revisit: Optional[int] = Field(None, description="재방문 횟수 (추후 추가)")
