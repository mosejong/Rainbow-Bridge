from fastapi import APIRouter

from app.schemas.tts import TtsCreate, TtsResponse
from app.services.tts import generate_tts

router = APIRouter()


@router.post("", response_model=TtsResponse, status_code=201)
async def synthesize_tts(body: TtsCreate):
    return await generate_tts(body)
