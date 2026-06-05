from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.schemas.message import MessageCreate, MessageResponse
from app.services.message import create_message, get_latest_message

router = APIRouter()


@router.get("/{pet_id}/latest", response_model=MessageResponse)
async def read_latest_message(pet_id: str, user: dict = Depends(get_current_user)):
    """반려동물의 가장 최근 추모 메시지 조회."""
    msg = await get_latest_message(pet_id)
    if not msg:
        raise HTTPException(status_code=404, detail="생성된 메시지가 없습니다.")
    return msg


@router.post("", response_model=MessageResponse, status_code=201)
async def generate_message(body: MessageCreate, user: dict = Depends(get_current_user)):
    return await create_message(body)
