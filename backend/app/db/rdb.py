"""SQLite RDB 연결 — 로그인/회원 관리용.

MongoDB(motor)는 반려동물·감정·메시지 등 서비스 데이터용.
SQLite(SQLAlchemy)는 사용자 인증(users 테이블)용으로 분리.
"""

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite+aiosqlite:///./rainbow_bridge.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
