# RAG 역할분담 & corpus 도메인 우선순위

> RAG 파이프라인(`ai/rag/`)·eval(`ai/rag/eval/`)·corpus 운영의 **책임 경계**와
> **corpus에 넣을 도메인 우선순위**를 정리합니다.
> 작성: 정환주(RAG 파이프라인·eval·인프라) / corpus 콘텐츠: 반소람.
> 팀 공통·윤리 경계는 [../CLAUDE.md](../CLAUDE.md) 우선.

---

## 1. corpus 도메인 우선순위 (무엇을 RAG에 넣나)

| 도메인 | 반영 | 우선순위 | 이유 | 현재 상태 |
|--------|:----:|:--------:|------|-----------|
| 장례 절차 안내 | ✅ | **1순위** | RAG 교과서적 용도, 정확성 직결 | `funeral.py` 있음 / RAG 미연결 · corpus 토픽 없음 |
| 미션 추천 | ✅ | **2순위** | 개인화 효과 실질적 | `mission.py` 있음 / RAG 미연결 · corpus 토픽 없음 |
| 감정 체크인 | ⚠️ | 보류 | 피드백 기능 여부 먼저 결정 | 백엔드 기능, 미연결 |
| 추모 메시지 | ⚠️ | 조건부 | 코퍼스 확보 방법이 관건 | `prompts/memorial.py`가 `rag_hits` 받을 자리만, 본체 배선 미완 · corpus는 샘플 5개(추억 토픽) |
| 위기 감지 | 🚫 | 제외 | 안전 시스템에 예측 불가능성 추가 위험 | `safety.py` (RAG 미연결 = 의도된 정답) |
| 건강 정보 | 🚫 | 제외 | 서비스 범위 밖 | `triage.py` 있음 / RAG 미연결 |
| 1인칭 편지 | 🚫 | 제외 | 윤리 경계와 충돌 | 없음 ([../CLAUDE.md](../CLAUDE.md) §0 부활·1인칭 금지) |

> 🚫 3개는 **RAG 대상에서 영구 제외**. 특히 위기 감지에 RAG를 붙이는 변경은 막습니다(안전 최우선).

---

## 2. 작업 분담

### 반소람 — corpus 콘텐츠 + ai/llm 연결

| 작업 | 근거 |
|------|------|
| `corpus.json` 보강 — 토픽당 3~5개 위로글 추가 | `ingest.py:13` "실제 위로글 코퍼스는 콘텐츠 담당(반소람)이 채웁니다" |
| `memorial.py`에 `retrieve()` 연결 — `generate_message()`에서 RAG 결과를 프롬프트에 주입 | `ai/llm` 담당 (`prompts/memorial.py`는 `rag_hits` 받을 준비 완료, 본체 호출만 추가) |
| corpus 수정 후 ingest 재실행 — `python -m rag.ingest` | corpus 작업자가 적재까지 책임 |
| eval 실행으로 corpus 품질 확인 — 추가할 때마다 Hit@1 떨어지지 않는지 | corpus 작성자 검증 책임 (도구·실행환경은 정환주가 핸드오프 — §3) |

### 정환주 — RAG 파이프라인 · eval · 인프라

| 작업 | 근거 |
|------|------|
| eval 도구 유지보수 — `ai/rag/eval/` 쿼리셋·지표 갱신 | 본인이 만든 도구 (`fda740c`) |
| eval용 패러프레이즈 쿼리셋 관리 — corpus 토픽 늘면 쿼리 추가 | eval 설계자 (`eval_queries.json`) |
| ChromaDB 운영 인프라 — 서버 배포 시 `_chroma` 볼륨·재적재 자동화 | GPU 서버·인프라 담당 |
| 🚫 경계 유지 — 위기·건강·1인칭에 RAG 붙는 변경 차단 | 안전·윤리 (§1) |

**접점:** 반소람이 corpus 추가 → `ingest` → eval 실행 후 **Hit@1 수치를 정환주에게 공유**. 수치 떨어지면 **정환주가 쿼리셋 보완**.

---

## 3. ⚠️ 분담이 굴러가려면 정환주가 선행할 것

현재 도구·코드 상태상 위 분담에 **구멍**이 있어, 본인이 먼저 처리해야 반소람 작업이 성립합니다.

1. **eval이 운영 corpus를 보게** — 현재 `eval_retrieval.py:35,56`은 `eval_corpus.json`(별도 데모, 격리 컬렉션 `rag_eval`)만 적재. 반소람이 운영 `corpus.json`을 늘려도 Hit@1이 안 움직임.
   → `--corpus` 인자 추가하거나, corpus 토픽 ↔ `eval_queries` 정답라벨 매핑 규칙을 반소람과 합의.
2. **eval 실행 핸드오프** — `CHROMA_PERSIST_DIR`·`LLM_API_KEY` 세팅 + `python -m rag.eval.eval_retrieval` 사용법을 반소람에 전달해야 "반소람이 eval 실행" 칸이 동작.
3. **`retrieve()` 인터페이스 합의** — ✅ 계약 확정·호환 검증 완료 (→ §5). 반소람은 `memorial.py` 배선만 추가.
4. **장례·미션 토픽 확장 대응** — corpus에 장례/미션 토픽이 생기면 eval 쿼리셋에 정답라벨 쿼리 추가(§1 ✅ 2개 도메인).

---

## 4. 현재 corpus 토픽 (참고)

- 운영 샘플(`data/corpus.sample.json`): 산책 · 밥 · 놀이 · 잠 · 사진 — 전부 **추억 기반(추모용) 자리표시**
- eval(`eval/eval_corpus.json`): + 그리움 · 아픔 · 일상복귀 · 작별
- → **장례 · 미션 토픽은 아직 없음.** §1 ✅ 1·2순위 작업 = 이 토픽 신설.

---

## 5. `retrieve()` ↔ 추모 메시지 연결 계약 (반소람 핸드오프)

> 정환주가 `retrieve()` 계약을 고정하고 호환성까지 확인했습니다. 반소람은 아래 배선만 추가하면 됩니다.

### 계약 (정환주 제공 — 변경 없음)

```python
from rag import retrieve
hits = retrieve(query: str, k: int | None = None) -> list[Hit]
# Hit = {"text": str, "score": float, "metadata": dict}
# - score: 코사인 유사도(1-거리), 클수록 가까움 (내림차순 정렬)
# - 컬렉션이 비어 있으면 [] 반환 (예외 아님)
```

### 호환성 (✅ 검증 완료)

- `prompts/memorial.py`의 `_format_rag(hits)`는 **`h["text"]`만** 사용 → `Hit` 키와 정확히 일치, **변환 불필요**.
- `build_user_prompt(..., rag_hits=...)`는 `Optional[List[dict]]`. `None`/`[]`이면 few-shot 자동 생략 → `retrieve()` 빈 결과와 그대로 안전.

### 반소람이 추가할 배선 (`memorial.py` `generate_message`, (2) 프롬프트 조립부)

```python
from rag import retrieve          # 파일 상단

# (2) prompt_kwargs 조립 — 위기 선체크(detect_crisis) 통과 뒤에만 실행됨(현 순서 유지).
query = "  ".join(filter(None, [note, *(pet.get("memories") or [])]))
rag_hits = retrieve(query, k=4) if query.strip() else None
prompt_kwargs = dict(
    ...,                          # 기존 그대로
    rag_hits=rag_hits,            # ← 이 한 줄 추가
)
```

### 반소람 결정 포인트

- **query 소스:** 위 예시는 `note + memories` 결합. note만/memories만 등 검색 품질 보고 조정.
- **k(개수):** few-shot 예시 수. 기본 4 제안.
- **위기 안전:** RAG는 반드시 `detect_crisis` 통과 후에만 호출 (현 (1)→(2) 순서 유지). 위기 입력에 위로글 few-shot 주입 금지.

---

## 6. eval 쿼리셋 작성 규칙 (장례·미션 토픽 확장 대비)

> 도구가 받는 **포맷·규칙**은 정환주가 고정. 실제 쿼리 **콘텐츠**는 운영 corpus에 해당 토픽 문서가 생긴 뒤
> 정환주·반소람 합의로 작성(지금 만들지 않음 — corpus 미존재).

### 포맷 (`eval_queries.json`)

```json
[
  {"query": "검색 문장", "expected_topic": "토픽명"}
]
```

### 규칙

1. `expected_topic` 은 corpus 문서의 `metadata.topic` 과 **글자까지 정확히 일치** (오타 시 전부 오답 처리).
2. **패러프레이즈 원칙** — `query` 는 정답 문서와 **표현이 안 겹치게** 작성. (단어매칭이 아닌 *의미검색* 정확도를 재는 게 목적.) 예: 문서 "동네 골목을 함께 걷던" ↔ 쿼리 "동네 한 바퀴 돌던".
3. 토픽당 **2개 이상** 권장 (현 데모도 산책·밥·작별이 2개씩).
4. 윤리 경계 동일 적용 — 1인칭·부활 표현 금지([../CLAUDE.md](../CLAUDE.md) §0).

### 장례·미션 토픽 추가 절차 (§1 ✅ 1·2순위)

1. (반소람) 운영 corpus 에 `metadata.topic` = `장례`/`미션` 문서 추가.
2. (정환주·반소람 합의) 위 규칙대로 해당 토픽 패러프레이즈 쿼리 추가.
3. (반소람) `--corpus`/`--queries` 로 측정 → `Hit@1` 정환주 공유 (§3·README 핸드오프).

> ⚠️ corpus 토픽과 쿼리 `expected_topic` 의 **명명 규칙(매핑)을 먼저 합의**해야 함. 한쪽만 바꾸면 전부 오답.

---

## 7. ChromaDB 운영/배포 (정환주 제공 · backend 적용 대기)

> 정환주가 **시딩 도구**를 제공. 실제 볼륨 마운트·배포 자동화는 **RAG 통합방식이 정해진 뒤** backend 담당(모세종·김윤한)이 적용.

### 제공된 것 (정환주, 의존 없음)

- **`ingest.seed_if_empty(path=None)`** — **콜드 스타트 시딩**. 컬렉션이 비어 있을 때만 corpus 1회 적재(멱등). 서버 첫 기동 hook에서 호출용.
  - ❗ **재적재 자동화 아님.** corpus 수정 후 재적재는 반소람 수동 경로(`python -m rag.ingest`, §3).
  - ❗ **import 시 자동 실행 안 함.** 임베딩 API·네트워크 필요 → 명시 호출만(CI/테스트 안전).
  - ❗ 현재 운영 corpus 가 `corpus.sample.json`(자리표시)뿐 → 지금 시딩하면 **샘플이 live `consolation` 에 들어감.** 함수가 이 경우 경고 로그를 크게 찍음. **운영 corpus(반소람) 준비 전 프로덕션 시딩 금지.**
- `_chroma` 영속 폴더는 `.gitignore` 처리됨(`.gitignore:70`). 커밋 안 됨.

### ⚠️ 미해결 — 배포 자동화 (통합방식 결정 의존)

현재 `backend/` 는 `rag` 를 import 하지 않고, `docker-compose.yml` 에 `_chroma` 볼륨이 없습니다.
RAG 를 **backend import** 로 둘지 **별도 REST 추론 서버**로 둘지 미확정([../CLAUDE.md](../CLAUDE.md) §3) → 아래는 결정 후 적용.

| 결정 후 챙길 것 | 비고 |
|----------------|------|
| `_chroma` 영속 볼륨 마운트 | 컨테이너 재시작에도 벡터 유지 (`mongo_data` 패턴 참고) |
| 시작 시 `seed_if_empty()` 1회 호출 | import 자동실행 ❌ — 시작 hook/엔트리포인트에서 명시 호출 |
| `LLM_API_KEY` 환경변수 | 임베딩 호출 (이미 `.env`) |
| import 방식이면 | backend 이미지에 `ai/rag` 포함 + 위 볼륨 |
| REST 방식이면 | 별도 RAG 서버 컨테이너에 볼륨·시딩 |

→ **통합방식 결정은 PM/백엔드(모세종) 안건.** 정해지면 정환주가 시딩 hook 연결 지원, backend 가 볼륨·compose 적용.
