from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MissionResponse(BaseModel):
    id: str
    pet_id: str
    title: str
    description: str
    completed: bool
    created_at: datetime
    completed_at: Optional[datetime]


class MissionComplete(BaseModel):
    completed: bool = True


class MissionRecommendRequest(BaseModel):
    pet_id: str
    emotion_score: Optional[int] = None
    day_since: Optional[int] = None


class MissionRecommendResponse(BaseModel):
    missions: list[str]
    source: str = "stub"
