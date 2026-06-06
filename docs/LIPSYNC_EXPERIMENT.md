# 반려동물 립싱크 비교 실험

> **작성일**: 2026-06-05
> **담당**: 모세종(실험 설계·방법 2), 정환주(GPU 서버·방법 1·3·4)
> **배경**: PERSO 립싱크가 동물 얼굴에서 동작하지 않음을 확인 후, 대안 4가지를 비교 실험

---

## 실험 조건

| 항목 | 값 |
|------|-----|
| 입력 영상 | `perso_result_364462.mp4` (LivePortrait 결과, 말티즈 정면) |
| 입력 사진 | `KakaoTalk_20260601_152327.jpg` (말티즈 정면) |
| 입력 음성 | `test_tts.mp3` (Google TTS 한국어) |
| 평가 기준 | 입 움직임 여부 / 음성 동기화 / 자연스러움(1~5) / 처리시간 |

---

## 베이스라인 (기존 결과)

| 방법 | 입 움직임 | 음성 동기화 | 비고 |
|------|----------|------------|------|
| PERSO 립싱크 (원본 영상) | ❌ | ✅ | 동물 얼굴 감지 실패 |
| 정적 사진 → PERSO | ❌ | ✅ | 입 자체가 없음 |

---

## 방법 1 — Wav2Lip

**한 줄 요약**: 오픈소스 face-agnostic 립싱크 모델로 동물 얼굴에 직접 음성 동기화 적용.

### 원리

Wav2Lip(Rudrabha/Wav2Lip)은 영상 속 얼굴 영역을 자동 감지한 뒤, 오디오 파형에 맞춰 입 모양을 생성·합성하는 face-agnostic 방식이다.
사람 얼굴에 최적화되어 있으나 동물처럼 얼굴 구조가 다른 경우에도 얼굴 감지 단계가 통과되면 입 영역에 결과를 합성한다.
GAN 기반 discriminator가 실제 립싱크 영상과 생성 결과의 차이를 줄여 자연스러운 입 움직임을 만들어낸다.

### 실행 (GPU 서버 — 정환주)

```bash
# 1) 레포 클론 및 의존성 설치
git clone https://github.com/Rudrabha/Wav2Lip
cd Wav2Lip
pip install -r requirements.txt

# 2) 가중치 다운로드 → checkpoints/wav2lip_gan.pth
mkdir -p checkpoints
# https://github.com/Rudrabha/Wav2Lip#getting-the-weights 에서 수동 다운로드

# 3) 립싱크 실행
python inference.py \
  --checkpoint_path checkpoints/wav2lip_gan.pth \
  --face ../perso_result_364462.mp4 \
  --audio ../test_tts.mp3 \
  --outfile ../outputs/method1_wav2lip.mp4
```

> 동물 얼굴 감지 실패 시 `--nosmooth` 옵션 추가 후 재시도.

### 장단점

| 구분 | 내용 |
|------|------|
| 장점 | face-agnostic 방식으로 동물 얼굴에도 시도 가능 |
| 장점 | 오픈소스, 추가 API 비용 없음 |
| 장점 | GPU 가속 시 처리 속도 빠름 |
| 단점 | 동물 얼굴 감지 실패 시 결과물 품질 저하 |
| 단점 | 털 있는 동물 특성상 입 주변 아티팩트 발생 가능 |
| 단점 | 사전 학습이 사람 중심이라 자연스러움 보장 불가 |

### 결과

**결과 파일**: `outputs/method1_wav2lip.mp4` · **상태**: ⬜ 미실행

| 항목 | 결과 |
|------|------|
| 입 움직임 | |
| 음성 동기화 | |
| 자연스러움 (1~5) | |
| 처리시간 | |
| 비고 | |

---

## 방법 2 — 얼굴 크롭 전처리 + PERSO 재시도

**한 줄 요약**: 강아지 얼굴을 ffmpeg으로 크롭·확대해 화면을 꽉 채운 뒤 PERSO 립싱크 재시도.

### 원리

PERSO는 사람 얼굴 전용 감지 모델을 내부에서 사용하기 때문에 원본 영상에서 강아지 얼굴이 차지하는 비율이 작으면 얼굴 감지에서 실패한다.
ffmpeg의 crop 필터로 강아지 얼굴 영역만 정사각형으로 잘라낸 뒤 512×512로 확대하면 화면을 꽉 채운 얼굴 이미지가 만들어져 PERSO의 얼굴 감지 통과 확률이 높아진다.
크롭된 영상을 PERSO 2단계(번역 → 립싱크)에 입력한다.

### 실행 (모세종)

```bash
# 1) ffmpeg 얼굴 크롭 및 리사이즈
ffmpeg -i perso_result_364462.mp4 \
  -vf "crop=ih:ih:(iw-ih)/2:0,scale=512:512" \
  -y outputs/method2_cropped.mp4

# 2) PERSO 립싱크 실행
python test_perso.py outputs/method2_cropped.mp4
```

> 얼굴 위치에 따라 크롭 좌표(x, y) 수동 조정 가능: `crop=ih:ih:x:y`

### 장단점

| 구분 | 내용 |
|------|------|
| 장점 | 기존 PERSO 인프라 재활용, 추가 설치 불필요 |
| 장점 | ffmpeg 전처리만으로 얼굴 감지 통과 가능성 향상 |
| 장점 | 클라우드 API 기반, 빠른 처리 |
| 단점 | PERSO가 사람 얼굴 전용이라 감지 여전히 불안정 |
| 단점 | 크롭 좌표를 영상마다 조정해야 할 수 있음 |
| 단점 | 업스케일로 인한 화질 저하 가능 |

### 결과

**결과 파일**: `outputs/result_lipsync_1780645871.mp4` · **상태**: ✅ 실행 완료

| 항목 | 결과 |
|------|------|
| 입 움직임 | ❌ 없음 |
| 음성 동기화 | 음성 교체만 됨 (ElevenLabs V3) |
| 자연스러움 (1~5) | 1 |
| 처리시간 | 약 3분 |
| 비고 | PERSO가 동물 얼굴을 사람으로 인식하지 못함. 크롭 전처리로도 해결 불가. PERSO 립싱크는 동물에서 구조적으로 작동 안 함. |

---

## 방법 3 — LivePortrait driving_multiplier 강화

**한 줄 요약**: 입 움직임 배율을 0.4 → 0.8로 높여 "말하는 것처럼 보이는" 과장된 뻐끔거림 유도.

### 원리

LivePortrait는 구동 영상(driving video)의 움직임을 소스 이미지에 전달할 때 `driving_multiplier` 값을 곱해 변형 강도를 조절한다.
기본값 0.4는 자연스러운 표정 복사에 최적화되어 있지만, 동물 얼굴처럼 움직임이 약하게 반영되는 경우 배율을 높이면 입 개폐 폭이 커져 "말하는 동물"처럼 보이는 효과를 얻을 수 있다.
완전한 음성-입술 동기화는 아니지만, 추모 영상 맥락에서 "살아 움직이는 느낌"을 주는 데 충분할 수 있다.

### 실행 (GPU 서버 — 정환주)

```bash
# GPU 서버에서 환경변수 변경 후 재시작
export LIVEPORTRAIT_DRIVING_MULTIPLIER=0.8
uvicorn server:app --host 0.0.0.0 --port 8001
```

```python
# 로컬에서 테스트 요청
import requests, os
from dotenv import load_dotenv
load_dotenv()

with open("KakaoTalk_20260601_152327.jpg", "rb") as f:
    resp = requests.post(
        f"{os.getenv('LIVEPORTRAIT_REMOTE_URL')}/generate",
        files={"source": f}, timeout=300
    )
with open("outputs/method3_high_multiplier.mp4", "wb") as out:
    out.write(resp.content)
```

### 장단점

| 구분 | 내용 |
|------|------|
| 장점 | 추가 모델 설치 없이 env 변경만으로 적용 |
| 장점 | 동물 얼굴에서도 별도 얼굴 감지 없이 작동 |
| 장점 | 처리 속도 빠름 |
| 단점 | TTS 음성과의 실제 립싱크 없음 |
| 단점 | 배율 너무 높이면 얼굴 변형이 부자연스러울 수 있음 |
| 단점 | driving 영상 패턴에 의존 |

### 실제 테스트 조건 (2026-06-06, 모세종 — Google Colab T4)

> ⚠️ 문서에 기록된 실행 방법(GPU 서버 env 변경)과 다르게, Colab에서 직접 inference_animals.py를 실행함.

| 항목 | 값 |
|------|-----|
| 소스 이미지 | `KakaoTalk_20260601_152327.jpg` (말티즈 정면) |
| 드라이빙 영상 | `060_TomCarper_calm_3clips.mp4` (CREMA-D calm 태그, 발화 영상) |
| driving_multiplier | 0.4 (기본값) |
| 옵션 | `--no_flag_stitching` |
| 실행 환경 | Google Colab T4 GPU |
| 출력 | concat 영상 (좌: 드라이빙 / 중: 원본 / 우: 합성 결과) |

```bash
# Colab에서 실행 순서
!git clone https://github.com/KwaiVGI/LivePortrait
%cd /content/LivePortrait
!pip install -r requirements.txt -q
# XPose CUDA 커스텀 ops 빌드 (필수)
%cd /content/LivePortrait/src/utils/dependencies/XPose/models/UniPose/ops
!python setup.py build install
%cd /content/LivePortrait
# 가중치 다운로드 (동물 모델만)
# hf_hub_download("KwaiVGI/LivePortrait", ...) 로 liveportrait_animals/ 만 받음
!python inference_animals.py \
  -s /content/KakaoTalk_20260601_152327.jpg \
  -d /content/060_TomCarper_calm_3clips.mp4 \
  -o /content/outputs/ \
  --no_flag_stitching \
  --driving_multiplier 0.4
```

### 결과

**결과 파일**: `KakaoTalk_20260601_152327--060_TomCarper_calm_3clips_concat.mp4` · **상태**: ✅ 실행 완료

| 항목 | 결과 |
|------|------|
| 입 움직임 | ✅ 있음 (사람 움직임의 32% 수준, 동기화 상관계수 0.84) |
| 음성 동기화 | ❌ 없음 (TTS 미결합 — 드라이빙 영상 기반 움직임만) |
| 자연스러움 (1~5) | 4 |
| 처리시간 | 약 1분 20초 (Colab T4) |
| 비고 | calm 태그 드라이빙 영상이 추모 맥락에 적합. 코 영역 미세 변형 아티팩트 있으나 추모 영상 수준에서 허용 가능. 후반 클립 전환 구간(8.8~9.7초) 블러 발생 — 단일 클립 드라이빙 영상으로 개선 가능. |

#### 상세 분석 (Claude web Sonnet 4.6)
- **입 동기화**: 상관계수 0.84, lag=0 (실시간 동기화)
- **움직임 강도**: 사람 대비 32% (코/입 영역 avg diff 22.8 vs 눈 위쪽 8.2)
- **아티팩트**: 코가 같이 당겨지는 변형, 후반 frame 228 diff 36.2 (블러)
- **추모 맥락 적합도**: 과장 없는 절제된 움직임, 차분한 시선 고정 — 의도에 부합

---

## 방법 4 — SadTalker

**한 줄 요약**: 사진 1장 + 오디오 → 오디오 기반 자연스러운 얼굴 애니메이션 생성.

### 원리

SadTalker(OpenTalker/SadTalker)는 얼굴 사진 1장과 오디오를 입력받아 3D 머리 포즈 + 표정 파라미터를 예측한 뒤 얼굴 애니메이션을 생성한다.
내부적으로 Audio2Exp(오디오 → 표정 계수)와 Audio2Pose(오디오 → 머리 움직임) 네트워크를 분리해 구동하기 때문에, Wav2Lip 대비 눈·볼·고개 움직임까지 자연스럽게 표현된다.
`--still` 옵션 사용 시 큰 머리 움직임 없이 입 위주의 잔잔한 애니메이션만 생성하므로 추모 영상의 차분한 분위기에 적합하다.

### 실행 (GPU 서버 — 정환주)

```bash
# 1) 설치
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker
pip install -r requirements.txt
bash scripts/download_models.sh   # 가중치 자동 다운로드

# 2) 추론
python inference.py \
  --driven_audio test_tts.mp3 \
  --source_image KakaoTalk_20260601_152327.jpg \
  --result_dir outputs/ \
  --still \
  --preprocess full
```

| 옵션 | 설명 |
|------|------|
| `--still` | 큰 머리 움직임 없이 입 위주 애니메이션 |
| `--preprocess full` | 얼굴 전체 처리, crop 없이 전체 얼굴 보존 |

### 장단점

| 구분 | 내용 |
|------|------|
| 장점 | 오디오 기반 표정 생성 — Wav2Lip보다 풍부한 표정 변화 |
| 장점 | `--still` 옵션으로 추모 영상 분위기에 맞는 차분한 움직임 조절 |
| 장점 | 사진 1장만으로 생성 가능 |
| 단점 | GPU 서버에 별도 설치 및 가중치 다운로드 필요 |
| 단점 | 동물 얼굴 공식 지원 없음 — 감지 실패 가능성 있음 |
| 단점 | 처리 시간이 상대적으로 길 수 있음 |

### 결과

**결과 파일**: `outputs/method4_sadtalker.mp4` · **상태**: ⬜ 미실행

| 항목 | 결과 |
|------|------|
| 입 움직임 | |
| 음성 동기화 | |
| 자연스러움 (1~5) | |
| 처리시간 | |
| 비고 | |

---

## 전체 비교 요약

| 항목 | 방법 1 Wav2Lip | 방법 2 크롭+PERSO | 방법 3 LivePortrait↑ | 방법 4 SadTalker |
|------|:---:|:---:|:---:|:---:|
| 동물 얼굴 지원 | △ face-agnostic | △ 크롭으로 보완 | ✅ 직접 지원 | △ 미지원(테스트 필요) |
| 음성 동기화 | ✅ | ✅ | ❌ 배율 기반 | ✅ |
| 설치 난이도 | 높음 | 낮음 | 최저 (env만) | 높음 |
| 추가 비용 | 없음 | PERSO API | 없음 | 없음 |
| 처리 속도 | 빠름 | 빠름 | 빠름 | 보통 |
| 자연스러움 | 중간 | 미지 | 4/5 | 높음 |
| 실행 위치 | GPU 서버 | 로컬+PERSO | GPU 서버 | GPU 서버 |
| 상태 | ⬜ | ✅ | ✅ | ⬜ |

---

## 결론 (2026-06-06)

### 채택: 방법 3 — LivePortrait driving_multiplier 0.4 + calm 드라이빙 영상

| 항목 | 결과 |
|------|------|
| PERSO 립싱크 (방법 2) | ❌ 드랍 — 동물 얼굴 감지 구조적 불가 |
| LivePortrait (방법 3) | ✅ 채택 — 입 동기화 0.84, 자연스러움 4/5 |
| Wav2Lip (방법 1) | ⬜ 미실행 — 방법 3 채택으로 불필요 |
| SadTalker (방법 4) | ⬜ 미실행 — 방법 3 채택으로 불필요 |

**채택 이유:**
- PERSO는 동물 얼굴에 구조적으로 작동 안 함 (크롭 전처리로도 해결 불가)
- LivePortrait는 동물 전용 모드(`inference_animals.py`) 제공, 별도 얼굴 감지 불필요
- calm 태그 드라이빙 영상 + multiplier 0.4 조합이 추모 영상 맥락에 적합 (과장 없는 절제된 움직임)
- 입 동기화 상관계수 0.84, 처리시간 약 1분 20초 (Colab T4 기준)

**남은 이슈:**
- 코 영역 미세 변형 아티팩트 — LivePortrait 구조적 한계, 허용 수준
- 후반 클립 전환 블러 (8.8~9.7초) — 단일 클립 드라이빙 영상으로 개선 가능

**다음 단계:**
- ElevenLabs TTS + LivePortrait 영상 합치기 → 발표 데모 완성
- 정환주: GPU 서버에서 동일 조건(TomCarper calm, multiplier 0.4) 실행 → 서비스 파이프라인 연결

---

## 부록 A — driving 영상 비교 + 소스 사진 가이드 (2026-06-06, 장민수)

> **배경:** 모세종님이 발화(말하는) driving 영상 7개 제공(`ai/liveportrait/driving/`).
> 어느 driving이 "말하는 동물" 효과에 최적인지, 그리고 소스 사진 조건이 결과에 어떤 영향을 주는지 로컬(RTX, conda `liveportrait`)에서 전수 비교.
> 모든 생성: `inference_animals.py --no_flag_stitching --driving_multiplier 0.4`.

### 측정 방법 (객관 지표)
- 결과 영상의 **입 영역(얼굴 하단 중앙: 세로 55~85%, 가로 30~70%)** 프레임 간 픽셀 절대차 평균 = **입 움직임 강도**
- `max(프레임차) / 평균(프레임차)` = **스파이크/평균** → 클립 전환 블러 정도(낮을수록 매끄러움)
- ⚠️ 한계: 픽셀차는 "입 여닫음"과 "머리 움직임"을 구분 못 함 → **눈 확인 병행 필수** (아래 결론은 지표+육안 합산)

### 실험 1 — driving 영상 비교

**소스 A: 말티즈(입 벌린 사진)** — calm 발화 4종
| driving | 입 움직임 | 스파이크/평균 |
|------|:---:|:---:|
| 015_JohnSarbanes0 | 3.46 | 4.6 |
| **027_EdMarkey0** | **5.21** | **3.0** |
| 052_JohnYarmuth | 3.63 | 3.9 |
| 060_TomCarper(기준선) | 3.76 | 3.4 |

**소스 B: 고양이 s39(입 다문 사진)** — calm 4 + LP 기본 3
| driving | 입 움직임 | 스파이크/평균 | 종류 |
|------|:---:|:---:|------|
| 015_JohnSarbanes0 | 1.32 | 4.5 | calm 발화 |
| 027_EdMarkey0 | 2.03 | 3.5 | calm 발화 |
| 052_JohnYarmuth | 1.52 | 3.8 | calm 발화 |
| 060_TomCarper | 1.68 | 3.8 | calm 발화 |
| **d11** | **5.67** | **1.7** | LP 기본(단일 클립) |
| d13 | 0.67 | 6.5 | LP 기본(세로영상·저모션) |
| d20 | 1.55 | 6.2 | LP 기본 |

### 핵심 발견

1. **소스 사진의 입 모양이 결정적 (driving보다 영향 큼)**
   - **입 벌린 사진**(말티즈) → 모델이 벌어진 입에서 **혀만 늘었다 줄임** → 픽셀차는 크지만 *말하는 티 X* (팀 육안 확인 일치)
   - **입 다문 사진**(고양이·토끼·햄스터) → 입을 **여닫음** → 픽셀차는 작아도 *말하는 느낌 O*
   - → **입 움직임 수치 ≠ 말하는 느낌.** 소스 사진 선택이 1순위. (PR #91 "이빨 발견"과 동일 원리)

2. **단일 클립 driving >> `_3clips` 이어붙임**
   - calm 4종은 전부 `_3clips`(3클립 concat) → 전환 구간 블러 → 스파이크/평균 3.4~4.6
   - **d11(단일 클립)** = 스파이크/평균 **1.7**로 압도적 매끄러움 + 입 움직임도 최고(5.67)
   - 본문 결론의 "후반 클립 전환 블러 → 단일 클립으로 개선 가능"을 **정량 확인**

3. **발화 클립 중 최적 = 027_EdMarkey0** (강아지·고양이 두 소스, 두 지표 모두 1등)

### 실험 2 — 다른 동물 일반화 (d11 driving)
| 동물 | 입 움직임 | 스파이크/평균 |
|------|:---:|:---:|
| 🐰 토끼 | 10.21 | 1.6 |
| 🐹 햄스터 | 5.46 | 1.8 |
| 🐱 고양이(참고) | 5.67 | 1.7 |

→ 입 다문 소스 + d11 조합이 **종 불문 자연스러운 발화 효과**. Day 4 "검출 성공" 단계 → "발화 생성 자연스러움"까지 확인. (팀 육안: "되게 자연스러워요")

### 결론·권장

| 항목 | 권장 |
|------|------|
| driving 영상 | **단일 클립** 우선(d11 수준). 발화 클립 쓰면 `_3clips`보다 **단일 클립화** 권장 |
| 발화 클립 최적 | 027_EdMarkey0 (calm·정면) |
| **소스 사진 가이드** | **① 입 다문 정면 ② 얼굴 또렷·정면 ③ 눈·코·입 가림 없음** — 입 벌린 사진은 혀만 늘어나 발화 효과 약함 |
| multiplier | 0.4 유지(추모 톤·과장 없음) |

### 향후 설계 (모세종님 방향 메모)
- **입 벌린 상태는 현재 수준으로 픽스**, 대신 **사진 입력 시 가이드 제시**(입 다문 정면 권장)로 품질 확보
- 데이터 축적 시: **사진/입 모양·종별로 최적 driving 영상을 DB에 두고 매칭**해서 인풋에 자동 주입 (종마다 최적 driving 다를 수 있음)
- 기록 사진 여러 장 중 **눈·코·입 잘 나온 컷 자동 선별** 후 생성

> 생성물 위치(로컬, gitignore): `output/_driving_compare/`(말티즈), `output/_driving_compare_cat/`(고양이 7종), `output/_driving_compare_animals/`(토끼·햄스터). concat 영상 = 좌:driving / 중:원본 / 우:결과.
