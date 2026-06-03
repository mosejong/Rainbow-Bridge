from datetime import datetime, timezone

from app.db.mongodb import mongodb
from app.schemas.emotion import EmotionCreate, EmotionResponse

# 위기 키워드 — 추후 반소람님 ai/llm/safety.py 로 교체 예정
_CRISIS_KEYWORDS = ["죽고싶", "따라가고싶", "없어지고싶", "살기싫"]
_CAUTION_KEYWORDS = ["포기", "힘들어", "지쳤어"]


def _collection():
    return mongodb.db["emotions"]


def _detect_risk(score: int, note: str | None) -> int:
    """위기 수준 반환 (0=정상, 1=주의, 2=위기)."""
    note_str = note or ""
    if any(kw in note_str for kw in _CRISIS_KEYWORDS):
        return 2
    if score <= 2:
        return 1
    if any(kw in note_str for kw in _CAUTION_KEYWORDS):
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
