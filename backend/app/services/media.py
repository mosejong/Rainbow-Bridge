import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import requests
from bson import ObjectId

from app.db.mongodb import mongodb

logger = logging.getLogger(__name__)

_PERSO_BASE = "https://api.perso.ai"
_PERSO_KEY = os.getenv("PERSO_API_KEY", "")
_PERSO_SPACE = int(os.getenv("PERSO_SPACE_SEQ", "0"))
_PERSO_HEADERS = {"XP-API-KEY": _PERSO_KEY, "Content-Type": "application/json"}

_UPLOAD_DIR = Path("uploads/media")
_VIDEO_DIR = Path("uploads/videos")
_TTS_DIR = Path("uploads/tts")


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


async def run_liveportrait(asset_id: str, source_path: str, pet_id: str = ""):
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

        # 2. TTS 음성 있으면 합치기 (pet_id를 인수로 받아 DB 재조회 불필요)
        if not pet_id:
            doc = await _collection().find_one({"_id": ObjectId(asset_id)})
            pet_id = doc.get("pet_id", "") if doc else ""
        tts_files = sorted(
            _TTS_DIR.glob(f"{pet_id}_*.mp3"),
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
        logger.exception("LivePortrait 처리 실패 asset_id=%s", asset_id)
        await _collection().update_one(
            {"_id": ObjectId(asset_id)},
            {"$set": {"status": "error"}},
        )


async def run_perso(asset_id: str):
    """voiced_url 영상을 PERSO에 업로드 → 더빙 → dubbed_url 저장."""
    try:
        doc = await _collection().find_one({"_id": ObjectId(asset_id)})
        if not doc or not doc.get("voiced_url"):
            return

        # voiced_url → 로컬 파일 경로 복원
        voiced_url = doc["voiced_url"]  # e.g. /uploads/videos/xxx.mp4
        local_path = Path(voiced_url.lstrip("/"))
        if not local_path.exists():
            raise FileNotFoundError(f"{local_path} 없음")

        def _upload_and_dub():
            file_name = local_path.name
            # 1. SAS 토큰
            sas = requests.get(
                f"{_PERSO_BASE}/file/api/upload/sas-token?fileName={quote(file_name)}",
                headers=_PERSO_HEADERS,
            ).json()
            blob_url = (sas.get("result") or sas)["blobSasUrl"]

            # 2. Azure 업로드
            with open(local_path, "rb") as f:
                requests.put(
                    blob_url,
                    data=f,
                    headers={
                        "x-ms-blob-type": "BlockBlob",
                        "Content-Type": "application/octet-stream",
                    },
                ).raise_for_status()

            # 3. 미디어 등록
            reg = requests.put(
                f"{_PERSO_BASE}/file/api/upload/video",
                headers=_PERSO_HEADERS,
                json={
                    "spaceSeq": _PERSO_SPACE,
                    "fileUrl": blob_url.split("?")[0],
                    "fileName": file_name,
                },
            ).json()
            media_seq = (reg.get("result") or reg)["seq"]

            # 4. 큐 초기화
            requests.put(
                f"{_PERSO_BASE}/video-translator/api/v1/projects/spaces/{_PERSO_SPACE}/queue",
                headers=_PERSO_HEADERS,
            )

            # 5. 프로젝트 생성
            create = requests.post(
                f"{_PERSO_BASE}/video-translator/api/v1/projects/spaces/{_PERSO_SPACE}/translate",
                headers=_PERSO_HEADERS,
                json={
                    "mediaSeq": media_seq,
                    "isVideoProject": True,
                    "sourceLanguageCode": "auto",
                    "targetLanguages": [
                        {"languageCode": "en", "ttsModel": "ELEVEN_V2"}
                    ],
                    "preferredSpeedType": "GREEN",
                    "title": f"rb_{asset_id}_{int(time.time())}",
                },
            ).json()
            raw = create.get("result") or create
            project_id = raw.get("projectId") or raw.get("startGenerateProjectIdList")
            if isinstance(project_id, list):
                project_id = project_id[0]

            # 6. 폴링 (최대 5분)
            for _ in range(60):
                prog = requests.get(
                    f"{_PERSO_BASE}/video-translator/api/v1/projects/{project_id}/space/{_PERSO_SPACE}/progress",
                    headers=_PERSO_HEADERS,
                ).json()
                status = (prog.get("result") or prog).get("progressReason") or ""
                if status == "Completed":
                    break
                if status == "Failed":
                    raise RuntimeError("PERSO 작업 실패")
                time.sleep(5)

            # 7. 다운로드 링크
            link = requests.get(
                f"{_PERSO_BASE}/video-translator/api/v1/projects/{project_id}/spaces/{_PERSO_SPACE}/download?target=dubbingVideo",
                headers=_PERSO_HEADERS,
            ).json()
            path = (
                (link.get("result") or {}).get("videoFile", {}).get("videoDownloadLink")
            )
            if path and path.startswith("/"):
                path = f"https://perso-saas-file-frontdoor.perso.ai{path}"

            # 8. 저장
            save_name = f"dubbed_{asset_id}.mp4"
            save_path = _VIDEO_DIR / save_name
            with requests.get(path, headers=_PERSO_HEADERS, stream=True) as r:
                r.raise_for_status()
                with open(save_path, "wb") as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
            return f"/uploads/videos/{save_name}"

        dubbed_url = await asyncio.to_thread(_upload_and_dub)
        await _collection().update_one(
            {"_id": ObjectId(asset_id)},
            {"$set": {"dubbed_url": dubbed_url}},
        )
    except Exception:
        logger.exception(
            "PERSO 더빙 실패 asset_id=%s", asset_id
        )  # 메인 서비스에 영향 없음
