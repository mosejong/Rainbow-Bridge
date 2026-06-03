from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class EmotionCreate(BaseModel):
    pet_id: str = Field(..., description="반려동물 ID")
    score: int = Field(
        ..., ge=1, le=10, description="감정 점수 (1=매우 힘듦, 10=괜찮음)"
    )
    note: Optional[str] = Field(None, description="감정 메모")

class EmotionResponse(BaseModel):
    id: str
    pet_id: str
    score: int
    note: Optional[str]
    risk_level: int = Field(..., description="위기 수준 (0=정상, 1=우려, 2=경고, 3=긴급)")
    created_at: datetime
    crisis_message: Optional[str] = Field(
        None, description="위기 감지 시 1393 안내 메시지 (risk_level >= 2일 때)"
    )
