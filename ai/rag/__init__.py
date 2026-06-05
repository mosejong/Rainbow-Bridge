"""레인보우 브릿지 RAG 패키지 (ai/rag) — ChromaDB 기반 검색.

위로글 코퍼스를 임베딩해 로컬 ChromaDB 에 저장하고(ingest), 보호자의 글과
의미가 가까운 문서를 검색합니다(retrieve). 임베딩은 기존 Gemini 키를 재사용하므로
추가 모델·무거운 의존성(torch 등)이 필요 없습니다.

⚠️ 윤리 경계(루트/ai CLAUDE.md): 검색 결과를 메시지에 쓸 때도 반려동물 1인칭·부활
   출력 금지 원칙은 그대로 적용됩니다(연결은 소비 측 책임).

공개 API (ai 디렉터리 기준):
    from rag import retrieve, ingest_corpus
"""

__all__ = ["retrieve", "ingest_corpus"]


# 지연 임포트 — `python -m rag.ingest` 실행 시 이중 임포트 경고를 피하고,
# `import rag` 만으로 chromadb 까지 끌어오지 않도록 합니다.
def __getattr__(name: str):
    if name == "retrieve":
        from .retrieve import retrieve

        return retrieve
    if name == "ingest_corpus":
        from .ingest import ingest_corpus

        return ingest_corpus
    raise AttributeError(f"module 'rag' has no attribute {name!r}")
