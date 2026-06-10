import app.core.ai_path  # noqa: F401
from datetime import datetime, timezone

from bson import ObjectId

from ai.evaluation.logs import (
    COLLECTION as LLM_LOGS,
    KIND_MISSION,
    alog_llm_call,
    measure_latency,
)
from ai.llm.config import get_config
from ai.llm.mission import recommend as _ai_recommend
from ai.llm.provider import generate
from app.db.mongodb import mongodb
from app.db.redis_client import get_recent_emotions
from app.schemas.mission import MissionResponse


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
    emotion_score = None
    try:
        records = await get_recent_emotions(pet_id)
        if records:
            emotion_score = records[0]["score"]
    except Exception:
        pass

    cfg = get_config()
    log_ok = True
    timer = None
    try:
        with measure_latency() as timer:
            missions_raw = _ai_recommend(
                emotion_score=emotion_score,
                generate=generate,
                count=5,
            )
    except Exception:
        log_ok = False
        missions_raw = [
            {
                "title": "오늘 산책하기",
                "description": "15분이라도 밖에 나가 바람을 쐬어보세요.",
                "category": "activity",
                "rationale": None,
            },
            {
                "title": "좋아하는 음악 듣기",
                "description": "마음이 편한 음악을 들으며 잠시 쉬어가세요.",
                "category": "rest",
                "rationale": None,
            },
            {
                "title": "소중한 사람에게 연락하기",
                "description": "가까운 가족이나 친구에게 안부를 전해보세요.",
                "category": "connection",
                "rationale": None,
            },
            {
                "title": "따뜻한 음료 마시기",
                "description": "따뜻한 차 한 잔으로 마음을 달래보세요.",
                "category": "rest",
                "rationale": None,
            },
            {
                "title": "반려동물과의 추억 기록하기",
                "description": "소중한 기억을 글이나 사진으로 남겨보세요.",
                "category": "record",
                "rationale": None,
            },
        ]
    finally:
        try:
            await alog_llm_call(
                mongodb.db[LLM_LOGS],
                kind=KIND_MISSION,
                pet_id=pet_id,
                model=cfg.model,
                provider=cfg.provider,
                latency_ms=timer.ms if timer else 0,
                ok=log_ok,
            )
        except Exception:
            pass

    now = datetime.now(timezone.utc)
    docs = [
        {
            "pet_id": pet_id,
            "title": m["title"],
            "description": m.get("description", ""),
            "category": m.get("category", ""),
            "rationale": m.get("rationale"),
            "completed": False,
            "created_at": now,
            "completed_at": None,
        }
        for m in missions_raw
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
