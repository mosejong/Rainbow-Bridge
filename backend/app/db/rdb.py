"""RDB 연결 — 로그인/회원 관리 + 1단계 일기·수의사 데이터용.

MongoDB(motor)는 반려동물·감정·메시지 등 서비스 데이터용.
RDB(SQLAlchemy)는 인증(users·vets) + 일기(pet_diaries·vet_advice) 테이블용.

DATABASE_URL 환경변수:
  미설정 → SQLite (개발/로컬)
  설정 시 → postgresql+asyncpg://... (운영)
"""

import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/rainbow_bridge.db")

_connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)
engine = create_async_engine(DATABASE_URL, echo=False, connect_args=_connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    if DATABASE_URL.startswith("sqlite"):
        import pathlib
        db_path = DATABASE_URL.split("///")[-1]
        pathlib.Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # 모델을 임포트해야 Base.metadata에 테이블이 등록됨
    import app.models.user  # noqa: F401
    import app.models.vet  # noqa: F401
    import app.models.pet_diary  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
