from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.db.mongodb import mongodb

router = APIRouter()


class PlayLogCreate(BaseModel):
    pet_id: str
    event_type: str = "tts"


@router.post("", status_code=201)
async def log_play(body: PlayLogCreate, user: dict = Depends(get_current_user)):
    await mongodb.db["play_logs"].insert_one(
        {
            "pet_id": body.pet_id,
            "event_type": body.event_type,
            "played_at": datetime.now(timezone.utc),
        }
    )
    return {"ok": True}
