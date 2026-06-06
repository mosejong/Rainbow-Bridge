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
| **MS Azure TTS** | 한국어 Neural 지원 | 스타일(감정) 태그 | 여러 종 | F0 무료 티어 있음 | **단가 확인 필요** | 상업 가능 | Google과 유사 포지션. 구체 수치 확인 필요 |
| (옵션) Amazon Polly | 한국어 Neural(Seoyeon) | 제한적 | 소수 | 12개월 무료 일부 | 확인 필요 | 상업 가능 | 감정/톤 약함. 후순위 |

> "확인 필요" = 웹에서 정확한 최신 수치 못 찾음. **추정 안 함** — 공식 페이지 직접 확인.

## 3. 추천 (2026-06-06 업데이트)

> ⚠️ **방향 전환**: PERSO 립싱크 드랍 확정 → TTS가 추모 영상의 **주력 오디오**가 됨.
> 기계음이 나오면 추모 영상 전체 몰입이 깨짐 → 음질이 가장 중요한 기준으로 격상.

1. **주력: ElevenLabs** — 감정 표현 최상, 성격별 목소리 매핑 가능 (stability/style 파라미터). 무료 10,000자/월로 테스트 먼저.
2. **폴백: Google Cloud TTS** — 이미 실동작, 장애 시 대체. 데모 중 ElevenLabs 할당량 초과 시 자동 전환.
3. **한국어 최고 음질 원하면:** 네이버 CLOVA Voice — 단, **저장·재사용 약관 먼저 확인** 필수.

**성격별 목소리 매핑 방향 (ElevenLabs)**:
- 활발·장난꾸러기 → 밝고 통통 튀는 목소리
- 순둥이·온화 → 따뜻하고 포근한 목소리
- 도도·독립적 (고양이) → 차분하고 낮은 목소리
- 노령·노견 → 느리고 온화한 목소리

**다음 작업 (정환주)**: ElevenLabs API 키 발급 → 한국어 목소리 샘플 청취 → 성격 4종 매핑 확정.

## 4. 출처

- [Google Cloud TTS 가격](https://cloud.google.com/text-to-speech/pricing)
- [네이버 CLOVA Voice](https://www.ncloud.com/product/aiService/clovaVoice) · [API 가이드](https://api.ncloud-docs.com/docs/ai-naver-clovavoice)
- [ElevenLabs 가격](https://elevenlabs.io/pricing/api)
- [타입캐스트 가격 안내](https://typecast.ai/kr/learn/answer-questions-about-typecast-pricing/)
