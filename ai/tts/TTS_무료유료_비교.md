# TTS 엔진 무료/유료 비교 — 한국어 어린이(남·여) 목소리 관점

> 작성: 정환주 · 2026-06-08 · TTS 엔진 후보 정리(팀 공유용).
> 배경: 서비스에 **발랄/귀여운/어린아이** 한국어 톤 필요. EL Voice Library엔 한국어 어린이 0종,
> Qwen3-TTS는 톤 "별로" 판정 → 무료/유료 전체를 다시 비교하고, 직접 실험할 데모를 추림.
> 상세 스파이크 기록 → [ENGINE_NOTES.md](ENGINE_NOTES.md) · Qwen3 단독 검토 → [QWEN3_TTS_평가체크.md](QWEN3_TTS_평가체크.md)

---

## 0. 한 줄 결론

- **한국어 "어린이 전용" 무료 오픈모델은 사실상 없음** — 전부 "일반 한국어 모델 + 어린이 톤 끌어내기"(voice design 묘사 or 어린이 음성 복제) 구조.
- **상업까지 진짜 무료**인 건 로컬 오픈모델뿐: **VoxCPM2 / Qwen3-TTS / Chatterbox / CosyVoice2 / MeloTTS**.
- "무료"로 보이지만 **상업 안 되는** 함정: **Edge TTS**(개인만, 상업=Azure 구독), **MiniMax**(freemium 유료), **F5·IndexTTS**(비상업 라이선스).
- 신형 **VoxCPM2**(2026-04, apache-2.0, 48kHz, 나이·성별 묘사)가 Qwen3 대체 1순위.

---

## 1. 무료 vs 유료 — 전체 비교표

| 엔진 | 한국어 | 어린이 톤 방법 | 라이선스 | **상업 사용** | 실행 | 근거 |
|------|:---:|------|------|:---:|:---:|------|
| **VoxCPM2** | ✅ | voice design(나이·성별 묘사) + 복제 | apache-2.0 | ✅ **무료** | 로컬 | [HF](https://huggingface.co/openbmb/VoxCPM2) "free for commercial use" |
| **Qwen3-TTS** | ✅ | instruct 묘사 + 복제 | apache-2.0 | ✅ **무료** | 로컬(셋업완료) | [GitHub](https://github.com/QwenLM/Qwen3-TTS) · 톤 "별로" 판정 |
| **Chatterbox** | ✅(23개국어) | 어린이 음성 복제(reference) | MIT | ✅ **무료** | 로컬/[데모](https://huggingface.co/spaces/ResembleAI/Chatterbox) | [GitHub](https://github.com/resemble-ai/chatterbox) |
| **CosyVoice2** | ✅(9개국어) | instruct 감정 + 복제 | apache-2.0 | ✅ **무료** | 로컬 | [HF](https://huggingface.co/FunAudioLLM/CosyVoice2-0.5B) |
| MeloTTS | ✅ | ❌ 고정 화자(톤 못 바꿈) | MIT | ✅ 무료 | 로컬 | [HF](https://huggingface.co/myshell-ai/MeloTTS-Korean) |
| **Edge TTS** | ✅(품질 좋음) | ❌ 어린이 전용 없음(pitch 흉내) | wrapper GPLv3 | ⚠️ **개인만**(상업=Azure 구독) | [데모](https://huggingface.co/spaces/innoai/Edge-TTS-Text-to-Speech) | [MS Q&A](https://learn.microsoft.com/en-us/answers/questions/2088770/are-opensource-edge-tts-free-for-commercial-use) |
| MiniMax | ✅ | ✅ 어린이 실재(Shy Girl·Enthusiastic Teen) | freemium | ❌ **유료**(무료 5회만) | 온라인 | [사이트](https://www.minimax.io/audio/text-to-speech/korean) |
| ElevenLabs | ✅(네이티브=유료) | 영어권 kid만(한국어 0종) | 상용 | ❌ **유료** | API | 라운드2 기록(ENGINE_NOTES §) |
| Google TTS | ✅ | ❌ 어린이 없음 | 상용 | ❌ **종량제** | API | 현재 폴백 |
| F5-TTS | ⚠️ | 복제 | **CC-BY-NC** | ❌ **상업금지** | 로컬 | [GitHub](https://github.com/SWivid/F5-TTS) |
| IndexTTS-2 | ⚠️ | 감정 복제 | 비상업 | ❌ **상업금지** | [데모](https://huggingface.co/spaces/IndexTeam/IndexTTS-2-Demo) | 라이선스 |

> ⚠️ CosyVoice2·Chatterbox·VoxCPM2의 **한국어 어린이 톤 실제 품질은 미청취** — 들어봐야 앎(아래 실험).

---

## 2. "무료"의 세 등급 (헷갈림 방지)

1. **진짜 무료 = 상업까지 OK** (우리 서비스에 바로 쓸 수 있음)
   → VoxCPM2 · Qwen3 · Chatterbox · CosyVoice2 · MeloTTS. 전부 **로컬 설치**, 추가 비용 0.
2. **체험만 무료 = 상업은 돈** (기준점·비교용으로만)
   → MiniMax(무료 5회), Edge TTS(개인 OK·상업은 Azure 구독).
3. **무료처럼 보이나 라이선스가 막음**
   → F5-TTS(CC-BY-NC), IndexTTS-2(비상업). 데모는 들어볼 수 있어도 **서비스 채택 불가**.

---

## 3. 환주님이 직접 실험할 무료 온라인 데모 (브라우저 클릭, 설치 0)

같은 위로 멘트를 넣고 들어보세요(언어 **Korean**):
> 오늘도 마음이 많이 무거우셨죠. 함께한 시간들은 사라지지 않고 당신 곁에 따뜻하게 남아 있어요.

| 우선 | 데모 | 링크 | 어떻게 |
|:---:|------|------|------|
| 1 | **VoxCPM Demo**(신형·상업무료) | https://huggingface.co/spaces/openbmb/VoxCPM-Demo | 텍스트 앞에 `(a cute little Korean girl, bright and playful)` 같은 **영어 묘사**를 괄호로 + 한국어 본문 |
| 2 | **Chatterbox**(MIT·상업무료) | https://huggingface.co/spaces/ResembleAI/Chatterbox | 어린이 목소리 클립을 reference로 올리면 그 톤 복제 |
| 3 | **Edge TTS**(품질 감만·상업X) | https://huggingface.co/spaces/innoai/Edge-TTS-Text-to-Speech | ko-KR 보이스 선택. 깔끔하지만 어린이 톤은 약함 |
| 참고 | **MiniMax**(기준점·상업유료) | https://www.minimax.io/audio/text-to-speech/korean | 어린이 보이스 "Shy Girl"(여)·"Enthusiastic Teen"(남). "목표 품질" 귀로 정하기 |

> 실험 시 메모: **어린이 느낌 / 발음 자연스러움 / 발랄함** 3개를 ○△✕로. EL 라운드2처럼 블라인드면 더 좋음.

---

## 4. 추천 우선순위 (상업무료 안에서)

1. **VoxCPM2** — 신형·48kHz·나이 묘사 지원, Qwen3가 안 됐던 걸 더 좋은 모델로 재도전. (로컬 설치 완료, 합성 대기)
2. **Chatterbox / CosyVoice2** — VoxCPM2도 별로면, 어린이 음성 **복제(reference)** 로 전환.
3. **최후** — 상업무료에서 어린이 톤이 다 안 되면, 어른 톤은 상업무료로 + 어린이만 별도 검토(데이터 파인튜닝은 비용 큼, 범위 밖).

> ❌ 제외 확정: F5·IndexTTS(상업금지), MiniMax·EL·Google(유료), Edge(상업 회색).
> 윤리: 어린이 목소리도 **보호자 대상 위로 낭독**용. 반려동물 1인칭/부활 ❌. 실제 사람 목소리 복제 시 권리·동의 필요(테스트는 OK).
