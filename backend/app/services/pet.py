import os
import shutil
from datetime import datetime, timezone

from bson import ObjectId
from fastapi import UploadFile

from app.db.mongodb import mongodb
from app.schemas.pet import PetCreate, PetPhotoResponse, PetResponse

_UPLOAD_DIR = "uploads/pets"


def _collection():
    return mongodb.db["pets"]


async def create_pet(data: PetCreate, user_id: int) -> PetResponse:
    doc = data.model_dump()
    doc["user_id"] = user_id
    doc["memorial_mode"] = False
    doc["created_at"] = datetime.now(timezone.utc)

    result = await _collection().insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return PetResponse(**doc)


async def get_pet(pet_id: str, user_id: int | None = None) -> PetResponse | None:
    query: dict = {"_id": ObjectId(pet_id)}
    if user_id is not None:
        query["user_id"] = user_id
    doc = await _collection().find_one(query)
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id"))
    return PetResponse(**doc)


async def get_pets_by_user(user_id: int) -> list[PetResponse]:
    cursor = _collection().find({"user_id": user_id}).sort("created_at", -1)
    pets = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        pets.append(PetResponse(**doc))
    return pets


async def upload_pet_photo(pet_id: str, file: UploadFile) -> PetPhotoResponse | None:
    doc = await _collection().find_one({"_id": ObjectId(pet_id)})
    if not doc:
        return None

    os.makedirs(_UPLOAD_DIR, exist_ok=True)
    ext = os.path.splitext(file.filename or "photo.jpg")[1] or ".jpg"
    filename = f"{pet_id}{ext}"
    filepath = os.path.join(_UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    photo_url = f"/uploads/pets/{filename}"
    await _collection().update_one(
        {"_id": ObjectId(pet_id)}, {"$set": {"photo_url": photo_url}}
    )
    return PetPhotoResponse(id=pet_id, photo_url=photo_url)


async def set_memorial_mode(pet_id: str) -> PetResponse | None:
    doc = await _collection().find_one_and_update(
        {"_id": ObjectId(pet_id)},
        {"$set": {"memorial_mode": True}},
        return_document=True,
    )
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id"))
    return PetResponse(**doc)
