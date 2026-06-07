"""블라인드 청취 하네스 — 라벨 가리고 사람이 직접 듣는다.

왜: 기존 TTS 비교는 CER(STT 받아쓰기 정확도)·Gemini 자동평가로 결론냈는데,
둘 다 "추모 영상에서 감정이 전달되느냐"를 못 잰다. TTS는 **사람이 직접 듣고
느낀 게 전부**다. 그래서 이 스크립트는 음질을 판정하지 *않는다*. 단지
엔진 라벨을 가려서(sample_01, sample_02 …) 듣는 사람이 선입견 없이 점수만
매기게 돕는다.

동작:
    1) _output/compare_google_*.mp3 + _output/compare/*.mp3 를 후보로 모은다.
    2) seed 고정 셔플로 _output/blind/sample_01.mp3 … 로 복사(순서로 정체 추정 불가).
    3) 정답키 _output/blind/_KEY.json (sample_NN → 원본) — 평가 끝나기 전엔 안 본다.
    4) 빈 평가지 _output/blind/RATING_SHEET.md 생성(자연스러움/감정전달/기계음).

실행:
    python -m ai.tts.blind_listen          # 최초 생성
    python -m ai.tts.blind_listen --force  # 샘플 추가 후 재셔플(평가지 덮어씀)

평가:
    sample_01 부터 순서대로 들으며 RATING_SHEET.md 채움 → 다 채운 뒤에만
    _KEY.json 열어 정체 확인 → 집계. (라운드2: el_ko_* 한국어 샘플을
    _output/compare/ 에 넣고 --force 로 재실행하면 자동 포함.)

⚠️ 주력 평가는 [pairwise_listen.py](현행 Google warm과 1:1 A/B) — 혼자 평가에 더 믿을 만함.
   이 블라인드(절대점수)는 보조.

⚠️ _output/ 는 .gitignore 됨 → blind/ 산출물도 git 미커밋(로컬 청취용).
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import random
import shutil
import sys

from .compare_elevenlabs import _SAMPLE_TEXT
from .tts import _OUTPUT_DIR

# Windows 콘솔(cp949)에서 한글 출력 깨짐/크래시 방지.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

_COMPARE_DIR = os.path.join(_OUTPUT_DIR, "compare")
_BLIND_DIR = os.path.join(_OUTPUT_DIR, "blind")
_KEY_PATH = os.path.join(_BLIND_DIR, "_KEY.json")
_SHEET_PATH = os.path.join(_BLIND_DIR, "RATING_SHEET.md")

# 재현용 고정 seed (시각·Math.random 의존 금지 — 같은 입력이면 같은 셔플).
_SEED = 20260607


def _collect_candidates() -> list[str]:
    """후보 mp3 경로 목록. Google 베이스라인 + compare/ 의 모든 엔진 샘플.

    _output/tts_*.mp3 같은 단편 테스트 파일은 제외(비교 대상 아님).
    """
    files = sorted(glob.glob(os.path.join(_OUTPUT_DIR, "compare_google_*.mp3")))
    files += sorted(glob.glob(os.path.join(_COMPARE_DIR, "*.mp3")))
    return files


def _source_label(path: str) -> str:
    """정답키용 원본 식별자 — 파일명 stem 그대로(엔진 추측 안 하고 정직하게)."""
    return os.path.splitext(os.path.basename(path))[0]


def _write_rating_sheet(n: int) -> None:
    rows = "\n".join(f"| sample_{i:02d} |  |  |  |  |" for i in range(1, n + 1))
    content = f"""# 블라인드 청취 평가지 — 라벨 가린 TTS 비교

> 멘트(전 샘플 동일):
> "{_SAMPLE_TEXT}"

> 🚨 **해석 주의 (꼭 읽기):**
> - 샘플 중엔 **ElevenLabs 영어권 보이스로 한국어를 읽힌 핸디캡 샘플**이 섞여 있을 수 있다.
>   한국어 억양이 어색하면 **엔진이 나빠서가 아니라 보이스 핸디캡**일 수 있으니 코멘트에 적을 것.
> - **EL 한국어 웹 샘플이 아직 없는 라운드면, 이 평가는 "결론"이 아니라
>   "정식 테스트에 투자할 가치가 있나" 보는 sanity check다.** 여기서 Google이 1등이어도 확정 아님.
>   진짜 결론은 EL 한국어 보이스까지 넣은 라운드에서 난다.

## 척도 (1~5, 높을수록 좋음)

- **자연스러움**: 진짜 사람 목소리에 가까운가
- **감정전달**: 추모·위로 상황에서 마음이 닿는가 ← **가장 중요**
- **기계음**: 5 = 전혀 기계 같지 않음 / 1 = 완전 로봇

## 평가 (sample_01 부터 순서대로, 라벨 모른 채 채울 것)

| 샘플 | 자연스러움 | 감정전달 | 기계음 | 코멘트 |
|------|:---------:|:-------:|:------:|--------|
{rows}

---

다 채운 **뒤에만** `_KEY.json` 을 열어 각 샘플의 정체(엔진)를 확인하고 집계하세요.
순서로 정체를 추측하지 마세요 — seed 셔플이라 의미 없습니다.
"""
    with open(_SHEET_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="블라인드 청취 하네스")
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 blind/ 를 지우고 재셔플(평가지 덮어씀 — 채운 내용 사라짐)",
    )
    args = parser.parse_args()

    candidates = _collect_candidates()
    if not candidates:
        print(
            f"[중단] 후보 mp3 없음. 먼저 `python -m ai.tts.compare_elevenlabs` 로 "
            f"샘플을 생성하세요. (찾은 위치: {_OUTPUT_DIR})"
        )
        return

    if os.path.isdir(_BLIND_DIR) and os.listdir(_BLIND_DIR):
        if not args.force:
            print(
                f"[중단] {_BLIND_DIR} 가 이미 있음. 평가 중일 수 있어 보호합니다.\n"
                f"        샘플을 추가해 다시 셔플하려면 --force 로 재실행하세요."
            )
            return
        shutil.rmtree(_BLIND_DIR)

    os.makedirs(_BLIND_DIR, exist_ok=True)

    # seed 고정 셔플 — 전역 random 안 건드리게 별도 인스턴스.
    order = candidates[:]
    random.Random(_SEED).shuffle(order)

    key: dict[str, str] = {}
    for i, src in enumerate(order, start=1):
        name = f"sample_{i:02d}.mp3"
        shutil.copy(src, os.path.join(_BLIND_DIR, name))
        key[f"sample_{i:02d}"] = _source_label(src)

    with open(_KEY_PATH, "w", encoding="utf-8") as f:
        json.dump(key, f, ensure_ascii=False, indent=2)

    _write_rating_sheet(len(order))

    print(f"== 블라인드 샘플 {len(order)}개 → {_BLIND_DIR} ==")
    print(f"  평가지: {_SHEET_PATH}")
    print(f"  정답키: {_KEY_PATH}  (평가 끝나기 전엔 열지 마세요)")
    print("\nsample_01 부터 순서대로 듣고 RATING_SHEET.md 를 채우세요.")


if __name__ == "__main__":
    main()
