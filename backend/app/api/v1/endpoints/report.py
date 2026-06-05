from typing import Optional

from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.schemas.report import ReportResponse
from app.services.report import get_report

router = APIRouter()


@router.get("/{pet_id}", response_model=ReportResponse)
async def read_report(
    pet_id: str, period: Optional[str] = None, user: dict = Depends(get_current_user)
):
    return await get_report(pet_id, period)
