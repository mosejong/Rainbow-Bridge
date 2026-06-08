from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.db.rdb import get_db
from app.schemas.pet_diary import VetAdviceCreate, VetAdviceResponse
from app.services.vet_advice import create_vet_advice

router = APIRouter()


@router.post("/{diary_id}/advice", response_model=VetAdviceResponse, status_code=201)
async def add_vet_advice(
    diary_id: int,
    body: VetAdviceCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
):
    try:
        return await create_vet_advice(db, diary_id, user["user_id"], body)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
