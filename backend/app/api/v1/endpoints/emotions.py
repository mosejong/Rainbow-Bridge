from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.schemas.emotion import EmotionCreate, EmotionResponse
from app.services.emotion import create_emotion

router = APIRouter()
CRISIS_HOTLINE = "1393"


@router.post("", response_model=EmotionResponse, status_code=201)
async def checkin_emotion(body: EmotionCreate, user: dict = Depends(get_current_user)):
    emotion = await create_emotion(body)
    if emotion.risk_level >= 2:
        emotion.crisis_message = (
            f"많이 힘드시군요. 혼자 감당하기 어려울 때는 "
            f"자살예방상담전화 {CRISIS_HOTLINE}로 연락해 주세요. 24시간 운영합니다."
        )
    return emotion
