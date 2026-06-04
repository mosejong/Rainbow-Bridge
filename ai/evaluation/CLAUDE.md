# CLAUDE.md — 평가 리포트 영역 (`ai/evaluation/`)

> 담당: **정환주**. 상위 [../CLAUDE.md](../CLAUDE.md) 규칙을 따르며 평가 영역만 보완합니다.
> 할 일: [../TODO.md](../TODO.md) `ai/evaluation` 블록 · 역할: [../ROLES.md](../ROLES.md).

---

## ⚠️ 혼동 주의 (이름이 같아 헷갈림)

- 여기 "평가" = **서비스 사용 데이터 리포트(MVP ⑧)** — 사용자/팀에게 보여주는 지표.
- **모델 성능 후기**는 여기 아님 → [../llm/MODEL_NOTES.md](../llm/MODEL_NOTES.md) (다름!).

---

## 1. 담당 범위

- MVP ⑧ 평가 지표·집계.

---

## 2. 인터페이스

- `build_report(pet_id, period) -> report`

---

## 3. 지표 (초안 — 팀 합의)

- 사용 횟수 · 감정 변화 추이 · 미션 완료율 · 재방문 등.

---

## 4. 백엔드 계약

- `GET /report/{pet_id}` 데이터 형태 합의.
- 출력 스키마는 프론트 차트/요약 UI 기준으로 정의·문서화.

---

## 5. GPU

- 집계는 GPU 거의 안 씀 → 추론 작업 틈틈이 진행 가능.

---

## 6. LLM 사용량 로깅 — 호출부 연결법 (핸드오프)

> `logs.py` 에 끼우기 쉬운 헬퍼(`LLMLog.from_openai`·`measure_latency`·`log_llm_call`)를 만들어 뒀습니다.
> **LLM 호출부 주인**(③ 메시지=모세종 `backend/.../message.py`, provider=반소람 `ai/llm/provider.py`)이
> 아래처럼 **best-effort 1~2줄**만 끼우면 `admin/usage` 집계가 실데이터로 채워집니다.
> ⚠️ 로그 저장 실패가 **사용자 응답을 깨면 안 됨** → 반드시 `try/except` 로 감싸세요. 원문 텍스트는 저장 안 합니다.

**백엔드(motor·async) — 예: `message.py` `create_message`:**
```python
from ai.evaluation.logs import LLMLog, KIND_MESSAGE, measure_latency

with measure_latency() as t:
    resp = client.chat.completions.create(...)   # 성공 시 resp, 실패 시 None
try:  # best-effort — 실패해도 메시지 응답엔 영향 없음
    log = LLMLog.from_openai(resp, kind=KIND_MESSAGE, pet_id=pet_id,
                             latency_ms=t.ms, ok=resp is not None)
    await mongodb.db["llm_logs"].insert_one(log.to_doc())
except Exception:
    pass
```

**동기 컨텍스트(pymongo/스크립트):** `log_llm_call(collection, resp, kind=KIND_MESSAGE, latency_ms=t.ms)` 한 줄.

- `kind` 값: `KIND_MESSAGE`(③) · `KIND_MISSION`(⑤) · `KIND_CRISIS`(⑦, `risk_level` 만 추가) 등.
- 토큰은 `resp.usage` 에서 가드 추출(없으면 0). `to_doc()` 의 `total_tokens` 가 `admin/usage` `$sum` 과 정합.
- 김윤한 `POST /api/v1/llm-logs`(#34)와 **writer 가 둘**이 됨 → 팀에서 한쪽으로 일원화할지 협의 필요.
</content>
