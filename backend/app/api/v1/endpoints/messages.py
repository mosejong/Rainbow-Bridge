from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.schemas.message import MessageCreate, MessageResponse
from app.services.message import create_message

router = APIRouter()


@router.post("", response_model=MessageResponse, status_code=201)
async def generate_message(body: MessageCreate, user: dict = Depends(get_current_user)):
    return await create_message(body)
