import os
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse, UserResponse
from app.db.mongodb import mongodb

_pwd_ctx = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,
    bcrypt__truncate_error=False,
)

_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
if not _SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY 환경변수가 설정되지 않았습니다.")
_ALGORITHM = "HS256"
_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))


def _hash_password(password: str) -> str:
    return _pwd_ctx.hash(password.encode("utf-8")[:72].decode("utf-8", errors="ignore"))


def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd_ctx.verify(
        plain.encode("utf-8")[:72].decode("utf-8", errors="ignore"), hashed
    )


def _create_token(user_id: int, email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": str(user_id), "email": email, "exp": expire},
        _SECRET_KEY,
        algorithm=_ALGORITHM,
    )


async def register(db: AsyncSession, data: RegisterRequest) -> UserResponse:
    existing = await db.scalar(select(User).where(User.email == data.email))
    if existing:
        raise ValueError("이미 사용 중인 이메일입니다.")

    user = User(
        email=data.email,
        password_hash=_hash_password(data.password),
        nickname=data.nickname,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


async def login(db: AsyncSession, email: str, password: str) -> TokenResponse:
    user = await db.scalar(select(User).where(User.email == email))
    if not user:
        raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다.")
    try:
        verified = _verify_password(password, user.password_hash)
    except Exception:
        verified = False
    if not verified:
        raise ValueError("이메일 또는 비밀번호가 올바르지 않습니다.")

    token = _create_token(user.id, user.email)
    await mongodb.db["access_logs"].insert_one(
        {
            "user_id": user.id,
            "email": user.email,
            "accessed_at": datetime.now(timezone.utc),
        }
    )
    return TokenResponse(access_token=token)
