"""A 보이스 순수 게인 다운 — 정상 후보(B~E) 음량에 맞춤(품질 손실 0, 가역).

지지직이 '핫한 파일의 재생 과부하'인지 '신호 자체 노이즈'인지 가르는 판별 단계.
스칼라 곱만 하므로 디노이즈/EQ 같은 음질 변형 없음.
실행: conda run --no-capture-output -n qwen3-tts python ai/tts/gain_match.py
출력: _output/typecast/A_fixed/typecast_tc_69c1…_{mk}_gain.wav
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
_TARGET_RMS = 0.06  # 정상 후보(B~E) rms 대역(0.045~0.067)에 맞춤
_PEAK_CEIL = 0.95  # 안전 한도(클리핑 방지)


def main() -> None:
    out = os.path.join(_DIR, "A_fixed")
    os.makedirs(out, exist_ok=True)
    srcs = sorted(glob.glob(os.path.join(_DIR, "_excluded", "typecast_tc_69c1*.wav")))
    print(f"== A 게인 매칭(목표 rms {_TARGET_RMS}) → {out} ==\n")
    for p in srcs:
        x, sr = sf.read(p)
        mono = x.mean(axis=1) if x.ndim > 1 else x
        rms = float(np.sqrt(np.mean(mono ** 2)))
        if rms == 0:
            continue
        gain = _TARGET_RMS / rms
        # 피크가 한도 넘으면 게인을 그만큼 더 줄임(클리핑 방지)
        peak_after = float(np.max(np.abs(x))) * gain
        if peak_after > _PEAK_CEIL:
            gain *= _PEAK_CEIL / peak_after
        y = x * gain
        base = os.path.basename(p).replace(".wav", "_gain.wav")
        dest = os.path.join(out, base)
        sf.write(dest, y, sr)
        print(
            f"saved {base} | gain ×{gain:.3f} | rms {rms:.3f}→{rms*gain:.3f} | "
            f"peak {float(np.max(np.abs(y))):.3f}"
        )
    print("\ndone — A_fixed/ 청취: 지지직 사라지면 음량/재생 문제(이걸로 채택), 남으면 신호 자체")


if __name__ == "__main__":
    main()
