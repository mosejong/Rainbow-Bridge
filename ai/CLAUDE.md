# CLAUDE.md — AI 파트 작업 가이드 (`ai/`)

> 이 파일은 Claude Code가 `ai/` 폴더에서 작업할 때 읽는 **AI 파트 전용** 가이드입니다.
> 팀 공통 규칙(브랜치·PR·커밋·1393)은 루트 [../CLAUDE.md](../CLAUDE.md)가 우선이며, 이 문서는 **AI 파트에만 추가 적용**됩니다.
> 할 일 목록은 [TODO.md](TODO.md) 참고.

---

## 0. 제일 중요 — 절대 경계 (윤리)

- ❌ **반려동물을 "부활"시키거나, 반려동물인 *척* 말하게 하는 출력 금지.** (1인칭 반려동물 화법 금지)
- ✅ 우리는 **보호자**를 향한, 기억 기반 **상징적 추모·위로 메시지**만 생성합니다.
- 🚨 **위기 안내 번호 `1393`은 어떤 경우에도 변경/누락 금지.** (자살예방상담전화 — `CRISIS_HOTLINE` 상수에서만 참조)
- 프롬프트·예시·테스트 데이터에도 이 경계를 그대로 적용하세요.

---

## 1. 폴더 & 영역 (세부 담당 미정)

> ⚠️ **AI 파트 세부 담당은 아직 안 정해졌습니다.** "담당" 열은 비워둠 — 팀 합의 후 채우세요.
> 루트 [../CLAUDE.md](../CLAUDE.md)의 팀표도 **초안** 단계라 그대로 확정 아님.

| 폴더 | 영역 | 담당 |
|------|------|------|
| `ai/llm/` | 추모 메시지(③)·미션 추천(⑤)·위기 감지(⑦) | _미정_ |
| `ai/tts/` | 음성 합성(④) | _미정_ |
| `ai/evaluation/` | 평가 지표·집계(⑧) | _미정_ |
| GPU 인프라 | RTX 5060 서버·로컬 추론(0-7) | _미정_ |

> 🎬 `ai/liveportrait/`(사진→영상, 가산점)는 **멀티모달(장민수) 담당** — AI 파트 역할 밖. GPU 자원만 정환주와 공유.

> 남의 하위 폴더를 크게 바꿔야 하면 먼저 알리고 별도 PR로 분리. (루트 규칙)

### 폴더별 가이드 (해당 폴더 작업 시 자동 로드)
- [llm/CLAUDE.md](llm/CLAUDE.md) — 반소람 (메시지·미션·위기·provider)
- [tts/CLAUDE.md](tts/CLAUDE.md) · [evaluation/CLAUDE.md](evaluation/CLAUDE.md) — 정환주
- 역할 분담 → [ROLES.md](ROLES.md) · GPU 운영 → [GPU_SERVER.md](GPU_SERVER.md) · 모델 후기 → [llm/MODEL_NOTES.md](llm/MODEL_NOTES.md)

---

## 2. 폴더 상세 구조 (제안 — 담당 확정 후 조정)

```
ai/
├── CLAUDE.md / TODO.md
├── llm/
│   ├── provider.py     # 로컬↔PERSO 추상화 (generate)
│   ├── config.py       # 모델·온도 등 파라미터
│   ├── prompts/        # 프롬프트 템플릿 (코드와 분리)
│   │   ├── memorial.py · mission.py · safety.py
│   ├── memorial.py     # ③ 추모 메시지
│   ├── mission.py      # ⑤ 미션 추천
│   ├── safety.py       # ⑦ 위기 감지
│   └── tests/
├── tts/                # ④ 음성 합성
└── evaluation/         # ⑧ 평가·집계
# (liveportrait/ 는 멀티모달 장민수 담당 — AI 파트 아님)
```

---

## 3. 백엔드와의 인터페이스 (계약 — 결정 C로 확정)

- 아키텍처상 AI는 **별도 추론 서버(REST)** 로 그려져 있음 → 백엔드 `services/` 가 HTTP 호출.
  단, 통합 방식(독립 서버 vs import)은 **미확정** → [TODO.md](TODO.md) 선행결정 B 참고.
- 백엔드 경로 규약: `/api/v1/...` 소문자 복수 명사. 응답 JSON, 에러 `{ "detail": "..." }`.

### 기능별 입출력 초안 (확정 아님 — 백엔드와 합의 후 채움)

| 기능 | 입력(요청) | 출력(응답) |
|------|-----------|-----------|
| ③ 메시지 | `pet{name,species,period,memories[]}`, `emotion{mood,note}`, `tone` | `{content, tone, source}` |
| ⑤ 미션 | `emotion`, `history[]` | `[{title, category}, ...]` |
| ⑦ 위기 | `text`, `context?` | `{risk_level, subject, signals[], hotline_required, reason}` |
| ④ TTS | `text`, `tone` | `{audio_path, duration, format}` |
| ⑧ 평가 | `pet_id`, `period` | `report{...}` |

> ⑦ 위기 감지는 백엔드 ②(감정 체크인)·③(메시지)에서 **양쪽 호출** → 스키마를 가장 먼저 고정.

---

## 4. LLM 전략 (개발 vs 시연)

| 용도 | 개발 단계 | 평가/시연 |
|------|-----------|-----------|
| 메시지/미션/위기 | **로컬 LLM** (할당량 절약) | **PERSO API** |

- 같은 코드가 로컬·PERSO 둘 다 호출하도록 **provider 추상화** (`LLM_PROVIDER` 분기).
- PERSO는 할당량 제한 → 개발 중엔 로컬, 시연 직전에만 PERSO.
- 엔진 후보: **RTX 5060 8GB 기준 llama.cpp(GGUF Q4) 권장**, 작은 모델이면 vLLM·SGLang. 상세 → [GPU_SERVER.md](GPU_SERVER.md).
- 로컬 모델을 테스트하면 후기를 [llm/MODEL_NOTES.md](llm/MODEL_NOTES.md) 에 남기세요.

---

## 5. 위기 감지 원칙 (🚨 안전 최우선)

> ⑦은 사람 안전과 직결 → 별도 원칙으로 강조. 상세 설계는 [TODO.md L-⑦](TODO.md).

- **함정:** 펫로스는 "죽음·이별" 단어가 정상 대화에 가득 → 단순 키워드는 오탐 폭발.
  → **표현 대상(subject) 구분**(self/pet/other)이 1번. 반려동물 죽음 언급은 위기 아님.
- **다층 + 보수적 융합:** 규칙(L0) + LLM 분류(L1) → 애매하면 **한 단계 올림.** 미탐(놓침)이 치명적.
- **4등급:** L0 정상 / L1 우려 / L2 경고(1393 우선) / L3 긴급(생성중단+1393 전면).
- LLM 위기 분류는 **JSON 강제 출력**(자유 생성 ❌).
- 위기 로그는 등급·신호 위주, **원문 PII 최소화.**
- 골든 테스트셋으로 **미탐 0 회귀 검증.**

---

## 6. 프롬프트 관리

- 프롬프트는 코드에 흩지 말고 `llm/prompts/` 에 **분리·버전 관리.**
- 시스템 프롬프트에 윤리 경계(§0)를 **항상 명시.**
- 변경 시 예시 입출력·테스트 같이 갱신.

---

## 7. 환경 변수 (`.env`)

AI 파트가 채울 값 (현재 비어 있음 — 엔진 결정 후 `.env.example`·`SETUP.md`·`ARCHITECTURE.md §5` 동시 갱신):

```
LLM_PROVIDER=        # 예: vllm | sglang | perso (담당 결정)
LLM_BASE_URL=
LLM_MODEL=
LLM_API_KEY=
PERSO_API_KEY=
PERSO_API_BASE_URL=
TTS_PROVIDER=
TTS_API_KEY=
```
> `LIVEPORTRAIT_MODE`·`REPLICATE_API_TOKEN`은 멀티모달(장민수)용 — `.env.example` 에만 있고 AI 파트는 다루지 않음.

- 🚫 비밀키·모델 가중치(`.safetensors`)·영상/음성 파일은 **커밋 금지** (`.gitignore` 처리).
- 키는 `.env` 에만. `.env.example` 에는 빈 값/예시만.

---

## 8. 코드 스타일 / 테스트

- Python: `black`(포맷) + `ruff`(린트), snake_case.
- 외부 호출 래퍼는 작게, 타임아웃·예외 처리 포함(추론 실패 graceful).
- 핵심 함수(`generate_message`·`detect_crisis`·`recommend`)는 테스트 필수.
- 백엔드와 공유 코드가 `backend/` 에 들어가면 그쪽 CI(`ruff·black·pytest`) → push 전 로컬 검사.

---

## 9. Git (요약 — 상세는 루트 문서)

- 🚫 `main`·`dev` 직접 push 금지. **본인 이름 브랜치 → PR(`dev`) → 리뷰 → 머지.** (브랜치명은 루트 문서 표 참고)
- 커밋: Conventional Commits + 한국어 (`feat: 위기 감지 등급 분류 v1 추가`).
- 작업 끝나면 개인 일지([../docs/devlog/members/](../docs/devlog/members/)) + 통합 일지 한 줄 + [PROGRESS.md](../docs/PROGRESS.md) 갱신.
</content>
