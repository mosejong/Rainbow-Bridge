"""RAG 파이프라인 테스트 — 임베딩 API 없이 ChromaDB 왕복을 검증합니다.

실제 Gemini 호출 없이(키 불필요) 동작하도록 `embed_texts`/`embed_query` 를
결정적 가짜 벡터로 교체합니다. 키워드 5개의 등장 여부로 벡터를 만들어,
질문과 같은 주제의 문서가 top-1 으로 나오는지 확인합니다.

chromadb 는 실제로 사용합니다(로컬 임시 폴더에 저장 → 격리).
"""

from __future__ import annotations

import importlib
import json
import math

import pytest

from ..ingest import ingest_corpus
from ..retrieve import retrieve

# 패키지 __init__ 이 retrieve/ingest_corpus 함수를 같은 이름으로 바인딩하므로,
# 모듈 객체는 importlib 로 명시적으로 가져와 monkeypatch 합니다.
ingest_mod = importlib.import_module("rag.ingest")
retrieve_mod = importlib.import_module("rag.retrieve")

_KEYWORDS = ["산책", "밥", "놀이", "잠", "사진"]


def _fake_vec(text: str) -> list[float]:
    """키워드 등장 여부로 만든 단위 벡터(없으면 작은 균일값)."""
    v = [1.0 if kw in text else 0.0 for kw in _KEYWORDS]
    if not any(v):
        v = [0.01] * len(_KEYWORDS)
    norm = math.sqrt(sum(x * x for x in v))
    return [x / norm for x in v]


def _fake_embed_texts(texts):
    return [_fake_vec(t) for t in texts]


def _fake_embed_query(text):
    return _fake_vec(text)


@pytest.fixture()
def rag_env(tmp_path, monkeypatch):
    """임시 chroma 폴더 + 가짜 임베딩으로 격리된 RAG 환경."""
    corpus = [
        {"id": "d-walk", "text": "산책 자리표시 문서", "metadata": {"topic": "산책"}},
        {"id": "d-meal", "text": "밥 자리표시 문서", "metadata": {"topic": "밥"}},
        {"id": "d-play", "text": "놀이 자리표시 문서", "metadata": {"topic": "놀이"}},
    ]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")

    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "_chroma"))
    monkeypatch.setenv("RAG_COLLECTION", "test_consolation")
    # 임베딩만 가짜로 — ingest/retrieve 가 import 한 이름을 직접 교체.
    monkeypatch.setattr(ingest_mod, "embed_texts", _fake_embed_texts)
    monkeypatch.setattr(retrieve_mod, "embed_query", _fake_embed_query)
    return str(path)


def test_ingest_then_retrieve_roundtrip(rag_env):
    n = ingest_corpus(rag_env)
    assert n == 3

    hits = retrieve("오늘 산책 가고 싶었어요", k=2)
    assert hits, "결과가 비어 있으면 안 됨"
    assert hits[0]["text"] == "산책 자리표시 문서"
    assert hits[0]["metadata"]["topic"] == "산책"
    assert 0.0 <= hits[0]["score"] <= 1.0001


def test_metadata_source_defaulted_on_ingest(rag_env, tmp_path):
    # metadata 없는 항목도 source 키가 채워져 Chroma 거부를 피한다.
    corpus = [{"text": "밥 메타없는 문서"}]
    p = tmp_path / "nometa.json"
    p.write_text(json.dumps(corpus, ensure_ascii=False), encoding="utf-8")
    assert ingest_corpus(str(p)) == 1

    hits = retrieve("밥", k=1)
    assert hits[0]["metadata"].get("source") == "nometa.json"


def test_retrieve_empty_collection_returns_empty(rag_env, monkeypatch):
    # 적재하지 않은 다른 컬렉션 → 빈 결과(예외 없이).
    monkeypatch.setenv("RAG_COLLECTION", "empty_coll")
    assert retrieve("아무거나") == []
