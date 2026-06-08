"""Qwen3-TTS VoiceDesign — 한국어 '발랄·귀여운·어린아이' 톤 샘플 생성 (스파이크).

EL Voice Library 에 한국어 어린아이 보이스가 없어(§6, ENGINE_NOTES) 대안으로
Qwen3-TTS-1.7B-VoiceDesign 을 로컬에서 돌려 `instruct` 자연어로 원하는 음색을
직접 설계한다. 같은 보호자 위로 멘트(윤리: 1인칭/특정 반려동물 ❌)를 톤만 바꿔 합성.

전용 conda 환경에서 실행:
    conda run -n qwen3-tts python -m ai.tts.qwen3_design
출력:
    ai/tts/_output/qwen3_{라벨}.wav  → EL JY·Annie 와 직접 A/B.
"""

from __future__ import annotations

import os
import sys

# anaconda libiomp5 중복 크래시 우회 (torch import 전에 설정).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

# 경로 독립 계산 (compare_elevenlabs/tts.py 는 google-cloud 의존 → qwen 환경에서 import 금지).
_OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_output", "qwen3")

_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"

# 보호자 대상 위로 멘트 — compare_elevenlabs._SAMPLE_TEXT 와 동일 텍스트(비교 공정).
_TEXT = (
    "오늘도 마음이 많이 무거우셨죠. 함께한 시간들은 사라지지 않고 "
    "당신 곁에 따뜻하게 남아 있어요. 너무 자책하지 마시고, "
    "천천히 호흡하며 오늘 하루를 보내셔도 괜찮아요."
)

# (파일라벨, instruct) — 합격한 child(어린아이) 느낌 계승 + 남자아이 변형 3종.
# 기존 balbal/cute/child wav 는 _output/qwen3 에 그대로 둠(안 지움). 이번엔 남자아이만 새로.
_DESIGNS: tuple[tuple[str, str], ...] = (
    ("boy", "A playful, childlike, innocent voice like a cheerful little boy"),
    ("boy_bright", "A bright, energetic, playful little boy voice, cheerful and lively"),
    ("boy_soft", "A soft, gentle, innocent little boy voice, calm and tender"),
)


def _load_model():
    import torch
    from qwen_tts import Qwen3TTSModel

    if not torch.cuda.is_available():
        print("[warn] CUDA 사용 불가 → CPU 추론(느림). torch cu128 설치 확인 필요.")
        device, dtype, attn = "cpu", torch.float32, None
    else:
        print(f"[gpu] {torch.cuda.get_device_name(0)}")
        device, dtype, attn = "cuda:0", torch.bfloat16, None  # flash-attn 미설치 → 기본

    kwargs = dict(device_map=device, dtype=dtype)
    if attn:
        kwargs["attn_implementation"] = attn
    return Qwen3TTSModel.from_pretrained(_MODEL_ID, **kwargs)


def _generate(model, text: str, instruct: str):
    """VoiceDesign 합성. 패키지 버전별 메서드명 차이 방어."""
    last_exc = None
    for method in ("generate_voice_design", "generate_custom_voice"):
        fn = getattr(model, method, None)
        if fn is None:
            continue
        for kw in (
            dict(text=text, language="korean", instruct=instruct),
            dict(text=text, language="korean", speaker="default", instruct=instruct),
        ):
            try:
                return fn(**kw)
            except TypeError as e:
                last_exc = e
                continue
    raise RuntimeError(f"VoiceDesign 호출 실패(메서드/시그니처 불일치): {last_exc}")


def main() -> None:
    import time

    import soundfile as sf
    import torch

    os.makedirs(_OUT_DIR, exist_ok=True)
    print(f"== Qwen3-TTS VoiceDesign 한국어 샘플 → {_OUT_DIR} ==")
    print(f"텍스트({len(_TEXT)}자): {_TEXT}\n")
    model = _load_model()
    cuda = torch.cuda.is_available()

    tot_infer = 0.0  # 누적 추론시간(s)
    tot_audio = 0.0  # 누적 오디오 길이(s)
    n = 0
    for label, instruct in _DESIGNS:
        dest = os.path.join(_OUT_DIR, f"qwen3_{label}.wav")
        try:
            if cuda:
                torch.cuda.reset_peak_memory_stats()
            t0 = time.perf_counter()
            out = _generate(model, _TEXT, instruct)
            dt = time.perf_counter() - t0

            wavs, sr = out if isinstance(out, tuple) else (out, 24000)
            wav = wavs[0] if hasattr(wavs, "__len__") and not hasattr(wavs, "ndim") else wavs
            sf.write(dest, wav, sr)

            dur = len(wav) / sr
            rtf = dt / dur if dur else 0.0
            vram = torch.cuda.max_memory_allocated() / 1e9 if cuda else 0.0
            audio_tok = int(dur * 12)  # 12Hz 코덱 → 오디오 토큰 ≈ 길이×12 (추정)
            tot_infer += dt
            tot_audio += dur
            n += 1
            print(
                f"saved qwen3_{label}.wav | 추론 {dt:.1f}s | 오디오 {dur:.1f}s | "
                f"RTF {rtf:.2f} | VRAM peak {vram:.1f}GB | "
                f"텍스트 {len(_TEXT)}자 | 오디오토큰 ~{audio_tok}(추정,12Hz)"
            )
        except Exception as e:
            print(f"[fail] {label}: {type(e).__name__}: {str(e)[:200]}")

    if n:
        avg_rtf = tot_infer / tot_audio if tot_audio else 0.0
        print(
            f"\n[누적 리소스] {n}건 | 총 추론 {tot_infer:.1f}s | 총 오디오 {tot_audio:.1f}s | "
            f"평균 RTF {avg_rtf:.2f} | 총 오디오토큰 ~{int(tot_audio * 12)}(추정)"
        )
    print("done — _output/qwen3/ 남자아이 청취 (qwen3_child 와 비교)")


if __name__ == "__main__":
    main()
