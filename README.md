# 🌈 레인보우 브릿지 (Rainbow Bridge)

> 반려동물을 떠나보낸 보호자의 **펫로스(Pet Loss) 회복**을 돕는 AI 기반 애프터케어 서비스

[![Status](https://img.shields.io/badge/status-developing-yellow)]()
[![Period](https://img.shields.io/badge/period-2026.06.01~06.19-blue)]()

---

## 📌 이게 뭔가요?

반려동물을 떠나보낸 보호자가 겪는 **펫로스(Pet Loss)** 를 돕는 서비스입니다.
AI로 반려동물을 "부활"시키거나 대신 말하게 하는 서비스가 **아닙니다.**
보호자가 기억을 정리하고, 감정을 돌보고, 다시 일상으로 돌아가도록 곁에서 돕습니다.

| 구분 | 우리가 하는 것 | 우리가 안 하는 것 |
|------|----------------|-------------------|
| 메시지 | 기억 기반 **상징적 추모 메시지** | 반려동물인 척 말하기 |
| 목적 | 보호자의 **회복과 일상 복귀** | AI 부활 / 실시간 대화 |
| 영상 | 마지막 모습을 **영상으로 보관** | 가짜 대화 영상 |

---

## ✨ 핵심 기능 (프로토타입)

| # | 기능 | 설명 | 상태 |
|---|------|------|------|
| 1 | 반려동물 프로필 입력 | 이름·종·함께한 기간·추억 등 | ✅ |
| 2 | 보호자 감정 체크인 | 오늘의 감정 상태 기록 | ✅ |
| 3 | 기억 기반 추모 메시지 생성 | Gemini AI로 개인화 위로 메시지 생성 | ✅ |
| 4 | 음성 톤 선택 + TTS 낭독 | Google Cloud TTS로 메시지 낭독 | ✅ |
| 5 | 일상 복귀 미션 추천 | AI 맞춤 회복 활동 제안 | ✅ |
| 6 | 추모 타임라인 저장 | 기록을 시간순으로 보관 | ✅ |
| 7 | 위험 감정 안전 라우팅 | 위기 감지 시 1393 즉시 안내 | ✅ |
| 8 | 평가 리포트 | 감정 추이·미션 완료율 시각화 | 🟡 |

**가산점(멀티모달):** 사진 업로드 → LivePortrait → MP4 영상 생성 → 다운로드

> 진행 상황은 [docs/PROGRESS.md](docs/PROGRESS.md) 에서 실시간으로 확인하세요.

---

## 🧱 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | FastAPI (Python), MongoDB, SQLite (인증) |
| Frontend | Vite + React + Tailwind CSS |
| AI / LLM | Gemini API (`gemini-2.5-flash`) |
| TTS | Google Cloud Text-to-Speech (ko-KR-Neural2-A) |
| 멀티모달 | LivePortrait (animals 모드), PERSO API (영상 더빙) |
| Infra | NCP Cloud Server, Docker, GitHub Actions 자동 배포 |

자세한 구조는 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) 참고.

---

## 📁 폴더 구조

```
rainbow-bridge/
├── backend/          # FastAPI 백엔드 (모세종, 김윤한)
│   ├── app/
│   │   ├── api/      # 라우터 (엔드포인트)
│   │   ├── core/     # 설정, 공통 유틸
│   │   ├── models/   # DB 모델
│   │   ├── schemas/  # 요청/응답 스키마 (Pydantic)
│   │   ├── services/ # 비즈니스 로직
│   │   └── db/       # DB 연결
│   └── tests/
├── frontend/         # 프론트엔드 (민경이, 장민수)
├── ai/               # AI 엔진 (반소람, 정환주)
│   ├── llm/          # 추모 메시지 생성
│   ├── tts/          # 음성 합성
│   ├── liveportrait/ # 사진→영상
│   └── evaluation/   # 평가 리포트
├── docs/             # 📚 문서 (필독!)
│   ├── CONTRIBUTING.md   # 협업 규칙
│   ├── GIT_GUIDE.md      # Git 사용법 (꼭 읽기)
│   ├── PROGRESS.md       # 프로토타입 진행도
│   ├── ARCHITECTURE.md   # 시스템 구조
│   ├── SETUP.md          # 개발 환경 셋업
│   └── devlog/           # 개발일지 (통합 + members/사람별)
└── scripts/          # 유틸 스크립트
```

---

## 🚀 빠른 시작

> 처음 합류했다면 **반드시** 아래 순서대로 읽으세요.

1. 📖 [docs/GIT_GUIDE.md](docs/GIT_GUIDE.md) — Git/브랜치/커밋 사용법 (가장 먼저!)
2. 🤝 [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) — 협업 규칙·컨벤션
3. ⚙️ [docs/SETUP.md](docs/SETUP.md) — 내 PC에 개발 환경 세팅
4. 🗺️ [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — 전체 구조 이해
5. ✅ [docs/PROGRESS.md](docs/PROGRESS.md) — 내가 맡은 일 확인

```bash
# 1. 레포 클론
git clone https://github.com/mosejong/Rainbow-Bridge.git
cd Rainbow-Bridge

# 2. 환경 변수 준비
cp .env.example .env
cp frontend/.env.example frontend/.env

# 3. 백엔드 실행
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000/docs

# 4. 프론트엔드 실행
cd frontend && npm install && npm run dev  # http://localhost:5173
```

> 실서버: http://101.79.19.87 (프론트) · http://101.79.19.87:8000 (API)

---

## 👥 팀 (팀 5)

| 이름 | 역할 |
|------|------|
| 모세종 | PM + 백엔드 |
| 김윤한 | 백엔드 / 홈서버 운영 |
| 반소람 | AI 엔지니어 |
| 정환주 | AI 엔지니어 / GPU 서버 |
| 민경이 | 프론트엔드 |
| 장민수 | 멀티모달 (사진→영상) |

---

## 📅 일정

- **2026-06-01** 프로젝트 시작 / 레포 셋업
- **2026-06-19** 발표

---

## 📜 라이선스 / 안내

교육 과정 팀 프로젝트입니다. 위기 상황 안내 번호(1393)는 임의로 변경하지 마세요.
