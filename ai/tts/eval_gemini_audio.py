"""Google TTS 톤별 자연스러움·감정표현 자동평가 — Gemini 멀티모달 오디오.

STT(CER)는 발음만 잰다 → 자연스러움·감정은 못 잰다. 이를 보완해 Gemini 2.5
flash 에 mp3 를 직접 들려주고 1~5 점수를 받는다.

⚠️ 점수 성격: **LLM 청취 판단(참고용)** — MOS 같은 검증된 지표 아님. 톤 간
   상대 비교/로봇음 진단용으로만 쓰고, 절대 점수로 신뢰하지 말 것.
⚠️ **Google(ko-KR-Neural2-A)만 평가** — 실제 프로덕션 엔진이라 confound 없음.
   ElevenLabs Free 샘플은 영어권 보이스라 한국어 평가가 불공정 → 제외(ENGINE_NOTES §5).
⚠️ 윤리(ai/tts/CLAUDE.md §5): 평가 대상은 보호자 위로 멘트 음성뿐. 점수만 매김.

실행: python -m ai.tts.eval_gemini_audio
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time

from .compare_elevenlabs import _load_dotenv
from .tts import _OUTPUT_DIR

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

_MODEL = os.environ.get("GEMINI_AUDIO_MODEL", "gemini-2.5-flash")

_PROMPT = (
    "이것은 반려동물을 떠나보낸 보호자를 위로하는 한국어 TTS 음성입니다.\n"
    "아래 두 항목을 각각 1~5 정수로 평가하세요.\n"
    "- naturalness: 기계음 없이 사람처럼 자연스러운 정도 (5=매우 자연스러움)\n"
    "- emotion: 따뜻함·공감 등 감정 전달 정도 (5=풍부함)\n"
    "comment 는 한국어 한 문장으로 근거를 적으세요."
)


def _schema(types):
    return types.Schema(
        type=types.Type.OBJECT,
        properties={
            "naturalness": types.Schema(type=types.Type.INTEGER),
            "emotion": types.Schema(type=types.Type.INTEGER),
            "comment": types.Schema(type=types.Type.STRING),
        },
        required=["naturalness", "emotion", "comment"],
    )


def _generate(client, types, data, cfg, tries: int = 5):
    """503/429 일시 과부하는 backoff 재시도. 그 외 예외는 즉시 전파."""
    last = None
    for i in range(tries):
        try:
            return client.models.generate_content(
                model=_MODEL,
                contents=[
                    types.Part.from_bytes(data=data, mime_type="audio/mpeg"),
                    _PROMPT,
                ],
                config=cfg,
            )
        except Exception as exc:
            last = exc
            msg = str(exc)
            if any(
                k in msg for k in ("503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED")
            ):
                time.sleep(2 * (i + 1))
                continue
            raise
    raise last


def main() -> None:
    _load_dotenv()
    # .env 의 LLM_API_KEY 에는 인라인 주석(# ...)이 붙어 있어 떼어낸다.
    api_key = os.environ.get("LLM_API_KEY", "").split("#")[0].strip()
    if not api_key:
        print("[skip] LLM_API_KEY 없음 → .env 설정 후 재실행")
        return
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("[skip] google-genai 미설치 → `python -m pip install google-genai`")
        return

    files = sorted(glob.glob(os.path.join(_OUTPUT_DIR, "compare_google_*.mp3")))
    if not files:
        print("분석할 Google mp3 없음 → 먼저 `python -m ai.tts.compare_elevenlabs`")
        return

    client = genai.Client(api_key=api_key)
    cfg = types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=_schema(types)
    )

    print(f"== Google TTS 톤별 Gemini 자동평가 (model: {_MODEL}) ==\n")
    rows = []
    for path in files:
        tone = os.path.basename(path).replace("compare_google_", "").replace(".mp3", "")
        with open(path, "rb") as f:
            data = f.read()
        try:
            resp = _generate(client, types, data, cfg)
            obj = json.loads(resp.text)
            n, e, c = obj["naturalness"], obj["emotion"], obj["comment"]
            rows.append((tone, n, e, c))
            print(f"[{tone}] 자연스러움 {n}/5  감정표현 {e}/5\n   {c}")
        except Exception as exc:
            print(f"[warn] {tone} 평가 실패: {exc}")

    if rows:
        print("\n== 요약 (참고용 LLM 판단, MOS 아님) ==")
        for tone, n, e, _c in rows:
            print(f"  {tone:8}  자연 {n}/5  감정 {e}/5")


if __name__ == "__main__":
    main()
