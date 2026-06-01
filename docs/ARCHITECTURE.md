# 🗺️ 시스템 아키텍처 (ARCHITECTURE)

> 전체 그림을 이해하기 위한 문서입니다. 세부 구현은 코드/각 영역 담당 결정.

---

## 1. 전체 구성도

```
                         [ 사용자 (보호자) ]
                                │
                                ▼
                      ┌───────────────────┐
                      │     Frontend       │  (민경이, 장민수)
                      │   웹 클라이언트     │
                      └─────────┬─────────┘
                                │ REST API (/api/v1/...)
                                ▼
            ┌───────────────────────────────────────┐
            │            Backend (FastAPI)            │  (모세종, 김윤한)
            │  api → services → models → db           │
            └───┬───────────┬───────────┬────────────┘
                │           │           │
        ┌───────▼──┐  ┌─────▼─────┐  ┌──▼──────────┐
        │ MongoDB  │  │  AI 엔진   │  │  멀티모달    │
        │ (홈서버)  │  │ (GPU서버)  │  │ LivePortrait│
        │  김윤한   │  │  반소람    │  │   장민수     │
        │          │  │  정환주    │  │   + TTS     │
        └──────────┘  └───────────┘  └─────────────┘
```

---

## 2. 서버 / 인프라

| 서버 | 담당 | 스택 | 역할 |
|------|------|------|------|
| 백엔드 메인 | 김윤한 | Ubuntu + Docker + MongoDB | API 서버, DB |
| GPU 추론 | 정환주 | RTX 5060 | 로컬 LLM, LivePortrait, TTS 추론 |

- 백엔드 ↔ AI/GPU 서버는 HTTP(내부 API)로 통신
- 개발 단계: 각자 로컬에서 돌리고, 통합 시 홈서버/GPU서버로 배포

---

## 3. 백엔드 레이어 구조

```
backend/app/
├── main.py            # FastAPI 진입점, 라우터 등록
├── api/v1/
│   ├── router.py      # v1 라우터 통합
│   └── endpoints/     # 기능별 엔드포인트 (pets, emotions, messages, ...)
├── core/              # 설정(config), 공통 의존성, 예외 처리
├── schemas/           # 요청/응답 모델 (Pydantic) — API 계약
├── models/            # MongoDB 문서 모델
├── services/          # 비즈니스 로직 (AI 호출, 위기 감지 등)
└── db/                # MongoDB 연결
```

**원칙:** `endpoints` 는 얇게 → 로직은 `services` 로. AI/외부 호출도 `services` 안에서.

---

## 4. 데이터 모델 (초안 — 확정 아님)

> 실제 필드는 각 기능 담당이 PR에서 확정. 아래는 시작점.

```
Pet            { _id, name, species, period, memories[], photo_url?, created_at }
EmotionCheckin { _id, pet_id, mood, note, risk_flag, created_at }
MemorialMessage{ _id, pet_id, content, tone, source(perso|local), created_at }
Mission        { _id, pet_id, title, done, created_at }
TimelineItem   { _id, pet_id, type, ref_id, created_at }
MediaAsset     { _id, pet_id, kind(video|audio), url, created_at }
```

---

## 5. AI 엔진 전략

| 용도 | 개발 단계 | 평가/시연 |
|------|-----------|-----------|
| 추모 메시지 LLM | 로컬 LLM (할당량 절약) | **PERSO API** |
| TTS | (담당 결정) | (담당 결정) |
| 영상 생성 | LivePortrait 로컬(RTX 5060) | 로컬 / Replicate fallback |

> 🔧 **로컬 LLM 엔진·모델은 AI 담당(반소람·정환주)이 결정 후 이 표와 `.env`, `SETUP.md` 를 채웁니다.** (현재 비워둠)

---

## 6. 핵심 플로우

### 추모 메시지 생성
```
프로필+감정 입력 → services.message_service
   → (위기 감지 services.safety) → 위험이면 1393 안내 우선
   → LLM 프롬프트 구성 → LLM(로컬/PERSO) 호출
   → 메시지 저장(Mongo) → 타임라인 기록 → 응답
```

### 위험 감정 안전 라우팅 (최우선)
```
감정 체크인/메시지 입력 → 위기 키워드/패턴 감지
   → 감지 시: 생성 응답보다 1393 안내를 우선 노출
   → 로그 기록
```

### 사진 → 영상 (가산점)
```
사진 업로드 → 저장 → LivePortrait(GPU) → MP4
   → (선택) TTS 음성과 FFmpeg 합성 → 다운로드 URL 제공
```

---

## 7. API 규약

- 베이스: `/api/v1`
- 경로: 소문자, 복수 명사 (`/pets`, `/emotions`, `/messages`, `/missions`, `/timeline`, `/media`)
- 응답: JSON, 에러는 `{ "detail": "..." }`
- 인증: (MVP 단순화 — 추후 결정)

---

## 8. 보안 / 윤리 원칙

- 비밀키는 `.env` 만. 코드/깃 금지.
- 위기 안내(1393) 는 어떤 경우에도 누락/변경 금지.
- "반려동물인 척" 응답 생성 금지 — 상징적 위로 메시지로만.
- 사진/영상 등 개인 자료는 git 미포함, 저장소 접근 최소화.
