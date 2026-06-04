from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.pet import PetCreate, PetPhotoResponse, PetResponse
from app.services.pet import create_pet, get_pet, set_memorial_mode, upload_pet_photo

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


@router.post("/{pet_id}/photo", response_model=PetPhotoResponse)
async def upload_photo(pet_id: str, file: UploadFile = File(...)):
    result = await upload_pet_photo(pet_id, file)
    if not result:
        raise HTTPException(status_code=404, detail="반려동물 정보를 찾을 수 없습니다.")
    return result


@router.patch("/{pet_id}/memorial", response_model=PetResponse)
async def switch_memorial(pet_id: str):
    pet = await set_memorial_mode(pet_id)
    if not pet:
        raise HTTPException(status_code=404, detail="반려동물 정보를 찾을 수 없습니다.")
    return pet
