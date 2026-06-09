# TTS 엔진 조사 — 통합 정본 (`ai/tts/`)

> 담당: 정환주 · TTS 엔진 선택 근거의 **단일 정본(SSOT)**.
> 2026-06-09 통합: 흩어져 있던 `TTS_무료유료_비교.md`·`AZURE_TTS_조사.md`·`QWEN3_TTS_평가체크.md`·`TTS_라이선스_튜닝_조사.md`를 **이 문서 하나로 합침**(원본 4개 삭제). 엔진 관련 문의는 여기만 보면 됩니다.
> 같이 보는 문서: 샘플 생성법 → [SAMPLE_생성_가이드.md](SAMPLE_생성_가이드.md) · 아바타 핸드오프 → [AVATAR_HANDOFF.md](AVATAR_HANDOFF.md) · 폴더 규칙 → [CLAUDE.md](CLAUDE.md).

---

## 0. PM 결정 요약 (세종님 — 여기만 봐도 결정됩니다) ⭐

**질문은 하나: 폴백 TTS 보이스를 `ElevenLabs`로 바꿀까, 현행 `Google`을 유지할까.**
품질은 EL이 결판났고, **남은 변수는 비용 하나**입니다.

### EL vs Google — 비용·품질 한 표 (2026 기준, 출처 §9)

| 항목 | **Google Cloud TTS (현행)** | **ElevenLabs** |
|------|------------------------------|----------------|
| **사람 블라인드 A/B 품질** | 기준(앵커). "기계음" 평 | **9전 9승** (한국어, §3) |
| **무료 한도** | Neural2 100만자/월, WaveNet 400만자/월 | **무료=상업 ❌** (개발/시연도 한국어 네이티브 보이스는 막힘) |
| **초과 단가** | Neural2 $16, WaveNet $4 (/100만자) | 플랜 정액: **Starter $5/월~, API Pro $99/월** |
| **상업 라이선스** | 가능 (데모 단계 사실상 0원) | **유료 플랜부터** |
| **연동 상태** | **이미 연동·실동작** (`ko-KR-Neural2-A`) | 미연동 (전환 시 키·플랜·코드 작업) |

### 결론은 두 부분 (한쪽만 보면 안 됨)
1. **품질 = EL 압승 (해결됨).** 사람 블라인드 A/B에서 EL 한국어 9종이 현행 Google warm을 **9/9**로 이김. "Google 기계음" 문제 EL이 실제 해소. → 이 질문은 끝.
2. **비용 = 미결정 (PM/팀 판단).** EL은 무료=상업 ❌ → 폴백 운영하려면 유료 플랜($5/월~). CLOVA를 비교에서 뺀 그 "유료 기본료" 벽이 EL에도 똑같이 적용. **"품질 우위 vs 월 구독"** 트레이드오프는 PM 결정 사안.

### 🔒 스코프 한정 (오해 금지)
이 비교 대상은 **폴백/standalone 한국어 TTS 보이스(`voiced_url` 경로)** 뿐입니다.
**주력 파이프라인인 PERSO 아바타 + 내장 TTS는 이 결과와 무관.** "EL 승"을 "오디오 스택 전체 교체"로 읽지 마세요.

### 추천
- **저비용 우선이면** → Google 유지(무료한도 큼·이미 연동). 품질은 ①LLM 감정 리라이팅(§4, 엔진무관 공통레버)으로 일부 보완.
- **품질 우선 + 월 구독 수용이면** → EL Starter로 전환, 폴백 보이스만 교체. 깔끔한 보이스: `bomisori·annie·esther·jason`.
- **상업 무료 + 발랄/어린아이 톤이 꼭 필요하면** → 로컬 오픈모델(Qwen3·VoxCPM2 등, §5) 별도 트랙. 단 한국어 톤 품질은 아직 미합격.

---

## 1. 현재 우리 셋업 (코드 근거)

- 엔진: **Google Cloud Text-to-Speech**
- 목소리(기본): `ko-KR-Neural2-A` ([tts.py](tts.py) `_VOICE_NAME`, `TTS_VOICE`로 변경 가능)
- 선택 가능 목소리: `female_a`(기본)·`female_b`·`male_c`·`female_wavenet` ([tts.py](tts.py) `_VOICES`)
- 톤: `warm`·`calm`·`hopeful`·`soft` (각 `speaking_rate`·`pitch` 매핑, [tts.py](tts.py) `_TONE_MAP`)
- 긴 글 분할: 문장 경계 기준 4500자 ([tts.py](tts.py) `_split_text`)
- 패키지: `google-cloud-texttospeech>=2.16` (`ai/requirements.txt`)

> 🔁 **2026-06-05 방향 전환:** 추모 낭독을 PERSO 단독 TTS로 교체하려 했으나 **PERSO 단독 TTS 없음**(팀 확정) → **PERSO AI Human 아바타 낭독 MP4를 주력, Google TTS는 안정성 폴백**으로 전환. 아바타·매핑 핸드오프 → [AVATAR_HANDOFF.md](AVATAR_HANDOFF.md).

> ⚠️ **`soft` 톤:** 프론트(`TtsPage.jsx`)가 `soft`를 보내는데 백엔드 톤셋엔 없어 조용히 `warm`으로 폴백되던 버그 → `soft`를 받게 추가해 해결. 다만 반소람 메시지 톤 ↔ TTS 톤은 **1:1 매핑 계약**이라 최종 톤셋은 반소람과 합의 필요.

---

## 2. 엔진 전체 비교표 (라이선스 × 비용 × 감정튜닝 × 우리 실험)

> "우리 실험" = 이 레포에서 실제로 합성·청취·A/B 한 결과(다른 데 없는 고유 데이터).
> "확인 필요" = 공식 수치 못 찾음 → **추정 안 함**, 공식 페이지 직접 확인.

### 2-1. 직접 실험한 엔진 (이 레포에서 합성/청취함)

| 엔진 | 라이선스 / 상업 | 비용 | 감정 튜닝 (A) | 파인튜닝 (B) | 우리 실험 결과 |
|------|----------------|------|---------------|:---:|----------------|
| **Google Cloud TTS** (현 폴백) | 상용 / 가능 | 무료 100만자/월, 초과 Neural2 $16·WaveNet $4 (/100만자) | ② prosody(rate·pitch)만 | ❌(서비스형) | 베이스라인. Gemini 자동평가 warm 5/5. **사람 A/B에서 EL에 9전 9패** → "기계음" 평 |
| **ElevenLabs** | 상용 / **무료=상업 ❌** | Starter $5/월~, API Pro $99/월 | ③ 감정(다국어 v2)·⑤ 복제 | 일부(전문 보이스) | **라운드2 사람 블라인드 A/B 9전 9승**(한국어, §3). 단 Free API는 한국어 네이티브 보이스 막힘 → 유료 전환 필요 |
| **Qwen3-TTS** (`1.7B-VoiceDesign`) | **apache-2.0 / 상업 무료** | 로컬 0 (API는 Alibaba 별도) | ④ instruct 음색설계·⑤ 복제 | ✅ Base single-speaker(JSONL) | 로컬 GPU 작동(VRAM~4.6GB). **발랄/귀여운/어린아이 톤 매칭 "별로" 판정**(§5) |
| **VoxCPM2** | **apache-2.0 / 상업 무료** | 로컬 0 | ④ 괄호 영어 음색묘사(나이·성별) | ⚠️ **확인 필요** | 로컬 작동, 어린이 차분 톤 6종 합성(`_output/voxcpm/`). 청취 평가 진행 단계 |
| **Typecast** | 상용 / **유료** | 유료 | 성우 완성형 보이스(감정 일부) | ❌ | 한국어 보이스 합성·청취(`_output/typecast/`). **유료라 무료 비교 제외** |
| **CLOVA Voice** | 상용 / **유료(Premium 기본료)** | 유료 | 감정형 보이스 일부 | ❌ | 테스트했으나 **소스 삭제·유료라 제외** |

### 2-2. 조사만 한 엔진 (라이선스·방법 확인, 직접 합성 안 함/일부만)

| 엔진 | 라이선스 / 상업 | 비용 | 감정 튜닝 (A) | 파인튜닝 (B) | 메모 |
|------|----------------|------|---------------|:---:|------|
| **Azure TTS** | 상용 / 가능 | 무료 50만자/월, $16/100만자 (장문 $100) | ③ 스타일태그 — **한국어는 `InJoon(남) sad` 1개뿐** | ❌ | 한국어 감정 이점 거의 없음. Neural HD 자연스러움이 잠재 강점. 미청취. 상세 §6 |
| **CosyVoice2-0.5B** | **apache-2.0 / 상업 무료** | 로컬 0 | ③④⑤ instruct 감정 + `[laughter]`·`<strong>` + 복제 | ✅ foundation | 9개국어·한국어. **한국어 톤 품질 미청취** |
| **Chatterbox (Multilingual)** | **MIT / 상업 무료** | 로컬 0 | ⑤ 복제 + `exaggeration`(감정강도)·`cfg_weight` | ✅ LoRA | 23개국어. 감정강도 슬라이더 명확. **한국어 톤 미청취** |
| **MeloTTS** | MIT / 상업 무료 | 로컬 0 | ❌ 고정 화자(속도만) | 제한적 | 한국어 되나 목소리 못 바꿈 → 발랄/어린이 부적합 |
| **MiniMax** | freemium / **유료**(무료 5회) | 유료 | ③ 어린이 보이스 실재(Shy Girl·Teen) | ❌ | "목표 품질" 기준점용 |
| **Edge TTS** | wrapper GPLv3 / **개인만**(상업=Azure 구독) | 개인 0 | ② pitch 흉내(어린이 전용 없음) | ❌ | 품질 감만 보기용. 상업 회색 |
| **Amazon Polly** | 상용 / 종량제 | 종량 | 제한적(Neural Seoyeon) | ❌ | 감정/톤 약함. 후순위 |
| **SparkTTS** | apache-2.0 / 상업 무료 | 로컬 0 | 복제+pitch | 일부 | **한국어 없음(중·영)** → 탈락 |
| **Kokoro** | apache / 상업 무료 | 로컬 0 | ❌ 고정 | ❌ | **한국어 없음** → 탈락 |
| **F5-TTS** | **CC-BY-NC / 상업 금지** | — | ⑤ 복제 | 커뮤니티만 | 라이선스로 **서비스 채택 불가** |
| **IndexTTS-2** | **비상업 / 상업 금지** | — | ⑤ 복제 + 감정강도(0~1) ◎ | 파인튜닝 필요 | 감정제어 강력하나 **상업 금지** → 탈락 |

> **"무료"의 세 등급 (헷갈림 방지):**
> 1. **진짜 무료(상업 OK)** = 로컬 오픈모델: VoxCPM2·Qwen3·Chatterbox·CosyVoice2·MeloTTS. 추가비용 0.
> 2. **체험만 무료(상업은 돈)** = MiniMax(5회)·Edge TTS(개인만).
> 3. **무료처럼 보이나 라이선스가 막음** = F5-TTS(CC-BY-NC)·IndexTTS-2(비상업). 데모만 가능, 채택 불가.

> 한국어 특화 엔진(CLOVA·Typecast)은 **유료 기본료**라 무료 비교 범위에서 제외(2026-06-07). 본질은 **EL vs Google**.

---

## 3. EL vs Google 사람 A/B (라운드2) — 핵심 결정 근거

> 방법: 동일 보호자 위로 멘트를 EL 한국어 보이스 vs Google warm(앵커)으로 1:1, 좌우 seed 셔플 → 블라인드 청취 "더 위로되는 쪽" 선택. 실행 [pairwise_listen.py](pairwise_listen.py).
> 텍스트: "오늘도 마음이 많이 무거우셨죠. …"(1인칭/특정 반려동물 ❌ — 음색만 비교)

**결과: EL 9전 0무 0패.**
- 사용자(정환주)가 elevenlabs.io 웹(`Eleven Multilingual v2`)에서 한국어 보이스 **9종**을 직접 골라 받음: `annakim·annie·bomisori·esther·jason·juan·leeho·mrk·onyu`.
- 9페어 전부 EL 선택. 블라인드라 무작위면 9개 다 EL일 확률 1/512 → 편향 없는 일관된 신호.
- 사용자 종합평: **"Google은 너무 기계 목소리, ElevenLabs는 사람 목소리 같아 자연스럽다."** → 원래 문제(기계음) EL이 실제 해소.
- 라운드1(영어권 핸디캡): Google 6승1무 → 라운드2(진짜 한국어): EL 9승. **완전 역전 = 라운드1 Google 우세는 EL 보이스 핸디캡 탓이었음 입증.**

**정직한 단서 (과장 안 함):**
- EL도 완벽 아님 — 일부 보이스 운율 튐: `juan`("따라" 강조)·`leeho`("성의 없음")·`mrk`("따/호" 강조)·`onyu`("따뜻" 어색). `annakim` 살짝 노이즈.
- **흠 적은 깔끔한 그룹**: `bomisori·annie·esther·jason`. 실채택 시 이쪽 우선.
- 청취자 n=1(블라인드 9/9). 강한 신호지만 팀이 원하면 2번째 귀(강사)로 확인 가능 — 선택사항, 비차단.

**성격별 목소리 매핑 방향 (EL 향후 적용 참고):**
- 활발·장난꾸러기 → 밝고 통통 튀는 / 순둥이·온화 → 따뜻하고 포근한 / 도도·독립적(고양이) → 차분하고 낮은 / 노령·노견 → 느리고 온화한.

> 🚨 **Free 플랜 제약 (2026-06-06 실측):** Free 키는 API로 Library(한국어 네이티브) 보이스 사용 불가(HTTP 402 `paid_plan_required` / 400 `free_users_not_allowed`). → API 합성은 영어권 기본 보이스만 → 한국어에 영어 억양 오염. **진짜 한국어 테스트는 유료 Creator+ 필요 = EL 전환의 핵심 비용 변수.** [[elevenlabs-free-tier-korean-limit]]

---

## 4. 감정을 입히는 5가지 방법 (튜닝 = 이것)

> "감정 튜닝" = **추론 시점 감정/톤 제어**(학습 없이 즉시). 가중치 파인튜닝(B)은 §7.

| # | 방법 | 어떻게 | 어느 엔진 | 학습 |
|---|------|--------|----------|:---:|
| ① | **LLM 텍스트 리라이팅** | TTS 넣기 전 LLM이 문장을 감정 있게 변형 + 호흡/쉼표/말줄임 삽입. "슬프게 읽어줘"·히든워드(추모용)로 톤 자체 변경 | **모든 엔진 공통** | ❌ |
| ② | **prosody 조절** | rate·pitch·볼륨을 SSML/파라미터로 손조절 | Google·Azure·Polly | ❌ |
| ③ | **스타일/감정 태그** | `sad`·`cheerful` 등 미리 정의된 스타일 선택 | Azure(한국어 `sad` 1개), CosyVoice2 | ❌ |
| ④ | **자연어 음색 설계 (instruct)** | "차분하고 따뜻한 어린아이 목소리" 같은 글 묘사로 음색·감정·운율 설계 | Qwen3·VoxCPM2·CosyVoice2 | ❌ |
| ⑤ | **음성 복제 (reference)** | 3~10초 클립으로 톤·말투 복제. 감정강도 슬라이더 동반(Chatterbox `exaggeration`, IndexTTS2 0~1) | Chatterbox·CosyVoice2·Qwen3·F5·IndexTTS2 | ❌ |
| — | **(B) 파인튜닝** | 내 데이터(wav+텍스트)로 재학습해 목소리 고정 | Qwen3·CosyVoice2·Chatterbox | ✅ |

> **추모 서비스 핵심 조합:** ①(LLM 감정 리라이팅) + ④/⑤(음색 설계·복제). **①은 어떤 엔진을 쓰든 먼저 얹을 수 있는 가장 싼 레버 → 엔진 결정과 별개로 ①부터 적용 가능.**

---

## 5. 발랄·귀여운·어린아이 톤 + 오픈모델 (Qwen3 등)

> 동기: 라운드2 EL 9종은 **차분·따뜻** 위주. 서비스엔 **발랄/귀여운/어린아이** 톤도 필요.
> 탐색 스크립트: [find_voices.py](find_voices.py)(EL 한국어 네이티브 필터).

### 5-1. EL Voice Library 한국어 탐색
- 발랄(upbeat): `JY - Trendy K-Culture Vlog Girl`(seoul) `bQlkYuipD5BHEhntA5iz`
- 귀여운(cute): `Annie`(seoul) `Lb7qkOn5hF8p7qfCDH8q` — 라운드2 9종 중 하나, 샘플 보유(`_output/compare/el_ko_annie.mp3`)
- 🔴 **어린아이(kid) 한국어 네이티브 = 0종** (`search="kid"` 전부 비한국어). **EL은 한국어 어린아이 목소리 없음.** 발랄/귀여운 young 성인이 EL 한국어 상한.

### 5-2. Qwen3-TTS (어린아이/발랄 톤의 무료 대안)
- 모델: **`Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign`** (Alibaba, 2026-01-22 공개). VoiceDesign=글로 음색 설계 / CustomVoice=프리셋 / Clone=3초 복제. 전부 apache-2.0(**상업 무료**).
- 로컬 실행 ✅: conda `qwen3-tts`(Python 3.12) + torch cu128(Blackwell sm_120). **VRAM peak ≈ 4.6GB**(8GB 여유). 속도 RTF ≈ 2.1(미리 생성이라 무방, 실시간 부적합).
  - ⚠️ language 토큰은 **소문자 `korean`**(대문자는 silent fallback → 영어 억양 오염). Windows는 `KMP_DUPLICATE_LIB_OK=TRUE` 필요. [[qwen3-tts-local-setup]]
- ⚠️ **톤 품질은 아직 합격 못 함:** 발랄/귀여운/어린아이/남자아이 생성은 되나 사용자 청취 "별로"(`_output/qwen3/`). 한국어 자연스러움 정식 블라인드 A/B는 미실시. 로컬 다이얼 UI: [qwen3_webui.py](qwen3_webui.py) [[qwen3-tts-webui-dial]]

### 5-3. 어린이 톤 — 상업무료 후보 순위
1. **VoxCPM2** — 신형(2026-04)·48kHz·나이/성별 묘사, Qwen3 대체 1순위. (로컬 설치 완료, 청취 진행)
2. **Chatterbox / CosyVoice2** — 어린이 음성 **복제(reference)** 로 전환.
3. **최후** — 다 안 되면 어른 톤은 상업무료 + 어린이만 별도 검토(파인튜닝은 §7 보류).

> 직접 들어볼 무료 온라인 데모(설치 0, 언어 **Korean**):
> VoxCPM https://huggingface.co/spaces/openbmb/VoxCPM-Demo · Chatterbox https://huggingface.co/spaces/ResembleAI/Chatterbox · Qwen3 https://huggingface.co/spaces/Qwen/Qwen3-TTS-Voice-Design
> ❌ 제외 확정: F5·IndexTTS(상업금지), MiniMax·EL·Google(유료/종량), Edge(상업 회색).
> 윤리: 어린이 목소리도 **보호자 대상 위로 낭독**용. 반려동물 1인칭/부활 ❌. 사람 목소리 복제 시 권리·동의 필요.

---

## 6. Azure TTS 조사 (다른 팀 사용 건 확인 → 전환 불필요)

> 작성 2026-06-05 · 다른 팀이 Azure 쓴다 하여 검토. **결론: 현행 Google 유지, Azure 전환 불필요.**
> (단 품질 면에선 이후 EL이 Google을 9-9로 이김 §3 — Azure는 미청취. 무료 합성 가능해지면 블라인드 편입 검토하되 1순위 후보는 EL.)

**왜 전환 불필요:**
1. Azure 헤드라인 강점(감정 스타일)이 **한국어엔 거의 안 닿음** — 한국어 감정 스타일은 `InJoon(남) sad` 1개뿐(아래 12종), 우리 기본은 여성 → Azure도 prosody 수동 조절뿐(Google과 동률).
2. 무료 한도 절반(Google 100만 → Azure 50만 자/월), 단가는 $16/100만자로 동일.
3. 전환 비용: 새 구독(카드 인증)·SDK 연동·반소람 톤매핑 재합의. 폴백 엔진 교체는 ROI 낮음.

**한국어(ko-KR) 음성 12종 (MS Learn 확정):** SunHi/Hyunsu(Neural HD), SunHi·InJoon·BongJin·GookMin·Hyunsu·JiMin·SeoHyeon·SoonBok·YuJin(표준), HyunsuMultilingual. **감정 스타일은 `InJoonNeural`의 `sad` 단 1개**, 나머지 11종 스타일 태그 없음.

**가격:** Neural $16/100만자(Google과 동일), 무료 F0 월 50만자(조정 불가), 장문 $100/100만자. 리전 Korea Central 지원.
> 외부 평: Google=빠르고 안정 / Azure=더 자연스럽고 표현 풍부. Azure 진짜 잠재 강점은 **Neural HD 자연스러움**(미청취).

---

## 7. 파인튜닝 보류 — 현재 환경 제약 (2026-06-08)

어린아이+감정 목소리를 파인튜닝(가중치 학습)으로 고정하는 방향 검토했으나 **현재 환경에선 시작 자체가 불가** → 보류(자원 확보 시 재개).

| 벽 | 내용 |
|----|------|
| **GPU** | 공식 파인튜닝=full SFT → 1.7B **20GB+**, 0.6B **12GB+**. RTX 5060 **8GB로 불가** ([sft_12hz.py](https://github.com/QwenLM/Qwen3-TTS/blob/main/finetuning/sft_12hz.py)) |
| **데이터** | 사람 녹음 **30분+** 필요. 어린이(미성년) 음성 학습은 **법적·윤리 장벽**(개인정보·아동보호·동의). 보유 없음 |
| **LoRA 경량** | 8GB 가능성 있으나 비공식·검증 부담 |

→ **우선 instruct(학습 0)로 어린아이+감정 합성 진행**(`qwen3_emotion.py`, `_output/qwen3_emotion/`). 24GB+ GPU와 음성 데이터 확보 시 LoRA/파인튜닝 재개 검토.
> 파인튜닝 = "어떤 목소리?"(화자 고정) / 감정 = 추론 시점 제어 → **다른 축**. 감정 요구는 파인튜닝 없이 instruct로 우선 충족 가능.

---

## 8. (참고) 자동평가가 왜 결정 근거가 아니었나

> 결정 근거는 §3 사람 A/B뿐. 아래 자동지표는 **사료(史料)** — 왜 자동지표로 결론내면 안 되는지의 기록.

- **CER(STT 발음 오류율)은 틀린 지표.** 8개 mp3 전부 CER 0.0%(`analyze_stt`) = 변별력 0. "또렷한가"일 뿐 "감정 전달되나"와 무관.
- **Gemini 오디오 자동평가는 이해상충**(Gemini=Google 제품) + 기계 점수. warm 5/5(`eval_gemini_audio`)도 사람 청취 전엔 못 믿음 → 라운드2에서 실제로 EL에 9/9 패.
- **라운드1 EL은 테스트 미성립** — Free가 한국어 네이티브 보이스를 막아 영어권 보이스로 한국어를 읽힌 것. 라운드2(웹 수동 한국어)로 비로소 공정 비교 성립.
- ⚠️ GPU(RTX 5060=Blackwell sm_120) STT 경로는 ct2 4.7.2 inference hang → CPU/int8 사용(CER은 device 무관, 결과 동일).

---

## 9. 출처

- [Google Cloud TTS 가격](https://cloud.google.com/text-to-speech/pricing) · [ElevenLabs 가격](https://elevenlabs.io/pricing/api)
- [Azure Speech 가격](https://azure.microsoft.com/en-us/pricing/details/speech/) · [Azure 쿼터·F0](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits) · [Azure 한국어 음성·스타일](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
- [Qwen3-TTS GitHub](https://github.com/QwenLM/Qwen3-TTS) · [HF 모델카드](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign)
- [VoxCPM2](https://huggingface.co/openbmb/VoxCPM2) · [CosyVoice2](https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B) · [arXiv 2412.10117](https://arxiv.org/html/2412.10117v1)
- [Chatterbox](https://github.com/resemble-ai/chatterbox) · [MeloTTS-Korean](https://huggingface.co/myshell-ai/MeloTTS-Korean)
- [F5-TTS](https://github.com/SWivid/F5-TTS)(CC-BY-NC) · [IndexTTS-2 데모](https://huggingface.co/spaces/IndexTeam/IndexTTS-2-Demo)(비상업) · [arXiv 2506.21619](https://arxiv.org/pdf/2506.21619)
- [Edge TTS 상업 사용 Q&A](https://learn.microsoft.com/en-us/answers/questions/2088770/are-opensource-edge-tts-free-for-commercial-use) · [MiniMax 한국어](https://www.minimax.io/audio/text-to-speech/korean)
- [Google vs Azure vs ElevenLabs 비교](https://ttsforfree.com/en/blogs/google-vs-azure-vs-elevenlabs-tts-comparison/)
