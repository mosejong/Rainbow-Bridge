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

- 현재 톤(`TtsTone`, [tts.py](tts.py)): `female`·`male`·`narration` **3종 고정** (2026-06-11 확정).
- **톤은 발화 속도·피치(`_TONE_MAP`)와 목소리(`_TONE_VOICE`)를 함께 결정.**
  - `female` → `female_a`(ko-KR-Neural2-A), 1인칭 여성
  - `male` → `male_c`(ko-KR-Neural2-C), 1인칭 남성
  - `narration` → `female_b`(ko-KR-Neural2-B), 3인칭 나레이션 — female_a와 목소리 구별
- Qwen3 서버 연결 시: `female`→girl / `male`→boy / `narration`→woman (seed 21424, atempo=0.9).
- 기본 톤: `narration` (3인칭 편지가 먼저 나옴).

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
