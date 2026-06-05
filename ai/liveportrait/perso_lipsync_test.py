"""PERSO 립싱크 검증용 테스트 스크립트 (멀티모달 — 장민수).

voiced 영상(LivePortrait + TTS 낭독) → PERSO video-translator → 립싱크 영상.
동물 얼굴 립싱크 동작·품질 확인용 **로컬 검증 도구**입니다.
(백엔드 정식 연동은 모세종님 `backend/app/services/media.py::run_perso`)

검증 결과·발견은 EXPERIMENT.md "2026-06-05 PERSO 립싱크 실연동 검증" 참고.

사용법:
    python ai/liveportrait/perso_lipsync_test.py <입력영상.mp4> [target_lang]
    # target_lang 기본 ko (ko→ko = 번역 없이 한국어 유지 + 립싱크)

필요 환경변수(.env): PERSO_API_KEY, (선택) PERSO_SPACE_SEQ, PERSO_API_BASE_URL

⚠️ 외부(PERSO Azure)로 영상이 업로드됩니다. 개인 반려동물 사진 말고 검증용 샘플만 사용.
⚠️ /lip-sync 엔드포인트는 GET 전용이라, translate(같은 언어)로 립싱크를 유도합니다.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests

_REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_env(path: Path) -> dict:
    """의존성 없이 .env 파싱 (KEY=VALUE)."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


_ENV = _load_env(_REPO_ROOT / ".env")
BASE_URL = _ENV.get("PERSO_API_BASE_URL") or "https://api.perso.ai"
API_KEY = _ENV.get("PERSO_API_KEY", "")
SPACE_SEQ = int(_ENV.get("PERSO_SPACE_SEQ") or "555198")
HEADERS = {"XP-API-KEY": API_KEY, "Content-Type": "application/json"}


def run_lipsync(file_path: str, target_lang: str = "ko") -> str | None:
    """영상을 PERSO에 올려 더빙(립싱크)하고 결과 mp4 경로를 반환."""
    if not API_KEY:
        print("[중단] PERSO_API_KEY 없음 (.env 확인)")
        return None
    fpath = Path(file_path)
    if not fpath.exists():
        print(f"[중단] 입력 파일 없음: {fpath}")
        return None

    name = fpath.name

    # 1. SAS 토큰
    sas = requests.get(
        f"{BASE_URL}/file/api/upload/sas-token?fileName={quote(name)}",
        headers=HEADERS, timeout=30,
    ).json()
    blob_url = (sas.get("result") or sas).get("blobSasUrl")
    if not blob_url:
        print(f"[1] SAS 실패: {sas}")
        return None
    print("[1] SAS 토큰 OK")

    # 2. Azure 업로드
    with open(fpath, "rb") as f:
        requests.put(
            blob_url, data=f,
            headers={"x-ms-blob-type": "BlockBlob",
                     "Content-Type": "application/octet-stream"},
            timeout=120,
        ).raise_for_status()
    print("[2] 업로드 OK")

    # 3. 미디어 등록
    reg = requests.put(
        f"{BASE_URL}/file/api/upload/video",
        headers=HEADERS,
        json={"spaceSeq": SPACE_SEQ, "fileUrl": blob_url.split("?")[0], "fileName": name},
        timeout=30,
    ).json()
    media_seq = (reg.get("result") or reg).get("seq")
    if not media_seq:
        print(f"[3] 등록 실패: {reg}")
        return None
    print(f"[3] mediaSeq={media_seq}")

    # 4. 큐 초기화
    requests.put(
        f"{BASE_URL}/video-translator/api/v1/projects/spaces/{SPACE_SEQ}/queue",
        headers=HEADERS, timeout=30,
    )

    # 5. 프로젝트 생성 (translate — 같은 언어면 번역 없이 립싱크)
    create = requests.post(
        f"{BASE_URL}/video-translator/api/v1/projects/spaces/{SPACE_SEQ}/translate",
        headers=HEADERS,
        json={
            "mediaSeq": media_seq,
            "isVideoProject": True,
            "sourceLanguageCode": target_lang,
            "targetLanguages": [{"languageCode": target_lang, "ttsModel": "ELEVEN_V2"}],
            "preferredSpeedType": "GREEN",
            "title": f"rb_lipsync_{int(time.time())}",
        },
        timeout=60,
    ).json()
    raw = (create.get("result") or create).get("projectId") or (
        create.get("result") or create
    ).get("startGenerateProjectIdList")
    project_id = raw[0] if isinstance(raw, list) else raw
    if not project_id:
        print(f"[5] 생성 실패: {create}")
        return None
    print(f"[5] projectId={project_id}")

    # 6. 폴링 (최대 10분)
    purl = (f"{BASE_URL}/video-translator/api/v1/projects/{project_id}"
            f"/space/{SPACE_SEQ}/progress")
    for _ in range(120):
        prog = requests.get(purl, headers=HEADERS, timeout=30).json()
        status = (prog.get("result") or prog).get("progressReason") or ""
        print(f"[6] 상태: {status}")
        if status == "Completed":
            break
        if status == "Failed":
            print(f"[6] 실패: {prog}")
            return None
        time.sleep(5)
    else:
        print("[6] 타임아웃")
        return None

    # 7. 다운로드
    link = (
        requests.get(
            f"{BASE_URL}/video-translator/api/v1/projects/{project_id}"
            f"/spaces/{SPACE_SEQ}/download?target=dubbingVideo",
            headers=HEADERS, timeout=30,
        ).json().get("result", {}).get("videoFile", {}).get("videoDownloadLink")
    )
    if not link:
        print("[7] 다운로드 링크 없음")
        return None
    if link.startswith("/"):
        link = f"https://perso-saas-file-frontdoor.perso.ai{link}"

    out_dir = _REPO_ROOT / "output" / "_perso_test"
    out_dir.mkdir(parents=True, exist_ok=True)
    save = out_dir / f"perso_result_{project_id}.mp4"
    with requests.get(link, headers=HEADERS, stream=True, timeout=120) as resp:
        resp.raise_for_status()
        with open(save, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
    print(f"[완료] 저장: {save}")
    return str(save)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    run_lipsync(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "ko")
