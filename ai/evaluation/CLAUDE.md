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
</content>
