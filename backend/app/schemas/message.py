from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    pet_id: str = Field(..., description="반려동물 ID")
    tone: str = Field("warm", description="메시지 톤 (warm·calm·hopeful)")
    emotion_score: Optional[int] = Field(None, ge=1, le=10, description="감정 점수")
    note: Optional[str] = Field(None, description="보호자 메모")
    consent: bool = Field(False, description="1인칭 편지 동의 여부")


class MessageResponse(BaseModel):
    id: str
    pet_id: str
    content: str = Field(..., description="생성된 추모 메시지")
    tone: str
    source: str = Field(..., description="생성 출처 (local·perso·stub)")
    risk_level: int = Field(0, description="위기 수준 (0=정상, 2=위기 시 1393 우선)")
    crisis_message: Optional[str] = Field(None, description="위기 시 1393 안내")
    created_at: datetime
