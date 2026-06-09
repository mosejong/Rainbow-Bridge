# 🧠 AI 파트 할 일 (TODO)

> AI 파트 전반(`llm`·`tts`·`evaluation`·`liveportrait`) 세부 작업 목록입니다.
> 작업 규칙·윤리 경계는 [CLAUDE.md](CLAUDE.md), 전체 진행도는 [../docs/PROGRESS.md](../docs/PROGRESS.md).
> 상태: ⬜ 시작 전 · 🟡 진행 중 · 🔵 리뷰(PR) · ✅ 완료 · ⛔ 막힘
> 단계 아이콘: 🎯 설계 · 🔧 구현 · 🧪 테스트 · 🔌 통합 · 📄 문서

---

## 📌 담당 범위

> ⚠️ **세부 담당은 아직 미정** — "담당" 열은 팀 합의 후 채웁니다. 폴더/영역만 확정.

| 출처 | 항목 | 담당 | 폴더 |
|------|------|------|------|
| 0-5 | 로컬 LLM 엔진 결정·세팅 | _미정_ | `llm/` |
| 0-6 | PERSO API 연동 테스트 | _미정_ | `llm/` |
| 0-7 | GPU 서버(RTX 5060) 셋업 | _미정_ | 인프라 |
| MVP ③ | 추모 메시지 프롬프트/LLM | _미정_ | `llm/` |
| MVP ⑤ | 미션 추천 로직 | _미정_ | `llm/` |
| MVP ⑦ | 위기 감정 감지 로직 🚨 | _미정_ | `llm/` |
| MVP ④ | TTS 엔진 | _미정_ | `tts/` |
| MVP ⑧ | 평가 지표/집계 | _미정_ | `evaluation/` |

> 🎬 `liveportrait`(사진→영상, 가산점)는 **멀티모달(장민수) 담당** — AI 파트 TODO 범위 밖. GPU 자원만 공유.

---

## 🚦 선행 결정 (막히면 전부 막힘 — 가장 먼저)

- [ ] **결정 A — 로컬 LLM 엔진/모델** (AI 파트 협의)
  - [x] RTX 5060 VRAM 확인 → **8GB** (양자화 필수, 7B Q4가 상한)
  - [ ] 엔진 선정: 8GB 기준 **llama.cpp(GGUF Q4)** 권장 / 작은 모델이면 vLLM·SGLang ([GPU_SERVER.md](GPU_SERVER.md))
  - [ ] 한국어 모델 2~3종(Qwen2.5-7B, EXAONE-3.5 등) 실제 구동 → **[llm/MODEL_NOTES.md](llm/MODEL_NOTES.md) 에 후기 작성**
  - [ ] 후기 근거로 개발용 모델 확정
  - [ ] 결정 후 → `.env.example` · `../docs/SETUP.md §2-1` · `../docs/ARCHITECTURE.md §5` 채우기
- [ ] **결정 B — AI ↔ 백엔드 통합 방식** (AI 파트 + 백엔드 협의)
  - [ ] (A) 독립 추론 서버(FastAPI REST, GPU 분리) vs (B) 백엔드 직접 import
  - [ ] 결정 후 → `CLAUDE.md §3` 갱신
- [ ] **결정 C — 입출력 스키마 고정** (AI 파트 + 백엔드 협의)
  - [ ] ③/⑤/⑦/④/⑧ 각 함수의 요청·응답 JSON을 백엔드 `schemas/` 와 합의
  - [ ] 합의안을 `CLAUDE.md §3` 계약 표에 기록

---

# 🟨 ai/llm

## L-0. 공통 기반 (provider)

- [ ] 🎯 패키지 구조 확정
  ```
  llm/
  ├── __init__.py
  ├── provider.py      # 로컬/PERSO 추상화
  ├── config.py        # 모델·온도 등 파라미터
  ├── prompts/
  │   ├── memorial.py  # ③ 템플릿
  │   └── mission.py   # ⑤ 템플릿
  │   └── safety.py    # ⑦ 분류 프롬프트
  ├── memorial.py      # ③
  ├── mission.py       # ⑤
  ├── safety.py        # ⑦
  └── tests/
  ```
- [ ] 🔧 `provider.generate(prompt, *, max_tokens, temperature, json_mode=False) -> str`
  - [ ] `LLM_PROVIDER` 로 로컬↔PERSO 분기
  - [ ] 타임아웃·재시도·예외 처리 (외부 호출 실패 graceful)
  - [ ] `json_mode` 일 때 구조화 출력 강제(⑦에서 사용)
- [ ] 🧪 로컬·PERSO 각각 호출 1회 성공 스모크 테스트
- [ ] 📄 PERSO 연동 테스트(0-6): 엔드포인트·인증·할당량 메모 기록

## L-③. 추모 메시지 생성 ⭐

- [ ] 🎯 입력 스키마 정의: `pet{name, species, period, memories[]}` + `emotion{mood, note}` + `tone`
- [ ] 🎯 출력 스키마 정의: `{content, tone, source(local|perso)}`
- [ ] 🎯 프롬프트 설계 (`prompts/memorial.py`)
  - [ ] 시스템 규칙: **보호자 대상** 상징적 위로, 반려동물 1인칭 ❌, 부활 ❌
  - [ ] 추억 키워드 자연 삽입, 길이·문체 가이드
  - [ ] 톤 변형(따뜻함/담담함/희망 등 — ④ TTS 톤과 연동 대비)
- [ ] 🔧 `memorial.generate_message(pet, emotion, tone) -> dict`
  - [ ] 생성 전 `safety.detect_crisis` 선호출 → 위기면 메시지보다 안내 우선
  - [ ] 후처리 가드: 1인칭/부활 표현 탐지 시 재생성 또는 차단
- [ ] 🧪 정상 입력 출력 품질 점검(샘플 5종)
- [ ] 🧪 가드레일 테스트: 금지 표현이 출력에 없는지 자동 검사
- [ ] 📄 예시 입출력 3~5개 문서화

## L-⑤. 미션 추천

- [ ] 🎯 미션 풀(작은 회복 활동) 초안 작성 (산책/사진정리/편지쓰기 등 카테고리화)
- [ ] 🎯 추천 전략 결정: 룰 기반 / LLM 기반 / 하이브리드
- [ ] 🔧 `mission.recommend(emotion, history) -> [{title, category}, ...]`
  - [ ] 감정 등급 → 미션 난이도 매핑 (무기력엔 아주 작은 미션부터)
  - [ ] 최근 완료/반복 회피 로직(history 반영)
- [ ] 🧪 감정별 추천 결과 적절성 점검
- [ ] 📄 미션 풀·매핑 규칙 문서화

## L-⑦. 위기 감정 감지 🚨 (최우선)

> 핵심 함정: 펫로스는 "죽음·이별" 단어가 정상 대화에 가득 → **표현 대상(subject) 구분**이 1번.

### 설계
- [ ] 🎯 위험 등급 4단계 정의
  - L0 정상 / L1 우려(무기력·"의미없다") / L2 경고(본인 사망욕구·"따라가고싶다") / L3 긴급(구체 계획·수단)
- [ ] 🎯 `subject` 구분 규칙: `self` | `pet` | `other` (반려동물 죽음 언급은 L0로 내림)
- [ ] 🎯 펫로스 특화 신호 사전 작성
  - 직접(죽고/사라지고/끝내고 싶다) · 수동적(살 이유 없다) · **따라감(나도 따라가고 싶다)** · 긴급(수단/시점)
- [ ] 🎯 응답 정책 매핑: L0=평소 / L1=공감강화 / L2=1393 우선+톤조정 / L3=생성중단+1393 전면

### 구현 (다층)
- [ ] 🔧 L0 규칙 레이어: 강한 직접 표현 사전 매칭 (빠른 확정)
- [ ] 🔧 L1 LLM 레이어: `prompts/safety.py` 분류 프롬프트 + `json_mode`
- [ ] 🔧 L2 융합: `max(규칙, LLM)` + 보수적 보정(애매하면 한 단계 ↑)
- [ ] 🔧 `safety.detect_crisis(text, context=None) -> {risk_level, subject, signals[], hotline_required, reason}`
- [ ] 🔧 `CRISIS_HOTLINE` 상수에서만 1393 참조 (하드코딩 금지)

### 테스트·운영
- [ ] 🧪 골든 테스트셋 구축 (등급별 + 함정 케이스 "봄이가 죽었어요"=L0)
- [ ] 🧪 **미탐(놓침) 0 목표** 회귀 테스트, 오탐율도 기록
- [ ] 🔧 위기 로그: 등급·신호 위주 저장, **원문 PII 최소화**
- [ ] 🔌 백엔드 ②(감정 체크인)·③(메시지) 공유 인터페이스 확정
- [ ] 📄 등급 정의·사전·응답정책 문서화

---

# 🎙️ ai/tts — MVP ④ (정환주)

- [x] 🎯 엔진 결정(잠정): **Google Cloud TTS** → ⚠️ **2026-06-06 방향 전환: ElevenLabs 주력, Google 폴백**
  - PERSO 드랍 → TTS가 주력 오디오 됨 → 음질이 핵심 기준으로 격상
  - Google TTS 기계음은 추모 영상 몰입 방해 → ElevenLabs로 전환
  - 성격별 목소리 매핑: 활발/순둥이/도도/노령 4종
- [x] 🎯 톤 옵션 정의 — `TtsTone`(warm/calm/hopeful/soft) + `_TONE_MAP`(속도·피치) → *반소람 ③ 톤과 값 합의 필요*
- [x] 🔧 `tts.synthesize(text, tone)` 골격 + 긴 텍스트 분할(`_split_text`)
- [ ] 🔧 **ElevenLabs API 키 발급** + `pip install elevenlabs` + 한국어 목소리 샘플 청취
- [ ] 🎯 성격 4종 목소리 매핑 확정 (활발/순둥이/도도/노령) + ElevenLabs voice_id 기록
- [ ] 🔧 `tts.synthesize()` ElevenLabs 연동 + Google 폴백 분기
- [ ] 🧪 성격별 샘플 TTS 생성 → 추모 영상에 붙여서 감정 테스트
- [ ] 🔧 `duration` 추정값 → 정확값(ffprobe 등)으로 교체, MP3 합치기 정밀화(pydub)
- [ ] 🔌 출력 포맷·저장 위치 백엔드 `MediaAsset` 와 합의 / `POST /api/v1/tts` 스텁(**김윤한**과) → 장민수 플레이어 언블락
- [ ] 🔧 `_output/` 음성 파일 `.gitignore` 등록 확인
- [ ] 📄 톤 매핑·사용법 문서화 (`../tts/CLAUDE.md §6` 후기 포함)

---

# 📊 ai/evaluation — MVP ⑧ (정환주)

- [x] 🎯 평가 지표 정의 (사용 횟수·감정 추이·미션 완료율·재방문)
- [x] 🔧 `llm_logs` 스키마(`LLMLog`) + 저장 헬퍼(`save_log`) — **원문 PII 미저장**, 비식별 지표만
- [x] 🔧 `build_report(pet_id, period, *, llm_logs, emotion_checkins, missions, access_counts)` — 순수 함수(DB 주입)
- [x] 🔧 일상복귀 신호(`recovery_signal`) 통합 — build_report 출력에 포함 + `GET /report/{pet_id}` 노출(2026-06-09). 접속빈도 근거(`access_counts`)=pet 소유자 `access_logs` 버킷팅. emotion 키 `mood`→`score` 백엔드 정합
- [ ] 🔌 LLM 호출부에 `save_log` 훅 연결 (반소람 provider 호출 지점과 협의)
- [ ] 🔌 백엔드 `GET /api/v1/admin/usage`·`/report/{pet_id}` 가 `llm_logs` 읽도록 (**김윤한**과 컬렉션 합의)
- [ ] 🎯 리포트 출력 스키마 프론트 차트와 확정 (**민경이**)
- [ ] 🔧 재방문 지표 — 세션/접속 로그 스키마 확정 후 추가
- [x] 🧪 샘플 데이터로 집계 정확성 검증 — `test_report`·`test_recovery_signal`·`test_report_aggregation`·`test_report_service`(get_report 끝단)
- [ ] 📄 지표 정의·스키마 문서화

---

## 🔗 의존성 / 진행 순서

```
결정 A·B·C ─▶ llm/provider.py ─┬─▶ ⑦ 위기 감지 (🥇 먼저 안정화)
                               ├─▶ ③ 추모 메시지
                               └─▶ ⑤ 미션 추천
GPU 셋업(0-7) ─▶ ④ TTS
백엔드 스키마 합의 ─▶ ⑧ 평가
```

- 🥇 **⑦ 위기 감지 + provider.py** (안전 최우선 + 모든 LLM 기능 토대)
- 🥈 ③ 추모 메시지 → ⑤ 미션
- 🥉 ④ TTS / ⑧ 평가

---

## ✅ 완료 기준 (Definition of Done)

- [ ] 로컬 LLM·PERSO 둘 다 동작 (provider 분기)
- [ ] 출력에 반려동물 1인칭/부활 표현 없음 (가드레일 테스트 통과)
- [ ] 위기 입력 시 1393 안내가 항상 우선, 미탐 0 (골든셋 통과)
- [ ] 입출력 스키마가 백엔드와 일치 (결정 C)
- [ ] `ruff`·`black` 통과, 핵심 함수 테스트 존재
- [ ] `.env.example`·`SETUP.md`·`PROGRESS.md` 갱신, 개발일지 작성
</content>
