"""벡터 스토어 — ChromaDB(로컬 영속). 임베딩은 우리가 직접 주입합니다.

`embedding_function` 을 지정하지 않으므로 Chroma 기본 임베더(sentence-transformers)
다운로드가 일어나지 않습니다. add/query 시 `embeddings.py` 로 계산한 벡터를 직접
넘깁니다. 거리 척도는 코사인(`hnsw:space=cosine`).

저장 폴더(`CHROMA_PERSIST_DIR`)는 로컬 디스크에 영속됩니다(.gitignore 처리).
"""

from __future__ import annotations

from typing import Dict

import chromadb

from .config import get_rag_config

# persist_dir 별 클라이언트 캐시(같은 경로는 재사용 — 테스트는 경로가 달라 격리됨).
_clients: Dict[str, "chromadb.api.ClientAPI"] = {}


def _client() -> "chromadb.api.ClientAPI":
    cfg = get_rag_config()
    if cfg.persist_dir not in _clients:
        _clients[cfg.persist_dir] = chromadb.PersistentClient(path=cfg.persist_dir)
    return _clients[cfg.persist_dir]


def get_collection():
    """설정의 컬렉션을 가져오거나 없으면 생성합니다(코사인 거리)."""
    cfg = get_rag_config()
    return _client().get_or_create_collection(
        name=cfg.collection,
        metadata={"hnsw:space": "cosine"},
    )
