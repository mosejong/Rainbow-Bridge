from fastapi import APIRouter, HTTPException

from app.schemas.mission import (
    MissionComplete,
    MissionRecommendRequest,
    MissionRecommendResponse,
    MissionResponse,
)
from app.services.mission import complete_mission, create_default_missions, get_missions

router = APIRouter()


@router.get("/{pet_id}", response_model=list[MissionResponse])
async def list_missions(pet_id: str):
    missions = await get_missions(pet_id)
    if not missions:
        missions = await create_default_missions(pet_id)
    return missions


@router.patch("/{mission_id}/complete", response_model=MissionResponse)
async def done_mission(mission_id: str, body: MissionComplete):
    mission = await complete_mission(mission_id)
    if not mission:
        raise HTTPException(status_code=404, detail="미션을 찾을 수 없습니다.")
    return mission


# TODO: 반소람님 미션 추천 로직 연결 후 서비스 레이어로 이동
_RECOMMEND_POOL = [
    "오늘 5분 산책하기",
    "좋아하는 음악 한 곡 듣기",
    "추억 사진 한 장 꺼내보기",
    "따뜻한 음료 한 잔 마시기",
    "오늘 감정 일기 한 줄 쓰기",
    "창문 열고 바람 맞기",
    "가까운 사람에게 안부 전하기",
]


@router.post("/recommend", response_model=MissionRecommendResponse)
async def recommend_missions(body: MissionRecommendRequest):
    """AI 맞춤 미션 추천 — 반소람님 로직 연결 전 스텁."""
    count = 3 if (body.emotion_score or 5) >= 5 else 2
    return MissionRecommendResponse(
        missions=_RECOMMEND_POOL[:count],
        source="stub",
    )
