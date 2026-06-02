# ⚙️ 개발 환경 셋업 (SETUP)

> 내 PC에 개발 환경을 세팅하는 문서입니다. 영역별로 본인 파트만 보면 됩니다.
> 막히면 [GIT_GUIDE.md](GIT_GUIDE.md) → 그래도 안 되면 팀 채널.

---

## 0. 공통 (전원)

### 필수 설치
- [Git](https://git-scm.com)
- [Python 3.11](https://www.python.org/downloads/) (백엔드/AI) — **3.11 권장 (CI와 동일)**, 3.10~3.13도 대부분 동작하나 문제 발생 시 3.11로 맞출 것
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
cd backend

# MongoDB 실행 (docker-compose 사용)
docker compose up -d

# 종료 (데이터 유지)
docker compose down

# 종료 + 데이터 삭제
docker compose down -v
```
- `.env` 의 `MONGO_URI`, `MONGO_DB_NAME` 확인
- 홈서버 연결 정보는 김윤한이 별도 공유

---

## 2. AI 엔진 (반소람, 정환주)

### 2-1. 개발용 LLM (Gemini)
> 🔄 결정 변경(2026-06-02): 로컬 EXAONE → **Gemini API** (강사 권고 + 8GB GPU 제약). 상세 — [../ai/llm/MODEL_NOTES.md](../ai/llm/MODEL_NOTES.md)

- 사용: **Gemini API** (OpenAI 호환 엔드포인트 제공, GPU 불필요)
- 키 발급: [Google AI Studio](https://aistudio.google.com/apikey) → API 키 생성
- 모델: **gemini-2.5-flash** (빠르고 한국어 양호. 정확한 태그는 AI Studio에서 확인)
- `.env` 채울 값: `LLM_PROVIDER=gemini`, `LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/`, `LLM_MODEL=gemini-2.5-flash`, `LLM_API_KEY=<발급키>`
- 연결 확인: `python ai/llm/smoke_gemini.py`
- (선택) **로컬 폴백** — 오프라인/프라이버시 시: Ollama + `exaone3.5:7.8b` (`LLM_PROVIDER=ollama`, `LLM_BASE_URL=http://localhost:11434/v1`)

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
