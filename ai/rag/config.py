"""RAG 설정 — .env 값을 한곳에서 읽어 임베딩·벡터스토어가 사용합니다.

임베딩은 **기존 Gemini 키(LLM_API_KEY)·엔드포인트를 재사용**합니다(별도 키 불필요).
LLM 쪽 config.py 와 같은 방식(.env → 데이터클래스)이라 패턴이 일관됩니다.

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

# 임베딩 기본값 (Gemini OpenAI 호환 엔드포인트 — LLM 과 동일 base).
_DEFAULT_EMBED_BASE_URL: Final[str] = (
    "https://generativelanguage.googleapis.com/v1beta/openai/"
)
_DEFAULT_EMBED_MODEL: Final[str] = "gemini-embedding-001"


@dataclass(frozen=True)
class RAGConfig:
    """RAG(임베딩+벡터스토어)에 필요한 설정 묶음."""

    api_key: str  # 임베딩 API 키(= LLM_API_KEY 재사용)
    embed_base_url: str
    embed_model: str
    embed_dim: (
        int  # 0 이면 모델 기본 차원(3072) 사용. >0 이면 그 차원으로 요청+재정규화
    )
    timeout: float
    max_retries: int
    persist_dir: str  # ChromaDB 로컬 저장 폴더
    collection: str
    top_k: int
    corpus_path: str


def get_rag_config() -> RAGConfig:
    """현재 환경변수로부터 RAG 설정을 읽어옵니다."""
    return RAGConfig(
        api_key=os.getenv("LLM_API_KEY", ""),
        embed_base_url=os.getenv(
            "EMBED_BASE_URL",
            os.getenv("LLM_BASE_URL", _DEFAULT_EMBED_BASE_URL),
        ),
        embed_model=os.getenv("EMBED_MODEL", _DEFAULT_EMBED_MODEL),
        embed_dim=int(os.getenv("EMBED_DIM", "768")),
        timeout=float(os.getenv("LLM_TIMEOUT", "30")),
        max_retries=int(os.getenv("LLM_MAX_RETRIES", "2")),
        persist_dir=os.getenv("CHROMA_PERSIST_DIR", "ai/rag/_chroma"),
        collection=os.getenv("RAG_COLLECTION", "consolation"),
        top_k=int(os.getenv("RAG_TOP_K", "4")),
        corpus_path=os.getenv("RAG_CORPUS_PATH", "ai/rag/data/corpus.sample.json"),
    )
