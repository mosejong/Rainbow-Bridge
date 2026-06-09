"""고역 EQ 컷(하이쉘프) — '쩅한'(날카로운 고역) 톤다운 후처리.

목소리 높이·속도는 그대로 두고, 고역대(치찰음·쨍함)만 살짝 깎는다.
순수 EQ라 원본은 안 건드리고 새 파일로만 뽑음(가역). RBJ biquad high-shelf.

실행:
  # 0) 대상 파일 먼저 생성 (girl 배치 — qwen3em_girl_read_v9.wav 등 산출)
  conda run --no-capture-output -n qwen3-tts python ai/tts/qwen3_emotion.py --batch girl
  # 1) 강도별 프리셋 한번에(청취 비교용)
  conda run --no-capture-output -n qwen3-tts python ai/tts/tone_down.py
  # 수동 수치 조절: 컷오프Hz 감쇠dB [Q]   (dB는 음수=감쇠)
  conda run --no-capture-output -n qwen3-tts python ai/tts/tone_down.py 4000 -5
  # 다른 파일 지정
  conda run --no-capture-output -n qwen3-tts python ai/tts/tone_down.py 4000 -5 0.707 ai/tts/_output/.../foo.wav
출력: 같은 폴더의 eq/ 하위 — {원본}_eq_fc{fc}_{db}dB.wav
"""

from __future__ import annotations

import os
import sys

import numpy as np
import soundfile as sf
from scipy.signal import lfilter

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

_SRC = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "_output", "qwen3_emotion", "qwen3em_girl_read_v9.wav",
)

# 인자 없을 때 한번에 뽑는 강도별 프리셋: (cutoff Hz, gain dB, Q)
# 살짝 → 중간. 고역 시작점(fc)과 깎는 양(dB)을 달리해 결을 비교.
_PRESETS: tuple[tuple[float, float, float], ...] = (
    (5000, -3, 0.707),   # 아주 살짝(초고역만 -3)
    (4000, -4, 0.707),   # 살짝
    (4000, -6, 0.707),   # 중간
    (3000, -5, 0.707),   # 더 넓게(쨍함 영역 크게)
)


def peaking(x: np.ndarray, sr: int, fc: float, gain_db: float, Q: float = 3.0) -> np.ndarray:
    """RBJ peaking(벨) EQ — 중심 fc 좁은 대역만 감쇠(노치). 협대역 쨍함 타겟용."""
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * fc / sr
    cosw, sinw = np.cos(w0), np.sin(w0)
    alpha = sinw / (2 * Q)
    b = np.array([1 + alpha * A, -2 * cosw, 1 - alpha * A])
    a = np.array([1 + alpha / A, -2 * cosw, 1 - alpha / A])
    b, a = b / a[0], a / a[0]
    if x.ndim > 1:
        return np.stack([lfilter(b, a, x[:, c]) for c in range(x.shape[1])], axis=1)
    return lfilter(b, a, x)


def find_harsh_peak(x: np.ndarray, sr: int, lo: float = 2000, hi: float = 9000) -> float:
    """lo~hi 대역에서 가장 튀는(에너지 최대) 주파수 = 쨍함 후보 중심."""
    mono = x.mean(axis=1) if x.ndim > 1 else x
    spec = np.abs(np.fft.rfft(mono))
    freqs = np.fft.rfftfreq(len(mono), 1 / sr)
    band = (freqs >= lo) & (freqs <= hi)
    fc = float(freqs[band][np.argmax(spec[band])])
    return fc


def high_shelf(x: np.ndarray, sr: int, fc: float, gain_db: float, Q: float = 0.707) -> np.ndarray:
    """RBJ cookbook high-shelf. gain_db<0 이면 fc 위 고역을 감쇠."""
    A = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * fc / sr
    cosw, sinw = np.cos(w0), np.sin(w0)
    alpha = sinw / (2 * Q)
    sa = 2 * np.sqrt(A) * alpha
    b0 = A * ((A + 1) + (A - 1) * cosw + sa)
    b1 = -2 * A * ((A - 1) + (A + 1) * cosw)
    b2 = A * ((A + 1) + (A - 1) * cosw - sa)
    a0 = (A + 1) - (A - 1) * cosw + sa
    a1 = 2 * ((A - 1) - (A + 1) * cosw)
    a2 = (A + 1) - (A - 1) * cosw - sa
    b = np.array([b0, b1, b2]) / a0
    a = np.array([1.0, a1 / a0, a2 / a0])
    if x.ndim > 1:  # 채널별 필터
        return np.stack([lfilter(b, a, x[:, c]) for c in range(x.shape[1])], axis=1)
    return lfilter(b, a, x)


def _read(src: str):
    """입력 wav 읽기 — 없으면 생성 명령 안내 후 종료(no-arg 기본 파일 누락 방지)."""
    if not os.path.exists(src):
        sys.exit(
            f"❌ 입력 없음: {os.path.basename(src)}\n"
            "   먼저 생성: conda run -n qwen3-tts python ai/tts/qwen3_emotion.py --batch girl"
        )
    return sf.read(src)


def process(src: str, fc: float, gain_db: float, Q: float) -> None:
    x, sr = _read(src)
    y = high_shelf(x, sr, fc, gain_db, Q)
    peak = float(np.max(np.abs(y)))
    if peak > 0.999:  # 필터로 약간 솟은 피크만 살짝 정규화(음색 영향 없음)
        y = y * (0.99 / peak)
    out_dir = os.path.join(os.path.dirname(src), "eq")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.basename(src).replace(".wav", f"_eq_fc{int(fc)}_{int(gain_db)}dB.wav")
    dest = os.path.join(out_dir, base)
    sf.write(dest, y, sr)
    print(f"saved {base} | fc={fc}Hz gain={gain_db}dB Q={Q} | peak {peak:.3f}→{float(np.max(np.abs(y))):.3f}")


def process_notch(src: str, fc: float, gain_db: float, Q: float) -> None:
    x, sr = _read(src)
    y = peaking(x, sr, fc, gain_db, Q)
    peak = float(np.max(np.abs(y)))
    if peak > 0.999:
        y = y * (0.99 / peak)
    out_dir = os.path.join(os.path.dirname(src), "eq")
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.basename(src).replace(".wav", f"_notch_fc{int(fc)}_{int(gain_db)}dB_Q{Q}.wav")
    dest = os.path.join(out_dir, base)
    sf.write(dest, y, sr)
    print(f"saved {base} | notch fc={fc:.0f}Hz gain={gain_db}dB Q={Q} | peak {peak:.3f}")


def main() -> None:
    args = sys.argv[1:]
    # 노치 스윕 모드: notch [파일]  — 3~7kHz 대역별 노치를 깔아 쨍한 대역을 청취로 짚기
    if args and args[0] == "notch":
        src = args[1] if len(args) > 1 else _SRC
        print("== 노치 스윕 → 대역별 -12dB Q3 (쨍함 빠지는 fc 청취로 찾기) ==")
        print(f"원본: {os.path.basename(src)}\n")
        for fc in (3000, 4000, 5000, 6000, 7000):
            process_notch(src, fc, -12, 3.0)
        print("\ndone — 어느 fc 가 쨍함 잡는지 청취 → 그 fc 로 미세조정:")
        print("  python ai/tts/tone_down.py notch1 <fc> <dB> <Q>")
        return
    # 노치 단일: notch1 fc dB Q [파일]
    if args and args[0] == "notch1":
        fc = float(args[1])
        gain_db = float(args[2]) if len(args) > 2 else -12.0
        Q = float(args[3]) if len(args) > 3 else 3.0
        src = args[4] if len(args) > 4 else _SRC
        print(f"== 노치 단일 fc={fc:.0f}Hz ==")
        process_notch(src, fc, gain_db, Q)
        return
    # 수동: fc dB [Q] [파일]
    if args and args[0].replace(".", "").isdigit():
        fc = float(args[0])
        gain_db = float(args[1]) if len(args) > 1 else -5.0
        Q = float(args[2]) if len(args) > 2 else 0.707
        src = args[3] if len(args) > 3 else _SRC
        print(f"== 수동 EQ → {os.path.join(os.path.dirname(src), 'eq')} ==")
        process(src, fc, gain_db, Q)
    else:
        src = args[0] if args else _SRC
        print(f"== 강도별 프리셋 {len(_PRESETS)}종 → {os.path.join(os.path.dirname(src), 'eq')} ==")
        print(f"원본: {os.path.basename(src)}\n")
        for fc, db, Q in _PRESETS:
            process(src, fc, db, Q)
    print("\ndone — eq/ 폴더 청취. 맘에 드는 fc·dB 확정되면 그 값으로 재실행.")


if __name__ == "__main__":
    main()
