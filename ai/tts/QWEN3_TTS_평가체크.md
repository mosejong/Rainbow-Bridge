# Qwen3-TTS 평가 체크 — 발랄/귀여운/어린아이 한국어 목소리

> 작성: 정환주 · 2026-06-08 · TTS 엔진 후보 검토(팀 공유용).
> 배경: 라운드2 EL 9종은 차분·따뜻 위주 → 서비스에 **발랄/귀여운/어린아이** 톤이 필요.
> EL Voice Library엔 **한국어 어린아이 보이스가 0종**(영어권만) → 대안으로 Qwen3-TTS 검토.
> 상세 스파이크 기록은 [ENGINE_NOTES.md §6](ENGINE_NOTES.md) 참고.

---

## 0. 한 줄 결론

- **모델 정체·로컬 실행·VRAM·라이선스는 전부 확인 완료** — 로컬 무료·상업 가능·8GB GPU에 들어감.
- **한국어 "톤 품질"은 아직 합격 못 함** — 발랄/귀여운/어린아이/남자아이 생성은 되지만 사용자 청취 평가 "별로". 톤 매칭이 핵심 과제로 남음.
- **온라인 데모로 누구나 설치 없이 바로 확인 가능**(아래 5번).

---

## 1. 어떤 모델인가? (Qwen3? Qwen2.5-Omni? CosyVoice?)

- ✅ **Qwen3-TTS** 맞음. (Qwen2.5-Omni ❌, CosyVoice ❌ — 전부 다른 모델)
- 정확히 우리가 쓴 건 **`Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign`**.
- 제작: **Alibaba Cloud Qwen 팀**, 2026-01-22 오픈소스 공개.
- 라인업: `1.7B-{Base, CustomVoice, VoiceDesign}`, `0.6B-{Base, CustomVoice}` + 코덱 토크나이저.
  - **VoiceDesign** = 글(instruct)로 음색 설계 / **CustomVoice** = 프리셋 화자 / **Clone** = 3초 샘플 복제.
- 출처: [GitHub QwenLM/Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) · [HF 모델카드](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign)

## 2. 실제 한국어 샘플 들어봤나? — 자연스러운지

- ✅ 들어봄. 로컬에서 한국어로 직접 합성(같은 보호자 위로 멘트, 음색만 변경).
  - 1차: 발랄/귀여운/어린아이 (`_output/qwen3/qwen3_{balbal,cute,child}.wav`)
  - 2차: 남자아이 3종 (`_output/qwen3/qwen3_boy{,_bright,_soft}.wav`)
- ⚠️ **정직한 평가**: 사용자 청취 결과 **원하는 톤(발랄/귀여운/어린아이/남자아이) 매칭은 "별로"**.
  - 한국어 **발음/억양 자연스러움 자체**에 대한 정식 블라인드 평가는 **아직 안 함**(EL 라운드2 같은 A/B 필요).
  - 즉 "한국어 자연스러움 합격"이라고 **단정 못 함** — 추가 청취·비교가 남음.
- ⚠️ language 토큰은 **소문자 `korean`** 이어야 함(대문자는 silent fallback → 영어 억양 오염, 라운드1 함정).

## 3. 로컬 실행 가능한가? — VRAM (RTX 5060 8GB 기준)

- ✅ **로컬 실행 됨** (RTX 5060에서 실측). 환경: conda `qwen3-tts`(Python 3.12) + **torch cu128**(Blackwell sm_120).
- **VRAM peak ≈ 4.6GB** (1.7B, bfloat16) → **8GB에 여유 있음**. LLM과 동시 구동은 빡빡 → 온디맨드 로딩 권장.
- **속도: RTF ≈ 2.1** (flash-attn 미설치, manual PyTorch) = 14초 오디오에 ~30초.
  - 추모 영상은 **미리 생성**이라 무방. **실시간 스트리밍엔 부적합** → 필요 시 flash-attn 설치 또는 0.6B 경량판.
- ⚠️ Windows 주의: anaconda libiomp5 충돌 → `KMP_DUPLICATE_LIB_OK=TRUE` 필요. sox 경고는 무시 가능.

## 4. 라이선스 — 상업 서비스 가능한가?

- ✅ **apache-2.0** → **상업 서비스 가능**. (EL 유료 구독과 결정적 차이 — 로컬이라 추가 비용 0)
- 단 제작사 권고: 사기·딥페이크 등 악용 금지(일반 상식 수준).

## 5. 온라인으로 직접 들어보기 (설치 없이, 누구나)

- **공식 데모(메인)**: https://huggingface.co/spaces/Qwen/Qwen3-TTS
- **Voice Design 전용**: https://huggingface.co/spaces/Qwen/Qwen3-TTS-Voice-Design
- 사용법: 텍스트(한국어) 입력 → **Language를 Korean** 으로 → 목소리 설명(instruct, 영어 권장) 또는 참고음성 업로드(복제) → Generate.
- (참고) 로컬 한국어 UI도 만들어 둠: `ai/tts/qwen3_webui.py` (라벨 한국어 + 프리셋 버튼), `conda run -n qwen3-tts python ai/tts/qwen3_webui.py` → http://127.0.0.1:8000

## 6. 다른 무료 모델 비교 (1차 출처로 확인 — 추측 아님)

| 모델 | 한국어 | 톤 제어 | 상업 무료 | 근거 |
|------|:---:|------|:---:|------|
| **Qwen3-TTS** | ✅ | instruct 설계 + 복제 | ✅ apache-2.0 | 실측 |
| **CosyVoice2-0.5B** | ✅(9개국어) | instruct 감정 + 복제 | ✅ apache-2.0 | [HF](https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B) |
| **Chatterbox(Multilingual)** | ✅(23개국어) | 감정(exaggeration) + 복제 | ✅ MIT | [GitHub](https://github.com/resemble-ai/chatterbox) |
| **MeloTTS** | ✅ | ❌ 고정 화자·속도만 | ✅ MIT | [GitHub](https://github.com/myshell-ai/MeloTTS) |
| SparkTTS | ❌ 중·영만 | 복제+pitch/속도 | ✅ apache-2.0 | [GitHub](https://github.com/SparkAudio/Spark-TTS) |
| Kokoro | ❌ 없음 | ❌ 고정 | ✅ apache | [HF](https://huggingface.co/hexgrad/Kokoro-82M) |
| F5-TTS | ❌ | 복제 | ❌ **가중치 CC-BY-NC(상업금지)** | [GitHub](https://github.com/SWivid/F5-TTS) |
| IndexTTS-2 | ❌ 영어중심 | 감정 ◎ | ❌ 비상업 | 검색 |

- **한국어 + 톤제어 + 상업무료** 다 되는 건 **Qwen3 / CosyVoice2 / Chatterbox** 3개뿐.
- MeloTTS는 한국어 되지만 **목소리를 못 바꿔**(고정+속도만) 발랄/귀여운/어린아이엔 부적합.
- SparkTTS·Kokoro = 한국어 없음 / F5·IndexTTS = 상업 금지 → 서비스 탈락.
- ⚠️ CosyVoice2·Chatterbox는 **라이선스·한국어 지원만 확인**, **한국어 톤 품질은 미청취**(설치해 합성해봐야 앎).

## 7. 남은 검증 / 다음 할 일

1. **한국어 톤 품질 블라인드 A/B** — Qwen3 vs (CosyVoice2/Chatterbox) vs EL, 발랄/귀여운/어린아이 멘트로. EL 라운드2 방식.
2. **Voice Cloning 시도** — instruct(글 묘사)는 들쭉날쭉 → 원하는 목소리 클립 3~5초 복제가 더 정확. Qwen3·CosyVoice2·Chatterbox 다 지원.
3. 톤 확정 후에야 `tts.py` 본체 통합(백엔드 계약·톤매핑은 반소람 합의·`.env`).
