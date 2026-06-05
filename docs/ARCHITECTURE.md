# 🗺️ 시스템 아키텍처 (ARCHITECTURE)

> 전체 그림을 이해하기 위한 문서입니다. 세부 구현은 코드/각 영역 담당 결정.
> **최종 수정:** 2026-06-05

---

## 📊 시각 자료 (산출물)

| 자료 | 파일 | 설명 |
|------|------|------|
| 서비스 파이프라인 | [rainbow_bridge_pipeline.svg](rainbow_bridge_pipeline.svg) | 5개 서비스 영역 전체 흐름 |
| 시스템 구성도 | [system_architecture_final.svg](system_architecture_final.svg) | 인프라·서버·외부 API 관계 |
| 사용자 흐름도 | [user_flow_fixed.svg](user_flow_fixed.svg) | 회원가입→추모영상 사용자 여정 |

> 시각 자료는 스크럼 발표 자료로 활용. GPT 생성 SVG.

---

## 1. 전체 구성도

```
                         [ 사용자 (보호자) ]
                                │  HTTPS
                                ▼
                 ┌─────────────────────────────┐
                 │  rainbow-bridge.duckdns.org  │  Vite + React + Tailwind
                 │  (nginx, Let's Encrypt SSL)  │  (민경이, 장민수)
                 └──────────────┬──────────────┘
                                │ /api/ 프록시
                                ▼
          ┌─────────────────────────────────────────────┐
          │         Backend (FastAPI, Docker)             │  (모세종, 김윤한)
          │  api/ → services/ → schemas/ → db/            │
          │  NCP 서버 101.79.19.87:8000                  │
          └──┬──────────────┬──────────────┬─────────────┘
             │              │              │
    ┌─────────┴──┐   ┌──────┴─────┐  ┌────┴──────────────┐
    │  MongoDB   │   │ SQLite RDB │  │    외부 AI API     │
    │ (Docker)  │   │ (users 인증)│  │  Gemini API (LLM)  │
    └────────────┘   └────────────┘  │  Google Cloud TTS  │
                                     │  PERSO API (영상)  │
                                     │  카카오맵 API      │
                                     └───────────────────┘
                                              │
                                   ┌──────────┴──────────┐
                                   │    AI / 멀티모달     │
                                   │  ChromaDB (RAG)     │
                                   │  LivePortrait (영상) │
                                   │  (반소람·정환주·장민수)│
                                   └─────────────────────┘
```

---

## 2. 서버 / 인프라

| 서버 | 주소 | 담당 | 스택 | 역할 |
|------|------|------|------|------|
| NCP 실서버 | rainbow-bridge.duckdns.org | 모세종·김윤한 | Ubuntu 24.04 | 백엔드 API + 프론트 서빙 |
| MongoDB | 101.79.19.87 | 김윤한 | Docker | 서비스 데이터 DB |
| GPU 서버 | 정환주 홈 | 정환주 | RTX 5060 | LivePortrait 추론 |
| 홈서버 HDD | 김윤한 홈 | 김윤한 | /mnt/hdd 436GB | 영상/모델 파일 저장 |

**인프라 현황 (2026-06-05 기준)**
- HTTPS: Let's Encrypt + DuckDNS (`rainbow-bridge.duckdns.org`)
- nginx: `/api/` → `localhost:8000` 프록시, 프론트 정적 서빙
- Docker Compose: MongoDB + Backend 컨테이너 통합 운영
- GitHub Actions: `dev` 머지 시 NCP 자동 빌드·배포
- SQLite DB (`rainbow_bridge.db`): 사용자 인증 전용
- MongoDB: 반려동물·감정·메시지·미션·타임라인·LLM 로그

---

## 3. 백엔드 레이어 구조

```
backend/app/
├── main.py               # FastAPI 진입점, CORS, 정적파일, lifespan
├── api/v1/
│   ├── router.py         # v1 라우터 통합
│   └── endpoints/        # auth, pets, emotions, messages, tts, missions,
│                         # timeline, report, llm_logs, hospitals, media
├── core/
│   ├── config.py         # 환경변수 로드
│   ├── deps.py           # JWT 인증 의존성 (get_current_user)
│   └── ai_path.py        # sys.path 레포 루트 추가 (ai/ import용)
├── schemas/              # 요청/응답 Pydantic 모델
├── models/
│   └── user.py           # SQLAlchemy User 모델 (인증용 RDB)
├── services/             # 비즈니스 로직 (AI 호출, 위기 감지 등)
└── db/
    ├── mongodb.py        # Motor 비동기 MongoDB 연결
    └── rdb.py            # SQLAlchemy 비동기 SQLite (users 테이블)
```

**원칙:** `endpoints` 는 얇게 → 로직은 `services` 로. AI/외부 호출도 `services` 안에서.

---

## 4. 데이터 모델

### MongoDB 컬렉션 (서비스 데이터)
```
Pet            { _id, user_id, name, species, period, memories[], photo_url?, created_at }
EmotionCheckin { _id, pet_id, score(1-10), note, risk_level(0-3), created_at }
MemorialMessage{ _id, pet_id, content, tone, source, created_at }
Mission        { _id, pet_id, title, description, category, completed(bool), created_at }
TimelineItem   { _id, pet_id, type, content, created_at }
LlmLog         { _id, pet_id, prompt, response, provider, tokens_used, created_at }
MediaAsset     { _id, pet_id, source_url, video_url, voiced_url, dubbed_url, status, created_at }
```

### SQLite 테이블 (인증)
```
User { id(int PK), email(unique), password_hash, nickname, is_active, created_at }
```

### risk_level 정의
| 값 | 의미 | 처리 |
|----|------|------|
| 0 | 정상 | 정상 응답 |
| 1 | 우려 | 정상 응답 + 내부 기록 |
| 2 | 경고 | 1393 안내 포함 응답 |
| 3 | 긴급 | 1393 안내 우선 노출, 메시지 생성 중단 |

---

## 5. AI 엔진 전략

| 용도 | 엔진 | 비고 |
|------|------|------|
| 추모 메시지·미션·상담 LLM | **Gemini API** (`gemini-2.5-flash`) | OpenAI 호환 엔드포인트 |
| 위기 감지 | L0 규칙 + L1 Gemini 분류 | 보수적 융합, 골든셋 30종 통과 |
| TTS | **Google Cloud TTS** (`ko-KR-Neural2-A`) | warm/calm/soft 톤, gTTS 폴백 |
| RAG 검색 | **ChromaDB** + Gemini 임베딩 | 위로글 코퍼스 few-shot 주입 |
| 영상 생성 | **LivePortrait** (animals 모드) | driving_multiplier=0.4 |
| 영상 더빙·립싱크 | **PERSO API** | 선택적 후처리 단계 (voiced_url 입력) |

---

## 6. 핵심 플로우

### 로그인 / 인증
```
POST /auth/register → bcrypt 해싱 → SQLite 저장
POST /auth/login → 비밀번호 검증 → JWT 발급 → localStorage 저장
                → GET /pets → 기존 펫 있으면 /emotion, 없으면 /profile
이후 모든 요청 → Authorization: Bearer <token> 자동 삽입 (axiosInstance)
```

### 추모 메시지 생성 (RAG 연결)
```
입력(pet_id, note, tone) → assess_crisis(L0+L1)
   → risk_level 2+: 1393 안내 반환 (메시지 생성 중단)
   → risk_level 0-1: ChromaDB retrieve() → few-shot 프롬프트 구성
                   → Gemini 추모 메시지 생성
                   → 1인칭 가드 후처리 → MongoDB 저장 → 응답
```

### TTS 낭독
```
POST /tts { pet_id, text, tone } → Google Cloud TTS 합성
   → 실패 시 gTTS 자동 폴백
   → uploads/tts/{pet_id}_{tone}_{hash}.mp3 저장
   → audio_url 반환 → 프론트 재생
```

### 사진 → 추모 영상 (멀티모달)
```
사진 업로드(POST /media/upload) [TTS 완료 필수]
   → LivePortrait(animals 모드, 강도 0.4) → 무음 영상
   → TTS mp3 + FFmpeg 합치기 → voiced_url (서비스 기본 결과물)
   → (선택) POST /media/{id}/perso → PERSO 립싱크 → dubbed_url
```

### 위기 감지 플로우
```
사용자 입력 → L0 규칙 레이어 (키워드·패턴)
            → L1 Gemini 분류 (JSON 강제 출력)
            → 보수적 융합 (애매하면 상위 등급)
            → risk_level 2+: 1393 즉시 안내 (생성 중단)
```

---

## 7. API 엔드포인트 목록

| 경로 | 메서드 | 기능 |
|------|--------|------|
| `/api/v1/auth/register` | POST | 회원가입 |
| `/api/v1/auth/login` | POST | 로그인 → JWT |
| `/api/v1/pets` | POST/GET | 반려동물 프로필 |
| `/api/v1/pets/{id}` | GET | 펫 단건 조회 |
| `/api/v1/emotions` | POST | 감정 체크인 + 위기감지 |
| `/api/v1/messages/{pet_id}` | POST | 추모 메시지 생성 (Gemini) |
| `/api/v1/messages/{pet_id}/latest` | GET | 최근 메시지 조회 |
| `/api/v1/tts` | POST | TTS 음성 합성 |
| `/api/v1/missions/{pet_id}` | GET | 미션 목록 |
| `/api/v1/missions/{id}/complete` | PATCH | 미션 완료 |
| `/api/v1/timeline/{pet_id}` | GET/POST | 추모 타임라인 |
| `/api/v1/report/{pet_id}` | GET | 평가 리포트 |
| `/api/v1/hospitals` | GET | 동물병원 검색 (카카오맵) |
| `/api/v1/media/upload` | POST | 사진 업로드 → LivePortrait |
| `/api/v1/media/{id}` | GET | 영상 생성 상태 조회 |
| `/api/v1/media/{id}/perso` | POST | PERSO 립싱크 요청 |
| `/uploads/*` | GET | 정적 파일 서빙 (tts, media) |

---

## 8. 보안 / 윤리 원칙

- 비밀키는 `.env` 만. 코드·git 커밋 금지.
- 위기 안내 **1393** 은 어떤 경우에도 누락·변경 금지.
- **"반려동물인 척" 1인칭 응답 생성 금지** — 보호자 대상 상징적 위로 메시지만.
- 사진/영상 등 개인 자료는 git 미포함, `uploads/` 서버 로컬 보관.
- 비밀번호: bcrypt 해싱, JWT 인증 전 엔드포인트 적용.
- PERSO 립싱크: 기술 검증용. 서비스 메인은 voiced_url(잔잔한 영상+TTS) 사용.
