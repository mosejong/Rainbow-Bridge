from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pet_diary import PetDiary, VetAdvice
from app.schemas.pet_diary import VetAdviceCreate, VetAdviceResponse


async def create_vet_advice(
    db: AsyncSession, diary_id: int, vet_id: int, data: VetAdviceCreate
) -> VetAdviceResponse:
    diary = await db.scalar(select(PetDiary).where(PetDiary.id == diary_id))
    if not diary:
        raise ValueError("일기 기록을 찾을 수 없습니다.")

    advice = VetAdvice(
        diary_id=diary_id,
        vet_id=vet_id,
        content=data.content,
        prescription=data.prescription,
    )
    db.add(advice)
    await db.commit()
    await db.refresh(advice)
    return VetAdviceResponse.model_validate(advice)
