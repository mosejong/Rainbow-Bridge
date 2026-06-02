"""레인보우 브릿지 백엔드 진입점."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.mongodb import mongodb


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    mongodb.connect()
    yield
    # 종료 시
    mongodb.close()


app = FastAPI(
    title="레인보우 브릿지 API",
    description="반려동물 장례 이후 보호자의 추모와 일상 복귀를 돕는 애프터케어 서비스",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS (프론트 로컬 개발용 — 운영 시 도메인 제한)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# v1 라우터 등록
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["system"])
async def health_check():
    """서버 상태 확인용 헬스체크."""
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/", tags=["system"])
async def root():
    return {"message": "🌈 Rainbow Bridge API", "docs": "/docs"}
