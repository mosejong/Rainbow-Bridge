# RAG 검색 품질 실증 (`ai/rag/eval/`)

> 작성: 정환주 · 2026-06-05 · RAG 파이프라인이 **실제로 의미검색이 되는지** 실 임베딩으로 측정.

## 무엇을 검증했나

기존 `data/corpus.sample.json`(자리표시 5개)은 토픽 단어가 1개씩만 달라 **단어매칭**만 확인됨.
여기선 문서와 **표현이 안 겹치는 패러프레이즈 쿼리**로 진짜 *의미검색* 정확도를 잼.

- 예: 문서 "동네 골목을 함께 걷던" ↔ 쿼리 "동네 한 바퀴 돌던" (공통 단어 없음 → 임베딩이 의미로 매칭해야 정답)
- 실 임베딩(Gemini `gemini-embedding-001`, 768차원)으로 호출.
- eval 전용 컬렉션/폴더로 격리 → 운영 `consolation` 미오염.

## 결과 (2026-06-05)

| 지표 | 값 |
|------|-----|
| 문서 / 쿼리 | 15 / 12 |
| **Hit@1** | **100%** |
| Hit@3 | 100% |
| MRR | 1.000 |

→ 패러프레이즈 쿼리 12개 전부 정답 토픽을 **rank 1**로 끌어옴(유사도 0.73~0.83). ChromaDB + Gemini 임베딩 파이프라인이 의미검색으로 정상 동작함을 확인.

## 실행

```bash
cd ai
python -m rag.eval.eval_retrieval        # top-3 (기본 데모셋)
python -m rag.eval.eval_retrieval --k 5
# 다른 corpus 평가 (대응 쿼리셋 동반 필수):
python -m rag.eval.eval_retrieval --corpus ../data/corpus.json --queries <쿼리셋.json>
```

- `.env`(루트)의 `LLM_API_KEY` 필요(임베딩 호출).
- 재실행 안전: 안정 ID upsert + 격리 컬렉션.
- `--corpus`/`--queries` 미지정 시 데모셋 사용. **어떤 corpus 를 지정해도** 적재는 격리 컬렉션(`rag_eval`/`_chroma_eval`)에만 → 운영 `consolation` 미오염.

## 반소람 핸드오프 — corpus 수정 시 회귀 확인

corpus 에 위로글을 추가/수정한 뒤 검색 품질이 떨어지지 않았는지 직접 확인하는 절차.

1. (최초 1회) `.env`(루트)에 `LLM_API_KEY`(Gemini) 설정 확인. 격리 환경은 스크립트가 자동 설정(`setdefault`).
2. corpus 수정 → 적재: `python -m rag.ingest`
3. eval 실행 → `Hit@1`·`Hit@3`·`MRR` 확인.
4. **`Hit@1` 수치를 정환주에게 공유.** 떨어졌으면 정환주가 쿼리셋 보완.

⚠️ **운영 corpus 측정은 대응 쿼리셋이 있어야 가능.** 현재 `eval_queries.json` 은 데모(`eval_corpus`) 전용 →
운영 corpus 토픽(산책·밥… + 장례·미션 신설)에 맞는 쿼리셋은 정환주와 매핑 규칙 합의 후 작성([../ROLES_RAG.md](../ROLES_RAG.md) §3·§5).
그 전까지는 위 **기본 데모 실행으로 도구·환경에 익숙해지는 단계**.

## 한계 / 다음

- **코퍼스·쿼리는 평가용 데모.** 운영 위로글 코퍼스는 콘텐츠 담당(반소람) 채움 → 그때 같은 스크립트로 재측정.
- 토픽 15개 소규모라 100%는 상한 신호일 수 있음 → 운영 코퍼스 규모 커지면 혼동 토픽(예: 산책↔일상복귀) 구분력 재확인 필요.
- 1단계(건강관리) 의료기록 RAG로 확장 시: 일기 데이터모델(모세종) 확정 후 의료 도메인 쿼리셋 추가.

## 파일

- [eval_corpus.json](eval_corpus.json) — 데모 문서 15개(보호자 대상 위로 톤, 1인칭·부활 ❌)
- [eval_queries.json](eval_queries.json) — 패러프레이즈 쿼리 12개 + 정답 토픽
- [eval_retrieval.py](eval_retrieval.py) — 적재→검색→Hit@1·Hit@3·MRR
