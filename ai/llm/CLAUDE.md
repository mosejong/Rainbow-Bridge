# CLAUDE.md — LLM 영역 (`ai/llm/`)

> 담당: **반소람**. 상위 [../CLAUDE.md](../CLAUDE.md) 규칙을 따르며 LLM 영역만 보완합니다.
> 할 일: [../TODO.md](../TODO.md) `ai/llm` 블록 · 역할: [../ROLES.md](../ROLES.md).

---

## 1. 담당 범위

- MVP ③ 추모 메시지 · ⑤ 미션 추천 · ⑦ 위기 감지 🚨
- `provider.py`(로컬↔PERSO 추상화) · 0-6 PERSO 연동

---

## 2. 절대 경계 (재강조)

- ❌ 반려동물 1인칭/부활 → ✅ **보호자 대상 상징적 위로**만.
- 🚨 `1393`은 `CRISIS_HOTLINE` 상수에서만. 누락/변경 금지.

---

## 3. provider 추상화

- `generate(prompt, *, max_tokens, temperature, json_mode=False) -> str`
- `LLM_PROVIDER` 로 **로컬(정환주 GPU 서버)↔PERSO** 분기.
- 로컬 = 정환주 GPU의 OpenAI 호환 서버 → 접속 정보 [../GPU_SERVER.md](../GPU_SERVER.md).
- 타임아웃·재시도·예외 처리(추론 실패 graceful).

---

## 4. 프롬프트 관리

- `prompts/` 에 분리·버전 관리. 시스템 프롬프트에 윤리 경계(§2) 항상 명시.
- 변경 시 예시 입출력·테스트 같이 갱신.

---

## 5. 위기 감지 핵심 (🚨 최우선)

- **subject 구분**(self/pet/other) — 반려동물 죽음 언급은 위기 아님(오탐 방지).
- **4등급**(L0~L3) · **다층 + 보수적 융합**(애매하면 ↑) · **JSON 강제 출력**.
- **골든 테스트셋으로 미탐 0** 회귀 검증. 상세 → [../TODO.md L-⑦](../TODO.md).

---

## 6. 모델 후기 ★

- 로컬 모델을 바꿔 테스트하면 **반드시 [MODEL_NOTES.md](MODEL_NOTES.md) 에 후기**.
- 반소람은 **한국어 위로 톤 품질**(1인칭 안 나오는지 포함) 위주로 기록.
- 속도·VRAM 수치는 정환주가 같은 문서에 기록.

---

## 7. 백엔드 계약 / 테스트

- 입출력 스키마: [../CLAUDE.md §3](../CLAUDE.md) 표 / 결정 C로 확정.
- 테스트: 가드레일(금지 표현 없음) + 골든셋(위기) + 핵심 함수.
</content>
