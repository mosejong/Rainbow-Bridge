# TTS 모델 라이선스 + 튜닝(감정 입히기) 조사 — 통합 정리

> 작성: 정환주 · 2026-06-08 · 팀 공유용.
> 배경: 서비스에 **감정이 실린 진정성 있는 추모 목소리**가 필요.
> 그동안 다룬 TTS 엔진을 **라이선스 + "어떻게 감정을 입히나(튜닝)"** 관점으로 한 곳에 모음.
> 흩어진 원본: [ENGINE_NOTES.md](ENGINE_NOTES.md)(상세 스파이크) · [TTS_무료유료_비교.md](TTS_무료유료_비교.md)(라이선스 표) · [AZURE_TTS_조사.md](AZURE_TTS_조사.md) · [QWEN3_TTS_평가체크.md](QWEN3_TTS_평가체크.md).

---

## 0. 스코프 (이 문서가 다루는 "튜닝")

여기서 "감정 튜닝"은 **추론 시점 감정/톤 제어**가 핵심이라, 이 문서는 그걸 중심으로 다룹니다.
혼동 방지를 위해 "튜닝"을 두 층으로 나눕니다:

| 층 | 의미 | 비용·난이도 |
|----|------|------------|
| **A. 감정/톤 제어** (추론 시점) | 학습 없이 즉시 — prosody, 스타일태그, 자연어 묘사(instruct), 음성복제, **LLM 텍스트 리라이팅** | 낮음 (바로 가능) |
| **B. 파인튜닝** (가중치 학습) | 내 데이터로 모델을 재학습해 특정 목소리/말투 고정 | 높음 (데이터·GPU·시간) |

> 본문은 **A(감정 제어)** 를 주로 다루고, **B(파인튜닝)** 는 모델별 지원 여부만 보조 컬럼으로 표기합니다.
> "튜닝 = 가중치 파인튜닝"만 따로 깊게 보고 싶으면 그 방향으로 확장 가능합니다(범위 밖, 별도 요청).

---

## 1. 한 줄 결론

- **감정 입히는 방법은 5가지** (§2) — 그중 **"LLM으로 텍스트를 먼저 감정 있게 고쳐 쓰기"는 엔진과 무관**하게 어디든 얹을 수 있는 공통 레버.
- **상업까지 무료 + 감정 자연어 제어**가 되는 로컬 오픈모델: **Qwen3-TTS · VoxCPM2 · CosyVoice2 · Chatterbox**.
- **파인튜닝까지 공식 지원**하는 오픈모델: **Qwen3-TTS**(single-speaker), **CosyVoice2**, **Chatterbox**(LoRA). F5-TTS는 공식 미지원(커뮤니티만), VoxCPM2는 **확인 필요**.
- 라이선스 함정(무료처럼 보이나 상업 금지/유료): **F5-TTS·IndexTTS2**(비상업), **Edge TTS**(개인만), **MiniMax**(freemium), **EL·Google·Azure·Typecast·CLOVA**(유료/종량).

---

## 2. 감정을 입히는 5가지 방법 (튜닝 = 이것)

| # | 방법 | 어떻게 | 어느 엔진 | 학습 필요 |
|---|------|--------|----------|:---:|
| ① | **LLM 텍스트 리라이팅** | TTS 넣기 전에 LLM이 문장을 감정 있게 변형 + 호흡/쉼표/말줄임 삽입. "슬프게 읽어줘" 지시·히든워드(추모용 프롬프트)로 출력 톤 자체를 바꿈 | **모든 엔진 공통** (엔진 무관) | ❌ |
| ② | **prosody 조절** | 속도(rate)·음높이(pitch)·볼륨을 SSML/파라미터로 손조절 | Google·Azure·Polly | ❌ |
| ③ | **스타일/감정 태그** | `sad`·`cheerful` 등 미리 정의된 감정 스타일 선택 | Azure(한국어는 `sad` 1개), CosyVoice2(`[laughter]`·`<strong>`) | ❌ |
| ④ | **자연어 음색 설계 (instruct/voice design)** | "차분하고 따뜻한 어린아이 목소리" 같은 **글 묘사**로 음색·감정·운율을 통째로 설계 | Qwen3-TTS·VoxCPM2·CosyVoice2 | ❌ |
| ⑤ | **음성 복제 (reference)** | 원하는 톤의 3~10초 클립을 주면 그 목소리·말투를 복제. 감정 강도 슬라이더 동반(Chatterbox `exaggeration`, IndexTTS2 0~1) | Chatterbox·CosyVoice2·Qwen3·F5·IndexTTS2 | ❌ |
| — | **(B) 파인튜닝** | 내 데이터(wav+텍스트)로 재학습해 목소리 고정 | Qwen3·CosyVoice2·Chatterbox 등 | ✅ |

> **추모 서비스 핵심 조합**: ①(LLM 감정 리라이팅) + ④/⑤(목소리 설계·복제). ①은 어떤 엔진을 쓰든 먼저 얹을 수 있는 가장 싼 레버 → **엔진 결정과 별개로 ①부터 적용 가능.**

---

## 3. 모델별 통합표 — 라이선스 × 튜닝 × 우리 실험 결과

> 라이선스 셀은 [TTS_무료유료_비교.md](TTS_무료유료_비교.md)·[ENGINE_NOTES.md](ENGINE_NOTES.md) 검증분 재사용(재조사 아님).
> "우리 실험" = 이 레포에서 실제로 합성·청취·A/B 한 결과(다른 데 없는 우리 고유 데이터).

### 3-1. 직접 실험한 엔진 (이 레포에서 합성/청취함)

| 엔진 | 라이선스 / 상업 | 감정 튜닝 방법 (A) | 파인튜닝 (B) | 우리 실험 결과 |
|------|----------------|-------------------|:---:|----------------|
| **Google Cloud TTS** (현 폴백) | 상용 / 종량제(무료 100만자/월) | ② prosody(rate·pitch)만 | ❌(서비스형) | 현행 베이스라인. Gemini 자동평가 warm 5/5. **사람 A/B에서 EL에 9전 9패** → "기계음" 평 |
| **ElevenLabs** | 상용 / **무료=상업 ❌**(Starter $5/월~) | ③ 감정(다국어 v2)·⑤ 복제 | 일부(전문 보이스) | **라운드2 사람 블라인드 A/B 9전 9승**(한국어). 단 Free API는 한국어 네이티브 보이스 막힘 → 유료 전환 필요 |
| **Qwen3-TTS** (`1.7B-VoiceDesign`) | **apache-2.0 / 상업 무료** | ④ instruct 음색설계·⑤ 복제 | ✅ Base 시리즈 single-speaker(JSONL) | 로컬 GPU 작동(VRAM~4.6GB). **발랄/귀여운/어린아이 톤 매칭 "별로" 판정** |
| **VoxCPM2** | **apache-2.0 / 상업 무료** | ④ 괄호 안 영어 음색묘사(나이·성별) | ⚠️ **확인 필요**(공식 문서 미확인) | 로컬 작동, 어린이 차분 톤 6종 합성(`_output/voxcpm/`). 청취 평가 진행 단계 |
| **Typecast** | 상용 / **유료** | 성우 완성형 보이스 선택(감정 일부) | ❌ | 한국어 보이스 합성·청취(`_output/typecast/`). **유료라 무료 비교에선 제외** |
| **CLOVA Voice** | 상용 / **유료(Premium 기본료)** | 감정형 보이스 일부 | ❌ | 테스트했으나 **소스 삭제(pyc만 잔존)·유료라 제외** |

### 3-2. 조사만 한 엔진 (라이선스·방법 확인, 직접 합성은 안 함 또는 일부만)

| 엔진 | 라이선스 / 상업 | 감정 튜닝 방법 (A) | 파인튜닝 (B) | 메모 |
|------|----------------|-------------------|:---:|------|
| **Azure TTS** | 상용 / 종량제(무료 50만자/월) | ③ 스타일태그 — **한국어는 `InJoon(남) sad` 1개뿐** | ❌(서비스형) | 한국어 감정 이점 거의 없음. Neural HD 자연스러움이 잠재 강점. 미청취 |
| **CosyVoice2-0.5B** | **apache-2.0 / 상업 무료** | ③④⑤ — instruct 감정 + `[laughter]`·`<strong>` 마커 + 복제 | ✅ 지원(foundation 모델) | 9개국어·한국어. **한국어 톤 품질 미청취** |
| **Chatterbox (Multilingual)** | **MIT / 상업 무료** | ⑤ 복제 + `exaggeration`(0~1+ 감정강도)·`cfg_weight`(0~1 pacing) | ✅ LoRA(`lora.py`) | 23개국어. 감정강도 슬라이더가 명확. **한국어 톤 미청취** |
| **MeloTTS** | MIT / 상업 무료 | ❌ 고정 화자(속도만) | 제한적 | 한국어 되지만 목소리 못 바꿈 → 발랄/어린이 부적합 |
| **MiniMax** | freemium / **유료**(무료 5회) | ③ 어린이 보이스 실재(Shy Girl·Teen) | ❌ | "목표 품질" 기준점용. 상업 유료 |
| **Edge TTS** | wrapper GPLv3 / **개인만**(상업=Azure 구독) | ② pitch 흉내(어린이 전용 없음) | ❌ | 품질 감만 보기용. 상업 회색 |
| **Amazon Polly** | 상용 / 종량제 | 제한적(Neural Seoyeon) | ❌ | 감정/톤 약함. 후순위 |
| **SparkTTS** | apache-2.0 / 상업 무료 | 복제+pitch | 일부 | **한국어 없음(중·영)** → 서비스 탈락 |
| **Kokoro** | apache / 상업 무료 | ❌ 고정 | ❌ | **한국어 없음** → 탈락 |
| **F5-TTS** | **CC-BY-NC / 상업 금지** | ⑤ 복제 | ❌ 공식 미지원(예정), 커뮤니티 한국어 변종 존재 | 라이선스로 **서비스 채택 불가** |
| **IndexTTS2** | **비상업 / 상업 금지** | ⑤ 복제 + 감정강도(0~1), speaker/emotion 분리 ◎ | 다국어 확장은 파인튜닝 필요 | 감정제어 강력하나 **상업 금지** → 탈락 |

> ⚠️ CosyVoice2·Chatterbox·VoxCPM2의 **한국어 톤 실제 품질은 미청취** — 들어봐야 앎. F5·IndexTTS·MiniMax·EL·Google·Azure·Typecast·CLOVA·Edge는 라이선스/유료벽으로 상업 채택 제약.

---

## 4. 추모 서비스 적용 메모 (엔진 중립)

- **①(LLM 감정 리라이팅)부터** — 엔진을 뭘 고르든 먼저 적용 가능한 공통 레버. 메시지 텍스트를 "위로·추모 톤"으로 LLM이 다듬고 호흡/쉼을 넣은 뒤 TTS에 전달.
- **상업무료 + 감정 자연어 제어** 후보는 **Qwen3-TTS / VoxCPM2 / CosyVoice2 / Chatterbox** 4개. 이 안에서 한국어 톤 품질을 블라인드 A/B(EL 라운드2 방식)로 가려야 결론.
- **파인튜닝(B)** 까지 가면 우리 목표 목소리를 고정할 수 있음 — Qwen3(single-speaker)·CosyVoice2·Chatterbox(LoRA)가 후보. 단 데이터·GPU·시간 비용 큼 → 감정제어(A)로 충분한지 먼저 확인 후 결정.
- 윤리: 어떤 목소리든 **보호자 대상 위로 낭독**용. 반려동물 1인칭/부활 ❌. 사람 목소리 복제 시 권리·동의 필요(테스트는 OK). 위기(`1393`) 경계 유지.

---

## 5. 파인튜닝 보류 — 현재 환경 제약 (2026-06-08)

어린아이+감정 목소리를 **파인튜닝(가중치 학습)으로 고정**하는 방향을 검토했으나, 현재
환경에서는 **시작 자체가 불가**해 보류한다(근거 기록 — 자원 확보 시 재개).

| 벽 | 내용 | 출처 |
|----|------|------|
| **GPU** | 공식 파인튜닝 = full SFT(메모리절감 없음) → 1.7B **20GB+**, 0.6B **12GB+**. RTX 5060 **8GB로 불가** | [sft_12hz.py](https://github.com/QwenLM/Qwen3-TTS/blob/main/finetuning/sft_12hz.py) |
| **데이터** | 사람 녹음 음성 **30분+** 필요. 어린이(미성년) 음성 학습은 **법적·윤리 장벽**(개인정보·아동보호·동의). 보유 데이터 없음, 합성 wav 재사용 불가 | — |
| **LoRA 경량** | 8GB 가능성 있으나 **비공식·검증 부담** | — |

→ **우선 instruct(학습 0)로 어린아이+감정 합성 진행** (`qwen3_emotion.py`,
`_output/qwen3_emotion/`). 24GB+ GPU와 음성 데이터가 확보되면 LoRA/파인튜닝 재개 검토.

> 정리: 파인튜닝 = "*어떤 목소리?*"(화자 고정), 감정 = 추론 시점 제어 → **다른 축**.
> 감정 요구는 파인튜닝 없이 instruct로 우선 충족 가능.

---

## 6. 출처

- [TTS_무료유료_비교.md](TTS_무료유료_비교.md) · [ENGINE_NOTES.md](ENGINE_NOTES.md) · [AZURE_TTS_조사.md](AZURE_TTS_조사.md)(라이선스·가격 1차 출처 링크 다수 포함)
- CosyVoice2 감정/instruct·fine-tune — [arXiv 2412.10117](https://arxiv.org/html/2412.10117v1) · [HF FunAudioLLM/CosyVoice2-0.5B](https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B)
- Chatterbox exaggeration·cfg_weight·LoRA — [GitHub resemble-ai/chatterbox](https://github.com/resemble-ai/chatterbox) · [chatterbox-streaming(fine-tune)](https://github.com/davidbrowne17/chatterbox-streaming)
- Qwen3-TTS fine-tune(single-speaker)·voice design — [GitHub QwenLM/Qwen3-TTS finetuning](https://github.com/QwenLM/Qwen3-TTS/tree/main/finetuning)
- F5-TTS(공식 fine-tune 미지원·커뮤니티 한국어)·IndexTTS2(감정 0~1·비상업) — [arXiv 2506.21619](https://arxiv.org/pdf/2506.21619) · [F5-TTS fine-tune 가이드](https://instavar.com/blog/ai-production-stack/F5_TTS_Fine_Tuning_Voice_Cloning_Guide)
</content>
</invoke>
