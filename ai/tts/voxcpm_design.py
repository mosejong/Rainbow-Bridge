"""VoxCPM2 Voice Design — 한국어 어린이(여아·남아) 톤 샘플 생성 (스파이크).

Qwen3-TTS 톤이 "별로" 판정 → 신형 VoxCPM2(2026-04, apache-2.0, 48kHz)로 재도전.
Voice Design = 본문 앞 괄호 안에 영어 음색 묘사(나이·성별·톤)를 넣으면 reference 없이 새 목소리 생성.
같은 보호자 위로 멘트(윤리: 1인칭/특정 반려동물 ❌, 톤만 변경)를 어린이 톤으로 합성.

전용 conda 환경에서 실행(파일 직접 — `-m` 금지, ai/tts/__init__.py 가 google-cloud 끌어옴):
    conda run --no-capture-output -n qwen3-tts python ai/tts/voxcpm_design.py
출력:
    ai/tts/_output/voxcpm/voxcpm_{라벨}.wav  → 어린이 톤 청취.
"""

from __future__ import annotations

import os
import sys

# anaconda libiomp5 중복 크래시 우회 (torch import 전).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

_OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_output", "voxcpm")
_MODEL_ID = "openbmb/VoxCPM2"

# 보호자 대상 위로 멘트 — qwen3_design._TEXT 와 동일(엔진 간 공정 비교).
_TEXT = (
    "오늘도 마음이 많이 무거우셨죠. 함께한 시간들은 사라지지 않고 "
    "당신 곁에 따뜻하게 남아 있어요. 너무 자책하지 마시고, "
    "천천히 호흡하며 오늘 하루를 보내셔도 괜찮아요."
)

# (파일라벨, 영어 음색 묘사) — 괄호로 본문 앞에 붙임.
# 밝고 발랄한 톤은 제외하고, 추모 낭독에 맞는 차분한 어린이 톤만 비교한다.
_DESIGNS: tuple[tuple[str, str], ...] = (
    (
        "girl_calm",
        "A calm little Korean girl, soft, warm, gentle, innocent and comforting voice",
    ),
    (
        "girl_whisper",
        "A quiet little Korean girl, very soft, tender, shy and peaceful voice",
    ),
    (
        "girl_warm",
        "A gentle little Korean girl, warm, slow, sincere and soothing voice",
    ),
    (
        "boy_calm",
        "A calm little Korean boy, soft, warm, gentle, innocent and comforting voice",
    ),
    (
        "boy_whisper",
        "A quiet little Korean boy, very soft, tender, shy and peaceful voice",
    ),
    (
        "boy_warm",
        "A gentle little Korean boy, warm, slow, sincere and soothing voice",
    ),
)

# Voice Design 변동성 대비 재현용 시드(고정). 별로면 바꿔서 재생성.
_SEED = 1234


def _load_model():
    import torch
    from voxcpm import VoxCPM

    if torch.cuda.is_available():
        print(f"[gpu] {torch.cuda.get_device_name(0)}")
    else:
        print("[warn] CUDA 사용 불가 → CPU 추론(느림). torch cu128 확인 필요.")
    # load_denoiser=False: 합성 음성은 이미 깨끗 → 디노이저 불필요(속도↑, VRAM↓).
    return VoxCPM.from_pretrained(_MODEL_ID, load_denoiser=False)


def _generate(model, text: str):
    """VoxCPM generate — README 예시 인자. 버전차 대비 kwargs 단계적 축소."""
    last_exc = None
    for kw in (
        dict(cfg_value=2.0, inference_timesteps=10),
        dict(cfg_value=2.0),
        dict(),
    ):
        try:
            return model.generate(text=text, **kw)
        except TypeError as e:
            last_exc = e
            continue
    raise RuntimeError(f"generate 호출 실패(시그니처 불일치): {last_exc}")


def _sample_rate(model) -> int:
    for path in ("tts_model", "model"):
        obj = getattr(model, path, None)
        sr = getattr(obj, "sample_rate", None) if obj is not None else None
        if sr:
            return int(sr)
    sr = getattr(model, "sample_rate", None)
    return int(sr) if sr else 48000  # VoxCPM2 기본 48kHz


def main() -> None:
    import time

    import soundfile as sf
    import torch

    os.makedirs(_OUT_DIR, exist_ok=True)
    print(f"== VoxCPM2 Voice Design 한국어 어린이 샘플 → {_OUT_DIR} ==")
    print(f"텍스트({len(_TEXT)}자): {_TEXT}\n")

    try:
        torch.manual_seed(_SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(_SEED)
    except Exception:
        pass

    model = _load_model()
    sr = _sample_rate(model)
    cuda = torch.cuda.is_available()
    print(f"[sample_rate] {sr}Hz\n")

    tot_infer = 0.0
    tot_audio = 0.0
    n = 0
    for label, design in _DESIGNS:
        dest = os.path.join(_OUT_DIR, f"voxcpm_{label}.wav")
        prompt = f"({design}){_TEXT}"  # 괄호 묘사 + 한국어 본문
        try:
            if cuda:
                torch.cuda.reset_peak_memory_stats()
            t0 = time.perf_counter()
            wav = _generate(model, prompt)
            dt = time.perf_counter() - t0

            if hasattr(wav, "ndim") and wav.ndim > 1:
                wav = wav.squeeze()
            sf.write(dest, wav, sr)

            dur = len(wav) / sr
            rtf = dt / dur if dur else 0.0
            vram = torch.cuda.max_memory_allocated() / 1e9 if cuda else 0.0
            tot_infer += dt
            tot_audio += dur
            n += 1
            print(
                f"saved voxcpm_{label}.wav | 추론 {dt:.1f}s | 오디오 {dur:.1f}s | "
                f"RTF {rtf:.2f} | VRAM peak {vram:.1f}GB | 묘사: {design}"
            )
        except Exception as e:
            print(f"[fail] {label}: {type(e).__name__}: {str(e)[:200]}")

    if n:
        avg_rtf = tot_infer / tot_audio if tot_audio else 0.0
        print(
            f"\n[누적] {n}건 | 총 추론 {tot_infer:.1f}s | 총 오디오 {tot_audio:.1f}s | "
            f"평균 RTF {avg_rtf:.2f}"
        )
    print("done — _output/voxcpm/ 어린이 톤 청취 (Qwen3 와 비교)")


if __name__ == "__main__":
    main()
