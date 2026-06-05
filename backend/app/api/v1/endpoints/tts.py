from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.schemas.tts import TtsCreate, TtsResponse
from app.services.tts import generate_tts

router = APIRouter()


@router.post("", response_model=TtsResponse, status_code=201)
async def synthesize_tts(body: TtsCreate, user: dict = Depends(get_current_user)):
    return await generate_tts(body)
