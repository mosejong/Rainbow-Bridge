from datetime import datetime, timezone


from app.db.mongodb import mongodb
from app.schemas.emotion import EmotionCreate, EmotionResponse

# 위기 감지 키워드 — 반소람님 AI 로직으로 교체 예정
_RISK_KEYWORDS = ["죽고싶", "따라가고싶", "없어지고싶", "살기싫", "포기"]


def _collection():
    return mongodb.db["emotions"]


def _detect_risk(score: int, note: str | None) -> bool:
    if score <= 2:
        return True
    if note and any(kw in note for kw in _RISK_KEYWORDS):
        return True
    return False


async def create_emotion(data: EmotionCreate) -> EmotionResponse:
    risk_flag = _detect_risk(data.score, data.note)

    doc = data.model_dump()
    doc["risk_flag"] = risk_flag
    doc["created_at"] = datetime.now(timezone.utc)

    result = await _collection().insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return EmotionResponse(**doc)
