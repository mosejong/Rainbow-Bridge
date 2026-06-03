from datetime import datetime, timezone

from bson import ObjectId

from app.db.mongodb import mongodb
from app.schemas.message import MessageCreate, MessageResponse

CRISIS_HOTLINE = "1393"

# 위기 키워드 — 반소람님 safety.py 연동 전 임시
_CRISIS_KEYWORDS = ["죽고싶", "따라가고싶", "없어지고싶", "살기싫"]

# TODO: 반소람님 provider.py 완성 후 실제 LLM 호출로 교체
_STUB_MESSAGES = {
    "warm": "함께한 시간들이 당신 마음 깊은 곳에서 언제나 따뜻하게 빛나고 있을 거예요. 그 소중한 기억들이 당신 곁에 늘 있습니다.",
    "calm": "소중한 인연은 시간이 지나도 마음속에 조용히 머뭅니다. 함께한 모든 순간이 당신의 일부로 남아 있어요.",
    "hopeful": "사랑했던 기억은 사라지지 않아요. 그 기억이 당신이 다시 일어설 수 있는 힘이 되어줄 거예요.",
}


def _collection():
    return mongodb.db["messages"]


def _is_crisis(note: str | None) -> bool:
    note_str = note or ""
    return any(kw in note_str for kw in _CRISIS_KEYWORDS)


async def create_message(data: MessageCreate) -> MessageResponse:
    is_crisis = _is_crisis(data.note)
    risk_level = 2 if is_crisis else 0

    if is_crisis:
        content = (
            f"많이 힘드시군요. 혼자 감당하기 어려울 때는 "
            f"자살예방상담전화 {CRISIS_HOTLINE}로 연락해 주세요. 24시간 운영합니다."
        )
        source = "safety"
    else:
        tone = data.tone if data.tone in _STUB_MESSAGES else "warm"
        content = _STUB_MESSAGES[tone]
        source = "stub"  # TODO: provider.py 연결 후 "local" 또는 "perso" 로 변경

    doc = {
        "pet_id": data.pet_id,
        "content": content,
        "tone": data.tone,
        "source": source,
        "risk_level": risk_level,
        "created_at": datetime.now(timezone.utc),
    }

    # 타임라인 연동용 — pets 컬렉션에 마지막 메시지 ID 기록
    result = await _collection().insert_one(doc)
    doc["id"] = str(result.inserted_id)

    await mongodb.db["pets"].update_one(
        {"_id": ObjectId(data.pet_id)},
        {"$push": {"timeline_refs": {"type": "message", "ref_id": doc["id"]}}},
    )

    response = MessageResponse(**doc)
    if is_crisis:
        response.crisis_message = content
    return response
