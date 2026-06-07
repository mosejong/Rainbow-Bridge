# TTS 엔진 후기·비교 (`ai/tts/`)

> [CLAUDE.md §6](CLAUDE.md) "엔진 비교하면 이 폴더에 기록" 규칙에 따른 조사 노트.
> 작성: 정환주 · 2026-06-04 · 데모/프로덕션 엔진 선택 근거용.

> 🔁 **2026-06-05 방향 전환:** 추모 낭독을 PERSO 단독 TTS로 교체하려 했으나 **PERSO 단독 TTS 없음**(팀 문서 확정) → **PERSO AI Human 아바타 낭독 MP4를 주력, 아래 Google TTS는 안정성 폴백**으로 전환. 아바타·매핑 핸드오프 → [AVATAR_HANDOFF.md](AVATAR_HANDOFF.md).

---

## 1. 현재 우리 셋업 (코드 근거)

- 엔진: **Google Cloud Text-to-Speech**
- 목소리(기본): `ko-KR-Neural2-A` ([tts.py](tts.py) `_VOICE_NAME`, `TTS_VOICE`로 변경 가능)
- 선택 가능 목소리(이번 추가): `female_a`(기본)·`female_b`·`male_c`·`female_wavenet` ([tts.py](tts.py) `_VOICES`)
- 톤: `warm`·`calm`·`hopeful`·`soft` (각 `speaking_rate`·`pitch` 매핑, [tts.py](tts.py) `_TONE_MAP`)
- 긴 글 분할: 문장 경계 기준 4500자 ([tts.py](tts.py) `_split_text`)
- 패키지: `google-cloud-texttospeech>=2.16` (`ai/requirements.txt`)

> ⚠️ **`soft` 톤 합의 필요:** 프론트(`TtsPage.jsx`)가 이미 `soft`를 보내는데 백엔드 톤셋엔 없어
> 조용히 `warm`으로 폴백되던 버그가 있었음 → ④에서 `soft`를 받게 추가해 해결.
> 다만 ③(반소람 메시지 톤)↔④ TTS 톤은 **1:1 매핑 계약**이라, `soft` 포함 최종 톤셋은 반소람과 합의 필요.

## 2. 엔진 비교표

| 엔진 | 한국어 음질 | 감정/톤 | 목소리 수(한국어) | 무료 한도 | 초과 단가 | 상업 라이선스 | 비고 |
|------|------------|---------|------------------|-----------|-----------|---------------|------|
| **Google Cloud TTS (현재)** | 양호(Neural2) | rate·pitch 조절 | 여러 종(Neural2/WaveNet/Standard) | Neural2 100만자/월, WaveNet 400만자/월 | Neural2 $16, WaveNet $4 (/100만자) | 상업 가능 | 이미 연동·실동작. 데모 사실상 0원. **현 비교 기준(앵커)** |
| **ElevenLabs** | 다국어 v2 한국어 지원 | **감정 표현 최상** | 다수(복제 가능) | 무료=상업 ❌ | Starter $5/월~, API Pro $99/월 | 상업은 유료플랜부터 | **사람 블라인드 A/B에서 Google warm 9전 9승**(2026-06-07, §5). 품질 우위 확정, 단 상업=유료가 결정 변수 |
| **MS Azure TTS** | 양호(Neural, 한국어 46종 프리뷰 추가) | **스타일(감정) 태그 — InJoon `sad` 등 ◎** | 여러 종(SunHi·InJoon·Hyunsu…) | 월 50만자 | Neural $16 /100만자 (장문 $100) | 상업 가능 | 감정 스타일이 Google보다 강점. 상세 → [AZURE_TTS_조사.md](AZURE_TTS_조사.md) |
| (옵션) Amazon Polly | 한국어 Neural(Seoyeon) | 제한적 | 소수 | 12개월 무료 일부 | 확인 필요 | 상업 가능 | 감정/톤 약함. 후순위 |

> "확인 필요" = 웹에서 정확한 최신 수치 못 찾음. **추정 안 함** — 공식 페이지 직접 확인.

## 3. 추천 (2026-06-06 업데이트)

> ⚠️ **방향 전환**: PERSO 립싱크 드랍 확정 → TTS가 추모 영상의 **주력 오디오**가 됨.
> 기계음이 나오면 추모 영상 전체 몰입이 깨짐 → 음질이 가장 중요한 기준으로 격상.
> ✅ **2026-06-07 라운드2 사람 A/B 완료**: EL 한국어 보이스가 Google warm을 **블라인드 9전 9승**(상세 §5).
> → 품질은 **EL 우위로 결판**. 단 **비용(상업=유료)** 은 PM/팀 결정으로 남음. 대상은 **폴백 TTS(`voiced_url`)** 한정.

1. **품질 결론: ElevenLabs (한국어) 우위** — 사람 블라인드 A/B에서 EL 9종이 현행 Google warm을 9/9로 이김. 사용자평 "Google 기계음 / EL 사람 같음" → **원래 문제(기계음) 해소.** 깔끔한 보이스: `bomisori·annie·esther·jason`. 라운드1(영어권 핸디캡 전패)은 테스트 미성립이었음이 역전으로 입증.
2. **비용 결론: 미결정(팀)** — EL은 무료=상업 ❌, 프로덕션/폴백은 유료 플랜부터(Starter $5/월~). CLOVA를 뺀 그 유료벽이 EL에도 적용. "품질 우위 vs 월 구독" 트레이드오프는 팀 판단.
3. **현행 Google Cloud TTS** — 이미 실동작·무료한도 큼·한국어 네이티브(Neural2-A). 품질에선 졌으나 **비용·연동 면에서 폴백으로 유지할 이유는 남음.** 최종 채택은 1·2 종합해 PM 결정.

> 한국어 특화 엔진(CLOVA·Typecast 등)은 검토했으나 **CLOVA Premium = 유료 기본료**라 무료 비교 범위에서 제외(2026-06-07). 본질은 EL vs Google.

**성격별 목소리 매핑 방향 (ElevenLabs — 향후 적용 참고)**:
- 활발·장난꾸러기 → 밝고 통통 튀는 목소리
- 순둥이·온화 → 따뜻하고 포근한 목소리
- 도도·독립적 (고양이) → 차분하고 낮은 목소리
- 노령·노견 → 느리고 온화한 목소리

**진행 기록 (정환주)**: ① 라운드1 A/B(영어권 핸디캡, Google 6승1무 — 미성립) → ② **EL 한국어 9종 웹 수동 생성 → 라운드2 A/B 완료: EL 9전 9승**(§5). **자동평가(CER·Gemini)는 결정 근거에서 제외, 참고용만.** 다음: 비용(상업=유료) 포함해 **PM 최종 채택 결정** + 채택 시 폴백 경로(`voiced_url`) 엔진 교체.

## 4. 출처

- [Google Cloud TTS 가격](https://cloud.google.com/text-to-speech/pricing)
- [ElevenLabs 가격](https://elevenlabs.io/pricing/api)

## 5. 샘플 비교 청취 결과 (스파이크 — 채우는 중)

> 방법: 동일한 보호자 위로 멘트 1개를 ElevenLabs(성격 4종) vs Google 현행으로 합성해 A/B 청취.
> 생성: `python -m ai.tts.compare_elevenlabs` → `ai/tts/_output/compare/*.mp3` (키 필요, *.mp3 비커밋)
> 텍스트: "오늘도 마음이 많이 무거우셨죠. …" (1인칭/특정 반려동물 ❌ — 음색만 비교)

### ElevenLabs (model: eleven_multilingual_v2, language_code=ko)

> 🚨 **Free 플랜 제약 (2026-06-06 실측)**: Free 키는 **API 로 Library(한국어 네이티브)
> 보이스 사용 불가** (HTTP 402 `paid_plan_required` / 400 `free_users_not_allowed`).
> → API 합성은 **계정 기본 보이스(영어권)** 만 가능 → 아래 샘플은 한국어에 **영어 억양**이 섞임.
> **진짜 한국어 음질·성격 매핑 테스트는 유료 Creator+ 전환 필요.** ElevenLabs 전환의 핵심 비용 변수.

생성 보이스(Free 기본·자동배정 — 영어권):

| 성격 | voice_id (사용) | STT 발음(CER↓) | 자연스러움 | 감정표현 | 메모 |
|------|----------|----------------|-----------|----------|------|
| 활발 | Roger (CwhRBWXzGAHq8TQ4Fs17) | 0.0% | —(주관) | —(주관) | 영어권 Free 보이스 — 한국어 억양 섞임 |
| 순둥이 | Sarah (EXAVITQu4vr4xnSDxMaL) | 0.0% | —(주관) | —(주관) | 영어권 Free 보이스 |
| 도도 | Laura (FGY2WhTYpPnrIDTdsKH5) | 0.0% | —(주관) | —(주관) | 영어권 Free 보이스 |
| 노령 | Charlie (IKne3meq5aSn9XLyUdCD) | 0.0% | —(주관) | —(주관) | 영어권 Free 보이스 |

한국어 네이티브 후보(유료 전환 시 사용 — 실행 시 자동 출력됨):
`Nara-Warm`(qWofGdsKN4woEPGCzrdX 여중년 서울) · `Totoring-Calm`(d4fa1MBr1OVekaed8x4e 여청년 서울) ·
`Jin-Warm`(rvVNwZozYG4hTIbVUvHi 남중년) · `Dae-Mature`(HHlsD8ZpKBtIAyvlCGoz 남중년 서울) ·
`Yimi-Calm`(TLp6VWy7y0kTr5KDx4gQ 여청년 서울) · `Juha-Calm`(hmewQCBsQh48wGHkpNwo 여)

### Google 현행 베이스라인 (ko-KR-Neural2-A)

> 자연스러움·감정표현 = **Gemini 2.5 flash 오디오 자동평가**(참고용 LLM 판단, MOS 아님).
> 실행 `python -m ai.tts.eval_gemini_audio`. ElevenLabs는 영어 Free보이스 confound로 **제외**(공정 비교 불가).

| 톤 | STT 발음(CER↓) | 자연스러움(1~5) | 감정표현(1~5) | Gemini 코멘트 |
|----|----------------|----------------|---------------|---------------|
| **warm** | 0.0% | **5** | **5** | 따뜻한 톤·자연스러운 흐름으로 위로 잘 전달 (최고) |
| hopeful | 0.0% | 4 | 4 | 자연스러운 발음·따뜻한 톤, 위로 전달 양호 |
| soft | 0.0% | 4 | 4 | 위로하는 톤, 감정 전달 양호 |
| calm | 0.0% | 4 | 3 | 자연스럽지만 감정 전달 다소 아쉬움 |

### STT 발음 분석 (faster-whisper large-v3 / CPU·int8 / beam5, 2026-06-06)

- 방법: 위 8개 mp3를 STT로 받아쓰기 → 원문 대비 **CER(글자오류율, 낮을수록 또렷)**. 실행 `python -m ai.tts.analyze_stt`.
- 결과: **8개 전부 CER 0.0%** — ElevenLabs·Google 모두 STT가 원문을 완벽히 받아씀.
- 해석: large-v3는 억양이 섞여도 단어만 맞으면 정확히 받아씀 → **CER로는 두 엔진 변별 불가**. 자연스러움·감정·억양은 STT로 측정 못 함(주관 청취 필요 → 위 표 "—").
- ⚠️ GPU(RTX 5060 = Blackwell sm_120) 경로는 ct2 4.7.2가 inference에서 hang(모델 로드는 성공) → CPU/int8 사용. **CER은 device 무관**이라 결과 동일.

### 결론 (2026-06-07 — 라운드2 사람 A/B 실측 완료)

✅ **라운드2 완료: EL 한국어 보이스가 현행 Google warm을 블라인드로 9전 9승.** 이전 "Google 유지" 철회는 옳았고, 이제 그 자리를 **사람 청취 실측 결과**가 채운다.

**라운드2 방법·결과 (`pairwise_listen` A/B):**
- 사용자(정환주)가 elevenlabs.io 웹(model `Eleven Multilingual v2`)에서 한국어 보이스를 직접 듣고 **9종**을 추려 받음: `annakim·annie·bomisori·esther·jason·juan·leeho·mrk·onyu`.
- 각 EL 보이스 vs **Google warm(앵커)** 1:1, 좌우 seed 셔플 → 어느 쪽이 EL인지 모른 채 "더 위로되는 쪽" 선택.
- **결과: 9페어 전부 EL 선택 → EL 9승 0무 0패.** 블라인드라 만약 그냥 찍었다면 9개 다 EL이 나올 확률은 1/512 → 사실상 편향 없는 일관된 신호.
- 사용자 종합평: **"Google은 너무 기계 목소리, ElevenLabs는 사람 목소리 같아 자연스럽다."** → **원래 문제였던 Google "기계음"을 EL이 실제로 해소.**
- 라운드1(영어권 핸디캡): Google 6승1무 → 라운드2(진짜 한국어): EL 9승. **완전 역전 = 라운드1의 Google 우세는 EL 보이스 핸디캡 탓이었음이 입증.**
- 콘텐츠 검증 OK: 사용자 코멘트가 멘트 속 단어("따뜻의 따", "호흡의 호")를 짚음 → EL 샘플이 **올바른 공통 텍스트**를 읽었음(비교 공정).

**정직한 단서 (과장 안 함):**
- EL도 완벽은 아님 — 일부 보이스에서 특정 단어 운율이 튐: `juan`("따라" 강조)·`leeho`("성의 없는 느낌")·`mrk`("따/호" 강조)·`onyu`("따뜻" 어색). `annakim`은 살짝 노이즈.
- **흠 적은 깔끔한 그룹**: `bomisori`·`annie`·`esther`·`jason`. 실채택 시 이 쪽 우선 권장.
- 청취자 **n=1(블라인드 9/9)**. 강한 신호지만, 팀이 원하면 2번째 귀(예: 강사)로 확인 가능 — 선택사항, 비차단.

**그래서 결론은 두 부분 (한쪽만 쓰면 세종님 지적의 거울상 실수):**
1. **품질 = EL 압승 (해결됨).** 사람 블라인드 A/B로 EL이 Google warm(Gemini가 최고점 준 톤)을 9/9로 이김. Google 기계음 문제 해소. **이 질문은 끝났다.**
2. **비용 = 미결정 (PM/팀 결정).** EL은 **무료=상업 ❌**, 프로덕션/폴백 사용은 유료 플랜부터(Starter $5/월~, API Pro $99/월 — §2). CLOVA를 비교에서 뺀 그 "유료 기본료" 벽이 **EL에도 똑같이 적용**된다. "품질 우위 vs 월 구독 비용" 트레이드오프는 스파이크가 아니라 팀이 결정할 사안.

**범위 한정 (오해 금지):** 이번 비교 대상은 **standalone/폴백 한국어 TTS 보이스(`voiced_url` 경로)** = Google warm 단일 톤 vs EL. **주력 파이프라인인 PERSO 아바타 + 내장 TTS는 이 결과와 무관**([[tts-voiced-url-perso-decision]]). "EL 승"을 "오디오 스택 전체 교체"로 읽지 말 것.

> 아래 라운드1 표·CER·Gemini 수치는 **사료(史料)로 보존**(왜 자동지표로 결론내면 안 되는지의 기록). 결정 근거는 위 라운드2 사람 A/B뿐.

### (참고) 이전 자동평가가 왜 결정 근거가 아니었나
- **CER은 틀린 지표.** STT 받아쓰기 정확도일 뿐, "감정 전달되나"와 무관. 8개 전부 0.0% = 변별력 0.
- **Gemini 자동평가는 이해상충**(Gemini=Google 제품) + 기계가 점수. warm 5/5도 사람 청취 전엔 못 믿음 → 라운드2에서 실제로 EL에 9/9 패.
- **라운드1 EL은 테스트 미성립** — Free가 한국어 네이티브 보이스를 막아 영어권 보이스로 한국어를 읽힌 것. 라운드2(웹 수동 한국어)로 비로소 공정 비교 성립.

