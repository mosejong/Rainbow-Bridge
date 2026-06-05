"""인제스트 — 위로글 코퍼스(JSON)를 임베딩해 ChromaDB 에 적재합니다.

코퍼스 형식 (JSON 배열):
    [
      {"id": "선택", "text": "위로글 본문", "metadata": {"선택": "값"}},
      ...
    ]

실행 (ai 디렉터리에서):
    python -m rag.ingest                         # RAG_CORPUS_PATH 기본 경로 사용
    python -m rag.ingest --corpus rag/data/corpus.sample.json

⚠️ 실제 위로글 코퍼스는 콘텐츠 담당(반소람)이 채웁니다. 윤리 경계(1인칭·부활 금지,
   1393)는 코퍼스 텍스트에도 그대로 적용해야 합니다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import List, Optional

from .config import get_rag_config
from .embeddings import embed_texts
from .store import get_collection


def _stable_id(text: str) -> str:
    """본문 기반 안정 ID — 재실행 시 같은 글은 같은 ID(중복 적재 방지)."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def _load_corpus(path: str) -> List[dict]:
    """코퍼스 JSON 을 읽어 {id, text, metadata} 목록으로 정규화합니다."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("코퍼스는 JSON 배열이어야 합니다: [{text, ...}, ...]")

    source = Path(path).name
    items: List[dict] = []
    for row in raw:
        text = str((row or {}).get("text", "") or "").strip()
        if not text:
            continue
        # Chroma 는 빈 metadata 를 거부하므로 최소 source 키를 보장합니다.
        metadata = dict(row.get("metadata") or {})
        metadata.setdefault("source", source)
        items.append(
            {
                "id": str(row.get("id") or _stable_id(text)),
                "text": text,
                "metadata": metadata,
            }
        )
    return items


def ingest_corpus(path: Optional[str] = None, *, batch_size: int = 64) -> int:
    """코퍼스를 임베딩해 벡터스토어에 upsert 합니다.

    Args:
        path: 코퍼스 JSON 경로. None 이면 설정의 `RAG_CORPUS_PATH`.
        batch_size: 한 번에 임베딩할 문서 수.

    Returns:
        적재(또는 갱신)한 문서 수.
    """
    cfg = get_rag_config()
    src = path or cfg.corpus_path
    items = _load_corpus(src)
    if not items:
        return 0

    col = get_collection()
    for start in range(0, len(items), batch_size):
        chunk = items[start : start + batch_size]
        vecs = embed_texts([it["text"] for it in chunk])
        col.upsert(
            ids=[it["id"] for it in chunk],
            embeddings=vecs,
            documents=[it["text"] for it in chunk],
            metadatas=[it["metadata"] for it in chunk],
        )
    return len(items)


def seed_if_empty(path: Optional[str] = None) -> int:
    """**콜드 스타트 시딩** — 컬렉션이 비어 있을 때만 코퍼스를 1회 적재합니다.

    서버 첫 기동 시 빈 벡터스토어를 채우는 용도. 컬렉션에 문서가 이미 있으면
    그대로 두고 0 을 반환합니다(멱등).

    ⚠️ **재적재 자동화가 아닙니다.** corpus.json 을 고친 뒤 다시 적재하는 것은
       콘텐츠 담당(반소람)의 수동 경로(`python -m rag.ingest`) 책임입니다
       (ROLES_RAG.md §3·eval/README). 이 함수는 컬렉션이 비어야만 동작합니다.

    ⚠️ **import 시 자동 실행 금지.** 임베딩 API(LLM_API_KEY)·네트워크가 필요하므로
       모듈 로드가 아니라 서버 시작 hook 등에서 **명시적으로** 호출하세요.

    Returns:
        새로 적재한 문서 수. 이미 차 있으면 0.
    """
    cfg = get_rag_config()
    col = get_collection()
    existing = col.count()
    if existing > 0:
        print(
            f"[RAG seed] 컬렉션 '{cfg.collection}' 이미 {existing}개 적재됨 → 시딩 건너뜀"
        )
        return 0

    src = path or cfg.corpus_path
    is_sample = "sample" in Path(src).name.lower()
    n = ingest_corpus(src)
    if is_sample:
        print(
            f"[RAG seed] ⚠️ 샘플 자리표시 {n}개를 운영 컬렉션 '{cfg.collection}'에 적재 "
            f"← {src} — 실제 위로글 아님(반소람 운영 코퍼스 교체 전까지 임시)"
        )
    else:
        print(f"[RAG seed] 콜드 스타트 적재 {n}개 → '{cfg.collection}' ← {src}")
    return n


def main() -> None:
    parser = argparse.ArgumentParser(description="위로글 코퍼스를 ChromaDB 에 적재")
    parser.add_argument(
        "--corpus",
        default=None,
        help="코퍼스 JSON 경로(기본: RAG_CORPUS_PATH)",
    )
    args = parser.parse_args()

    n = ingest_corpus(args.corpus)
    cfg = get_rag_config()
    print(f"적재 완료: {n}개 → collection='{cfg.collection}' @ {cfg.persist_dir}")


if __name__ == "__main__":
    main()
