from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class PetDiaryCreate(BaseModel):
    pet_id: str
    record_date: date
    meal_amount: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="식사량 0.0~1.0"
    )
    meal_note: Optional[str] = Field(None, max_length=200)
    symptoms: Optional[str] = None
    walked: bool = False
    walk_minutes: Optional[int] = Field(None, ge=0)
    weight_kg: Optional[float] = Field(None, ge=0.0)
    notes: Optional[str] = None


class PetDiaryResponse(BaseModel):
    id: int
    pet_id: str
    user_id: int
    record_date: date
    meal_amount: Optional[float]
    meal_note: Optional[str]
    symptoms: Optional[str]
    walked: bool
    walk_minutes: Optional[int]
    weight_kg: Optional[float]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class VetAdviceCreate(BaseModel):
    content: str
    prescription: Optional[str] = None


class VetAdviceResponse(BaseModel):
    id: int
    diary_id: int
    vet_id: int
    content: str
    prescription: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
