from fastapi import APIRouter, HTTPException

from app.schemas.mission import (
    MissionComplete,
    MissionItem,
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
    MissionItem(title="오늘 5분 산책하기", description="집 근처를 잠깐 걸어보세요.", category="activity"),
    MissionItem(title="좋아하는 음악 한 곡 듣기", description="마음이 편해지는 음악을 들어보세요.", category="rest"),
    MissionItem(title="추억 사진 한 장 꺼내보기", description="함께한 사진을 천천히 바라보세요.", category="remembrance"),
    MissionItem(title="따뜻한 음료 한 잔 마시기", description="따뜻한 차를 우려 천천히 마셔보세요.", category="rest"),
    MissionItem(title="오늘 감정 일기 한 줄 쓰기", description="오늘 느낀 감정을 짧게 적어보세요.", category="record"),
    MissionItem(title="창문 열고 바람 맞기", description="잠시 창문을 열어 바깥 공기를 느껴보세요.", category="rest"),
    MissionItem(title="가까운 사람에게 안부 전하기", description="가족이나 친구에게 짧게 안부를 전해보세요.", category="connection"),
]


@router.post("/recommend", response_model=MissionRecommendResponse)
async def recommend_missions(body: MissionRecommendRequest):
    """AI 맞춤 미션 추천 — 반소람님 로직 연결 전 스텁."""
    count = 3 if (body.emotion_score or 5) >= 5 else 2
    return MissionRecommendResponse(
        missions=_RECOMMEND_POOL[:count],
        source="stub",
    )
