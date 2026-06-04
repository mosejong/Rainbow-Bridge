"""④ TTS 서비스 — ai/tts(Google Cloud TTS)를 백엔드 응답으로 연결.

추모 메시지(보호자 대상 위로 낭독)를 음성으로 합성해, 프론트가 재생할 수 있는
정적 URL(`/uploads/tts/...`)로 돌려줍니다.

⚠️ 윤리: 보호자 대상 낭독만. 반려동물 1인칭/목소리 흉내 ❌ (../CLAUDE.md §1).
"""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from app.schemas.tts import TtsCreate, TtsResponse

# backend/app/services/tts.py → parents[3] = 레포 루트
_REPO_ROOT = Path(__file__).resolve().parents[3]

# 백엔드는 backend/ 에서 실행돼 루트 .env 를 자동 로드하지 않음 → 명시 로드.
# (Google 클라이언트는 GOOGLE_APPLICATION_CREDENTIALS 를 os.environ 에서 직접 읽음)
load_dotenv(_REPO_ROOT / ".env")

# 인증 키 경로가 상대경로면 루트 기준 절대경로로 보정 (백엔드 cwd 문제 회피).
_cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if _cred and not os.path.isabs(_cred):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((_REPO_ROOT / _cred).resolve())

# 합성 결과를 정적 서빙 폴더(main.py 의 /uploads 마운트)에 바로 저장.
os.environ.setdefault("TTS_OUTPUT_DIR", "uploads/tts")

# ai/tts import 하려면 레포 루트가 sys.path 에 있어야 함(backend/ 에서 실행되므로).
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from ai.tts import TtsTone, synthesize  # noqa: E402


async def generate_tts(data: TtsCreate) -> TtsResponse:
    """추모 메시지를 음성으로 합성해 재생용 URL 을 반환합니다.

    synthesize() 는 동기·블로킹(네트워크) 호출이라 스레드에서 실행해
    이벤트 루프를 막지 않습니다.
    """
    try:
        tone = TtsTone(data.tone)
    except ValueError:
        tone = TtsTone.WARM  # 알 수 없는 톤은 기본값으로 안전 처리

    # pet_id 를 파일명에 넣어 추적 가능하게 (출력 폴더는 uploads/tts).
    filename = f"{data.pet_id}_{tone.value}_{abs(hash(data.text)) % 10_000_000}.mp3"
    result = await asyncio.to_thread(synthesize, data.text, tone, filename=filename)

    return TtsResponse(
        audio_url=f"/uploads/tts/{filename}",
        duration=result["duration"],
        format=result["format"],
    )
