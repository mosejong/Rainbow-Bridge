"""Typecast 합성본 노이즈/클리핑 진단 — A(지지직 보고) vs 정상 후보 비교.

지지직 원인 후보: ① 디지털 클리핑(볼륨 과다) ② 모델 아티팩트(고주파 글리치)
③ 코덱/샘플레이트. 객관 지표로 어느 쪽인지 가른다.
실행: conda run --no-capture-output -n qwen3-tts python ai/tts/analyze_noise.py
"""

from __future__ import annotations

import glob
import os
import sys

import numpy as np
import soundfile as sf

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_output", "typecast")


def stat(p: str) -> None:
    x, sr = sf.read(p)
    if x.ndim > 1:
        x = x.mean(axis=1)
    peak = float(np.max(np.abs(x)))
    clip = float(np.mean(np.abs(x) >= 0.999))  # 풀스케일 도달 비율
    near = float(np.mean(np.abs(x) >= 0.95))  # 거의 풀스케일
    d = np.abs(np.diff(x))
    glitch = float(np.mean(d > 0.3))  # 인접 샘플 급변(지지직/클릭)
    rms = float(np.sqrt(np.mean(x ** 2)))
    crest = peak / rms if rms else 0.0  # 크레스트 팩터(낮으면 압축/클리핑 의심)
    print(
        f"{os.path.basename(p):54s} sr={sr} peak={peak:.4f} "
        f"clip%={clip*100:.3f} near95%={near*100:.3f} "
        f"glitch%={glitch*100:.3f} rms={rms:.4f} crest={crest:.2f}"
    )


def main() -> None:
    if len(sys.argv) > 1:  # 인자로 받은 glob 들만 측정
        for pat in sys.argv[1:]:
            for p in sorted(glob.glob(pat)):
                stat(p)
        return
    print("=== A (tc_69c1… · 지지직 보고) — _excluded ===")
    for p in sorted(glob.glob(os.path.join(_DIR, "_excluded", "typecast_tc_69c1*.wav"))):
        stat(p)
    print("\n=== refine (재합성 조합) ===")
    for p in sorted(glob.glob(os.path.join(_DIR, "refine", "*.wav"))):
        stat(p)
    print("\n=== 정상 후보 비교 (B: tc_66596206…) ===")
    for p in sorted(glob.glob(os.path.join(_DIR, "typecast_tc_66596206*.wav"))):
        stat(p)
    print(
        "\n해석: clip%·near95%·glitch% 가 A에서 정상 대비 크게 높으면 → 볼륨/클리핑 문제"
        "(target_lufs·volume 낮춰 재합성). glitch만 높고 clip 정상이면 → 모델 아티팩트"
        "(ssfm-v21·seed 변경). 둘 다 정상이면 → 코덱/재생기 의심."
    )


if __name__ == "__main__":
    main()
