from datetime import datetime, timezone
from app.db.mongodb import mongodb
from app.schemas.emotion import EmotionCreate, EmotionResponse

_RISK_KEYWORDS_L2 = ["없어지고싶", "살기싫", "포기"]
_RISK_KEYWORDS_L3 = ["죽고싶", "따라가고싶"]

def _collection():
    return mongodb.db["emotions"]

def _detect_risk(score: int, note: str | None) -> int:
    if note:
        if any(kw in note for kw in _RISK_KEYWORDS_L3):
            return 3
        if any(kw in note for kw in _RISK_KEYWORDS_L2):
            return 2
    if score <= 1:
        return 2
    if score <= 3:
        return 1
    return 0

async def create_emotion(data: EmotionCreate) -> EmotionResponse:
    risk_level = _detect_risk(data.score, data.note)
    doc = data.model_dump()
    doc["risk_level"] = risk_level
    doc["created_at"] = datetime.now(timezone.utc)
    result = await _collection().insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return EmotionResponse(**doc)
