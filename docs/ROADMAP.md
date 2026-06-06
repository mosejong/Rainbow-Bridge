# 레인보우 브릿지 발표까지 로드맵

> **작성:** 2026-06-06 · 모세종
> **목표:** 발표 데모 완성 + 서비스 안정화
> **현재 상태:** 핵심 8개 기능 완료, 멀티모달·수의사 플랫폼 마무리 단계

---

## 🗓️ 단계별 목표

| 단계 | 기간 | 목표 |
|------|------|------|
| **Phase 1** | 지금 ~ 06-08 | ElevenLabs TTS 연결 + LivePortrait 서비스 파이프라인 완성 |
| **Phase 2** | 06-09 ~ 06-12 | 수의사 플랫폼 완성 + E2E 통합 테스트 |
| **Phase 3** | 06-13 ~ 06-18 | 발표 시나리오 리허설 + 버그 픽스 |
| **발표** | 06-19 | 시연 데모 |

---

## 👤 팀원별 지금 당장 할 일

### 모세종 (PM + 백엔드)
**읽을 문서:** 없음 (작성자)

| 우선순위 | 할 일 | 완료 기준 |
|---------|------|---------|
| 🔴 1 | ⑧ 평가 리포트 API — `build_report()` 실연결 | `GET /api/v1/report/{pet_id}` 실데이터 반환 |
| 🔴 2 | 발표 시나리오 스크립트 작성 | 5분 시연 흐름 문서화 |
| 🟡 3 | E2E 테스트 — 전체 흐름 한 번에 통과 확인 | 로그인→추모영상 다운로드 완주 |

---

### 김윤한 (백엔드 / 홈서버)
**읽을 문서:** [`docs/PROGRESS.md`](PROGRESS.md)

| 우선순위 | 할 일 | 완료 기준 |
|---------|------|---------|
| 🔴 1 | `chromadb>=0.5` requirements.txt 추가 → PR #114 CI 수정 | CI 초록불 |
| 🔴 2 | 수의사 로그인 API 완성 | `POST /vets/register`, `POST /vets/login` 동작 |
| 🔴 3 | VetAdvice 저장 API 완성 | `POST /diaries/{diary_id}/advice` 동작 |
| 🟡 4 | 미디어 다운로드 API | `GET /media/{asset_id}/download` 파일 반환 |

---

### 반소람 (AI 엔지니어)
**읽을 문서:** [`docs/PERSO_STRATEGY.md`](PERSO_STRATEGY.md), [`ai/TODO.md`](../ai/TODO.md)

| 우선순위 | 할 일 | 완료 기준 |
|---------|------|---------|
| 🔴 1 | pytest CI ImportError 수정 | `ruff·black·pytest` 초록불 |
| 🔴 2 | vet_protocol RAG 구현 | `category=vet_protocol` 쿼리 동작, 내원 유도 포함 |
| 🟡 3 | TTS 톤↔메시지 톤 매핑 재합의 (정환주와) | `soft` 포함 4종 톤셋 확정 |

---

### 정환주 (AI 엔지니어 / GPU 서버)
**읽을 문서:** [`ai/tts/ENGINE_NOTES.md`](../ai/tts/ENGINE_NOTES.md), [`ai/TODO.md`](../ai/TODO.md), [`docs/LIPSYNC_EXPERIMENT.md`](LIPSYNC_EXPERIMENT.md)

| 우선순위 | 할 일 | 완료 기준 |
|---------|------|---------|
| 🔴 1 | ElevenLabs API 키 발급 + 한국어 목소리 샘플 청취 | 성격 4종 voice_id 확정 |
| 🔴 2 | `tts.synthesize()` ElevenLabs 연동 | TTS 결과물 추모 영상에 붙여서 감정 테스트 |
| 🔴 3 | GPU 터널 연결 → LivePortrait remote 추론 | 장민수 `server.py` 연결 완료 |
| 🟡 4 | ⑧ 평가 리포트 `save_log` 훅 LLM 호출부에 연결 | `GET /admin/usage` 실데이터 |

> **PERSO 드랍 확정.** 더 이상 PERSO 관련 작업 불필요.
> LIPSYNC_EXPERIMENT.md 읽고 LivePortrait 방향 숙지.

---

### 민경이 (프론트엔드)
**읽을 문서:** [`docs/PROGRESS.md`](PROGRESS.md)

| 우선순위 | 할 일 | 완료 기준 |
|---------|------|---------|
| 🔴 1 | 수의사 웹 화면 (`VITE_TARGET=hospital`) | 로그인 + 펫 목록 + 조언 입력 화면 완성 |
| 🟡 2 | TTS 성격 선택 UI 추가 여부 결정 | 활발/순둥이/도도/노령 선택 → 모세종과 협의 |

---

### 장민수 (멀티모달)
**읽을 문서:** [`docs/PERSO_STRATEGY.md`](PERSO_STRATEGY.md), [`docs/LIPSYNC_EXPERIMENT.md`](LIPSYNC_EXPERIMENT.md)

| 우선순위 | 할 일 | 완료 기준 |
|---------|------|---------|
| 🔴 1 | GPU 터널 연결 (정환주와) | remote 추론 `server.py` 동작 확인 |
| 🔴 2 | LivePortrait GPU 서버에서 동일 조건 실행 | TomCarper calm + multiplier 0.4, 결과 파일 생성 |
| 🟡 3 | LIPSYNC_EXPERIMENT.md 방법 3 결과 GPU 서버 버전으로 보완 | 처리시간·결과 기록 |

> **PERSO 드랍 확정.** PERSO 관련 코드는 별도 제거 불필요 (opt-in이라 발표에 영향 없음).

---

## 🏁 발표까지 전체 체크리스트

### 기능 완성
- [ ] ⑧ 평가 리포트 API 실연결 (모세종)
- [ ] 수의사 로그인·조언 API (김윤한)
- [ ] 수의사 웹 화면 (민경이)
- [ ] vet_protocol RAG (반소람)
- [ ] ElevenLabs TTS 연동 (정환주)
- [ ] LivePortrait GPU 서버 연결 (장민수·정환주)
- [ ] ElevenLabs TTS + LivePortrait 영상 합치기 데모 완성

### 품질
- [ ] CI 전체 초록불 (ruff·black·pytest)
- [ ] E2E 전체 흐름 통과 (로그인→추모영상 다운로드)
- [ ] 위기 감지 1393 안내 동작 확인
- [ ] risk_level 0~3 문서화

### 발표 준비
- [ ] 5분 시나리오 스크립트 확정
- [ ] 데모 계정·샘플 데이터 준비
- [ ] 발표 슬라이드 초안
- [ ] 리허설 1회

---

## 🔗 핵심 문서 링크

| 문서 | 내용 |
|------|------|
| [`PERSO_STRATEGY.md`](PERSO_STRATEGY.md) | PERSO 드랍 확정, 새 파이프라인 |
| [`LIPSYNC_EXPERIMENT.md`](LIPSYNC_EXPERIMENT.md) | 립싱크 실험 전체 결과 + 결론 |
| [`ai/tts/ENGINE_NOTES.md`](../ai/tts/ENGINE_NOTES.md) | TTS 엔진 비교, ElevenLabs 방향 |
| [`PROGRESS.md`](PROGRESS.md) | 기능별 현재 상태 |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | 전체 시스템 구조 |
| [`docs/ETHICS_추모표현_가이드.md`](ETHICS_추모표현_가이드.md) | 추모 표현 허용/금지 경계 |
