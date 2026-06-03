from typing import Optional

from fastapi import APIRouter

from app.schemas.report import ReportResponse
from app.services.report import get_report

router = APIRouter()


@router.get("/{pet_id}", response_model=ReportResponse)
async def read_report(pet_id: str, period: Optional[str] = None):
    return await get_report(pet_id, period)
