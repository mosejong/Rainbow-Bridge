from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class LlmLogCreate(BaseModel):
    pet_id: str = Field(..., description="반려동물 ID")
    endpoint: str = Field(..., description="호출된 API 엔드포인트")
    model: str = Field(default="gemini-2.5-flash", description="사용된 모델명")
    tokens_used: Optional[int] = Field(None, description="사용 토큰 수")

class LlmLogResponse(BaseModel):
    id: str = Field(..., description="로그 ID")
    pet_id: str
    endpoint: str
    model: str
    tokens_used: Optional[int]
    created_at: datetime
