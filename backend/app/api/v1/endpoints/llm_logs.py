from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from app.db.mongodb import mongodb
from app.schemas.llm_log import LlmLogCreate

router = APIRouter()
COLLECTION = "llm_logs"

@router.post("", status_code=201)
async def create_llm_log(payload: LlmLogCreate):
    """LLM 호출 로그를 llm_logs 컬렉션에 저장합니다."""
    doc = payload.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    result = await mongodb.db[COLLECTION].insert_one(doc)
    if not result.inserted_id:
        raise HTTPException(status_code=500, detail="로그 저장 실패")
    return {"inserted_id": str(result.inserted_id), "message": "로그 저장 완료"}

@router.get("")
async def get_llm_logs(pet_id: str | None = None, limit: int = 20):
    """llm_logs 조회 (pet_id 필터 옵션)."""
    query = {"pet_id": pet_id} if pet_id else {}
    cursor = mongodb.db[COLLECTION].find(query).sort("created_at", -1).limit(limit)
    logs = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        logs.append(doc)
    return {"logs": logs, "count": len(logs)}
