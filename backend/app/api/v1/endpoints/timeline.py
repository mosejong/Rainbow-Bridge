"""타임라인 엔드포인트 — 반려동물별 추모 기록 조회."""

from fastapi import APIRouter, HTTPException

from app.db.mongodb import mongodb

router = APIRouter()


@router.get("/{pet_id}", tags=["timeline"])
async def get_timeline(pet_id: str):
    """특정 반려동물의 타임라인 기록을 최신순으로 반환합니다."""
    cursor = mongodb.db["timeline"].find(
        {"pet_id": pet_id},
        sort=[("_id", -1)],
    )
    records = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        records.append(doc)

    if not records:
        raise HTTPException(status_code=404, detail="해당 반려동물의 타임라인 기록이 없습니다.")

    return records
