# ⚙️ 개발 환경 셋업 (SETUP)

> 내 PC에 개발 환경을 세팅하는 문서입니다. 영역별로 본인 파트만 보면 됩니다.
> 막히면 [GIT_GUIDE.md](GIT_GUIDE.md) → 그래도 안 되면 팀 채널.

---

## 0. 공통 (전원)

### 필수 설치
- [Git](https://git-scm.com)
- [Python 3.11+](https://www.python.org/downloads/) (백엔드/AI)
- VS Code (권장)

### 레포 받기
```bash
git clone <레포_주소>
cd rainbow-bridge
cp .env.example .env       # Windows: Copy-Item .env.example .env
```
→ `.env` 열어서 값 채우기 (각 파트 담당이 안내)

---

## 1. 백엔드 (모세종, 김윤한)

```bash
cd backend

# 가상환경
python -m venv .venv
# 활성화
#   Windows PowerShell:  .venv\Scripts\Activate.ps1
#   Mac/Linux:           source .venv/bin/activate

pip install -r requirements.txt

# 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- 확인: 브라우저 `http://localhost:8000/docs` (자동 API 문서)
- 헬스체크: `http://localhost:8000/health`

### MongoDB (김윤한)
```bash
# 로컬 테스트용 (Docker)
docker run -d --name rainbow-mongo -p 27017:27017 mongo:7
```
- `.env` 의 `MONGO_URI`, `MONGO_DB_NAME` 확인
- 홈서버 연결 정보는 김윤한이 별도 공유

### Docker / docker-compose (김윤한)
> 통합 실행 환경. 작성 후 이 칸 갱신.
```bash
# docker compose up -d   (compose 파일 준비되면)
```
- [ ] docker-compose.yml 작성 — _담당: 김윤한, 작성 후 명령어 여기 채우기_

---

## 2. AI 엔진 (반소람, 정환주)

### 2-1. 로컬 LLM
> ✅ 결정: **Ollama + EXAONE-3.5-7.8B** (RTX 5060 8GB 기준). 2.4B/7.8B 비교 후 확정 — [../ai/llm/MODEL_NOTES.md](../ai/llm/MODEL_NOTES.md)

- 사용 엔진: **Ollama** (OpenAI 호환 API 제공, 8GB 개발 환경에 적합)
- 모델: **exaone3.5:7.8b** (1인칭 회피·위기 분류 안정성으로 채택). 저사양 PC는 `exaone3.5:2.4b` 대안 (빠르나 1인칭 위반 위험)
- 설치 / 실행 방법:
  ```bash
  # Ollama 설치 후
  ollama pull exaone3.5:7.8b
  # 서버는 보통 자동 실행 (API: http://localhost:11434)
  # 테스트: POST http://localhost:11434/api/chat
  ```
- `.env` 채울 값: `LLM_PROVIDER=ollama`, `LLM_BASE_URL=http://localhost:11434/v1`, `LLM_MODEL=exaone3.5:7.8b`, `LLM_API_KEY`(Ollama는 불필요)
- ⚠️ 8GB에선 7.8B가 일부 CPU로 넘어가 느릴 수 있음 → 다른 GPU 앱 정리 권장

### 2-2. PERSO API (평가/시연)
> 🚧 담당 기입. 할당량 제한 있으니 개발 중엔 로컬 LLM 사용.

- 발급/엔드포인트: _____________________
- `.env` 채울 값: `PERSO_API_KEY`, `PERSO_API_BASE_URL`

### 2-3. TTS
> 🚧 담당 기입.

- 엔진: _____________________
- 설치/실행:
  ```bash
  # 담당 기입
  ```

---

## 3. 멀티모달 — LivePortrait (장민수, 정환주)

> 🚧 GPU 서버(RTX 5060) 기준. 담당이 설치 절차 확정 후 채우기.

- LivePortrait 설치/모델 다운로드: _____________________
- 로컬 실행 방법:
  ```bash
  # 담당 기입
  ```
- Replicate fallback 사용 시: `.env` 의 `REPLICATE_API_TOKEN` 설정, `LIVEPORTRAIT_MODE=replicate`
- FFmpeg 설치 필요 (영상+음성 합성): [ffmpeg.org](https://ffmpeg.org)

---

## 4. 프론트엔드 (민경이)

> 🚧 프레임워크 결정 후 채우기.

- 프레임워크: _____________________
- 설치/실행:
  ```bash
  # 담당 기입
  ```
- 백엔드 API 주소: 기본 `http://localhost:8000`

---

## 5. 트러블슈팅

| 증상 | 해결 |
|------|------|
| `uvicorn` 명령 없음 | 가상환경 활성화했는지 확인 |
| PowerShell 가상환경 활성화 막힘 | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` 후 재시도 |
| MongoDB 연결 실패 | 도커 컨테이너 켜졌는지 `docker ps` 확인, `MONGO_URI` 확인 |
| `.env` 값 반영 안 됨 | 서버 재시작 |
| 포트 8000 이미 사용중 | `--port 8001` 등으로 변경 |
