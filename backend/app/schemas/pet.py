from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PetCreate(BaseModel):
    name: str = Field(..., description="반려동물 이름")
    species: str = Field(..., description="종 (예: 강아지, 고양이)")
    breed: Optional[str] = Field(None, description="품종")
    years_together: float = Field(..., description="함께한 기간 (년)")
    memories: Optional[str] = Field(None, description="기억·추억 메모")
    photo_url: Optional[str] = Field(None, description="사진 URL")


class PetResponse(BaseModel):
    id: str = Field(..., description="반려동물 ID")
    name: str
    species: str
    breed: Optional[str]
    years_together: float
    memories: Optional[str]
    photo_url: Optional[str]
    created_at: datetime
