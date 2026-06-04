from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.rdb import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.auth import login, register

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=201)
async def register_user(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await register(db, body)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login_user(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        return await login(db, body.email, body.password)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
