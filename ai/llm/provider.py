"""LLM provider — 로컬(Ollama)·Gemini·PERSO 를 OpenAI 호환으로 통일한 추상화.

`memorial.generate_message` 등 LLM 기능은 이 모듈의 `generate` 를 주입받아 실제
모델을 호출합니다(provider 추상화 — ../CLAUDE.md §4). Gemini·Ollama·PERSO 모두
OpenAI 호환 엔드포인트라 `config` 의 base_url/model/api_key 만 바꾸면 동일하게 동작.

호출이 일시적으로 실패하면(타임아웃·레이트리밋·5xx) 짧게 재시도하고, 끝내 실패하면
`LLMError` 로 감싸 던집니다(추론 실패 graceful — 상위에서 안내로 대체 가능).
"""

from __future__ import annotations

import time
from functools import lru_cache
from typing import Final, Optional

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)

from .config import get_config


class LLMError(RuntimeError):
    """LLM 호출이 재시도 후에도 실패했을 때."""


# 일시적 오류 → 재시도. (인증 실패·400 등 영구 오류는 즉시 실패)
_RETRYABLE: Final[tuple[type[Exception], ...]] = (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
)


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    """OpenAI 호환 클라이언트(설정 기반, 1회 생성 후 캐시)."""
    cfg = get_config()
    if not cfg.api_key:
        raise LLMError(
            "LLM_API_KEY 가 비어 있습니다. .env 에 키를 설정하세요(.env.example 참고)."
        )
    return OpenAI(api_key=cfg.api_key, base_url=cfg.base_url, timeout=cfg.timeout)


def _sleep_backoff(attempt: int) -> None:
    """지수 백오프: 0.5s, 1s, 2s ..."""
    time.sleep(0.5 * (2**attempt))


def generate(
    prompt: str,
    *,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    json_mode: bool = False,
) -> str:
    """프롬프트를 LLM 에 보내고 응답 텍스트를 반환합니다.

    Args:
        prompt: 모델에 보낼 전체 프롬프트(시스템+사용자 합본 문자열).
        max_tokens: 생성 토큰 상한. None 이면 config 기본값.
        temperature: 샘플링 온도. None 이면 config 기본값.
        json_mode: True 면 구조화 JSON 출력 강제(⑦ 위기 분류에서 사용).

    Returns:
        모델 응답 문자열(앞뒤 공백 제거).

    Raises:
        LLMError: 설정 누락 또는 재시도 후에도 호출 실패.
    """
    cfg = get_config()
    client = _client()

    kwargs: dict = {
        "model": cfg.model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": cfg.max_tokens if max_tokens is None else max_tokens,
        "temperature": cfg.temperature if temperature is None else temperature,
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    # thinking 제어(Gemini): 빈 값이면 미전송(미지원 provider 호환).
    if cfg.reasoning_effort:
        kwargs["reasoning_effort"] = cfg.reasoning_effort

    last_err: Optional[Exception] = None
    for attempt in range(cfg.max_retries + 1):
        try:
            resp = client.chat.completions.create(**kwargs)
            return (resp.choices[0].message.content or "").strip()
        except _RETRYABLE as e:
            last_err = e
            if attempt < cfg.max_retries:
                _sleep_backoff(attempt)
                continue
            break
        except APIStatusError as e:  # 5xx 만 재시도, 4xx 는 즉시 실패
            last_err = e
            if e.status_code >= 500 and attempt < cfg.max_retries:
                _sleep_backoff(attempt)
                continue
            break

    raise LLMError(
        f"LLM 호출 실패 ({cfg.provider}/{cfg.model}): {last_err}"
    ) from last_err
