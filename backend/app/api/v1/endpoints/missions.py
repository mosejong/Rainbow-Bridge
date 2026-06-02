from fastapi import APIRouter, HTTPException

from app.schemas.mission import MissionComplete, MissionResponse
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
