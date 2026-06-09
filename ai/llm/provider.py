"""LLM provider — 로컬(Ollama)·Gemini·PERSO 를 OpenAI 호환으로 통일한 추상화.

`memorial.generate_message` 등 LLM 기능은 이 모듈의 `generate` 를 주입받아 실제
모델을 호출합니다(provider 추상화 — ../CLAUDE.md §4). Gemini·Ollama·PERSO 모두
OpenAI 호환 엔드포인트라 `config` 의 base_url/model/api_keys 만 바꾸면 동일하게 동작.

복원력(강사님 6/9 지적 대응):
  1) 429(할당량 소진) → 즉시 다음 키로 전환(LLM_API_KEY=key1,key2 형식).
  2) 모든 키가 소진되면 폴백 모델(LLM_FALLBACK_MODEL, 예: gemini-1.5-flash)로 한 번 더
     전체 키를 재시도 — 무료 할당량은 모델별로 따로라 폴백 모델엔 남아 있을 수 있음.
  3) 타임아웃·5xx 같은 일시적 오류는 같은 키로 재시도(지수 백오프).
끝내 다 실패하면 `LLMError` 를 던집니다(상위에서 graceful 안내로 대체 가능).
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


# generate() 가 끝내 실패(LLMError)했을 때 상위(생성 기능)에서 쓰는 안내문.
# 🚫 실패를 '가짜 생성물'로 숨기지 마세요 — 반드시 명백한 안내문으로만 노출.
#    (펫로스 특성상 가짜 추모 메시지를 진짜로 오해하면 위험)
LLM_UNAVAILABLE_NOTICE: Final[str] = (
    "지금은 메시지를 준비하지 못했어요. 잠시 후 다시 시도해 주세요."
)


@lru_cache(maxsize=8)
def _client(api_key: str, base_url: str, timeout: float) -> OpenAI:
    """키당 OpenAI 호환 클라이언트를 캐시해서 반환합니다."""
    return OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)


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

    429(할당량 소진) 시 다음 키로, 모든 키 소진 시 폴백 모델로 자동 전환.
    전부 실패하면 LLMError.

    Args:
        prompt: 모델에 보낼 전체 프롬프트(시스템+사용자 합본 문자열).
        max_tokens: 생성 토큰 상한. None 이면 config 기본값.
        temperature: 샘플링 온도. None 이면 config 기본값.
        json_mode: True 면 구조화 JSON 출력 강제(⑦ 위기 분류에서 사용).

    Returns:
        모델 응답 문자열(앞뒤 공백 제거).

    Raises:
        LLMError: 키 미설정 또는 모든 키·모델 소진 후에도 호출 실패.
    """
    cfg = get_config()
    if not cfg.api_keys:
        raise LLMError(
            "LLM_API_KEY 가 비어 있습니다. .env 에 키를 설정하세요(.env.example 참고)."
        )

    base_kwargs: dict = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": cfg.max_tokens if max_tokens is None else max_tokens,
        "temperature": cfg.temperature if temperature is None else temperature,
    }
    if json_mode:
        base_kwargs["response_format"] = {"type": "json_object"}
    if cfg.reasoning_effort:
        base_kwargs["reasoning_effort"] = cfg.reasoning_effort

    # 시도할 모델: 기본 모델 → (전 키 소진 시) 폴백 모델. 빈/중복 폴백은 제외.
    models = [cfg.model]
    if cfg.fallback_model and cfg.fallback_model != cfg.model:
        models.append(cfg.fallback_model)

    last_err: Optional[Exception] = None
    for model in models:
        kwargs = {**base_kwargs, "model": model}
        for api_key in cfg.api_keys:
            client = _client(api_key, cfg.base_url, cfg.timeout)
            for attempt in range(cfg.max_retries + 1):
                try:
                    resp = client.chat.completions.create(**kwargs)
                    return (resp.choices[0].message.content or "").strip()
                except RateLimitError as e:
                    last_err = e
                    break  # 429 → 이 키 소진, 다음 키(다 소진되면 다음 모델)로
                except (APITimeoutError, APIConnectionError) as e:
                    last_err = e
                    if attempt < cfg.max_retries:
                        _sleep_backoff(attempt)
                        continue
                    break
                except APIStatusError as e:  # 5xx 재시도, 4xx 즉시 실패
                    last_err = e
                    if e.status_code >= 500 and attempt < cfg.max_retries:
                        _sleep_backoff(attempt)
                        continue
                    break

    tried = "→".join(models)
    raise LLMError(
        f"LLM 호출 실패 — 모든 키·모델 소진 ({cfg.provider}/{tried}): {last_err}"
    ) from last_err
