"""LLM 설정 — .env 값을 한곳에서 읽어 provider 가 사용합니다.

엔진 결정(2026-06-02): 개발용 **Gemini API**(OpenAI 호환 엔드포인트).
로컬 폴백(Ollama)·시연용 PERSO 도 모두 OpenAI 호환이라, `base_url`·`model`·`api_key`
만 바꾸면 같은 코드로 동작합니다. 상세 근거 → MODEL_NOTES.md.

🚫 키는 `.env` 에만(=`.env.example` 참고). 코드·문서에 하드코딩 금지.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Final

try:  # dotenv 가 없으면 OS 환경변수만 사용(graceful)
    from dotenv import load_dotenv

    load_dotenv()
except ModuleNotFoundError:  # pragma: no cover
    pass

# .env 미설정 시 폴백 기본값 (Gemini OpenAI 호환 엔드포인트)
_DEFAULT_BASE_URL: Final[str] = (
    "https://generativelanguage.googleapis.com/v1beta/openai/"
)
_DEFAULT_MODEL: Final[str] = "gemini-2.5-flash"


@dataclass(frozen=True)
class LLMConfig:
    """LLM 호출에 필요한 설정 묶음."""

    provider: str  # gemini | ollama | perso ... (기록용)
    base_url: str
    model: str
    api_key: str
    timeout: float  # 단일 요청 타임아웃(초)
    max_retries: int  # 일시적 오류 재시도 횟수
    max_tokens: int  # 기본 생성 토큰 상한
    temperature: float  # 기본 온도
    reasoning_effort: str  # Gemini thinking 제어("none"=끔). 빈 값이면 미전송


# Gemini 2.5-flash 는 thinking(내부 추론)이 기본 ON 이라 추론이 토큰을 먹어
# 응답이 잘립니다. 추모/미션 같은 생성엔 thinking 이 불필요하므로 기본 "none".
# (thinking 미지원 provider 는 .env LLM_REASONING_EFFORT= 로 비워 끄세요.)


def get_config() -> LLMConfig:
    """현재 환경변수로부터 설정을 읽어옵니다."""
    return LLMConfig(
        provider=os.getenv("LLM_PROVIDER", "gemini"),
        base_url=os.getenv("LLM_BASE_URL", _DEFAULT_BASE_URL),
        model=os.getenv("LLM_MODEL", _DEFAULT_MODEL),
        api_key=os.getenv("LLM_API_KEY", ""),
        timeout=float(os.getenv("LLM_TIMEOUT", "30")),
        max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "512")),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
        reasoning_effort=os.getenv("LLM_REASONING_EFFORT", "none"),
    )
