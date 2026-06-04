from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class LlmLogCreate(BaseModel):
    pet_id: str = Field(..., description="반려동물 ID")
    kind: str = Field(..., description="로그 종류 (message / crisis / mission 등)")
    model: str = Field(default="gemini-2.5-flash", description="사용된 모델명")
    tokens_used: Optional[int] = Field(None, description="사용 토큰 수")
    latency_ms: Optional[int] = Field(None, description="응답 지연 시간 (ms)")
    ok: bool = Field(True, description="정상 응답 여부")


class LlmLogResponse(BaseModel):
    id: str = Field(..., description="로그 ID")
    pet_id: str
    kind: str
    model: str
    tokens_used: Optional[int]
    latency_ms: Optional[int]
    ok: bool
    created_at: datetime
