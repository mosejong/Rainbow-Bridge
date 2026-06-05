"""검색 — 질문과 의미가 가까운 문서 top-k 를 반환합니다.

다른 모듈(예: 추모 메시지 프롬프트 조립)이 import 해서 쓰는 **공개 API**.
거리(코사인)를 0~1 유사도 점수로 바꿔 돌려줍니다(클수록 가까움).

    from rag import retrieve
    hits = retrieve("산책하던 게 그리워요", k=4)
    # [{"text": ..., "score": 0.87, "metadata": {...}}, ...]
"""

from __future__ import annotations

from typing import List, Optional, TypedDict

from .config import get_rag_config
from .embeddings import embed_query
from .store import get_collection


class Hit(TypedDict):
    text: str
    score: float  # 코사인 유사도(1 - 거리). 클수록 의미가 가까움
    metadata: dict


def retrieve(
    query: str,
    k: Optional[int] = None,
    *,
    where: Optional[dict] = None,
) -> List[Hit]:
    """질문과 가까운 문서를 검색합니다.

    Args:
        query: 검색할 질문/문장.
        k: 가져올 개수. None 이면 설정의 `RAG_TOP_K`.
        where: ChromaDB 메타데이터 필터. 예: ``{"category": "memorial"}``.

    Returns:
        유사도 내림차순 Hit 목록. 컬렉션이 비어 있으면 빈 리스트.
    """
    cfg = get_rag_config()
    top_k = cfg.top_k if k is None else k

    col = get_collection()
    count = col.count()
    if count == 0:
        return []

    qv = embed_query(query)
    query_kwargs: dict = {"query_embeddings": [qv], "n_results": min(top_k, count)}
    if where:
        query_kwargs["where"] = where
    res = col.query(**query_kwargs)

    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    hits: List[Hit] = []
    for i, doc in enumerate(docs):
        meta = metas[i] if i < len(metas) and metas[i] else {}
        dist = float(dists[i]) if i < len(dists) else 0.0
        hits.append({"text": doc, "score": 1.0 - dist, "metadata": meta})
    return hits
