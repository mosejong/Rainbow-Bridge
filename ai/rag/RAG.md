# RAG.md — 레인보우 브릿지 RAG 쉽게 보기

> 우리 프로젝트의 **RAG가 무엇이고, 어떻게 굴러가고, 어떻게 손대는지**를 한 번에 보는 안내서입니다.
> 작성·관리: 반소람(corpus 콘텐츠 + `ai/llm` 연결). 파이프라인 책임 경계·역할분담은 [ROLES_RAG.md](ROLES_RAG.md), 윤리 경계는 [../../CLAUDE.md](../../CLAUDE.md) §0 우선.

---

## 1. 한눈에 — 파이프라인

```
 corpus.json              embeddings.py          store.py (ChromaDB)
 (글 + 메타데이터)   ──▶   글을 숫자벡터로    ──▶  벡터 + 메타 저장
        │                  (Gemini 임베딩)         (ai/rag/_chroma)
        │  python -m ai.rag.ingest  ← 이 명령이 위 화살표를 실행(적재)
        │
        ▼
 retrieve.py  ──  질문을 벡터로 바꿔 가까운 글 top-k 검색
        │         retrieve(query, k=3, where={"category": "mission"})
        ▼
 ai/llm 프롬프트  ──  찾은 글을 "참고 예시"로 끼워 LLM 생성
 (memorial / mission / funeral)
```

- **임베딩**은 별도 키가 필요 없습니다 → 기존 **Gemini 키(`LLM_API_KEY`)를 재사용**합니다. ([config.py](config.py))
- 저장소는 로컬 **ChromaDB**(`ai/rag/_chroma` 폴더, 컬렉션 `consolation`).

---

## 2. corpus 현황 — 지금 무엇이 들어있나

`ai/rag/data/corpus.json` 기준 (총 **63건**):

| category | 개수 | 용도 | 쓰는 코드 | 상태 |
|----------|:---:|------|-----------|------|
| `memorial` | 45 | 추모·위로 메시지 생성 (③) | [../llm/memorial.py](../llm/memorial.py) `where={"category":"memorial"}` k=3 | ✅ 연결됨 |
| `funeral` | 13 | 장례 안내 Q&A | [../llm/funeral.py](../llm/funeral.py) `where={"category":"funeral"}` k=3 | ✅ 연결됨 |
| `mission` | 5 | 일상복귀 미션 추천 (⑤) — 모두 **반려동물이 떠난 뒤** 미션 | [../llm/mission.py](../llm/mission.py) `where={"category":"mission"}` k=3 | ✅ 연결됨 |

> 🚫 **위기 감지(⑦)·건강/증상·1인칭 편지에는 RAG를 붙이지 않습니다** (안전·윤리 — [ROLES_RAG.md](ROLES_RAG.md) §1).

### 검색은 반드시 `category` 필터로 분리

한 컬렉션에 3종류 글이 섞여 있으므로, **항상 `where`로 카테고리를 좁혀야** 엉뚱한 글이 안 섞입니다.

```python
from ai.rag.retrieve import retrieve
hits = retrieve("집 앞 산책이라도 해볼까요", k=3, where={"category": "mission"})
# hits = [{"text": "...", "score": 0.86, "metadata": {...}}, ...]  (유사도 내림차순)
```

---

## 3. 폴더·파일 지도 (`ai/rag/`)

| 파일 | 하는 일 |
|------|---------|
| `data/corpus.json` | **실제 운영 corpus** — 우리가 채우는 글 + 메타데이터 |
| `data/corpus.sample.json` | 데모용 샘플(5개). config 기본 경로가 이걸 가리킴 → §5 함정 주의 |
| `config.py` | `.env` 값 읽기 (임베딩 모델·차원·top_k·저장 경로 등) |
| `embeddings.py` | 글 → 벡터 (Gemini `gemini-embedding-001`, 768차원) |
| `store.py` | ChromaDB 컬렉션 핸들 |
| `ingest.py` | corpus.json을 임베딩해 ChromaDB에 **적재(upsert)** |
| `retrieve.py` | 질문과 가까운 글 top-k 검색 (**공개 API**) |
| `eval/` | 검색 품질 측정(Hit@1 등) — 정환주 도구 |
| `ROLES_RAG.md` | 역할분담·책임 경계 |
| `RAG.md` | (이 문서) RAG 사용 안내 |

---

## 4. 메타데이터 규칙 — 글 한 개의 형식

```json
{
  "id": "walk-01",
  "text": "함께 걷던 그 길이 달라 보이는 날이 있습니다. ...",
  "metadata": {
    "category": "memorial",   // ✅ 필수 — 검색 필터의 기준
    "topic": "산책"            // 토픽(eval 정답 라벨과 글자까지 일치해야 함)
  }
}
```

- **`category`는 필수** (없으면 검색 필터에서 빠짐).
- `id`를 비우면 본문 해시로 자동 부여(중복 적재 방지). 같은 글은 다시 넣어도 1건.

### 미션 "논문 근거"는 corpus가 아니라 코드에 있음

미션이 "왜 회복에 도움 되는지"를 보여주는 근거는 corpus 메타가 아니라
**분류(category)별 한 줄**로 코드에 둡니다 → [../llm/prompts/mission.py](../llm/prompts/mission.py)
`CATEGORY_RATIONALE` (5개 분류 ↔ 5개 회복 이론). 미션이 나올 때 그 분류의 근거가
자동으로 따라붙습니다([../llm/mission.py](../llm/mission.py)). LLM 이 지어내는 게 아니라
**큐레이션된 근거**라 일관·안전합니다.

---

## 5. 손대는 법 — corpus 추가/수정 워크플로

corpus를 고쳤으면 **반드시 재적재**해야 검색에 반영됩니다. JSON만 고치면 ChromaDB는 옛날 그대로예요.

```bash
# 1) data/corpus.json 편집 (글 추가 / 메타 보강)

# 2) 재적재 — 레포 루트에서 실행
python -m ai.rag.ingest --corpus ai/rag/data/corpus.json

# 3) (선택) 검색 품질 확인 — Hit@1 떨어지지 않는지
python -m ai.rag.eval.eval_retrieval
```

> ⚠️ **함정:** `config.py`의 기본 corpus 경로는 데모용 `corpus.sample.json`입니다.
> 그래서 운영 `corpus.json`을 적재할 땐 **`--corpus ai/rag/data/corpus.json`을 꼭 붙이거나**,
> `.env`에 `RAG_CORPUS_PATH=ai/rag/data/corpus.json`을 지정하세요. 안 그러면 샘플 5개만 적재됩니다.

### 윤리 경계는 corpus 텍스트에도 그대로

- ❌ 반려동물 1인칭/부활 표현 금지. ✅ **보호자를 향한 상징적 위로·기억**만.
- 🚨 위기 안내 번호 `1393`은 임의 변경 금지.
- 프롬프트뿐 아니라 **corpus 글·eval 쿼리에도** 같은 경계를 적용합니다.

---

## 6. 설정값 요약 (`.env` / [config.py](config.py))

| 키 | 기본값 | 의미 |
|----|--------|------|
| `LLM_API_KEY` | (필수) | 임베딩에 재사용하는 Gemini 키 |
| `EMBED_MODEL` | `gemini-embedding-001` | 임베딩 모델 |
| `EMBED_DIM` | `768` | 임베딩 차원 |
| `CHROMA_PERSIST_DIR` | `ai/rag/_chroma` | 벡터 저장 폴더 |
| `RAG_COLLECTION` | `consolation` | 컬렉션 이름 |
| `RAG_TOP_K` | `4` | 검색 기본 개수(호출 시 `k`로 덮어씀) |
| `RAG_CORPUS_PATH` | `corpus.sample.json` | 적재 기본 경로(운영은 `--corpus`로 지정) |

> 🚫 키는 `.env`에만. 코드·문서·커밋에 하드코딩 금지 (`.env.example`엔 빈 값만).

---

## 7. 더 보기

- [ROLES_RAG.md](ROLES_RAG.md) — RAG 역할분담·책임 경계·corpus 도메인 우선순위
- [eval/README.md](eval/README.md) — 검색 품질 평가 도구 사용법
- [../CLAUDE.md](../CLAUDE.md) — AI 파트 가이드 / [../llm/CLAUDE.md](../llm/CLAUDE.md) — LLM 영역
- [../../CLAUDE.md](../../CLAUDE.md) §3 — 팀 공통 RAG 활용 지침(4개 category 표)
