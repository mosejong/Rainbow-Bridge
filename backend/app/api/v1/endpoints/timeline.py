"""타임라인 엔드포인트 — 반려동물별 추모 기록 조회."""

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.services.timeline import get_timeline

router = APIRouter()


@router.get("/{pet_id}", tags=["timeline"])
async def read_timeline(pet_id: str, user: dict = Depends(get_current_user)):
    """반려동물의 추모 기록(메시지·감정·미션·영상)을 최신순으로 합쳐 반환. 없으면 빈 배열."""
    return await get_timeline(pet_id)
