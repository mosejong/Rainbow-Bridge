"""임베딩 — 텍스트를 벡터로 변환 (Gemini OpenAI 호환 `/embeddings`).

`provider.py` 의 OpenAI 클라이언트 패턴을 그대로 재사용합니다. 같은 Gemini
키·base_url 로 `/embeddings` 를 호출하므로 추가 의존성(torch·sentence-transformers)
없이 동작합니다.

Gemini `gemini-embedding-001` 은 기본 3072 차원이며, 더 작은 차원으로 자르면(MRL)
벡터가 정규화돼 있지 않습니다. 그래서 `EMBED_DIM>0` 으로 차원을 줄여 요청하면
여기서 **L2 재정규화**를 합니다(Google 권고 — 코사인 검색 정확도 유지).
"""

from __future__ import annotations

import math
import time
from functools import lru_cache
from typing import Final, List, Optional

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)

from .config import get_rag_config


class EmbeddingError(RuntimeError):
    """임베딩 호출이 재시도 후에도 실패했을 때."""


# 일시적 오류 → 재시도. (인증 실패·400 등 영구 오류는 즉시 실패) — provider.py 와 동일.
_RETRYABLE: Final[tuple[type[Exception], ...]] = (
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
)


@lru_cache(maxsize=1)
def _client() -> OpenAI:
    """OpenAI 호환 클라이언트(설정 기반, 1회 생성 후 캐시)."""
    cfg = get_rag_config()
    if not cfg.api_key:
        raise EmbeddingError(
            "임베딩 API 키가 비어 있습니다(.env 의 LLM_API_KEY). .env.example 참고."
        )
    return OpenAI(api_key=cfg.api_key, base_url=cfg.embed_base_url, timeout=cfg.timeout)


def _sleep_backoff(attempt: int) -> None:
    """지수 백오프: 0.5s, 1s, 2s ..."""
    time.sleep(0.5 * (2**attempt))


def _l2_normalize(vec: List[float]) -> List[float]:
    """벡터를 단위 길이로 정규화(0 벡터는 그대로)."""
    norm = math.sqrt(sum(x * x for x in vec))
    if norm == 0.0:
        return vec
    return [x / norm for x in vec]


def embed_texts(texts: List[str]) -> List[List[float]]:
    """여러 텍스트를 한 번에 임베딩합니다.

    Args:
        texts: 임베딩할 문자열 목록.

    Returns:
        각 텍스트의 벡터 목록(입력 순서 유지). 빈 입력이면 빈 리스트.

    Raises:
        EmbeddingError: 키 누락 또는 재시도 후에도 호출 실패.
    """
    if not texts:
        return []

    cfg = get_rag_config()
    client = _client()

    kwargs: dict = {"model": cfg.embed_model, "input": texts}
    if cfg.embed_dim:  # 0 이면 모델 기본 차원 사용(요청에 미포함)
        kwargs["dimensions"] = cfg.embed_dim

    last_err: Optional[Exception] = None
    for attempt in range(cfg.max_retries + 1):
        try:
            resp = client.embeddings.create(**kwargs)
            vecs = [list(item.embedding) for item in resp.data]
            if cfg.embed_dim:  # 잘린 차원은 비정규화 → 재정규화
                vecs = [_l2_normalize(v) for v in vecs]
            return vecs
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

    raise EmbeddingError(
        f"임베딩 호출 실패 ({cfg.embed_model}): {last_err}"
    ) from last_err


def embed_query(text: str) -> List[float]:
    """단일 질문 텍스트를 임베딩합니다(검색용 편의 함수)."""
    return embed_texts([text])[0]
