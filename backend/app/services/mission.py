from datetime import datetime, timezone

from bson import ObjectId

from app.db.mongodb import mongodb
from app.schemas.mission import MissionResponse

# 기본 미션 풀 — 반소람님 AI 추천 로직으로 교체 예정
_DEFAULT_MISSIONS = [
    ("오늘 산책하기", "15분이라도 밖에 나가 바람을 쐬어보세요."),
    ("좋아하는 음악 듣기", "마음이 편한 음악을 들으며 잠시 쉬어가세요."),
    ("소중한 사람에게 연락하기", "가까운 가족이나 친구에게 안부를 전해보세요."),
    ("따뜻한 음료 마시기", "따뜻한 차 한 잔으로 마음을 달래보세요."),
    ("반려동물과의 추억 기록하기", "소중한 기억을 글이나 사진으로 남겨보세요."),
]


def _collection():
    return mongodb.db["missions"]


async def get_missions(pet_id: str) -> list[MissionResponse]:
    cursor = _collection().find({"pet_id": pet_id}).sort("created_at", -1)
    results = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        results.append(MissionResponse(**doc))
    return results


async def create_default_missions(pet_id: str) -> list[MissionResponse]:
    now = datetime.now(timezone.utc)
    docs = [
        {
            "pet_id": pet_id,
            "title": title,
            "description": desc,
            "completed": False,
            "created_at": now,
            "completed_at": None,
        }
        for title, desc in _DEFAULT_MISSIONS
    ]
    result = await _collection().insert_many(docs)
    for doc, oid in zip(docs, result.inserted_ids):
        doc["id"] = str(oid)
    return [MissionResponse(**doc) for doc in docs]


async def complete_mission(mission_id: str) -> MissionResponse | None:
    now = datetime.now(timezone.utc)
    doc = await _collection().find_one_and_update(
        {"_id": ObjectId(mission_id)},
        {"$set": {"completed": True, "completed_at": now}},
        return_document=True,
    )
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id"))
    return MissionResponse(**doc)
