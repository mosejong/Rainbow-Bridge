# ⚙️ 개발 환경 셋업 (SETUP)

> 내 PC에 개발 환경을 세팅하는 문서입니다. 영역별로 본인 파트만 보면 됩니다.
> 막히면 [GIT_GUIDE.md](GIT_GUIDE.md) → 그래도 안 되면 팀 채널.
> **최종 수정:** 2026-06-04

---

## 0. 공통 (전원)

### 필수 설치
- [Git](https://git-scm.com)
- [Python 3.12](https://www.python.org/downloads/) (백엔드/AI)
- [Node.js 20+](https://nodejs.org/) (프론트엔드)
- VS Code (권장)

### 레포 받기
```bash
git clone https://github.com/mosejong/Rainbow-Bridge.git
cd Rainbow-Bridge

# 루트 환경변수
cp .env.example .env       # Windows: Copy-Item .env.example .env

# 프론트엔드 환경변수
cp frontend/.env.example frontend/.env
```

> `.env` 열어서 Gemini API 키, Google Cloud TTS 키 등 본인 파트 값 채우기.

---

## 1. 백엔드 (모세종, 김윤한)

```bash
cd backend

# 가상환경
python -m venv venv
# 활성화
#   Windows PowerShell:  venv\Scripts\Activate.ps1
#   Mac/Linux:           source venv/bin/activate

pip install -r requirements.txt

# 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- 확인: 브라우저 `http://localhost:8000/docs` (자동 API 문서)
- 헬스체크: `http://localhost:8000/health`

### push 전 CI 검사 (필수)
```bash
cd backend
ruff check . --fix && black . && pytest -q
```

### MongoDB (NCP 실서버)
- NCP 서버(`101.79.19.87`)에서 MongoDB Docker로 운영 중
- Docker Compose로 백엔드와 MongoDB를 같이 띄우는 경우 `.env`의 `MONGO_URI`는 `mongodb://rainbow_mongo:27017`
- Docker 없이 로컬 PC에서 `uvicorn`만 직접 띄우고 로컬 MongoDB를 쓸 때만 `mongodb://localhost:27017`
- 로컬 Docker MongoDB가 필요하면: `docker compose -f backend/docker-compose.yml up -d`

---

## 2. 프론트엔드 (민경이) — React Native + Expo

> ⚠️ `frontend/`(구버전 Vite+React)는 더 이상 사용하지 않습니다. **`frontend-rn/`** 에서 작업하세요.
> 자세한 가이드: [frontend-rn/README.md](../frontend-rn/README.md)

```bash
cd frontend-rn
npm install --legacy-peer-deps

# 개발 서버 실행 (Expo Go 앱으로 QR 스캔)
npx expo start --clear
```

### 백엔드 연결 설정
`frontend-rn/.env` 파일 (없으면 직접 생성):
```
EXPO_PUBLIC_API_URL=http://<내 PC IP>:8000
```
> ⚠️ `localhost`는 폰에서 안 됩니다. 실제 IP를 써야 해요.
> Windows: `ipconfig | Select-String "IPv4"` 로 확인

---

## 3. AI 엔진 (반소람, 정환주)

### 3-1. Gemini API (LLM)
- 키 발급: [Google AI Studio](https://aistudio.google.com/apikey) → API 키 생성
- `.env` 채울 값:
  ```
  LLM_PROVIDER=gemini
  LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
  LLM_MODEL=gemini-2.5-flash
  LLM_API_KEY=<발급키>
  ```
- 연결 확인: `python ai/llm/smoke_gemini.py`

### 3-2. Google Cloud TTS (정환주)
- 키 발급: Google Cloud Console → Text-to-Speech API 사용설정 → 서비스 계정 JSON 발급
- `.env` 채울 값:
  ```
  GOOGLE_APPLICATION_CREDENTIALS=./ai/tts/gcp-tts-key.json
  TTS_VOICE=ko-KR-Neural2-A
  ```
- 설치: `pip install -r ai/requirements.txt`
- ⚠️ 보호자 대상 낭독만. 반려동물 목소리 흉내 금지.

### 3-3. PERSO API — ~~드랍 (2026-06-06)~~
> 동물 얼굴 감지 구조적 불가 확인으로 드랍. LivePortrait 발화 driving으로 대체.
> `PERSO_API_KEY` 환경변수는 무시해도 됩니다.

### AI 테스트 실행
```bash
cd backend
pytest ai/llm/tests/ -v     # 위기감지 골든셋 등
```

---

## 4. 멀티모달 — LivePortrait (장민수, 정환주)

- GPU 서버 (RTX 5060, 정환주) 또는 홈서버 HDD (`/mnt/hdd`, 김윤한) 활용
- conda 환경 세팅:
  ```bash
  conda create -n liveportrait python=3.10
  conda activate liveportrait
  cd ai/liveportrait
  pip install -r requirements.txt
  ```
- 실행: `python ai/liveportrait/pipeline.py --input <사진> --output <결과>`
- 기본 강도: `driving_multiplier=0.4` (추모 톤 최적화 완료)
- Replicate fallback: `.env`의 `REPLICATE_API_TOKEN`, `LIVEPORTRAIT_MODE=replicate`
- FFmpeg 필요 (영상+음성 합성): [ffmpeg.org](https://ffmpeg.org)

---

## 5. NCP 실서버 접속 (모세종·김윤한)

```bash
# SSH 접속 (인증키 필요 — 모세종에게 문의)
ssh -i rainbow-bridge.pem root@101.79.19.87

# 서버 상태 확인
sudo systemctl status rainbow-bridge

# 서버 재시작
sudo systemctl restart rainbow-bridge

# 로그 확인
sudo journalctl -u rainbow-bridge -n 50 --no-pager

# dev 최신 코드 반영 (GitHub Actions 자동배포로 보통 불필요)
cd /root/Rainbow-Bridge && git pull origin dev
```

- 프론트: `http://101.79.19.87` (nginx 서빙)
- 백엔드: `http://101.79.19.87:8000`
- API 문서: `http://101.79.19.87:8000/docs`

---

## 6. 트러블슈팅

| 증상 | 해결 |
|------|------|
| `uvicorn` 명령 없음 | 가상환경 활성화했는지 확인 |
| PowerShell 가상환경 활성화 막힘 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| MongoDB 연결 실패 | `MONGO_URI` 확인, Docker 컨테이너 상태 `docker ps` |
| `.env` 값 반영 안 됨 | 서버 재시작 |
| 포트 8000 이미 사용중 | `--port 8001` 또는 기존 프로세스 종료 |
| 회원가입·로그인 실패 (localhost) | 프론트 `.env`의 `VITE_API_BASE_URL` 확인 |
| TTS 음성 안 나옴 | `GOOGLE_APPLICATION_CREDENTIALS` 경로·권한 확인 |
| NCP 서버 응답 없음 | `sudo systemctl status rainbow-bridge` 로 서버 상태 확인 |
