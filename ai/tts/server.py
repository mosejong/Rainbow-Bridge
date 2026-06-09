"""④ TTS 추론 HTTP 서비스 — GPU 서버(정환주)에서 실행.

NCP 백엔드엔 GPU 가 없으므로(=A안 불가), 백엔드가 텍스트를 HTTP 로 보내면
이 서비스가 GPU 로 Qwen3 합성 wav 를 만들어 돌려줍니다. LivePortrait 와 동일 패턴.

구조:
    [프론트] -> POST /tts (NCP 백엔드) -> HTTP -> [GPU 서버: 이 server.py /synthesize] -> Qwen3
                                        <-- wav --

  - 정환주(GPU): 이 server.py — synthesize() 를 /synthesize 로 노출.
  - 김윤한(백엔드): /tts 에서 TTS_SERVER_URL 로 이 서비스 HTTP 호출.

윤리: 보호자 대상 위로 낭독만. 반려동물 목소리 흉내 ❌.

실행 (GPU 서버, conda qwen3-tts 환경 — __init__.py 가 google-cloud 끌어오므로 `-m` 금지):
    pip install fastapi uvicorn
    conda run --no-capture-output -n qwen3-tts python ai/tts/server.py
    # 또는: cd ai/tts && uvicorn server:app --host 0.0.0.0 --port 8002
    # 그리고 터널(URL 을 백엔드 TTS_SERVER_URL 에 설정) → 터널·동시1개 제약은 ../GPU_SERVER.md

포트 8002 — webui(8000)·liveportrait(8001) 와 겹치지 않게.
VRAM ~4.6GB(첫 /synthesize 호출 때 온디맨드 로드). webui(8000)와 동시 구동 시
8GB 초과 주의 — qwen3 인스턴스는 하나만 띄울 것(../tts/CLAUDE.md §4).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.concurrency import run_in_threadpool

# server.py 와 qwen3_synthesize.py 가 같은 폴더 → 직접 import 되도록 경로 보장
# (top-level 모듈로 잡혀 ai/tts/__init__.py 의 google-cloud import 를 피함).
sys.path.insert(0, str(Path(__file__).resolve().parent))
from qwen3_synthesize import AVAILABLE_VOICES, synthesize  # noqa: E402

app = FastAPI(title="Qwen3 TTS 추론 서비스", version="1.0")


class SynthesizeRequest(BaseModel):
    """백엔드 /tts 가 보내는 합성 요청 — tts.py/qwen3_synthesize 계약과 동일."""

    text: str
    tone: str = "girl"  # AVAILABLE_VOICES: "boy" / "girl"


@app.get("/health")
def health() -> dict:
    """헬스 체크 — 터널·서비스 살아있는지 확인용 (모델 로드는 안 건드림)."""
    return {
        "status": "ok",
        "service": "qwen3-tts",
        "voices": list(AVAILABLE_VOICES),
    }


@app.post("/synthesize")
async def synthesize_endpoint(req: SynthesizeRequest) -> FileResponse:
    """텍스트 -> 확정 보이스(boy/girl) 낭독 wav. 오디오 파일을 그대로 반환.

    duration/format 메타는 응답 헤더(X-Audio-Duration / X-Audio-Format)로 전달.
    """
    try:
        # 블로킹(GPU 추론) 호출 → 스레드풀에서 실행해 이벤트 루프 안 막음.
        result = await run_in_threadpool(synthesize, req.text, req.tone)
    except ValueError as e:  # 빈 텍스트·미지원 보이스 → 400
        raise HTTPException(status_code=400, detail=str(e)) from e

    path = Path(result["audio_path"])
    return FileResponse(
        path=str(path),
        media_type="audio/wav",
        filename=path.name,
        headers={
            "X-Audio-Duration": str(result["duration"]),
            "X-Audio-Format": result["format"],
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8002")))
