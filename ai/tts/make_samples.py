"""TTS 실패 대비 샘플 mp3 생성 — GCP 키 있을 때 1회 실행.

각 톤별 **보호자 대상 일반 위로 멘트**를 합성해
`ai/tts/_samples/fallback_{tone}.mp3` 로 저장한다. 합성이 실패하는 상황
(키 없음·할당량 초과·네트워크 장애·데모 오프라인)에서 `synthesize()` 가
이 파일들로 폴백해 데모가 에러로 끊기지 않게 한다.

⚠️ 윤리: 특정 반려동물·1인칭 ❌. 보호자 대상 일반 안내 멘트만.
⚠️ 음성 파일은 .gitignore — 커밋 안 됨(각자 로컬 생성).

실행:
    python -m ai.tts.make_samples
필요:
    GOOGLE_APPLICATION_CREDENTIALS (서비스 계정 키) 설정.
"""

from __future__ import annotations

import os
import shutil

from .tts import _SAMPLE_DIR, TtsTone, synthesize

# 보호자 대상 일반 위로 멘트(특정 반려동물 언급·1인칭 ❌).
_FALLBACK_TEXT = "잠시 후 다시 들려드릴게요. 천천히 호흡하며 기다려 주세요."


def main() -> None:
    os.makedirs(_SAMPLE_DIR, exist_ok=True)
    for tone in TtsTone:
        result = synthesize(_FALLBACK_TEXT, tone)
        dest = os.path.join(_SAMPLE_DIR, f"fallback_{tone.value}.mp3")
        shutil.copyfile(result["audio_path"], dest)
        print(f"saved {dest} ({result['duration']}s)")
    print(f"done — {len(TtsTone)}개 샘플 → {_SAMPLE_DIR}")


if __name__ == "__main__":
    main()
