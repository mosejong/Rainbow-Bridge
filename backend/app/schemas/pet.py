from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MemoryItem(BaseModel):
    keyword: str = Field(..., description="추억 키워드 (예: 공원산책)")
    detail: str = Field("", description="구체적인 추억 내용 (비어있어도 됨)")


class PetCreate(BaseModel):
    name: str = Field(..., description="반려동물 이름")
    species: str = Field(..., description="종 (예: 강아지, 고양이)")
    breed: Optional[str] = Field(None, description="품종")
    period: Optional[str] = Field(
        None, description="함께한 기간 문자열 (예: 2018-01-01 ~ 2026-06-01)"
    )
    memories: Optional[list[MemoryItem]] = Field(None, description="추억 목록")
    photo_url: Optional[str] = Field(None, description="사진 URL")


class PetPhotoResponse(BaseModel):
    id: str = Field(..., description="반려동물 ID")
    photo_url: str = Field(..., description="저장된 사진 URL")


class PetResponse(BaseModel):
    id: str = Field(..., description="반려동물 ID")
    name: str
    species: str
    breed: Optional[str]
    period: Optional[str]
    memories: Optional[list[MemoryItem]]
    photo_url: Optional[str]
    memorial_mode: bool = Field(False, description="추모 모드 전환 여부")
    created_at: datetime
