"""앵커 대비 A/B 청취 — 혼자 들어도 믿을 만한 평가.

왜: 혼자 1~5점 매기기는 노이즈가 크다(기준이 머릿속에만 있어 흔들림). "둘 중
어느 게 더 위로되나?"처럼 **2개를 직접 비교**하면 훨씬 일관되고 쉽다. 그래서
모든 후보를 **현행 Google warm(앵커)** 와 1:1로 붙인다. 답해야 할 진짜 질문은
"지금 쓰는 것보다 명확히 나은 게 있나?" 하나뿐이고, 이 방식이 거기에 바로 답한다.

핵심 마음가짐(꼭): 목표는 **정밀한 점수**가 아니라 **차이가 있으면 잡아내기**다.
들어봐서 **구분이 안 되면 그게 결론**이다(= 엔진이 비슷 → 가격·라이선스로 결정).
확신 가는 판단("이건 확 와닿네 / 이건 로봇 같네")만 믿으면 된다. 통계 필요 없음.

동작:
    앵커 = _output/compare_google_warm.mp3 (현행 주력 톤).
    후보 = 나머지 모든 비교 샘플. 각 후보를 앵커와 한 쌍으로 만든다.
    각 쌍은 A/B 좌우를 seed 로 섞어(어느 쪽이 앵커인지 모르게) 복사:
        _output/pairs/pair_01_A.mp3 / pair_01_B.mp3
    정답키 _output/pairs/_PAIRS_KEY.json + 빈 평가지 PAIRS_SHEET.md 생성.

실행:
    python -m ai.tts.pairwise_listen          # 최초
    python -m ai.tts.pairwise_listen --force  # 후보 추가 후 재생성(평가지 덮어씀)

평가:
    pair_01_A ↔ pair_01_B 둘 다 듣고 "어느 게 더 위로되나" 한 칸만 고른다.
    다 채운 뒤 _PAIRS_KEY.json + 평가지를 클로드에게 주면 집계해준다.
    → 집계는 정직하게: 명확한 승 / 무승부 / 구분 불가 로만 보고(노이즈로 순위 안 지어냄).
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import sys

from .blind_listen import _collect_candidates, _source_label
from .compare_elevenlabs import _SAMPLE_TEXT
from .tts import _OUTPUT_DIR

# Windows 콘솔(cp949)에서 한글 출력 깨짐/크래시 방지.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

_PAIRS_DIR = os.path.join(_OUTPUT_DIR, "pairs")
_KEY_PATH = os.path.join(_PAIRS_DIR, "_PAIRS_KEY.json")
_SHEET_PATH = os.path.join(_PAIRS_DIR, "PAIRS_SHEET.md")

# 앵커 = 현행 주력 톤(Google warm). 모든 후보를 이것과 비교.
_ANCHOR_STEM = "compare_google_warm"
_SEED = 20260607


def _write_sheet(n: int) -> None:
    rows = "\n".join(f"| pair_{i:02d} |  |  |" for i in range(1, n + 1))
    content = f"""# A/B 청취 평가지 — 현행(앵커)과 1:1 비교

> 멘트(전 샘플 동일):
> "{_SAMPLE_TEXT}"

## 🛟 마음 편히 (꼭 읽기)

- **이 평가로 잘못된 결론이 팀에 가지 않습니다.** 클로드가 애매한 건 "애매함"으로만 보고하고,
  엔진 확정은 사람 점수가 **명확할 때만** 합니다. **느낀 대로만 고르면 되고, 틀릴 수가 없습니다.**
- 목표는 **정밀 점수가 아니라 "차이가 있으면 잡아내기"**.
- 둘 다 듣고 **구분이 안 되면 → "비슷"**. 그게 정상이고, 그것도 결론임.
- 확신 가는 것만 "A"/"B". 억지로 차이 만들지 말 것. **자신 없으면 다시 들어도 됩니다.**

## 방법

1. `pair_01_A.mp3` 듣고 → `pair_01_B.mp3` 듣고 → **어느 게 더 위로되나** 한 칸 고름.
2. 한쪽이 확 **로봇 같으면** 메모 칸에 적기("B가 기계음" 등).
3. `pair_02` … 끝까지. 어느 쪽이 현행인지 몰라도 됨(섞여 있음).

| 페어 | 더 위로되는 쪽 (A / 비슷 / B) | 한쪽이 로봇 같나(메모) | 코멘트 |
|------|:----------------------------:|:----------------------:|--------|
{rows}

---

다 채운 뒤 `_PAIRS_KEY.json` 과 이 표를 **클로드에게 그대로** 주세요.
각 페어에서 "현행 대비 후보가 이김/비슷/짐"으로 집계해, **명확한 승 / 무승부 / 구분 불가**만
정직하게 보고합니다. (애매한 건 억지 순위 안 매김 — 그러니 "잘못 평가할" 일이 없습니다.)
"""
    with open(_SHEET_PATH, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description="앵커 대비 A/B 청취")
    parser.add_argument(
        "--force",
        action="store_true",
        help="기존 pairs/ 를 지우고 재생성(평가지 덮어씀 — 채운 내용 사라짐)",
    )
    args = parser.parse_args()

    candidates = _collect_candidates()
    anchor = next((p for p in candidates if _source_label(p) == _ANCHOR_STEM), None)
    if anchor is None:
        print(
            f"[중단] 앵커 '{_ANCHOR_STEM}.mp3' 없음. 먼저 "
            f"`python -m ai.tts.compare_elevenlabs` 로 Google 샘플을 생성하세요."
        )
        return
    others = [p for p in candidates if p is not anchor]
    if not others:
        print("[중단] 비교할 후보가 없음(앵커뿐). 다른 엔진 샘플을 먼저 생성하세요.")
        return

    if os.path.isdir(_PAIRS_DIR) and os.listdir(_PAIRS_DIR):
        if not args.force:
            print(
                f"[중단] {_PAIRS_DIR} 가 이미 있음. 평가 중일 수 있어 보호합니다.\n"
                f"        후보를 추가해 다시 만들려면 --force 로 재실행하세요."
            )
            return
        shutil.rmtree(_PAIRS_DIR)
    os.makedirs(_PAIRS_DIR, exist_ok=True)

    key: dict[str, dict[str, str]] = {}
    for i, cand in enumerate(others, start=1):
        # 앵커를 A/B 어느 쪽에 둘지 페어마다 섞음(좌우 편향 제거).
        anchor_is_a = random.Random(_SEED + i).random() < 0.5
        a_src, b_src = (anchor, cand) if anchor_is_a else (cand, anchor)
        shutil.copy(a_src, os.path.join(_PAIRS_DIR, f"pair_{i:02d}_A.mp3"))
        shutil.copy(b_src, os.path.join(_PAIRS_DIR, f"pair_{i:02d}_B.mp3"))
        key[f"pair_{i:02d}"] = {
            "A": _source_label(a_src),
            "B": _source_label(b_src),
            "anchor_side": "A" if anchor_is_a else "B",
        }

    with open(_KEY_PATH, "w", encoding="utf-8") as f:
        json.dump(key, f, ensure_ascii=False, indent=2)
    _write_sheet(len(others))

    print(f"== A/B 페어 {len(others)}개 → {_PAIRS_DIR} ==")
    print(f"  앵커(현행): {_ANCHOR_STEM}  (각 페어에 좌우 섞여 들어감)")
    print(f"  평가지: {_SHEET_PATH}")
    print(f"  정답키: {_KEY_PATH}  (평가 끝나기 전엔 열지 마세요)")
    print("\npair_01_A ↔ pair_01_B 듣고 더 위로되는 쪽 고르기 → PAIRS_SHEET.md 채우기.")


if __name__ == "__main__":
    main()
