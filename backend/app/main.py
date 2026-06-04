"""레인보우 브릿지 백엔드 진입점."""

import os
from contextlib import asynccontextmanager

import app.core.ai_path  # noqa: F401 — ai/ sys.path 등록 (import 순서 중요)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.mongodb import mongodb
from app.db.rdb import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 시작 시
    await init_db()  # SQLite users 테이블 생성
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

# 업로드 파일 정적 서빙 (사진·TTS 음성)
_UPLOAD_DIR = "uploads"
os.makedirs(_UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_UPLOAD_DIR), name="uploads")


@app.get("/health", tags=["system"])
async def health_check():
    """서버 상태 확인용 헬스체크."""
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/", tags=["system"])
async def root():
    return {"message": "🌈 Rainbow Bridge API", "docs": "/docs"}
