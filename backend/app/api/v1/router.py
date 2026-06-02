"""v1 API 라우터 통합.

각 기능 담당이 endpoints/ 아래에 라우터를 만들고 여기에 등록합니다.
예시:
    from app.api.v1.endpoints import pets
    api_router.include_router(pets.router, prefix="/pets", tags=["pets"])
"""

from fastapi import APIRouter

from app.api.v1.endpoints import emotions, missions, pets

api_router = APIRouter()

api_router.include_router(pets.router, prefix="/pets", tags=["pets"])
api_router.include_router(emotions.router, prefix="/emotions", tags=["emotions"])
api_router.include_router(missions.router, prefix="/missions", tags=["missions"])

# from app.api.v1.endpoints import messages, timeline, media
# api_router.include_router(messages.router,  prefix="/messages",  tags=["messages"])
# api_router.include_router(timeline.router,  prefix="/timeline",  tags=["timeline"])
# api_router.include_router(media.router,     prefix="/media",     tags=["media"])
