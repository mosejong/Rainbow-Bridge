# 🖥️ GPU 서버 운영 가이드 (RTX 5060 8GB)

> 담당: 정환주. 팀 전체 AI 추론(LLM·TTS·영상)의 **물리적 허브**입니다.
> 관련: [ROLES.md](ROLES.md) · [TODO.md](TODO.md) · [tts/CLAUDE.md](tts/CLAUDE.md)

---

## 1. 하드웨어

- **RTX 5060 / VRAM 8GB**
- 8GB는 작은 편 → "다 띄우기"가 아니라 **LLM 상시 + 나머지 온디맨드 + fallback** 전략.

---

## 2. VRAM 예산 (8GB)

| 작업 | 대략 VRAM | 운영 |
|------|-----------|------|
| LLM 7B **Q4 양자화** | ~5–6GB | 상시 |
| LLM 7B fp16 | ~14GB | ❌ 불가 → 양자화 필수 |
| TTS | ~2–4GB | 온디맨드 |
| LivePortrait (장민수) | ~4–6GB | 멀티모달 — 이 GPU 공유 시 협의 |

> **LLM + TTS + LivePortrait 동시 상주는 8GB에선 불가.** 쓸 때 로드, 끝나면 VRAM 회수.
> LivePortrait는 **장민수(멀티모달) 담당** — 정환주 작업은 아니지만, 같은 GPU를 쓰면 VRAM이 겹치므로 자원 계획에만 포함.

---

## 3. 모델·엔진 선정 (8GB 기준)

- 8GB에선 **vLLM/SGLang으로 7B가 빡빡**(KV캐시 프리할당 때문).
- ✅ **권장: `llama.cpp`(llama-server) + GGUF Q4_K_M** — 8GB에 안정적, OpenAI 호환 서버 제공.
- 처리량 우선 + 작은 모델(3~4B)이면 vLLM/SGLang도 가능.
- 한국어 모델 후보: **Qwen2.5-7B-Instruct** / **EXAONE-3.5-7.8B** / (여유 두려면 3~4B급).
- 실제 구동 후기는 → [llm/MODEL_NOTES.md](llm/MODEL_NOTES.md).

---

## 4. LLM 추론 서버 띄우기 (권장: llama-server)

```bash
# GGUF Q4_K_M 모델 다운로드 후
llama-server -m ./models/qwen2.5-7b-instruct-q4_k_m.gguf \
  -ngl 99 -c 4096 \
  --host 0.0.0.0 --port 8001
```
- `-ngl 99` 전 레이어 GPU 로드 · `-c 4096` 컨텍스트(짧게 잡아 VRAM 절약)
- OpenAI 호환 엔드포인트: `http://<gpu-ip>:8001/v1/chat/completions`

### vLLM 대안 (작은 모델/처리량 우선)
```bash
vllm serve <model-awq> --quantization awq \
  --gpu-memory-utilization 0.85 --max-model-len 4096 --port 8001
```
> 8GB에선 7B AWQ도 타이트 → `--max-model-len` 줄이고 `nvidia-smi` 모니터링.

---

## 5. 상시 vs 온디맨드

| 구분 | 대상 | 비고 |
|------|------|------|
| 상시 | LLM 서버 1개 | ③⑦⑤가 전부 의존 |
| 온디맨드 | TTS (· LivePortrait는 장민수) | 쓸 때 프로세스 실행 → 끝나면 종료해 VRAM 회수 |

---

## 6. Fallback (터질 때 대비)

- LLM → **PERSO API**
- (멀티모달 LivePortrait → Replicate — 장민수 담당, GPU 부담 클 때 권장)
- 모델 2종(7B / 더 작은 것) 준비 → VRAM 부족 시 즉시 교체.

---

## 7. 네트워크 (홈서버 연동)

- 김윤한 홈서버 ↔ 정환주 GPU 서버 = HTTP 통신.
- 포트(예 8001) 방화벽 개방 / 내부망 또는 터널.
- ⚠️ **정환주 PC 꺼지면 팀 LLM 다운** → 전원·가동시간 관리도 역할.

---

## 8. 모니터링

```bash
nvidia-smi              # VRAM·사용량 확인
watch -n 1 nvidia-smi   # 실시간 (Linux)
```

---

## 9. provider 연동 값 (`.env`)

```
LLM_PROVIDER=llamacpp          # 또는 vllm
LLM_BASE_URL=http://<gpu-ip>:8001/v1
LLM_MODEL=qwen2.5-7b-instruct
```
> 값 확정되면 `.env.example` · [../docs/SETUP.md §2-1](../docs/SETUP.md) 도 채우세요.

---

## 10. 정환주 작업 순서

```
1. nvidia-smi 확인 (완료: 8GB)
2. LLM 추론 서버 띄우기 (llama-server, GGUF Q4) → 팀에 HTTP 노출  🥇
3. ④ TTS 엔진 (온디맨드)
4. ⑧ 평가 집계 (GPU 거의 안 씀 — 틈틈이)
```
> LivePortrait(가산점)는 **장민수 담당** — 정환주 작업 아님. 같은 GPU 쓰면 VRAM만 협의.

---

## 11. LivePortrait remote 터널 (→ 장민수 인계)

GPU 서버(:8001 LivePortrait)를 ngrok static domain 으로 외부 노출 — 장민수 remote 추론용. (GPU 인프라=정환주, 소비 코드=장민수)

- **고정 URL**: `https://rerun-devious-reaffirm.ngrok-free.dev` — ngrok 무료 **static domain**(2026-06-08 확정). 재시작·재발급해도 안 바뀜.
- **터널 명령**: `ngrok http --url=rerun-devious-reaffirm.ngrok-free.dev 8001` (`--domain` deprecated → `--url`).
- **자동시작**: 로그온 시 uvicorn(:8001)+ngrok 자동 기동(HKCU Run `RainbowBridgeGPU`, 레포 밖 스크립트).
- **백엔드 연결(장민수가 본인 `.env` 에)**:
  ```
  LIVEPORTRAIT_MODE=remote
  LIVEPORTRAIT_REMOTE_URL=https://rerun-devious-reaffirm.ngrok-free.dev
  ```
  소비처 = [liveportrait/pipeline.py](liveportrait/pipeline.py) `os.getenv("LIVEPORTRAIT_REMOTE_URL")`. (`.env.example` 엔 빈 값 + 위 주소 주석)
- **제약**: 로그온해야 뜸(잠금/미로그온 시 X) / PC 절전·종료 시 중단.
- **2026-06-09 변경**: ngrok 은 이제 8001 직결이 아니라 **프록시(8080)를 가리킴** → 루트(`/`)가 8001 LivePortrait 로 전달돼 위 URL·동작은 동일. 무료 동시 1터널 제약은 경로 공유로 해소(§12).

---

## 12. TTS remote 터널 (→ 김윤한 인계) + 경로 공유 프록시

NCP 백엔드엔 GPU 가 없어(=백엔드 직접 합성 불가) TTS 도 LivePortrait 처럼 GPU 서버에서 HTTP 제공. 무료 ngrok static domain 이 1개뿐이라(이미 §11 LivePortrait 가 점유), **리버스 프록시로 같은 도메인을 경로로 쪼개** 두 서비스를 노출한다.

```
https://rerun-devious-reaffirm.ngrok-free.dev/         -> 8001 LivePortrait (장민수, §11)
https://rerun-devious-reaffirm.ngrok-free.dev/tts/*    -> 8003 Qwen3 TTS    (윤한)
                         └ ngrok → 8080 프록시(gpu_proxy.py) → 경로 분기
```

- **TTS 고정 URL(백엔드 `/tts` 가 호출)**: `https://rerun-devious-reaffirm.ngrok-free.dev/tts`
- **백엔드 연결(김윤한이 본인 `.env` 에)**:
  ```
  TTS_SERVER_URL=https://rerun-devious-reaffirm.ngrok-free.dev/tts
  ```
  소비처 = 백엔드 `/tts`. (`.env.example` 엔 빈 값 유지)
- **엔드포인트**: `POST /tts/synthesize` `{text, tone(boy|girl)}` → wav (헤더 `X-Audio-Duration`/`X-Audio-Format`) · `GET /tts/health`.
  - ⚠️ 한글은 **UTF-8 JSON** 으로 전송(httpx/requests 는 자동). 깨지면 400 `error parsing the body` — 서버 버그 아님.
- **서버 코드**: [tts/server.py](tts/server.py) (`synthesize()` FastAPI 래핑, 포트 8003).
- **프록시 코드**: `C:\Rainbow_Bridge\gpu_proxy.py` (레포 밖 운영 글루, git 미포함). 루트→8001, `/tts/*`→8003(프리픽스 제거).
- **자동시작**: `gpu_server_start.ps1`(레포 밖) 이 로그온 시 프록시(8080)·TTS(8003)·ngrok(→8080) 일괄 기동. (2026-06-09 LP가 소람 PC로 이전돼 이 스크립트에서 LivePortrait(8001) 기동 블록 제거 — §13)
- **제약**: 로그온해야 뜸 / PC 절전·종료 시 중단 / TTS·webui(8000) VRAM(8GB) 동시 주의(qwen3 인스턴스 1개) / 영상(LivePortrait)+TTS 동시 추론 시 VRAM 협의.

### 12-1. 실연동 검증 (2026-06-09)

외부 고정 도메인 왕복 **실측 통과**:
- `GET /tts/health` → 200 `{"voices":["boy","girl"]}`.
- `POST /tts/synthesize` (한글 UTF-8) → **200, WAV 234KB, 4.9초, RIFF 헤더 정상**. 경로 = 외부 → ngrok → 8080 프록시 → 8003 TTS.

백엔드 호출 계약도 코드 일치 확인 — [../backend/app/services/tts.py](../backend/app/services/tts.py) `_qwen3_remote`:

| 항목 | 백엔드 | GPU 서버 | 일치 |
|------|--------|----------|------|
| 호출 URL | `{TTS_SERVER_URL}/synthesize` | `/tts/synthesize` | ✅ |
| 요청 바디 | `{text, tone}` | `SynthesizeRequest{text, tone}` | ✅ |
| tone 값 | `_map_tone_to_voice` → 항상 `boy`/`girl` | `AVAILABLE_VOICES=[boy,girl]` | ✅ (400 없음) |
| 응답 헤더 | `X-Audio-Duration`/`X-Audio-Format` | 동일 송신 | ✅ |

### 12-2. NCP 실서버 인계 체크리스트 (→ 김윤한, 정환주 권한 밖)

GPU측·계약은 검증 완료. 아래만 하면 **NCP → GPU 왕복 실연동 완성**:

1. NCP 실서버 `.env` 에 한 줄 추가 후 백엔드 재시작 (미설정 시 Google TTS 폴백 — 현재 상태):
   ```
   TTS_SERVER_URL=https://rerun-devious-reaffirm.ngrok-free.dev/tts
   ```
2. `POST /api/v1/tts` `{"pet_id":"<테스트>", "tone":"warm", "text":"무지개 다리 잘 건너가렴"}` 호출 → 응답 `{audio_url, duration, format}`(201), `/uploads/tts/*_girl_*.wav` 생성 확인.
3. 호출 시각 공유 시 정환주가 GPU 로그에서 왕복 실시간 확인.

---

## 13. LP 소람 PC 이전 후 — 2터널(TTS + LP) 동시 운용 (2026-06-09 검증)

§11/§12 의 "단일 ngrok 도메인 + 프록시 경로 공유"(`/`=LP, `/tts/*`=TTS)는 **LP·TTS 가 같은 GPU(정환주 PC)에 있다는 전제**였다. Day9 에 **LivePortrait 엔진이 정환주 GPU 에 미설치**임이 확인돼 발표 LP 호스트가 **반소람 PC**로 이전([liveportrait/SETUP_LivePortrait.md](liveportrait/SETUP_LivePortrait.md) §10) → 이 전제가 깨졌다. LP 와 TTS 가 **물리적으로 다른 PC** 이므로 한 머신의 프록시(8080)가 두 서비스를 경로로 쪼갤 수 없다.

### 13-1. 구조 — 2계정 2터널 (동시 1세션 제약 회피)

ngrok 무료는 **계정당 동시 1 에이전트 세션** 이라, 정환주·소람이 같은 토큰을 쓰면 동시 2터널이 불가하다. 그래서 **각자 다른 ngrok 계정**으로 분리 운용한다 — 계정이 다르면 세션 충돌이 원천적으로 없다.

```
TTS  : https://rerun-devious-reaffirm.ngrok-free.dev/tts/*  -> 정환주 GPU :8003 (고정 도메인, 상시)
LP   : https://<소람 무료 임의주소>.ngrok-free.dev/*         -> 소람 PC   :8001 (발표 직전 점등)
```

- 백엔드(NCP) `.env` 는 **두 변수**를 각각 가리킨다:
  ```
  TTS_SERVER_URL=https://rerun-devious-reaffirm.ngrok-free.dev/tts   # 정환주 (§12)
  LIVEPORTRAIT_REMOTE_URL=https://<소람 무료 임의주소>.ngrok-free.dev  # 소람 (발표 직전 공유 → 모세종이 반영)
  ```
- 소람 터널은 고정 도메인이 아니라 **무료 임의 주소**(현 ngrok 무료 신규 발급 도메인은 `.ngrok-free.dev`) → 켤 때마다 주소가 바뀌므로 **발표 직전 점등 후 모세종에게 공유**(SETUP §10·§11). 정환주 TTS 고정 도메인은 그대로 유지.
- **정환주 GPU 자동기동 정리(2026-06-09)**: LP 가 소람 PC 로 이전했으므로 `gpu_server_start.ps1`(레포 밖)에서 **LivePortrait(8001) 기동 블록 제거** → 다음 로그온부터 프록시(8080)·TTS(8003)·ngrok 만 기동. (정환주 GPU 엔 LP 미설치라 VRAM 점유는 원래 없었고, 헛도는 8001 기동만 정리.) 프록시 루트(`/`)→8001 경로는 죽지만 백엔드는 `/tts` 만 호출하므로 무해.

### 13-2. 검증 현황 — 터널 레벨 2터널 동시 운용 ✅ 실증 (2026-06-09)

소람 PC LP 호스트 셋업 완료(RTX 3060, LivePortrait animals 풀 설치 + `server.py`:8001 + ngrok) 후 **양쪽 터널을 동시에 health 호출 → 둘 다 200** 으로 실증됨. 정환주 측에서도 재실측 확인.

| 항목 | 결과 | 비고 |
|------|------|------|
| 구조: 별도 계정 → 동시 1세션 제약 회피 | ✅ 확정·실증 | 소람 ngrok 계정이 정환주와 달라, 동시 점등해도 무료 1세션 제한 안 걸림 |
| TTS 터널 라이브 | ✅ `GET /tts/health` → 200 `{"service":"qwen3-tts","voices":["boy","girl"]}` | 정환주 GPU, 상시 가동 |
| LP 터널 라이브 | ✅ `GET /health` → 200 `{"service":"liveportrait","mode":"local","driving_multiplier":0.5}` | 소람 PC, 발표 직전 점등(실측 시 가동) |
| 2터널 **동시** health | ✅ 둘 다 200 동시 응답 | 서로 막지 않음 — 동시 운용 성립 확인 |

> 검증 당시 소람 LP 주소: `https://enlarging-cane-vagrantly.ngrok-free.dev` (무료 랜덤 → 재점등 시 변동, §13-1·5 참고). **터널/GPU 레벨의 2터널 동시 운용은 통과.** 남은 것은 NCP 백엔드 `.env` 반영뿐(§13-3 step 3~4, 모세종).

### 13-3. 발표 직전 동시 운용 검증 체크리스트

소람 PC LP 터널이 뜬 시점에 아래를 순서대로:

1. **소람 PC**: `nvidia-smi` VRAM 확인 → `uvicorn server:app --port 8001` → `ngrok http 8001` (소람 본인 authtoken). 발급 주소 공유.
2. **양쪽 health 동시 호출** (둘 다 200이어야 동시 가동 확인):
   ```bash
   curl.exe https://rerun-devious-reaffirm.ngrok-free.dev/tts/health   # TTS 200
   curl.exe https://<소람주소>.ngrok-free.app/health                    # LP  200 (driving_multiplier 표시)
   ```
3. **백엔드 `.env`** 에 `LIVEPORTRAIT_REMOTE_URL` 반영(모세종) → 백엔드 재시작.
4. **백엔드 경유 양쪽 왕복**: `POST /api/v1/tts`(wav 생성) + LP 생성 경로 호출 → 각각 정상 응답.
   - 두 호출이 **서로 막지 않고** 각자 200/201 이면 = **2터널 동시 운용 검증 완료.**
5. **백업**: 터널이 죽어도 보여줄 사전 녹화본(장민수 보유, SETUP §11) 준비.
