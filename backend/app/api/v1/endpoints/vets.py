from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.rdb import get_db
from app.schemas.vet import (
    VetLoginRequest,
    VetRegisterRequest,
    VetResponse,
    VetTokenResponse,
)
from app.services.vet import login_vet, register_vet

router = APIRouter()


@router.post("/register", response_model=VetResponse, status_code=201)
async def register_vet_user(
    body: VetRegisterRequest, db: AsyncSession = Depends(get_db)
):
    try:
        return await register_vet(db, body)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login", response_model=VetTokenResponse)
async def login_vet_user(body: VetLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await login_vet(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
