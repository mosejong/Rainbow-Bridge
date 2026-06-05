"""④ TTS 합성 — Google Cloud TTS 연동 (골격/스텁).

추모 메시지를 보호자에게 음성으로 낭독합니다. 메시지 톤(③ 반소람)과 1:1로
매핑되는 TTS 톤을 받아 발화 속도·피치를 조절합니다.

엔진 선택(2026-06-02 잠정): **Google Cloud TTS**
  - 사유: LLM을 Gemini(클라우드)로 옮겨 GPU를 뗐는데, TTS만 로컬(Coqui 등)로
    돌리면 RTX 5060 8GB가 다시 빡빡. 17일 일정엔 클라우드가 안전.
  - 한국어 Neural2 음성 품질 양호. (최종 확정은 ../tts/CLAUDE.md §6 후기로)

⚠️ 윤리: 보호자 대상 위로 낭독만. 반려동물 목소리 흉내 ❌.

🚧 미완성(키·인증 필요):
  - Google Cloud TTS 인증(서비스 계정 `GOOGLE_APPLICATION_CREDENTIALS` 또는 API 키)
  - 음성 이름(`ko-KR-Neural2-*`)·요금 한도 확인
  - duration(재생 길이)은 ffprobe 실측(`_probe_duration`), 실패 시 글자수 추정 폴백

의존성: pip install google-cloud-texttospeech
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from enum import Enum
from typing import Final, Optional

# 음성 파일 저장 위치 — git 미포함(.gitignore). 백엔드 MediaAsset 와 합의 후 조정.
_OUTPUT_DIR: Final[str] = os.environ.get("TTS_OUTPUT_DIR", "ai/tts/_output")

# 한국어 음성 (Google Cloud TTS). 최종 음성/이름은 후기 비교 후 확정.
_LANGUAGE_CODE: Final[str] = "ko-KR"
_VOICE_NAME: Final[str] = os.environ.get("TTS_VOICE", "ko-KR-Neural2-A")

# 선택 가능한 목소리 레지스트리 — 친숙한 키 → Google Cloud voice 이름.
# UI 노출(목소리 고르기)은 백엔드 스키마(tone만 받음)·프론트 추가가 필요 → 핸드오프.
# 여기서는 ai/tts 단에서 voice 선택 "능력"만 추가하고 기본값은 현재 그대로 둔다.
_VOICES: Final[dict[str, str]] = {
    "female_a": "ko-KR-Neural2-A",  # 여성, 기본(현재 사용)
    "female_b": "ko-KR-Neural2-B",  # 여성, 다른 결
    "male_c": "ko-KR-Neural2-C",  # 남성
    "female_wavenet": "ko-KR-Wavenet-A",  # 여성, 저가 폴백(요금 절감)
}

# 호출부가 고를 수 있는 목소리 키 목록(공개).
AVAILABLE_VOICES: Final[tuple[str, ...]] = tuple(_VOICES)

# Google Cloud TTS 단일 요청 입력 길이 제한(바이트) — 길면 분할.
_MAX_CHARS: Final[int] = 4500

# 한국어 평균 발화 속도(대략) — duration 추정용(글자/초).
_CHARS_PER_SEC: Final[float] = 5.0


class TtsTone(str, Enum):
    """TTS 톤 — 메시지 톤(③ 반소람)과 1:1 매핑.

    값은 메시지 톤 키와 맞춥니다(반소람과 합의해 고정). 톤별로 발화
    속도·피치를 다르게 줍니다.
    """

    WARM = "warm"  # 따뜻함 — 부드럽고 약간 느리게
    CALM = "calm"  # 담담함 — 평이하게
    HOPEFUL = "hopeful"  # 희망 — 약간 밝고 보통 속도
    SOFT = "soft"  # 나직이 — 가장 부드럽고 낮게(프론트 '부드럽게' 대응)


@dataclass(frozen=True)
class _VoiceParams:
    speaking_rate: float  # 0.25~4.0 (1.0 기본)
    pitch: float  # -20.0~20.0 (0.0 기본)


# 톤 → 음성 파라미터. 추모 맥락이라 전체적으로 차분하게.
_TONE_MAP: Final[dict[TtsTone, _VoiceParams]] = {
    TtsTone.WARM: _VoiceParams(speaking_rate=0.92, pitch=-1.0),
    TtsTone.CALM: _VoiceParams(speaking_rate=0.95, pitch=0.0),
    TtsTone.HOPEFUL: _VoiceParams(speaking_rate=1.0, pitch=1.0),
    TtsTone.SOFT: _VoiceParams(speaking_rate=0.88, pitch=-2.0),
}


def _resolve_voice(voice: Optional[str]) -> str:
    """목소리 키(또는 None)를 실제 Google voice 이름으로 변환.

    None → 현재 기본값(`_VOICE_NAME`). 알려진 키 → 해당 voice 이름.
    미지원 키 → ValueError(호출부에서 폴백/안내 처리).
    """
    if voice is None:
        return _VOICE_NAME
    try:
        return _VOICES[voice]
    except KeyError as e:
        raise ValueError(
            f"지원하지 않는 목소리: {voice!r}. 가능: {', '.join(_VOICES)}"
        ) from e

_SENTENCE_SPLIT_RE: Final[re.Pattern[str]] = re.compile(r"(?<=[.!?。…\n])\s+")


def _split_text(text: str, max_chars: int = _MAX_CHARS) -> list[str]:
    """긴 텍스트를 문장 경계로 나눠 청크(<= max_chars)로 묶습니다."""
    sentences = _SENTENCE_SPLIT_RE.split(text.strip())
    chunks: list[str] = []
    buf = ""
    for s in sentences:
        if not s:
            continue
        if len(buf) + len(s) + 1 > max_chars and buf:
            chunks.append(buf)
            buf = s
        else:
            buf = f"{buf} {s}".strip()
    if buf:
        chunks.append(buf)
    return chunks or [text]


def _estimate_duration(text: str) -> float:
    """재생 길이(초) 대략 추정 — ffprobe 실측 실패 시 폴백."""
    return round(len(text.replace(" ", "")) / _CHARS_PER_SEC, 1)


def _probe_duration(path: str) -> Optional[float]:
    """ffprobe 로 음성 파일의 실제 재생 길이(초)를 측정. 측정 불가면 None.

    ffprobe 미설치·실행 실패·파싱 실패는 모두 None 으로 흡수해, 길이 측정
    실패가 합성 자체를 막지 않도록 합니다(호출부에서 추정값으로 폴백).
    """
    if shutil.which("ffprobe") is None:
        return None
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if out.returncode != 0:
            return None
        return round(float(json.loads(out.stdout)["format"]["duration"]), 1)
    except (subprocess.SubprocessError, ValueError, KeyError):
        return None


def synthesize(
    text: str,
    tone: TtsTone = TtsTone.WARM,
    *,
    voice: Optional[str] = None,
    filename: Optional[str] = None,
) -> dict:
    """텍스트를 음성으로 합성해 파일로 저장하고 메타데이터를 돌려줍니다.

    Args:
        text: 낭독할 보호자 대상 위로 메시지. (반려동물 1인칭 ❌)
        tone: 발화 톤(메시지 톤과 매핑).
        voice: 목소리 키(`AVAILABLE_VOICES` 중 하나). None이면 현재 기본 목소리.
        filename: 저장 파일명(미지정 시 자동).

    Returns:
        {"audio_path": str, "duration": float, "format": "mp3"}
        — 백엔드 MediaAsset 형태와 합의해 조정.

    Raises:
        RuntimeError: Google Cloud TTS 라이브러리/인증이 준비되지 않은 경우.

    🚧 현재는 골격입니다. 실제 호출에는 인증 설정이 필요합니다(모듈 docstring 참고).
    """
    if not text or not text.strip():
        raise ValueError("합성할 텍스트가 비어 있습니다.")

    params = _TONE_MAP[tone]
    voice_name = _resolve_voice(voice)
    chunks = _split_text(text)
    audio = _synthesize_google(chunks, params, voice_name)

    os.makedirs(_OUTPUT_DIR, exist_ok=True)
    name = filename or f"tts_{tone.value}_{abs(hash(text)) % 10_000_000}.mp3"
    path = os.path.join(_OUTPUT_DIR, name)
    with open(path, "wb") as f:
        f.write(audio)

    return {
        "audio_path": path,
        "duration": _probe_duration(path) or _estimate_duration(text),
        "format": "mp3",
    }


def _synthesize_google(
    chunks: list[str], params: _VoiceParams, voice_name: str = _VOICE_NAME
) -> bytes:
    """Google Cloud TTS 로 청크별 합성 후 MP3 바이트를 이어 붙입니다.

    🚧 인증(GOOGLE_APPLICATION_CREDENTIALS 등)이 없으면 명확한 에러를 냅니다.
    MP3 단순 concat 은 대부분 플레이어에서 재생되지만, 정밀 합성이 필요하면
    pydub/ffmpeg 로 교체하세요(TODO).
    """
    try:
        from google.cloud import texttospeech  # 지연 import (미설치 시 명확한 에러)
    except ImportError as e:  # pragma: no cover - 환경 의존
        raise RuntimeError(
            "google-cloud-texttospeech 미설치. `pip install google-cloud-texttospeech` "
            "후 인증(GOOGLE_APPLICATION_CREDENTIALS)을 설정하세요."
        ) from e

    client = texttospeech.TextToSpeechClient()
    voice = texttospeech.VoiceSelectionParams(
        language_code=_LANGUAGE_CODE, name=voice_name
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        speaking_rate=params.speaking_rate,
        pitch=params.pitch,
    )

    out = bytearray()
    for chunk in chunks:
        resp = client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=chunk),
            voice=voice,
            audio_config=audio_config,
        )
        out.extend(resp.audio_content)
    return bytes(out)
