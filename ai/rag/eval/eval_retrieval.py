"""RAG 검색 품질 실증 — 라벨된 쿼리셋으로 의미검색 정확도를 측정합니다.

기존 `corpus.sample.json`(자리표시 5개)은 토픽 단어가 1개씩만 달라 *단어매칭*만
검증됩니다. 여기서는 문서와 **표현이 겹치지 않는 패러프레이즈 쿼리**(예: 문서 "골목을
함께 걷던" ↔ 쿼리 "동네 한 바퀴 돌던")로 임베딩 기반 *의미검색*이 실제로 맞는 주제를
끌어오는지 봅니다.

- 실 임베딩(Gemini, `.env` 의 `LLM_API_KEY`)으로 호출 → 진짜 품질 수치.
- eval 전용 컬렉션/저장폴더로 격리 → 운영 `consolation` 컬렉션 미오염.
- 지표: Hit@1 · Hit@3 · MRR (검색 결과 문서의 `metadata.topic` 이 정답 토픽과 일치하는지).

실행 (ai 디렉터리에서):
    python -m rag.eval.eval_retrieval
    python -m rag.eval.eval_retrieval --k 5
    # 운영/다른 corpus 평가 (대응 쿼리셋 동반 필수):
    python -m rag.eval.eval_retrieval --corpus ../data/corpus.json --queries <쿼리셋.json>

⚠️ 기본 코퍼스/쿼리는 **평가용 데모**입니다. 운영 위로글 코퍼스는 콘텐츠 담당(반소람)이 채웁니다.
   --corpus 로 다른 corpus 를 지정해도 적재는 항상 격리 컬렉션(rag_eval/_chroma_eval)에만 →
   운영 consolation 컬렉션은 오염되지 않습니다.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Optional

# Windows 콘솔(cp949)에서도 한국어·기호가 깨지지 않게 stdout 을 UTF-8 로.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):  # pragma: no cover - 환경 의존
    pass

_HERE = Path(__file__).resolve().parent
_EVAL_CORPUS = _HERE / "eval_corpus.json"
_EVAL_QUERIES = _HERE / "eval_queries.json"


def _setup_isolated_env() -> None:
    """eval 전용 저장폴더/컬렉션으로 격리(운영 데이터 미오염). 이미 지정됐으면 존중."""
    os.environ.setdefault("CHROMA_PERSIST_DIR", str(_HERE / "_chroma_eval"))
    os.environ.setdefault("RAG_COLLECTION", "rag_eval")


def _short(text: str, n: int = 28) -> str:
    return text if len(text) <= n else text[:n] + "..."


def run_eval(
    k: int = 3,
    corpus_path: Optional[str] = None,
    queries_path: Optional[str] = None,
) -> dict:
    """corpus 를 적재하고 쿼리셋으로 검색 정확도를 측정해 결과를 출력합니다.

    corpus_path/queries_path 미지정 시 평가용 데모 셋(eval_corpus/eval_queries)을 씁니다.
    어떤 corpus 를 지정하든 적재는 격리 컬렉션(rag_eval/_chroma_eval)에만 → 운영 미오염.
    """
    # 격리 환경을 먼저 잡은 뒤 import(설정이 환경변수를 읽음).
    _setup_isolated_env()
    from ..ingest import ingest_corpus
    from ..retrieve import retrieve

    corpus = Path(corpus_path) if corpus_path else _EVAL_CORPUS
    q_path = Path(queries_path) if queries_path else _EVAL_QUERIES

    n = ingest_corpus(str(corpus))
    queries: List[dict] = json.loads(q_path.read_text(encoding="utf-8"))

    print(
        f"\ncorpus='{corpus.name}' · 쿼리셋='{q_path.name}' · 적재 {n}개 · "
        f"쿼리 {len(queries)}개 · top-{k} · 컬렉션='{os.environ['RAG_COLLECTION']}'\n"
    )
    print(f"{'쿼리':<26}{'정답':<8}{'결과(rank)':<10}{'top-1 (topic/score)'}")
    print("-" * 86)

    hit1 = hit_k = 0
    rr_sum = 0.0
    for q in queries:
        query = q["query"]
        expected = q["expected_topic"]
        hits = retrieve(query, k=k)

        rank: Optional[int] = None
        for i, h in enumerate(hits, start=1):
            if h["metadata"].get("topic") == expected:
                rank = i
                break

        if rank == 1:
            hit1 += 1
        if rank is not None:
            hit_k += 1
            rr_sum += 1.0 / rank

        top = hits[0] if hits else None
        top_str = (
            f"{top['metadata'].get('topic', '?')}/{top['score']:.2f}"
            if top
            else "(없음)"
        )
        mark = f"O {rank}" if rank == 1 else (f"~ {rank}" if rank else "X -")
        print(
            f"{_short(query):<26}{expected:<8}{mark:<10}{top_str}  {_short(top['text']) if top else ''}"
        )

    total = len(queries) or 1
    metrics = {
        "hit@1": hit1 / total,
        f"hit@{k}": hit_k / total,
        "mrr": rr_sum / total,
        "queries": total,
        "docs": n,
    }
    print("-" * 86)
    print(
        f"Hit@1 = {metrics['hit@1']:.0%}   "
        f"Hit@{k} = {metrics[f'hit@{k}']:.0%}   "
        f"MRR = {metrics['mrr']:.3f}\n"
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="RAG 검색 품질 실증(의미검색 정확도)")
    parser.add_argument("--k", type=int, default=3, help="top-k (기본 3)")
    parser.add_argument(
        "--corpus", type=str, default=None, help="평가할 corpus json 경로 (기본: eval_corpus.json)"
    )
    parser.add_argument(
        "--queries", type=str, default=None, help="쿼리셋 json 경로 (기본: eval_queries.json)"
    )
    args = parser.parse_args()
    run_eval(k=args.k, corpus_path=args.corpus, queries_path=args.queries)


if __name__ == "__main__":
    main()
