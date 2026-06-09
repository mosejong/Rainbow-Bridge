# LivePortrait(animals) 설치 가이드 — 발표 LP 서버 호스트용

> **목적:** 반려동물 사진 → 추모 영상(animals 모드)을 만드는 LivePortrait를 **새 PC에 처음부터 설치**하고,
> 우리 레포의 `server.py`(8001) + ngrok 터널로 백엔드가 호출할 수 있게 노출하는 전체 절차.
> **작성:** 장민수(멀티모달) · 2026-06-09. 발표 LP 호스트가 **반소람 PC**로 변경됨에 따라 작성.
> **검증 기준:** 장민수 PC(설치 완료·발표 확정본 생성 이력)의 실제 구성을 그대로 옮긴 것.

---

## 0. 읽기 전에 — 이 문서의 전제

- 대상 독자 = **소람님 + 소람님 PC의 Claude Code**. 명령은 위에서부터 순서대로 실행.
- ⚠️ **가장 큰 함정 2개** (아래 본문에서 상세):
  1. **torch는 "복사 금지"** — 장민수 PC는 `torch 2.13.0.dev+cu132`(nightly)지만 이건 특수 환경. **소람님 GPU에 맞는 버전을 따로 설치**해야 함.
  2. **XPose CUDA ops 빌드** — animals 모드는 XPose(키포인트 감지)에 의존하고, 그 안의 `MultiScaleDeformableAttention`은 **C++/CUDA 확장이라 직접 컴파일**해야 함. Windows에선 Visual Studio Build Tools + CUDA Toolkit 필요.
- ✅ "되는 것처럼 보임 ≠ 진짜 됨". 반드시 **§9 실제 생성 테스트**까지 통과해야 완료.

---

## 1. 사전 요구사항 (먼저 PC에 깔려 있어야 함)

| 항목 | 확인 명령 | 없으면 |
|------|-----------|--------|
| NVIDIA GPU + 드라이버 | `nvidia-smi` | GPU 드라이버 설치 |
| Anaconda/Miniconda | `conda --version` | Miniconda 설치 |
| Git | `git --version` | Git 설치 |
| **CUDA Toolkit** (nvcc) | `nvcc --version` | XPose 빌드에 필요 → CUDA Toolkit 설치 |
| **Visual Studio Build Tools** (C++) | — | XPose 빌드에 필요 → "Desktop development with C++" 설치 |
| ffmpeg | `ffmpeg -version` | [ffmpeg.org](https://ffmpeg.org) 받아 PATH 등록 (장민수 PC는 `C:\ffmpeg\bin`) |

> `nvidia-smi` 우측 상단 "CUDA Version"을 **메모**해두세요. §3 torch 버전 결정에 씁니다.

---

## 2. LivePortrait 원본 받기

```bash
# 작업 폴더로 이동 (예: C:\LivePortrait 또는 원하는 경로)
git clone https://github.com/KwaiVGI/LivePortrait
cd LivePortrait
```
- 장민수 PC 기준 commit: `9b294b3` (원본 main 최신이면 OK).

---

## 3. conda 환경 + PyTorch (⚠️ 핵심 함정)

```bash
# 장민수 PC와 동일한 python 3.11 환경 생성 (장민수 실측 3.11.15)
conda create -n liveportrait python=3.11 -y
conda activate liveportrait
```

### ⚠️ torch는 장민수 버전을 복사하지 마세요

- 장민수 PC: `torch 2.13.0.dev20260601+cu132` (CUDA 13.2 nightly) — **특수 환경이라 그대로 쓰면 안 됨**.
- **소람님 GPU/드라이버(§1에서 메모한 CUDA 버전)에 맞춰** 설치하세요. 일반적인 권장:

| 소람 GPU 세대 | 권장 설치 |
|---------------|-----------|
| RTX 20/30/40 (CUDA 11.8/12.x) | `pip install torch==2.3.0 torchvision==0.18.0 --index-url https://download.pytorch.org/whl/cu118` (또는 cu121) |
| RTX 50 시리즈 등 최신 | 최신 CUDA 필요 → [PyTorch 공식 선택기](https://pytorch.org/get-started/locally/)에서 본인 CUDA에 맞는 명령 사용 (필요시 nightly) |

```bash
# 설치 후 반드시 확인 — True 나와야 함
python -c "import torch; print(torch.__version__, torch.version.cuda, torch.cuda.is_available())"
```
> `torch.cuda.is_available()` 가 **False**면 영상이 GPU로 안 돌아갑니다. 여기서 멈추고 torch/CUDA 버전을 맞추세요.

---

## 4. 의존 패키지 설치

```bash
# LivePortrait 기본 의존 (requirements.txt → requirements_base.txt 포함)
pip install -r requirements.txt

# 우리 server.py 가 추가로 쓰는 것 (장민수 PC 설치 버전)
pip install fastapi==0.136.3 uvicorn python-multipart==0.0.30
```

장민수 PC `requirements_base.txt` 핵심 버전(참고): `numpy==1.26.4`, `opencv-python==4.10.0.84`, `onnxruntime-gpu==1.18.0`, `transformers==4.38.0`, `tyro==0.8.5`, `gradio==5.1.0`.

---

## 5. 모델 가중치 다운로드 (수 GB)

LivePortrait는 모델이 repo에 없어 **따로 받아야** 합니다. 공식 HuggingFace에서 받으면 animals·insightface·xpose가 **한 번에** 받아집니다.

```bash
pip install -U "huggingface_hub[cli]"
# pretrained_weights 폴더로 base + animals + insightface + xpose 일괄 다운로드
huggingface-cli download KwaiVGI/LivePortrait --local-dir pretrained_weights --exclude "*.git*"
```

### 다운로드 후 있어야 할 것 (장민수 PC 기준 — 빠지면 animals 안 됨)

```
pretrained_weights/
├── liveportrait_animals/
│   ├── base_models/           appearance_feature_extractor.pth, motion_extractor.pth,
│   │                          spade_generator.pth, warping_module.pth
│   ├── base_models_v1.1/      (동일 4개 .pth)
│   ├── retargeting_models/
│   └── xpose.pth              ← animals 키포인트(XPose) 가중치, 필수
├── liveportrait/              base_models, retargeting_models (사람용 — 있어도 무방)
└── insightface/models/buffalo_l/   2d106det.onnx, det_10g.onnx
```

---

## 6. ⚠️ XPose CUDA ops 빌드 (animals 최대 난관)

animals 모드는 XPose의 `MultiScaleDeformableAttention`(C++/CUDA 확장)을 빌드해야 import 됩니다. **이걸 안 하면 animals 추론 시 import 에러**가 납니다.

```bash
# (conda liveportrait 활성화 + §1의 VS Build Tools, CUDA Toolkit 설치 상태에서)
# Windows에서 빌드 실패 시 "x64 Native Tools Command Prompt for VS"에서 재시도(§11).
cd src/utils/dependencies/XPose/models/UniPose/ops
python setup.py build install
# 빌드 후 LivePortrait 루트로 복귀 — PowerShell엔 'cd -'가 없으니 경로로 직접 이동:
cd <소람님 LivePortrait 경로>
```

- 빌드 성공 시 산출물: `MultiScaleDeformableAttention.cp311-win_amd64.pyd` (장민수 PC에 존재 확인됨).
- 빌드 확인:
  ```bash
  python -c "import MultiScaleDeformableAttention; print('XPose ops OK')"
  ```
- **빌드 실패 시** → §10 트러블슈팅 참고 (대부분 VS Build Tools / nvcc 경로 문제).

---

## 7. 우리 레포 코드 배치 (server.py·pipeline.py)

영상 생성 엔진은 LivePortrait 폴더에 있고, **HTTP 서버 래퍼는 우리 레포**에 있습니다.

```bash
# 별도 폴더에 Rainbow-Bridge 클론 (이미 있으면 생략)
git clone https://github.com/mosejong/Rainbow-Bridge
# 사용할 파일: Rainbow-Bridge/ai/liveportrait/server.py, pipeline.py
```

- `pipeline.py`는 환경변수 `LIVEPORTRAIT_HOME`으로 LivePortrait 위치를 찾습니다(기본값 `c:\JMS\2_project\LivePortrait` = 장민수 경로). **소람님은 본인 LivePortrait 경로로 이 env를 지정**해야 합니다(§8).
- `perso_lipsync_test.py`는 드랍된 구버전 — 무시.

---

## 8. server.py 실행 (발표 레시피 env 포함)

```bash
conda activate liveportrait
cd Rainbow-Bridge/ai/liveportrait

# 환경변수 (Windows PowerShell 예시)
$env:LIVEPORTRAIT_HOME="<소람님 LivePortrait 경로>"          # 예: C:\LivePortrait
$env:LIVEPORTRAIT_DRIVING="<소람님 LivePortrait 경로>\assets\examples\driving\d3.mp4"
$env:LIVEPORTRAIT_DRIVING_MULTIPLIER="0.5"
# conda 환경명을 'liveportrait' 가 아닌 다른 이름으로 만들었다면 아래도 추가:
# $env:LIVEPORTRAIT_CONDA_ENV="<소람님이 만든 환경명>"

uvicorn server:app --host 0.0.0.0 --port 8001
```
> `pipeline.py`는 `LIVEPORTRAIT_HOME`(LivePortrait 위치)·`LIVEPORTRAIT_CONDA_ENV`(기본 `liveportrait`)로 엔진을 찾습니다. §3에서 환경명을 `liveportrait`로 만들었으면 `LIVEPORTRAIT_CONDA_ENV`는 생략 가능.

- **발표 확정 레시피**: driving=`d3.mp4`(차분한 모션) + multiplier=`0.5`(입 움직임 ~3.6). d3.mp4는 LivePortrait 기본 예제라 §5 다운로드에 포함됨.
- 헬스 체크: `curl.exe http://localhost:8001/health` → `"driving_multiplier": 0.5` 확인.
  > ⚠️ **PowerShell 주의**: 그냥 `curl`은 `Invoke-WebRequest` 별칭이라 `-F`·`-X`·`--output` 옵션이 안 먹힙니다. **반드시 `curl.exe`** 로 호출하세요(이 문서의 모든 curl 동일). cmd 창이면 `curl`도 OK.
  > ⚠️ 또한 `/health`는 **설정값만** 보여줄 뿐 실제 생성을 보장하지 않음. 반드시 §9까지 할 것.

---

## 9. ✅ 실제 생성 테스트 (가짜 성공 방지 — 이게 진짜 검증)

`/health` 통과로 끝내면 안 됩니다. **사진 1장을 실제로 넣어 영상이 나오는지** 확인해야 완료입니다.

```bash
# 방법 A) 엔진 직접 (LivePortrait 폴더에서) — 가장 확실
cd <소람님 LivePortrait 경로>
conda activate liveportrait
# s39.jpg = LivePortrait animals 공식 예제(고양이). 우리 pipeline.py와 동일 인자 구성.
python inference_animals.py -s assets/examples/source/s39.jpg \
  -d assets/examples/driving/d3.mp4 \
  -o animations \
  --no_flag_stitching --driving_multiplier 0.5
# → animations/ 폴더에 s39--d3.mp4 생기면 엔진 OK (XPose 빌드까지 정상이라는 뜻)

# 방법 B) 우리 서버 경유 (server.py 띄운 상태에서, 다른 터미널)
# PowerShell이면 curl 이 아니라 curl.exe (별칭 회피). 사진 경로는 영문 권장.
curl.exe -X POST http://localhost:8001/generate \
  -F "source=@<반려동물 사진.jpg>" --output test_result.mp4
# → test_result.mp4 가 정상 재생되면 서버까지 OK
```
> 여기까지 영상이 나오면 **본체 100% 작동 확정**. 이제 외부 노출(§10)로.

---

## 10. ngrok 터널 (백엔드가 호출하게 노출)

```bash
# ngrok 설치 (https://ngrok.com 가입 후 authtoken 등록)
ngrok config add-authtoken <소람님 토큰>

# 8001 노출
ngrok http 8001
```

- 출력된 `https://xxxx.ngrok-free.app` 주소를 **모세종님께 전달** → 백엔드 `.env`의 `LIVEPORTRAIT_REMOTE_URL`에 등록.
- 외부에서 확인: `curl.exe https://xxxx.ngrok-free.app/health`.
- (고정 도메인은 정환주님이 TTS용으로 이미 쓰는 중 → 소람님은 무료 임의 주소로 충분, 발표 직전에 켜고 주소 공유.)

---

## 11. 트러블슈팅

| 증상 | 원인 | 해결 |
|------|------|------|
| `torch.cuda.is_available()` False | torch-CUDA 버전 불일치 | §3 다시 — 본인 GPU CUDA에 맞는 torch 재설치 |
| animals 실행 시 `MultiScaleDeformableAttention` import 에러 | XPose ops 미빌드 | §6 빌드. VS Build Tools(C++) + CUDA Toolkit 설치 확인 |
| `setup.py build` 실패 (`cl.exe`/`nvcc` 없음) | 컴파일러 경로 | "x64 Native Tools Command Prompt for VS"에서 다시 빌드 |
| `cv2.imread` None / 한글 경로 못 읽음 | OpenCV 비ASCII 경로 버그 | 사진·경로를 **영문**으로. (server.py는 이미 영문 임시파일로 회피) |
| `driving 영상 없음: ...d0.mp4` 400 | `LIVEPORTRAIT_DRIVING` 미설정 | §8 env 설정 후 재기동 |
| 모델 못 찾음 | pretrained_weights 경로/누락 | §5 재다운로드, `LIVEPORTRAIT_HOME` 확인 |

---

## 12. 발표 당일 체크리스트 (PM 모세종님 당부 반영)

- [ ] 발표 호스트 PC = **소람님 PC** (절전·화면보호기 OFF)
- [ ] 크롬 탭·다른 AI 모델 전부 종료 (VRAM 확보)
- [ ] `nvidia-smi`로 VRAM 안정 확인 → **그다음** server.py(8001) → ngrok 순서
- [ ] ngrok 주소 모세종님께 전달 → 백엔드 `.env` 반영 확인
- [ ] **사전 녹화본 백업**: 터널이 죽어도 보여줄 발표 확정본 영상(음성+BGM 포함)을 별도 준비 (장민수 보유)

---

## 부록 — 장민수 PC 실측 구성 (소람 PC와 비교용)

| 항목 | 장민수 PC 값 | 소람 PC 주의 |
|------|--------------|--------------|
| conda env / python | `liveportrait` / 3.11.15 | 동일하게 |
| torch | 2.13.0.dev+cu132 (nightly) | **복사 금지** — 본인 GPU에 맞게 |
| LivePortrait repo | KwaiVGI/LivePortrait @9b294b3 | 동일 |
| 추가 의존 | fastapi 0.136.3, uvicorn, python-multipart 0.0.30 | 동일 |
| XPose ops | `.cp311-win_amd64.pyd` 빌드 완료 | **직접 빌드 필요** |
| ffmpeg | `C:\ffmpeg\bin` | 설치 + PATH |
| driving / multiplier | d3.mp4 / 0.5 | 동일 (발표 확정) |
