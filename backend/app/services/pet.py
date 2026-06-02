from datetime import datetime, timezone

from bson import ObjectId

from app.db.mongodb import mongodb
from app.schemas.pet import PetCreate, PetResponse


def _collection():
    return mongodb.db["pets"]


async def create_pet(data: PetCreate) -> PetResponse:
    doc = data.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)

    result = await _collection().insert_one(doc)
    doc["id"] = str(result.inserted_id)
    return PetResponse(**doc)


async def get_pet(pet_id: str) -> PetResponse | None:
    doc = await _collection().find_one({"_id": ObjectId(pet_id)})
    if not doc:
        return None
    doc["id"] = str(doc.pop("_id"))
    return PetResponse(**doc)
