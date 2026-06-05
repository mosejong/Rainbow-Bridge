import uuid
from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, Form
from app.schemas.media import MediaStatusResponse, MediaUploadResponse
from app.services.media import create_asset, get_asset, run_liveportrait

router = APIRouter()

_UPLOAD_DIR = Path("uploads/media")
_MAX_SIZE = 10 * 1024 * 1024  # 10MB
_ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp"}

@router.post("/upload", response_model=MediaUploadResponse, status_code=201)
async def upload_media(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    pet_id: str = Form(...),
):
    if file.content_type not in _ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다. (jpeg, png, gif, webp)")

    contents = await file.read()
    if len(contents) > _MAX_SIZE:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB를 초과할 수 없습니다.")

    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    save_path = _UPLOAD_DIR / f"{uuid.uuid4()}{ext}"

    save_path.write_bytes(contents)
    asset_id = await create_asset(pet_id, str(save_path))
    background_tasks.add_task(run_liveportrait, asset_id, str(save_path))
    return MediaUploadResponse(asset_id=asset_id)

@router.get("/{asset_id}", response_model=MediaStatusResponse)
async def get_media_status(asset_id: str):
    asset = await get_asset(asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="asset을 찾을 수 없습니다.")
    return MediaStatusResponse(**asset)
