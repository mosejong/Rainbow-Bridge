# MS Azure TTS 조사 — 다른 팀 사용 건 확인

> 작성: 정환주 · 2026-06-05 · 다른 팀에서 Azure TTS 쓴다 하여 성능·음질·도입 검토.
> 우리 현재 셋업(**Google Cloud TTS `ko-KR-Neural2-A`**) 기준 비교. 엔진 비교표 본문 → [ENGINE_NOTES.md §2](ENGINE_NOTES.md).
> ⚠️ 톤 만족도·1인칭 안 나오는지 등 품질 판정은 **반소람 평가 영역**과 같이 봐야 함([../CLAUDE.md §6](../CLAUDE.md)).

---

> ✅ **2026-06-07 갱신:** 아래 "Google 유지" 결론은 **사람 청취 없이** 나온 것이었고, 이후 사람 A/B로 재평가함 →
> **EL 한국어 보이스가 Google warm을 블라인드 9전 9승**([ENGINE_NOTES.md §5](ENGINE_NOTES.md) · [pairwise_listen.py](pairwise_listen.py)).
> **품질은 EL 우위로 결판**(단 EL 상업=유료가 비용 변수). 따라서 이 문서의 "Google 유지" 단정은 **품질 면에선 뒤집혔음**에 유의 —
> Azure 비교(음질·가격·감정스타일 데이터)는 여전히 유효하나, 엔진 선택의 1순위 후보는 이제 Azure가 아니라 **EL vs Google(비용)** 구도.

## 0. 보고용 결론 (TL;DR — 세종님께)

> **결론: 현행 Google TTS 유지 권장. Azure 전환 불필요.** (단 위 갱신 주의 — 엔진 선택 자체는 재평가 중)
>
> 1. Azure 헤드라인 강점(감정 스타일)이 **우리한텐 안 닿음** — 한국어 감정 스타일은 InJoon(남) `sad` 1개뿐, 우리 기본 음성은 여성 → Azure도 Google처럼 prosody 조절만 가능(동률).
> 2. **TTS는 이미 주력 아님** — PERSO 아바타 낭독이 주력, Google TTS는 폴백([ENGINE_NOTES.md](ENGINE_NOTES.md) 6행). 폴백 엔진 교체는 ROI 낮음.
> 3. **전환 비용** — 새 Azure 구독(카드 인증)·SDK 연동·무료한도 절반(100만→50만)·반소람과 톤매핑 재합의.
> 4. 단가·품질은 Google과 대등, 무료 한도는 Google이 2배.
>
> ➡️ 굳이 바꿀 이유 없음. **유지.** (음성 청취 A/B는 결론을 안 바꿔서 생략 — 아래 §6)

---

## 1. 음질 (제일 궁금한 부분)

- 신경망(neural) 음성 → 억양·리듬·감정 재현, **사람 녹음과 거의 구분 안 됨** (MS 공식 표현).
### 한국어(ko-KR) 음성 전체 — 12종 (MS Learn 공식 확정)

| 음성 | 성별 | 종류 | 감정 스타일 |
|------|------|------|------------|
| ko-KR-SunHi:DragonHDLatestNeural | 여 | Neural HD | 없음 |
| ko-KR-Hyunsu:DragonHDLatestNeural | 남 | Neural HD | 없음 |
| ko-KR-SunHiNeural | 여 | 표준 | 없음 |
| **ko-KR-InJoonNeural** | 남 | 표준 | **`sad`(슬픔) ✅** |
| ko-KR-BongJinNeural | 남 | 표준 | 없음 |
| ko-KR-GookMinNeural | 남 | 표준 | 없음 |
| ko-KR-HyunsuNeural | 남 | 표준 | 없음 |
| ko-KR-JiMinNeural | 여 | 표준 | 없음 |
| ko-KR-SeoHyeonNeural | 여 | 표준 | 없음 |
| ko-KR-SoonBokNeural | 여 | 표준 | 없음 |
| ko-KR-YuJinNeural | 여 | 표준 | 없음 |
| ko-KR-HyunsuMultilingualNeural | 남 | 다국어 | 없음 |

- ⚠️ **솔직한 한계:** 영어 등은 감정 스타일이 많지만, **한국어에서 명시적 감정 스타일은 `InJoon`의 `sad` 단 1개.** 나머지 11종은 스타일 태그 없음(rate·pitch·SSML prosody만).
  - 즉 "감정 스타일 강점"은 **한국어에선 InJoon(남성) 한정**. 여성 음성으로 슬픔 톤 주려면 우리 Google과 마찬가지로 prosody 수동 조절뿐.
- **Neural HD** 음성(SunHi·Hyunsu)은 최신 고품질 모델 → 자연스러움 자체는 HD가 우위 가능.
- 외부 비교 평: **Google = 빠르고 안정적 / Azure = 더 자연스럽고 표현 풍부.**
- 비교: 우리 현재 Google `Neural2-A`는 `speaking_rate`·`pitch`만 조절([tts.py](tts.py) `_TONE_MAP`).
- 리전: **Korea Central 포함** 다수 리전서 Speech 서비스 지원(한국 리전 사용 가능 → 지연·데이터 위치 이점).

## 2. 성능 (속도·지연)

- 실시간 합성 가능. 단 MS 공식 권고: **지연 민감하면 미리 생성(pre-generate)·엣지 배포**.
  - 우리 구조는 편지 MP3를 미리 만들어 두는 방식 → **지연 큰 이슈 아님**.
- 실시간 음성 대화가 필요하면 별도 **Voice Live API** 존재 → 우리 용도엔 과함(불필요).

## 3. 가격 (2026 기준)

| 항목 | Azure TTS | 우리 현재 Google |
|------|-----------|------------------|
| 신경망 TTS 단가 | **$16 / 100만 자** | Neural2 $16 / 100만 자 (동일), WaveNet $4 |
| 무료 한도 | **월 50만 자** | Neural2 100만 자/월, WaveNet 400만 자/월 |
| 장문 오디오(long audio) | $100 / 100만 자 | — |
| 상업 라이선스 | 가능 | 가능 |

- 단가는 거의 같음. **무료 한도는 Google이 2배** → 개발·시연 단계 비용은 Google 유리(데모는 사실상 0원).
- **무료 티어(F0) 상세 (MS Learn 확정):** 신경망 TTS **월 50만 자 무료**, 한도 **조정 불가**. 초과 시 유료(S0, $16/100만 자)로 과금. 프로토타입·저용량용 설계.

## 4. 우리 프로젝트 관점 비교

| 항목 | Azure | Google (현재) |
|------|-------|---------------|
| 한국어 자연스러움 | ◎ (특히 Neural HD) | ○ |
| **감정 스타일(sad/위로)** | △ — **한국어는 InJoon(남) `sad` 1개뿐**, 나머지 11종 없음 | △ (rate·pitch만) |
| 속도·안정성 | ○ | ◎ |
| 무료 한도 | 50만 자/월 | 100만 자/월 |
| 셋업 상태 | Azure 계정·키 신규 발급 필요 | **이미 연동·키 발급됨**([.env.example](../../.env.example) 64행) |

> ⚠️ 처음엔 "Azure 감정 스타일 강점"이라 봤으나, 한국어 12종 확인 결과 **명시적 감정 스타일은 InJoon(남) `sad` 1개뿐.** 우리 기본은 여성 → 여성으로 가면 Azure도 Google처럼 prosody 수동 조절뿐. **한국어 한정으론 감정 이점 거의 없음.** Azure의 진짜 잠재 강점은 **Neural HD 음성 자연스러움**.

## 5. 결론·추천

1. **현 단계: Google 유지 권장.** 이미 실동작 + 무료 한도 2배 + 상업 가능. Azure의 헤드라인 강점(감정 스타일)이 **우리 여성 기본 음성·한국어엔 거의 안 닿음**(§4 주석).
2. **TTS는 이미 주력 아님** — 방향 전환으로 **PERSO 아바타 낭독 MP4가 주력, Google TTS는 폴백**([ENGINE_NOTES.md](ENGINE_NOTES.md) 6행). 폴백 엔진 교체는 ROI 낮음. 퀄리티 레버는 아바타·PERSO 쪽.
3. **음성 청취 A/B 테스트는 안 함.** 유일하게 들어볼 거리(Azure HD 자연스러움)는 위 1·2 때문에 결론(유지)을 안 바꿈 + Azure 구독(카드 인증) 필요 → 실익 없어 생략.
4. 교체 결정 전 **반소람(톤 평가)·강사 확인** 권장. 음성도 "보호자 대상 위로 낭독"만, 반려동물 목소리 흉내 ❌([CLAUDE.md §5](CLAUDE.md)).

## 6. 안 한 것 (밝혀둠)

- **실제 음성 청취 A/B** — Azure 구독(카드·휴대폰 인증)이 있어야 합성 가능. 당시 "결론 안 바꿈"이라 생략했으나, **2026-06-07 그 생략이 잘못이었음**(청취 없이 엔진 결론낸 게 문제) → 사람 청취([pairwise_listen.py](pairwise_listen.py))로 재평가 완료(**EL이 Google warm에 9전 9승**, [ENGINE_NOTES.md §5](ENGINE_NOTES.md)). **Azure는 미청취** — 무료 합성 가능해지면 블라인드 편입 검토하되, 현재 1순위 후보는 EL.
- 그 외 음질·성능·가격·한국어 음성 전체·리전·무료티어는 공식 문서로 **확정 완료.**

## 7. 출처

- [Azure Speech 가격](https://azure.microsoft.com/en-us/pricing/details/speech/)
- [Azure Speech 쿼터·한도(F0 무료티어)](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/speech-services-quotas-and-limits)
- [Azure 언어·음성 지원(한국어 12종·스타일)](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support)
- [Azure Speech 지원 리전(Korea Central)](https://learn.microsoft.com/en-us/azure/ai-services/speech-service/regions)
- [Azure TTS 2025 개발자 가이드](https://www.videosdk.live/developer-hub/tts/azure-text-to-speech)
- [Google vs Azure vs ElevenLabs 비교](https://ttsforfree.com/en/blogs/google-vs-azure-vs-elevenlabs-tts-comparison/)
- [Azure 신규 한국어 음성 추가](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/azure-cognitive-services-releases-new-languages-and-voices-for-neural-text-to-sp/3672286)
