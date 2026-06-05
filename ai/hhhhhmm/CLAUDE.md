# CLAUDE.md — HHHHHMM 삶의 질 척도 (`ai/hhhhhmm/`)

> 담당: **정환주**. 상위 [../CLAUDE.md](../CLAUDE.md) 규칙을 따르며 이 영역만 보완합니다.
> 상태: **선택(가산점) · 도먼트 드래프트** — 팀+강사 합의 전까지 백엔드·프론트에 배선하지 않습니다.

---

## 1. 무엇인가

- **1단계(아플 때)** 보호자에게 반려동물 삶의 질(QoL) **참고 지표**를 제공.
- Villalobos 박사 **HHHHHMM Scale** 기반: 7개 항목 각 0~10점(10이 최상), 총점 0~70.
  - Hurt(통증) · Hunger(식사) · Hydration(수분) · Hygiene(위생) · Happiness(행복) · Mobility(거동) · More good days(좋은 날 비중)
- 원 척도 권고: 총점 **35 이상**이면 삶의 질 유지가 받아들일 만한 수준.

## 2. 인터페이스

- `score_qol(scores: dict[str,int]) -> dict` — 순수 함수(DB·LLM·GPU 없음).
  - 입력: 7개 항목 키 전부, 각 0~10 정수. 누락·여분·범위밖 → `ValueError`.
  - 출력: `total`·`tier`(maintainable/declining)·`interpretation`·`low_items`·`vet_referral`·`disclaimer`.
- 공개 심볼: `score_qol`, `QOL_CRITERIA` (`__init__.py`).

## 3. 절대 경계 (윤리 — 최우선)

- 🚫 **AI가 안락사 같은 결정을 대신 내리지 않습니다.** 결과엔 항상 면책 문구 포함.
- ✅ 결과엔 항상 **수의사 상담 안내**를 함께 제공.
- 🚫 QoL 점수로 **1393을 임의 연계하지 않습니다.** 보호자 정서 위기(자해·극단 선택)는
  이 모듈이 아니라 ⑦ 위기 감지([../llm/safety.py](../llm/safety.py))가 별도로 다룹니다(오탐 방지).
- 민감 주제 → **팀+강사 합의 후** 백엔드/프론트 연결.

## 4. 테스트

- `tests/test_qol.py` — 총점·등급·경계값(35)·검증 예외·안내/면책 상시 포함.
- 실행: `pytest ai/hhhhhmm/tests/ -q` (외부 의존 없음).

## 5. 남은 일 (합의 후)

- 백엔드 입력 스키마(7항목)·엔드포인트 합의(모세종).
- 프론트 입력 폼·결과 표시 UI(민경이).
- ③/⑦ 흐름과의 연계(위기 신호 동반 시 ⑦ 우선) — 반소람 합의.
