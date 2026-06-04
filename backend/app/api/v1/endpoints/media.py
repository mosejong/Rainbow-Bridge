import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, Form

from app.schemas.media import MediaStatusResponse, MediaUploadResponse
from app.services.media import create_asset, get_asset, run_liveportrait

router = APIRouter()

_UPLOAD_DIR = Path("uploads/media")


@router.post("/upload", response_model=MediaUploadResponse, status_code=201)
async def upload_media(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    pet_id: str = Form(...),
):
    _UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    ext = Path(file.filename).suffix if file.filename else ".jpg"
    save_path = _UPLOAD_DIR / f"{pet_id}_{os.urandom(4).hex()}{ext}"
    contents = await file.read()
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
