from fastapi import APIRouter

from app.schemas.message import MessageCreate, MessageResponse
from app.services.message import create_message

router = APIRouter()


@router.post("", response_model=MessageResponse, status_code=201)
async def generate_message(body: MessageCreate):
    return await create_message(body)
