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
- **제약**: 로그온해야 뜸(잠금/미로그온 시 X) / PC 절전·종료 시 중단 / ngrok 무료라 동시 1터널.
</content>
