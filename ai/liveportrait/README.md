# LivePortrait 파이프라인

> 담당: 장민수 (멀티모달) · GPU 자원 협의: 정환주
> 역할: 반려동물 사진 1장 → 자연스럽게 움직이는 짧은 MP4 영상 생성 (가산점 기능)
> 관련: [ARCHITECTURE.md](../../docs/ARCHITECTURE.md) · [PROGRESS.md](../../docs/PROGRESS.md) · [GPU_SERVER.md](../GPU_SERVER.md)

---

## 0. 윤리 경계 (제일 먼저 — 절대 금지)

이 서비스는 펫로스 **회복**을 돕는 추모 서비스입니다. 영상도 그 경계를 지킵니다.

- ❌ 반려동물이 **말하거나 보호자에게 대화 거는** 영상 (가짜 대화 영상)
- ❌ 죽은 반려동물을 **"부활"한 것처럼** 보이게 하는 연출
- ✅ 마지막 모습을 **잔잔하게 움직이는 상징적 추모 영상** (눈 깜빡임·고개 미세 움직임 정도)
- ✅ 보호자가 기억을 돌아보게 돕는 **차분한 톤**
- ✅ PERSO 립싱크/더빙은 LivePortrait 기본 산출물이 아니라 **선택형 후처리·기술 검증** 단계로만 연결

> [README.md](../../README.md) 표 기준: "마지막 모습을 영상으로 보관" ✅ / "가짜 대화 영상" ❌.
> 기본 LivePortrait 산출물은 잔잔한 움직임을 유지합니다. 립싱크가 필요한 경우에도 "기억 기반 AI 재해석 추모 영상" 라벨과 사용자 선택을 전제로 하며, 반려동물 1인칭 대화처럼 만들지 않습니다.

---

## 1. 개요 & 파이프라인

```
[사진 업로드]
    │
    ▼
[전처리]  얼굴/머리 영역 크롭·정렬 (사람 모델은 동물에 약함 → §3 확인)
    │
    ▼
[LivePortrait]  source 이미지 + driving(모션) → 프레임 생성
    │ (local GPU  또는  Replicate)
    ▼
[MP4 인코딩]
    │
    ▼
(선택) [FFmpeg]  + TTS 음성 합성
    │
    ▼
[다운로드 URL 제공]
```

> ⚠️ **핵심 개념:** LivePortrait는 사진 1장만으로 움직임을 "상상"하지 않습니다.
> **source(움직일 사진)** + **driving(움직임을 가져올 영상/모션)** 두 입력이 필요합니다.
> 우리는 보호자 사진을 source로 쓰고, driving은 미리 준비한 **잔잔한 모션 템플릿**(가벼운 끄덕임·눈 깜빡임)을 씁니다. → §4

---

## 2. 실행 모드

`.env`의 `LIVEPORTRAIT_MODE` 값으로 전환합니다.

| 모드 | 값 | 설명 | 쓰는 곳 |
|------|----|------|---------|
| 로컬 GPU | `local` | 이 머신 GPU 로 직접 추론 | 개발 PC · **GPU 서버의 server.py** |
| 원격 GPU | `remote` | 터널된 GPU 서비스(server.py)에 HTTP 호출 | **NCP 백엔드** (GPU 없음) |
| Replicate API | `replicate` | 클라우드 GPU fallback. 호출당 비용 | 로컬·서버 모두 막혔을 때 |

```ini
# .env  (키는 .env 에만, .env.example 에는 빈 값)
LIVEPORTRAIT_MODE=local          # local | remote | replicate
LIVEPORTRAIT_REMOTE_URL=         # remote 모드: 터널된 GPU 서비스 주소
REPLICATE_API_TOKEN=             # replicate 모드일 때만
```

> 셋 다 같은 `generate_video()` 인터페이스 → **호출부 변경 없이 스위칭**. (구조 상세 §5)

> 같은 입출력 인터페이스로 두 모드를 **스위칭 가능**하게 짭니다(AI 파트 provider 추상화와 같은 원칙).
> 로컬이 막히면 즉시 Replicate로 시연을 이어갈 수 있어야 함.

---

## 3. ⚠️ 동물 얼굴 & 라이선스 (가장 중요한 검증 항목)

### 동물 모드 현황

**공식 animals 모드 존재 확인.** 강아지·고양이·판다 등 ~230K 프레임으로 파인튜닝, 2025년 추가 데이터로 업데이트.
기본 사람 모드를 동물에 그대로 쓰면 얼굴 랜드마크 검출 실패·왜곡 위험 → **animals 모드 전용 가중치 필수.**

실행 시 stitching 모듈이 동물용으로 훈련되지 않아 반드시 비활성화:
```bash
python inference.py -s pet.jpg -d driving.mp4 --no_flag_stitching --flag_is_animal
```

### 🚨 라이선스 주의

animals 모드는 **XPose** 모델에 의존 → **비상업적 사용(non-commercial)만 허용.**
InsightFace buffalo_l 모델도 동일 제약.

| 사용 목적 | 가능 여부 |
|-----------|----------|
| 교육용 데모·수업 발표 | 아마 가능 (학교 과제) |
| 상업 서비스·외부 배포 | ❌ 불가 |

> **→ 팀장(모세종)님께 라이선스 범위 확인 필요.** 발표용 데모 수준이면 무방하나, 외부 공개 서비스라면 대안 필요.
> 대안: 동물 전용 다른 오픈소스 애니메이션 모델 탐색, 또는 정적 사진 슬라이드쇼로 방향 전환.

- [ ] 모세종님께 라이선스 확인 요청
- [ ] 동물 모드(`--flag_is_animal`)로 샘플 변환 테스트 → 품질 [개발일지](../../docs/devlog/members/장민수.md)에 기록
- 품종·각도 편차 큼 → **정면·얼굴 또렷한 사진** 안내를 MediaPage 업로드 UI에 추가

> 결론: ____________ (테스트 후 기입 — 품질·권장 입력 조건)

---

## 4. driving(모션 템플릿) 준비

source 사진에 입힐 "움직임 원본"입니다. 윤리 경계(§0)에 맞춰 **과하지 않게**.

- [ ] 잔잔한 모션 템플릿 1~2개 준비 (가벼운 눈 깜빡임·고개 끄덕임, 3~5초)
- [ ] 기본 템플릿은 말하는 입 모양 큰 영상 사용 금지 (대화 영상처럼 보임)
- [ ] PERSO 후처리용 테스트 템플릿은 별도 보관하고, 사용자 선택·라벨·1인칭 금지 조건을 지킴
- 템플릿 영상도 대용량 → git 미포함, 서버/스토리지에 별도 보관

---

## 5. GPU 서버 세팅 + 원격 추론 서비스 (정환주 서버, RTX 5060)

> **목표:** GPU 서버에 LivePortrait 설치 → `server.py`(추론 HTTP 서비스) 실행 →
> 터널 노출 → NCP 백엔드가 `remote` 모드로 호출. (구조: §2 / PR #95)
> 아래는 **Linux 기준**. Windows면 §10의 재현 명령·트러블슈팅을 그대로 쓰세요.

**VRAM (업데이트):** LLM이 **Gemini(클라우드)로 이전**돼 GPU 서버가 비었습니다.
→ 예전 "LLM과 동시 상주 불가" 제약 **해소**. LivePortrait가 GPU 전용 사용 가능.

### 5.1 LivePortrait 설치
```bash
# 1) 클론 (레포 밖, 서버 적당한 위치)
git clone https://github.com/KwaiVGI/LivePortrait && cd LivePortrait

# 2) conda 환경 (Python 3.10~3.11)
conda create -n liveportrait python=3.11 -y && conda activate liveportrait

# 3) PyTorch(서버 CUDA 버전에 맞게) + 의존성
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt

# 4) 사전학습 가중치 (humans + animals) — git 미포함
huggingface-cli download KwaiVGI/LivePortrait --local-dir pretrained_weights --exclude "*.git*"
```

### 5.2 Animals 모드 — XPose 컴파일 (필수)
동물 모드는 X-Pose CUDA 확장 컴파일이 필요합니다.
```bash
cd src/utils/dependencies/XPose/models/UniPose/ops
python setup.py build_ext --inplace
pip install -e . --no-build-isolation
cd -   # 원위치
```
> Windows는 MSVC·인코딩 이슈로 §10 명령을 그대로 사용. Linux는 보통 위로 끝남.

동작 확인:
```bash
python inference_animals.py -s assets/examples/source/s39.jpg \
  -d assets/examples/driving/d0.mp4 --no_flag_stitching
# → animations/s39--d0.mp4 생성되면 설치 OK
```

### 5.3 추론 서비스(server.py) 실행 + 터널
```bash
# Rainbow-Bridge 레포의 ai/liveportrait 위치 (server.py 있는 곳)
pip install fastapi uvicorn python-multipart
cd <Rainbow-Bridge>/ai/liveportrait
uvicorn server:app --host 0.0.0.0 --port 8001

# 다른 터미널: 터널 노출 (예시 — ngrok)
ngrok http 8001        # 발급된 https URL 을 백엔드에 전달
```
헬스 체크: `curl http://localhost:8001/health` → `{"status":"ok",...}`

### 5.4 환경변수
```bash
# GPU 서버 (server.py 가 실제 GPU 추론 = local 모드):
LIVEPORTRAIT_MODE=local                    # 기본값
LIVEPORTRAIT_HOME=/path/to/LivePortrait    # 5.1에서 클론한 경로
LIVEPORTRAIT_DRIVING=/path/to/driving.mp4  # 추모용 driving(§4), 없으면 예제 d0
LIVEPORTRAIT_DRIVING_MULTIPLIER=0.4

# NCP 백엔드 (모세종님) — 원격 GPU 호출:
LIVEPORTRAIT_MODE=remote
LIVEPORTRAIT_REMOTE_URL=https://<터널주소>  # 5.3의 ngrok URL
```
→ 백엔드 `run_liveportrait` 가 자동으로 원격 호출 (**호출부 코드 변경 불필요** — `generate_video` 시그니처 동일).

**필요 사항:** CUDA · LivePortrait 가중치(animals 포함) · XPose 컴파일 · fastapi/uvicorn/python-multipart
(FFmpeg 합치기·PERSO는 백엔드에서 처리 → GPU 서버엔 불필요)

---

## 6. Replicate Fallback (개발 우선 경로)

로컬 GPU가 없거나 꺼져 있어도 개발을 진행할 수 있는 클라우드 경로입니다.

**확인된 모델 슬러그:** `fofr/live-portrait` ([replicate.com/fofr/live-portrait](https://replicate.com/fofr/live-portrait))
**평균 처리 시간:** ~47초 / 호출 (Nvidia L40S GPU)

```python
# pip install replicate
import replicate

output = replicate.run(
    "fofr/live-portrait",           # 슬러그 확인 완료
    input={
        "image": open("pet.jpg", "rb"),       # source 사진
        "video": open("driving.mp4", "rb"),   # driving 영상
        # 파라미터 목록은 replicate.com/fofr/live-portrait/api 참고
        # animals 모드 파라미터 존재 여부 직접 확인 필요
    },
)
# output: 생성된 영상 URL
```

- [ ] Replicate 계정 + 토큰 발급
- [ ] `replicate.com/fofr/live-portrait/api` 에서 animals 관련 파라미터 확인
- [ ] 호출당 비용 확인 + 처리 시간 실측 기록 (가이드북 §6.4 호출 로그 의무)
- 비용 절약: 반복 디버깅은 짧은 영상·저해상도, 시연만 고품질

---

## 7. 백엔드 연동 API (계약 — 스키마 확정 전 초안)

> 입출력 스키마는 백엔드(모세종)·프론트와 **결정 C 합의** 후 고정. 아래는 제안.

| 항목 | 내용 |
|------|------|
| 업로드 | `POST /api/v1/media/upload` — `multipart/form-data` (file, `pet_id`) |
| 즉시 응답 | `{ "asset_id": "...", "status": "processing" }` (영상 생성은 수 초~수십 초) |
| 상태 조회 | `GET /api/v1/media/{asset_id}` → `{ "status": "done", "video_url": "..." }` |
| 데이터 모델 | `MediaAsset { _id, pet_id, kind: "video", url, status, created_at }` |
| 담당 (업로드/상태 API) | 모세종 |
| 담당 (다운로드 제공) | 김윤한 |
| 담당 (파이프라인·프론트) | 장민수 |

> 영상 생성이 느려서 **동기 응답이면 타임아웃** 위험 → `processing` → 폴링/완료 통지 구조 권장.
> 이 비동기 처리 방식을 모세종님과 먼저 합의해야 함.

---

## 8. FFmpeg 합성 (선택 — TTS 음성 입히기)

```bash
# 설치: https://ffmpeg.org  (서버에 직접 설치, git 미포함)
ffmpeg -i input_video.mp4 -i tts_audio.wav \
  -c:v copy -c:a aac -shortest output.mp4
```

- `-shortest`: 영상/음성 중 짧은 쪽에 맞춰 종료
- TTS는 ④ 정환주 담당 → 음성 포맷(wav/mp3)·길이 합의 필요
- 음성 입히더라도 §0 경계 유지: **낭독 톤의 위로 음성**이지 반려동물 목소리 흉내 ❌

---

## 9. 파일·보안 주의

- 모델 가중치(`.pth`·`.safetensors`·`.ckpt`) **git 커밋 절대 금지** (`.gitignore` 처리됨)
- 생성 영상(`.mp4`)·driving 템플릿·TTS 음성 **git 커밋 금지**
- 개인 반려동물 사진은 서버 `uploads/` 에만, 외부 노출 최소화 (ARCHITECTURE §8)
- Replicate 업로드 = 외부 서비스로 사진 전송 → 개인정보. 시연/테스트용 샘플 위주로 사용, 실사용자 사진 업로드는 정책 합의 후

---

## 10. 로컬 환경 세팅 기록 (2026-06-02)

> 장민수 로컬: RTX 3060 (12GB VRAM) · CUDA Toolkit 13.2 · Python 3.11 (conda: liveportrait)
> 클론 위치: `c:\JMS\2_project\LivePortrait\` (Rainbow-Bridge 레포 밖)

### 최종 설치 완료 상태

| 항목 | 결과 |
|------|------|
| conda 환경 생성 (Python 3.11) | ✅ |
| requirements.txt 설치 | ✅ |
| PyTorch 2.13.0.dev nightly + CUDA 13.2 | ✅ (공식 stable에 cu132 없어서 nightly 사용) |
| onnxruntime → CPU 버전으로 교체 | ✅ (cuDNN 없어도 동작) |
| Visual C++ Build Tools 설치 | ✅ |
| ninja 설치 | ✅ |
| XPose CUDA 확장 컴파일 | ✅ (`MultiScaleDeformableAttention.cp311-win_amd64.pyd`) |
| 사전학습 가중치 다운로드 (humans + animals) | ✅ |
| **Humans 모드** 파이프라인 | ✅ `animations/s0--d0.mp4` 생성 |
| **Animals 모드** (고양이 s39.jpg) | ✅ `animations/s39--d0.mp4` + `.gif` 생성 |

### 해결한 장벽 (재현 시 참고)

| 장벽 | 해결 방법 |
|------|-----------|
| PyTorch CUDA 버전 불일치 (기본 cu124 vs 시스템 13.2) | `pip install --force-reinstall torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu132` |
| onnxruntime-gpu cuDNN DLL 에러 | `pip uninstall onnxruntime-gpu && pip install onnxruntime` |
| Visual C++ Build Tools 없음 | [visualstudio.microsoft.com/visual-cpp-build-tools](https://visualstudio.microsoft.com/visual-cpp-build-tools) 수동 설치 |
| PyTorch cpp_extension OEM 인코딩 에러 | `cpp_extension.py` 47번 줄 `('oem',)` → `('utf-8', 'ignore')` 패치 |
| CUDA 전처리기 에러 (C1189) | `setup.py` cxx에 `/Zc:preprocessor` 추가, nvcc에 `-DCCCL_IGNORE_MSVC_TRADITIONAL_PREPROCESSOR_WARNING -Xcompiler /Zc:preprocessor` 추가 |
| ninja 없음 | `pip install ninja` |
| MultiScaleDeformableAttention 모듈 미인식 | `pip install -e . --no-build-isolation` (ops 폴더에서) |

### XPose 컴파일 전체 명령 (Windows 재현용)

```powershell
# 1. MSVC 환경 로드 후 컴파일
$vsPath = "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvars64.bat"
$opsDir = "C:\JMS\2_project\LivePortrait\src\utils\dependencies\XPose\models\UniPose\ops"
cmd /c "chcp 65001 && `"$vsPath`" && set DISTUTILS_USE_SDK=1 && cd /d `"$opsDir`" && conda run -n liveportrait python setup.py build_ext --inplace"

# 2. 사이트 패키지에 설치
cmd /c "chcp 65001 && `"$vsPath`" && set DISTUTILS_USE_SDK=1 && cd /d `"$opsDir`" && conda run -n liveportrait pip install -e . --no-build-isolation"
```

### animals 모드 실행

```bash
conda activate liveportrait
cd c:\JMS\2_project\LivePortrait
python inference_animals.py \
  -s assets/examples/source/s39.jpg \  # 고양이 사진
  -d assets/examples/driving/d0.mp4 \  # driving 영상
  --no_flag_stitching                  # animals 모드 필수 옵션
# 출력: animations/s39--d0.mp4 + .gif
```

---

## 11. 진행 상태

| 항목 | 담당 | 상태 |
|------|------|------|
| 로컬 환경 세팅 (conda + 가중치) | 장민수 | ✅ 2026-06-02 |
| XPose CUDA 확장 컴파일 | 장민수 | ✅ 2026-06-02 |
| Humans 모드 동작 확인 | 장민수 | ✅ 2026-06-02 |
| **Animals 모드 동작 확인 (고양이)** | 장민수 | ✅ 2026-06-02 |
| Replicate fallback 구현 | 장민수 | ⬜ |
| driving 모션 템플릿 준비 (§4) | 장민수 | ⬜ |
| 로컬 GPU 슬롯 협의 (정환주님) | 장민수·정환주 | ⬜ |
| 백엔드 upload/상태 API (비동기 합의) | 모세종 | ⬜ |
| FFmpeg 합성 스크립트 | 장민수 | ⬜ |
| 다운로드 제공 API | 김윤한 | ⬜ |
| MediaPage.jsx (업로드·결과 화면) | 장민수 | ⬜ |

### 다음 액션
1. **driving 모션 템플릿 다듬기** — 잔잔한 눈 깜빡임·끄덕임 템플릿 준비
2. **Replicate fallback 구현** — 로컬 GPU 꺼져 있을 때 대비
3. **백엔드 API 계약** — 모세종님과 upload 비동기 방식 합의

> 상태 변경 시 [PROGRESS.md](../../docs/PROGRESS.md) "멀티모달" 표도 같이 갱신.
