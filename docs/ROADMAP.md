# 레인보우 브릿지 발표까지 로드맵

> **작성:** 2026-06-06 · 모세종
> **목표:** 발표 데모 완성
> **모세종 역할 (지금부터):** 기능 개발 ❌ → **각자 완성한 기능을 서버에 연결·테스트**만 담당

---

## 모세종이 받아야 하는 것들

> 아래 항목이 팀원에게서 넘어와야 모세종이 연결·배포할 수 있음.
> **각자 완성해서 PR 올리면 모세종이 테스트하고 머지.**

| 받을 것 | 담당 | 기한 | 상태 |
|---------|------|------|------|
| ElevenLabs TTS 연동 코드 (`tts.synthesize()` ElevenLabs 분기) | 정환주 | 06-08 | ⬜ |
| GPU 터널 + LivePortrait remote 추론 동작 확인 | 정환주·장민수 | 06-08 | 🟡 |
| 수의사 로그인·조언 API (`/vets/register`, `/login`, `/advice`) | 김윤한 | 06-09 | 🟡 |
| 수의사 웹 화면 (`VITE_TARGET=hospital`) | 민경이 | 06-09 | 🟡 |
| vet_protocol RAG + pytest CI 수정 | 반소람 | 06-09 | 🟡 |
| ⑧ 리포트 `build_report()` 연결 가능한 상태 | 정환주 | 06-10 | ⬜ |

---

## 팀원별 할 일

### 정환주
**읽을 것:** [`ai/tts/ENGINE_NOTES.md`](../ai/tts/ENGINE_NOTES.md), [`docs/LIPSYNC_EXPERIMENT.md`](LIPSYNC_EXPERIMENT.md)

1. ElevenLabs API 키 발급 → 한국어 목소리 샘플 직접 들어보기
2. 성격 4종 voice_id 확정 (활발/순둥이/도도/노령)
3. `tts.synthesize()` ElevenLabs 분기 구현 → PR
4. GPU 터널 연결 → 장민수 `server.py` 연결 확인
5. `save_log` 훅 LLM 호출부 연결

> ⚠️ PERSO 드랍 확정. PERSO 관련 추가 작업 없음.
> LIPSYNC_EXPERIMENT.md 결론 읽고 LivePortrait 방향 숙지할 것.

---

### 김윤한
**읽을 것:** [`docs/PROGRESS.md`](PROGRESS.md)

1. `chromadb>=0.5` requirements.txt 추가 → PR #114 CI 수정
2. 수의사 API 완성 (`/register`, `/login`, `/advice`) → PR

---

### 반소람
**읽을 것:** [`ai/TODO.md`](../ai/TODO.md)

1. pytest CI ImportError 수정 → PR
2. vet_protocol RAG 구현 → PR
3. TTS 톤↔메시지 톤 4종 매핑 정환주와 합의

---

### 민경이
**읽을 것:** [`docs/PROGRESS.md`](PROGRESS.md)

1. 수의사 웹 화면 완성 (`VITE_TARGET=hospital`) → PR
2. TTS 성격 선택 UI 추가 여부 → 모세종과 협의

---

### 장민수
**읽을 것:** [`docs/PERSO_STRATEGY.md`](PERSO_STRATEGY.md), [`docs/LIPSYNC_EXPERIMENT.md`](LIPSYNC_EXPERIMENT.md)

1. 정환주 GPU 터널 연결되면 LivePortrait remote 추론 동작 확인
2. 결과 LIPSYNC_EXPERIMENT.md에 기록

> ⚠️ PERSO 드랍 확정. LIPSYNC_EXPERIMENT.md 결론 읽을 것.

---

## 모세종 할 일 (통합·테스트)

| 할 일 | 트리거 |
|------|--------|
| ⑧ 리포트 API `build_report()` 실연결 | 정환주 핸드오프 후 |
| ElevenLabs TTS 서버 연결·테스트 | 정환주 PR 머지 후 |
| 수의사 API 서버 배포·테스트 | 김윤한 PR 머지 후 |
| E2E 전체 흐름 테스트 | 모든 기능 머지 후 |
| 발표 시나리오 스크립트 작성 | Phase 2 완료 후 |
| 발표 데모 계정·샘플 데이터 준비 | 발표 1주 전 |

---

## 발표까지 체크리스트

### Phase 1 (~06-08)
- [ ] ElevenLabs TTS 연동 (정환주)
- [ ] GPU 터널 + LivePortrait remote (정환주·장민수)
- [ ] PR #114 CI 수정 (김윤한)

### Phase 2 (~06-12)
- [ ] 수의사 API + 웹 화면 (김윤한·민경이)
- [ ] vet_protocol RAG (반소람)
- [ ] ⑧ 리포트 API 실연결 (모세종)
- [ ] E2E 전체 통과

### Phase 3 (~06-18)
- [ ] 발표 시나리오 스크립트
- [ ] 데모 계정·샘플 데이터 준비
- [ ] 리허설 1회
- [ ] 버그 픽스

### 발표 (06-19)
- [ ] 시연 데모

---

## 핵심 문서

| 문서 | 내용 |
|------|------|
| [`PERSO_STRATEGY.md`](PERSO_STRATEGY.md) | PERSO 드랍, 새 파이프라인 |
| [`LIPSYNC_EXPERIMENT.md`](LIPSYNC_EXPERIMENT.md) | 립싱크 실험 결과 + 결론 |
| [`ai/tts/ENGINE_NOTES.md`](../ai/tts/ENGINE_NOTES.md) | ElevenLabs 방향 |
| [`PROGRESS.md`](PROGRESS.md) | 기능별 현재 상태 |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | 전체 구조 |
