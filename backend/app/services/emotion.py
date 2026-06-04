import sys
from datetime import datetime, timezone
from app.db.mongodb import mongodb
from app.schemas.emotion import EmotionCreate, EmotionResponse

sys.path.append("/home/kyh/Rainbow-Bridge")
from ai.llm.safety import assess_crisis


def _collection():
    return mongodb.db["emotions"]


async def create_emotion(data: EmotionCreate) -> EmotionResponse:
    result = assess_crisis(data.note or "")
    risk_level = int(result.risk_level)

    doc = data.model_dump()
    doc["risk_level"] = risk_level
    doc["created_at"] = datetime.now(timezone.utc)
    db_result = await _collection().insert_one(doc)
    doc["id"] = str(db_result.inserted_id)
    return EmotionResponse(**doc)
