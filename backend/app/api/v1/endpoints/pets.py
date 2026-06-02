from fastapi import APIRouter, HTTPException

from app.schemas.pet import PetCreate, PetResponse
from app.services.pet import create_pet, get_pet

router = APIRouter()


@router.post("", response_model=PetResponse, status_code=201)
async def register_pet(body: PetCreate):
    return await create_pet(body)


@router.get("/{pet_id}", response_model=PetResponse)
async def read_pet(pet_id: str):
    pet = await get_pet(pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="반려동물 정보를 찾을 수 없습니다.")
    return pet
