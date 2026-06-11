# CLAUDE.md — TTS 영역 (`ai/tts/`)

> 담당: **정환주**. 상위 [../CLAUDE.md](../CLAUDE.md) 규칙을 따르며 TTS 영역만 보완합니다.
> 할 일: [../TODO.md](../TODO.md) `ai/tts` 블록 · 역할: [../ROLES.md](../ROLES.md).

---

## 1. 담당 범위

- MVP ④ 음성 톤 선택 + TTS 낭독.

---

## 2. 인터페이스

- `synthesize(text, tone) -> {audio_path|bytes, duration, format}`
- 긴 텍스트 분할·합치기 처리, 한국어 발음·억양 품질 점검.

---

## 3. 톤 매핑

- 메시지 톤(반소람 ③)과 **1:1 매핑 테이블** — 반소람과 합의해 고정.
- 현재 톤(`TtsTone`, [tts.py](tts.py)): `warm`·`calm`·`hopeful`·`soft`·`male`·`narration`.
- **톤은 발화 속도·피치(`_TONE_MAP`)만 바꿈.** 목소리(성별)는 `_TONE_VOICE`로 따로 매핑.
  - `male`·`narration` → 남성 목소리(`male_c`=ko-KR-Neural2-C).
  - 그 외 톤은 매핑 없음 → 기본 목소리(`_VOICE_NAME`, 여성) 유지(하위호환).
  - ⚠️ 과거 버그: tone만 바꾸고 voice를 안 주면 `_resolve_voice`가 무조건 여성으로 폴백 → `_TONE_VOICE` + `_resolve_voice(voice, tone)`로 해결(2026-06-11).
  - 호출부에서 `voice`를 명시하면 그게 톤 기본보다 우선.

---

## 4. GPU 운영 (8GB)

- **온디맨드 로딩**: 쓸 때 로드, 끝나면 종료해 VRAM 회수.
- LLM 서버가 상시 구동 중이라 동시 사용 빡빡 → [../GPU_SERVER.md](../GPU_SERVER.md) 예산 참고.

---

## 5. 출력 / 보안

- 출력은 백엔드 `MediaAsset` 형태로 합의.
- 🚫 음성 파일은 git 미포함(.gitignore).
- 음성도 **보호자 대상 위로 낭독** — 반려동물 목소리 흉내 ❌.

---

## 6. 엔진 후기

- TTS 엔진을 비교하면 장단점·한국어 품질을 이 폴더에 기록(또는 형식은 [../llm/MODEL_NOTES.md](../llm/MODEL_NOTES.md) 참고).
</content>
