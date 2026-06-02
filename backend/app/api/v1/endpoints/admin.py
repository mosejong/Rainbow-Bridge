"""어드민 엔드포인트 — LLM 사용 현황 집계."""

from fastapi import APIRouter

from app.db.mongodb import mongodb

router = APIRouter()


@router.get("/usage", tags=["admin"])
async def get_usage():
    """llm_logs 컬렉션 기반 LLM 호출 현황을 반환합니다.

    llm_logs 도큐먼트 예시:
        {"model": "gpt-4o", "total_tokens": 512, "prompt": "...", ...}
    """
    collection = mongodb.db["llm_logs"]

    # 전체 호출 수
    total_calls = await collection.count_documents({})

    # 모델별 집계 (호출 수 + 토큰 합계)
    pipeline = [
        {
            "$group": {
                "_id": "$model",
                "calls": {"$sum": 1},
                "tokens": {"$sum": "$total_tokens"},
            }
        }
    ]
    by_model = {}
    total_tokens = 0
    async for doc in collection.aggregate(pipeline):
        model_name = doc["_id"] or "unknown"
        by_model[model_name] = {"calls": doc["calls"], "tokens": doc["tokens"]}
        total_tokens += doc["tokens"]

    # 최근 20개 로그
    cursor = collection.find(
        {},
        sort=[("_id", -1)],
    ).limit(20)
    recent_logs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        recent_logs.append(doc)

    return {
        "total_calls": total_calls,
        "total_tokens": total_tokens,
        "by_model": by_model,
        "recent_logs": recent_logs,
    }
