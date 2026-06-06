import uuid
from pathlib import Path

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import FileResponse
from app.core.deps import get_current_user
from app.schemas.media import MediaStatusResponse, MediaUploadResponse
from app.services.media import create_asset, get_asset, run_liveportrait, run_perso
from app.services.pet import get_pet

router = APIRouter()

_UPLOAD_DIR = Path("uploads/media")
_MAX_SIZE = 10 * 1024 * 1024  # 10MB
_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}


@router.post("/upload", response_model=MediaUploadResponse, status_code=201)
async def upload_media(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    pet_id: str = Form(...),
    user: dict = Depends(get_current_user),
):
    if not await get_pet(pet_id, user_id=user["user_id"]):
        raise HTTPException(status_code=404, detail="반려동물 정보를 찾을 수 없습니다.")

    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(
            status_code=400, detail="이미지 파일(JPEG, PNG, WebP)만 업로드 가능합니다."
        )

    contents = await file.read()
    if len(contents) > _MAX_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하여야 합니다.")

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    save_path = _UPLOAD_DIR / f"{uuid.uuid4().hex}{ext}"
    save_path.write_bytes(contents)

    asset_id = await create_asset(pet_id, str(save_path), user_id=user["user_id"])
    background_tasks.add_task(run_liveportrait, asset_id, str(save_path), pet_id)

    return MediaUploadResponse(asset_id=asset_id)


@router.get("/{asset_id}", response_model=MediaStatusResponse)
async def get_media_status(asset_id: str, user: dict = Depends(get_current_user)):
    asset = await get_asset(asset_id, user_id=user["user_id"])
    if not asset:
        raise HTTPException(status_code=404, detail="asset을 찾을 수 없습니다.")
    return MediaStatusResponse(**asset)


@router.post("/{asset_id}/perso", status_code=202)
async def request_perso(
    asset_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_current_user),
):
    """PERSO 다국어 더빙 비동기 요청. voiced_url 영상을 PERSO에 전송."""
    asset = await get_asset(asset_id, user_id=user["user_id"])
    if not asset:
        raise HTTPException(status_code=404, detail="asset을 찾을 수 없습니다.")
    if not asset.get("voiced_url"):
        raise HTTPException(
            status_code=400, detail="영상+음성 합치기가 완료되지 않았습니다."
        )

    background_tasks.add_task(run_perso, asset_id)
    return {
        "message": "PERSO 더빙 요청이 접수됐습니다.",
        "asset_id": asset_id,
        "status": "pending",
    }


@router.get("/{asset_id}/download")
async def download_media(
    asset_id: str,
    type: str = "video",
    user: dict = Depends(get_current_user),
):
    """미디어 파일 다운로드. type: video | voiced | dubbed"""
    asset = await get_asset(asset_id, user_id=user["user_id"])
    if not asset:
        raise HTTPException(status_code=404, detail="asset을 찾을 수 없습니다.")

    url_map = {
        "video": asset.get("video_url"),
        "voiced": asset.get("voiced_url"),
        "dubbed": asset.get("dubbed_url"),
    }

    if type not in url_map:
        raise HTTPException(
            status_code=400, detail="type은 video | voiced | dubbed 중 하나여야 합니다."
        )

    file_url = url_map[type]
    if not file_url:
        raise HTTPException(status_code=404, detail="아직 파일이 준비되지 않았습니다.")

    file_path = Path(file_url.lstrip("/"))
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=f"{asset_id}_{type}.mp4",
    )
