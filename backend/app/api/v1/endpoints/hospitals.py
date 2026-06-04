import os
import httpx
from fastapi import APIRouter, HTTPException, Query
from dotenv import load_dotenv
import app.core.ai_path  # noqa: F401  프로젝트 루트를 sys.path에 추가

load_dotenv()

router = APIRouter()

KAKAO_API_KEY = os.getenv("KAKAO_REST_API_KEY")
KAKAO_LOCAL_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"


@router.get("")
async def get_hospitals(
    query: str = Query(default="동물병원", description="검색어"),
    x: float = Query(..., description="경도 (longitude)"),
    y: float = Query(..., description="위도 (latitude)"),
    radius: int = Query(default=5000, description="반경 (미터, 최대 20000)"),
):
    """카카오맵 API로 주변 동물병원 검색."""
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": query, "x": x, "y": y, "radius": radius}

    async with httpx.AsyncClient() as client:
        response = await client.get(KAKAO_LOCAL_URL, headers=headers, params=params)

    if response.status_code != 200:
        raise HTTPException(status_code=502, detail="카카오맵 API 호출 실패")

    data = response.json()
    return {
        "total": data["meta"]["total_count"],
        "hospitals": data["documents"],
    }
