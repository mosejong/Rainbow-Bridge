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
| **Google Cloud TTS (현재)** | 양호(Neural2) | rate·pitch 조절 | 여러 종(Neural2/WaveNet/Standard) | Neural2 100만자/월, WaveNet 400만자/월 | Neural2 $16, WaveNet $4 (/100만자) | 상업 가능 | 이미 연동·실동작. 데모 사실상 0원 |
| **네이버 CLOVA Voice** | **최상위(한국어 특화)** | 감정·스타일 음성 다수 | 많음 | 기본 100만자(합산) | Premium 월정액+초과(원화) **확인 필요** | ⚠️ **이용정책 확인 필요** | 검색상 "생성 파일 저장·편집·재사용 제한" 문구 → 우리처럼 mp3 저장·재생 시 **걸릴 수 있음**. 약관 먼저 확인 |
| **타입캐스트(Typecast)** | 우수(성우 500+) | SSFM 감정 모델 강함 | 많음 | 월 5분 미만 무료 | 프로 39,000원/월~, **API 단가 별도 확인** | 상업 플랜 존재 | 감정 연기 강점. API 요금 공개 적음 |
| **ElevenLabs** | 다국어 v2 한국어 지원 | **감정 표현 최상** | 다수(복제 가능) | 무료=상업 ❌ | Starter $5/월~, API Pro $99/월 | 상업은 유료플랜부터 | 품질 최고지만 비쌈. 한국어 자연성은 CLOVA가 더 안정적일 수 있음 |
| **MS Azure TTS** | 양호(Neural, 한국어 46종 프리뷰 추가) | **스타일(감정) 태그 — InJoon `sad` 등 ◎** | 여러 종(SunHi·InJoon·Hyunsu…) | 월 50만자 | Neural $16 /100만자 (장문 $100) | 상업 가능 | 감정 스타일이 Google보다 강점. 상세 → [AZURE_TTS_조사.md](AZURE_TTS_조사.md) |
| (옵션) Amazon Polly | 한국어 Neural(Seoyeon) | 제한적 | 소수 | 12개월 무료 일부 | 확인 필요 | 상업 가능 | 감정/톤 약함. 후순위 |

> "확인 필요" = 웹에서 정확한 최신 수치 못 찾음. **추정 안 함** — 공식 페이지 직접 확인.

## 3. 추천 (2026-06-06 업데이트)

> ⚠️ **방향 전환**: PERSO 립싱크 드랍 확정 → TTS가 추모 영상의 **주력 오디오**가 됨.
> 기계음이 나오면 추모 영상 전체 몰입이 깨짐 → 음질이 가장 중요한 기준으로 격상.
> 🔄 **2026-06-06 스파이크 결과 반영**: ElevenLabs 전환 보류 → **Google 유지**로 확정(근거 §5).

1. **주력: Google Cloud TTS (현행 유지)** — 이미 실동작·유료, 한국어 네이티브(Neural2-A). 2026-06-06 비교 스파이크에서 **ElevenLabs 전환 근거 없음**(§5) → 현행 유지. 톤은 Gemini 평가 최고치인 **warm** 권장.
2. **재검토 후보: ElevenLabs** — 감정 표현 강점은 유효하나, **Free는 영어권 보이스만 API 사용 가능**해 한국어 평가 불가. **유료 Creator+ 전환 + 한국어 네이티브 보이스 재샘플** 시에만 재평가.
3. **한국어 최고 음질 옵션:** 네이버 CLOVA Voice — 단, **저장·재사용 약관 먼저 확인** 필수.

**성격별 목소리 매핑 방향 (ElevenLabs — 유료 전환 시 적용)**:
- 활발·장난꾸러기 → 밝고 통통 튀는 목소리
- 순둥이·온화 → 따뜻하고 포근한 목소리
- 도도·독립적 (고양이) → 차분하고 낮은 목소리
- 노령·노견 → 느리고 온화한 목소리

**다음 작업 (정환주)**: ElevenLabs 키 발급·샘플 비교 → **완료**(§5, Google 유지 결론). ElevenLabs 성격 매핑은 **유료 전환 판단 시** 한국어 보이스로 재샘플.

## 4. 출처

- [Google Cloud TTS 가격](https://cloud.google.com/text-to-speech/pricing)
- [네이버 CLOVA Voice](https://www.ncloud.com/product/aiService/clovaVoice) · [API 가이드](https://api.ncloud-docs.com/docs/ai-naver-clovavoice)
- [ElevenLabs 가격](https://elevenlabs.io/pricing/api)
- [타입캐스트 가격 안내](https://typecast.ai/kr/learn/answer-questions-about-typecast-pricing/)

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

### 결론 (한 줄)

- 전환 가치: **☑ 없음 → Google 유지** (현 시점 보류, 유료 한국어 테스트 시 재검토)
- 근거:
  1. **CER 변별 불가**: large-v3로 8개 전부 0.0% → 발음 명료도로는 ElevenLabs vs Google 우열을 못 가림.
  2. **Free 플랜 confound**: Free 키는 영어권 보이스만 API 사용 가능 → 샘플이 "영어 보이스의 한국어 발화"라 ElevenLabs 한국어 자연스러움/감정의 **공정 평가 불가**. 어떤 자동측정(Gemini·UTMOS)도 이 억양 confound는 못 풀음.
  3. 따라서 **전환 찬성 증거 없음** → 기존 "Google 유지 권장"(커밋 62883f6) 유지. ElevenLabs 진짜 평가는 **유료 Creator+ + 한국어 네이티브 보이스(Nara·Jin 등) 재샘플** 시에만 가능.
- 톤 진단(Gemini 참고, 전환 여부와 별개): **warm 5/5 최고**, calm 감정 3/5로 최저. **로봇음 톤은 없음**(전부 자연 4~5). 단 톤은 반소람 메시지 감정과 **1:1 계약**(§1)이라 자유 교체 대상은 아님 — "로봇음 톤 색출" 용도로만 참고.

