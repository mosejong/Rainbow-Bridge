from fastapi import APIRouter, Depends, HTTPException

from app.core.deps import get_current_user
from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.tts import TtsCreate, TtsResponse
from app.services.message import create_message, get_latest_message
from app.services.tts import generate_tts

router = APIRouter()


@router.post("/tts", response_model=TtsResponse, status_code=201)
async def synthesize_message_tts(
    body: TtsCreate, user: dict = Depends(get_current_user)
):
    """추모 메시지 낭독 TTS (프론트가 호출하는 경로). 합성 로직은 services/tts 공통."""
    return await generate_tts(body)


@router.get("/{pet_id}/latest", response_model=MessageResponse)
async def read_latest_message(pet_id: str, user: dict = Depends(get_current_user)):
    """반려동물의 가장 최근 추모 메시지 조회."""
    msg = await get_latest_message(pet_id)
    if not msg:
        raise HTTPException(status_code=404, detail="생성된 메시지가 없습니다.")
    return msg


@router.post("", response_model=MessageResponse, status_code=201)
async def generate_message(body: MessageCreate, user: dict = Depends(get_current_user)):
    body.guardian_nickname = user.get("nickname")
    return await create_message(body)
