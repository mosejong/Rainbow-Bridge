"""PERSO AI 립싱크 파이프라인 테스트.

voiced_url 영상(LivePortrait + TTS 합성)에 PERSO 립싱크를 적용하고
결과 영상을 다운로드합니다.

실행:
    python test_perso.py [영상파일경로]
    python test_perso.py               # 기본값: output_with_audio.mp4

주의: .env 파일에 PERSO_API_KEY, PERSO_SPACE_SEQ 필요.
"""

import os
import sys
import time
from urllib.parse import quote

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://api.perso.ai"
API_KEY = os.getenv("PERSO_API_KEY", "")
SPACE_SEQ = int(os.getenv("PERSO_SPACE_SEQ", "0"))
MEDIA_BASE = "https://portal-media.perso.ai"

if not API_KEY or not SPACE_SEQ:
    print("❌ .env에 PERSO_API_KEY, PERSO_SPACE_SEQ 필요")
    sys.exit(1)

HEADERS = {"XP-API-KEY": API_KEY, "Content-Type": "application/json"}
FILE_PATH = sys.argv[1] if len(sys.argv) > 1 else "output_with_audio.mp4"


def run():
    if not os.path.exists(FILE_PATH):
        print(f"❌ 파일 없음: {FILE_PATH}")
        return

    print(f"\n[PERSO] 립싱크 테스트 시작: {FILE_PATH}")
    print(f"   Space: {SPACE_SEQ}\n")

    # STEP 1: SAS 토큰
    file_name = os.path.basename(FILE_PATH)
    print("[1/6] SAS 토큰 발급...")
    sas = requests.get(
        f"{BASE_URL}/file/api/upload/sas-token?fileName={quote(file_name)}",
        headers=HEADERS,
    ).json()
    blob_url = (sas.get("result") or sas)["blobSasUrl"]
    print(f"  ✅ blobSasUrl 확보")

    # STEP 2: Azure 업로드
    print("[2/6] Azure 업로드...")
    with open(FILE_PATH, "rb") as f:
        requests.put(
            blob_url,
            data=f,
            headers={"x-ms-blob-type": "BlockBlob", "Content-Type": "application/octet-stream"},
        ).raise_for_status()
    print(f"  ✅ 완료")

    # STEP 3: 미디어 등록
    print("[3/6] 미디어 등록...")
    reg = requests.put(
        f"{BASE_URL}/file/api/upload/video",
        headers=HEADERS,
        json={"spaceSeq": SPACE_SEQ, "fileUrl": blob_url.split("?")[0], "fileName": file_name},
    ).json()
    media_seq = (reg.get("result") or reg)["seq"]
    print(f"  ✅ mediaSeq: {media_seq}")

    def _poll(pid, label):
        progress_url = f"{BASE_URL}/video-translator/api/v1/projects/{pid}/space/{SPACE_SEQ}/progress"
        for _ in range(120):
            prog = requests.get(progress_url, headers=HEADERS).json()
            status = (prog.get("result") or prog).get("progressReason") or ""
            print(f"  > {status or '처리중'}...", end="\r")
            if status == "Completed":
                print(f"\n  ✅ {label} 완료!")
                return True
            if status == "Failed":
                print(f"\n  ❌ {label} 실패: {prog}")
                return False
            time.sleep(5)
        return False

    # STEP 4: 번역(더빙) 프로젝트 생성
    print("[4/7] 번역 프로젝트 생성...")
    create = requests.post(
        f"{BASE_URL}/video-translator/api/v1/projects/spaces/{SPACE_SEQ}/translate",
        headers=HEADERS,
        json={
            "mediaSeq": media_seq,
            "isVideoProject": True,
            "sourceLanguageCode": "auto",
            "targetLanguages": [
                {"languageCode": "ko", "ttsModel": "ELEVEN_V3"}
            ],
            "preferredSpeedType": "GREEN",
            "title": f"rb_dub_{int(time.time())}",
        },
    ).json()

    raw = create.get("result") or create
    dub_id = raw.get("projectId") or raw.get("startGenerateProjectIdList")
    if isinstance(dub_id, list):
        dub_id = dub_id[0]
    print(f"  ✅ Dub Project ID: {dub_id}")

    # STEP 5: 번역 완료 대기
    print("[5/7] 번역 처리 대기...")
    if not _poll(dub_id, "번역"):
        return

    # STEP 6: 립싱크 프로젝트 생성 (번역 완료 후 별도 요청)
    print("[6/7] 립싱크 프로젝트 생성...")
    lipsync_res = requests.post(
        f"{BASE_URL}/video-translator/api/v1/projects/{dub_id}/spaces/{SPACE_SEQ}/lip-sync",
        headers=HEADERS,
        json={"preferredSpeedType": "GREEN", "title": f"rb_lipsync_{int(time.time())}"},
    ).json()
    raw2 = lipsync_res.get("result") or lipsync_res
    ls_id = raw2.get("startGenerateProjectIdList") or raw2.get("projectId")
    if isinstance(ls_id, list):
        ls_id = ls_id[0]
    print(f"  ✅ LipSync Project ID: {ls_id}")

    # STEP 6.5: 립싱크 완료 대기
    print("  립싱크 처리 대기...")
    if not _poll(ls_id, "립싱크"):
        return

    # STEP 7: 립싱크 영상 다운로드
    print("[7/7] 결과 다운로드...")
    link = requests.get(
        f"{BASE_URL}/video-translator/api/v1/projects/{ls_id}/spaces/{SPACE_SEQ}/download?target=lipSyncVideo",
        headers=HEADERS,
    ).json()
    path = (link.get("result") or {}).get("videoFile", {}).get("videoDownloadLink")

    if not path:
        print(f"  ❌ 다운로드 링크 없음: {link}")
        return

    download_url = f"{MEDIA_BASE}{path}" if path.startswith("/") else path
    os.makedirs("outputs", exist_ok=True)
    save_name = f"outputs/result_lipsync_{int(time.time())}.mp4"
    print(f"  다운로드 중: {download_url[:60]}...")
    with requests.get(download_url, headers=HEADERS, stream=True) as r:
        r.raise_for_status()
        with open(save_name, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)

    size_mb = os.path.getsize(save_name) / 1024 / 1024
    print(f"\n완료! -> {save_name} ({size_mb:.1f} MB)")
    print(f"   번역(ELEVEN_V3) -> 립싱크 2단계 완료")


if __name__ == "__main__":
    run()
