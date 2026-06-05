import asyncio
from datetime import datetime, timezone
from pathlib import Path

from bson import ObjectId

from app.db.mongodb import mongodb

_UPLOAD_DIR = Path("uploads/media")
_VIDEO_DIR = Path("uploads/videos")


def _collection():
    return mongodb.db["media_assets"]


async def create_asset(pet_id: str, source_path: str) -> str:
    doc = {
        "pet_id": pet_id,
        "source_url": f"/uploads/media/{Path(source_path).name}",
        "status": "processing",
        "video_url": None,
        "created_at": datetime.now(timezone.utc),
    }
    result = await _collection().insert_one(doc)
    return str(result.inserted_id)


async def get_asset(asset_id: str) -> dict | None:
    doc = await _collection().find_one({"_id": ObjectId(asset_id)})
    if not doc:
        return None
    return {
        "asset_id": str(doc["_id"]),
        "status": doc["status"],
        "video_url": doc.get("video_url"),
        "voiced_url": doc.get("voiced_url"),
        "dubbed_url": doc.get("dubbed_url"),
    }


async def run_liveportrait(asset_id: str, source_path: str):
    """백그라운드에서 LivePortrait 실행. 실패 시 status=error로 처리."""
    try:
        _VIDEO_DIR.mkdir(parents=True, exist_ok=True)

        import sys

        repo_root = str(Path(__file__).resolve().parents[3])
        if repo_root not in sys.path:
            sys.path.insert(0, repo_root)

        from ai.liveportrait.pipeline import generate_video, merge_audio

        # 1. LivePortrait 무음 영상 생성
        video_path = await asyncio.to_thread(
            generate_video, source_path, output_dir=str(_VIDEO_DIR)
        )

        # 2. TTS 음성 있으면 합치기 (uploads/tts/{pet_id}_*.mp3 최신 파일)
        doc = await _collection().find_one({"_id": ObjectId(asset_id)})
        pet_id = doc.get("pet_id", "") if doc else ""
        tts_dir = Path("uploads/tts")
        tts_files = sorted(
            tts_dir.glob(f"{pet_id}_*.mp3"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )

        voiced_path = None
        if tts_files:
            voiced_path = await asyncio.to_thread(
                merge_audio, video_path, str(tts_files[0]), output_dir=str(_VIDEO_DIR)
            )

        update = {
            "status": "done",
            "video_url": f"/uploads/videos/{Path(video_path).name}",
            "voiced_url": (
                f"/uploads/videos/{Path(voiced_path).name}" if voiced_path else None
            ),
        }

        await _collection().update_one(
            {"_id": ObjectId(asset_id)},
            {
                "$set": update,
            },
        )
    except Exception:
        await _collection().update_one(
            {"_id": ObjectId(asset_id)},
            {"$set": {"status": "error"}},
        )
