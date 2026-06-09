# 프로토타입 확정 보이스 (Qwen3-TTS VoiceDesign)

> 2026-06-09 · 정환주. 다이얼([qwen3_webui.py](qwen3_webui.py))에서 아래 값 그대로 넣으면 재현됩니다.
> ⚠️ **seed가 목소리의 핵심 ID** — seed 고정해야 같은 사람 목소리가 나옵니다(VoiceDesign은 seed마다 다른 화자).

---

## #1 — boy 차분·위로 (프로토타입 OK ✅)

- **원본 파일**: `ai/tts/_output/qwen3_emotion/qwen3em_dial_boy_older_w1_b0_normal_comfort_c1_normal_t0.7_s82363.wav`
- 사용자 다운로드본: `Downloads/audio (1).wav` (동일 오디오 — 파형 diff 0.00002 확인)

### 다이얼 재현 값

| 노브 | 값 |
|------|-----|
| 성별 | **boy** |
| 나이 | **older** (10세) |
| 다정함 | 1 |
| 밝기 | 0 |
| 피치 | normal |
| 감정 결 | **comfort** (위로) |
| 또렷함 | 1 |
| 쨍함 줄이기 | 0 (EQ 미사용) |
| 속도 | normal |
| 안정성 temp | 0.7 |
| **seed** | **82363** ← 고정 필수 |

> 같은 목소리 재현: seed **82363** 고정 + 위 슬라이더. 미세조정은 슬라이더만 바꾸되 seed는 유지.
> 다른 목소리 후보 찾기: seed만 굴리기("새 목소리" 버튼).

---

## #2 — girl 차분 (쨍함 EQ로 해결, 프로토타입 OK ✅)

- **원본 파일**: `ai/tts/_output/qwen3_emotion/qwen3em_dial_girl_older_w0_b0_low_calm_c0_normal_t0.5_s51412_eq9_4000.wav`
- 사용자 다운로드본: `Downloads/audio (4).wav` (동일 오디오 — 파형 diff 0.00002 확인)

### 다이얼 재현 값

| 노브 | 값 |
|------|-----|
| 성별 | **girl** |
| 나이 | **older** (10세) |
| 다정함 | 0 |
| 밝기 | 0 |
| 피치 | **low** |
| 감정 결 | **calm** (차분) |
| 또렷함 | 0 |
| **쨍함 줄이기** | **9** (fc 4000) ← girl 날카로움을 EQ로 해결한 핵심 |
| 속도 | normal |
| 안정성 temp | 0.5 |
| **seed** | **51412** ← 고정 필수 |

> girl은 합성만으론 쨍함이 안 빠져서(VoiceDesign 앵커 한계) **쨍함 줄이기 9 + 피치 low**로 잡음.
> 재현: seed **51412** 고정 + 위 슬라이더(쨍함 9 필수).

---

## #3 — boy 차분 (밝기 살짝, 프로토타입 OK ✅)

- **원본 파일**: `ai/tts/_output/qwen3_emotion/qwen3em_dial_boy_older_w1_b1_low_calm_c0_normal_t0.5_s29018_eq9_7000.wav`
- 사용자 다운로드본: `Downloads/audio (10).wav` (동일 오디오 — 파형 diff 0.00002 확인)

### 다이얼 재현 값

| 노브 | 값 |
|------|-----|
| 성별 | **boy** |
| 나이 | **older** (10세) |
| 다정함 | 1 |
| 밝기 | 1 |
| 피치 | **low** |
| 감정 결 | **calm** (차분) |
| 또렷함 | 0 |
| **쨍함 줄이기** | **9** |
| 쨍함 고역 fc(고급) | **7000** ← #2/#4(4000)와 다름, 좁게 깎음 |
| 속도 | normal |
| 안정성 temp | 0.5 |
| **seed** | **29018** ← 고정 필수 |

> #1과 다른 boy 화자(seed 29018). 밝기 1 + 쨍함 EQ는 fc 7000(좁게)로 살짝만 보정.

---

## #4 — girl 차분 (#2 다른 화자, 프로토타입 OK ✅)

- **원본 파일**: `ai/tts/_output/qwen3_emotion/qwen3em_dial_girl_older_w0_b0_low_calm_c0_normal_t0.5_s46286_eq9_4000.wav`
- 사용자 다운로드본: `Downloads/audio (6).wav` (동일 오디오 — 파형 diff 0.00002 확인)

### 다이얼 재현 값

| 노브 | 값 |
|------|-----|
| 성별 | **girl** |
| 나이 | **older** (10세) |
| 다정함 | 0 |
| 밝기 | 0 |
| 피치 | **low** |
| 감정 결 | **calm** (차분) |
| 또렷함 | 0 |
| **쨍함 줄이기** | **9** (fc 4000) |
| 속도 | normal |
| 안정성 temp | 0.5 |
| **seed** | **46286** ← 고정 필수 |

> #2(seed 51412)와 같은 레시피, **다른 화자**(seed 46286). 둘 중 청취 후 최종 1개 고르면 됨.
