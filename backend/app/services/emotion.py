from datetime import datetime, timezone

from ai.llm.safety import (
    detect_crisis as assess_crisis,
)  # assess_crisis PR 머지 후 교체

from app.db.mongodb import mongodb
from app.schemas.emotion import EmotionCreate, EmotionResponse

CRISIS_HOTLINE = "1393"


def _collection():
    return mongodb.db["emotions"]


async def create_emotion(data: EmotionCreate) -> EmotionResponse:
    # 반소람님 assess_crisis() — 규칙 레이어(L0). 나중에 LLM 레이어 추가해도 이 호출은 그대로.
    crisis = assess_crisis(data.note or "")
    risk_level = int(crisis.risk_level)

    doc = data.model_dump()
    doc["risk_level"] = risk_level
    doc["created_at"] = datetime.now(timezone.utc)

    result = await _collection().insert_one(doc)
    doc["id"] = str(result.inserted_id)

    response = EmotionResponse(**doc)
    if crisis.hotline_required:
        response.crisis_message = (
            f"많이 힘드시군요. 혼자 감당하기 어려울 때는 "
            f"자살예방상담전화 {CRISIS_HOTLINE}로 연락해 주세요. 24시간 운영합니다."
        )
    return response
