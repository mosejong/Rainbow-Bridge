"""TTS 발음 명료도 객관 분석 — faster-whisper STT 로 mp3 받아쓰기 → 원문 대비 CER.

CER(글자 오류율, 낮을수록 좋음)= STT 가 얼마나 정확히 알아들었나 = 발음 또렷함의
객관 지표. 같은 모델로 전부 받아쓰므로 파일 간 상대 비교는 공정.
※ 감정·자연스러움은 STT 로 측정 불가(주관 청취 필요). 발음/명료도만 잰다.

실행: python -m ai.tts.analyze_stt   (GPU 자동, 실패 시 CPU 폴백)
"""

from __future__ import annotations

import glob
import os
import re
import sys
import unicodedata

# conda OpenMP 런타임 중복 충돌 회피(ctranslate2/numpy 동시 로드 시).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# Windows: ctranslate2(GPU)가 pip 설치한 cuDNN/cuBLAS DLL 을 찾도록 검색경로 등록.
# (faster_whisper import 전에 실행돼야 함)
if sys.platform == "win32":
    import sysconfig

    _nv = os.path.join(sysconfig.get_paths()["purelib"], "nvidia")
    for _sub in ("cudnn", "cublas", "cuda_nvrtc", "cuda_runtime"):
        _p = os.path.join(_nv, _sub, "bin")
        if os.path.isdir(_p):
            os.add_dll_directory(_p)

from .compare_elevenlabs import _COMPARE_DIR, _SAMPLE_TEXT
from .tts import _OUTPUT_DIR

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

_MODEL = os.environ.get("WHISPER_MODEL", "large-v3")
# RTX 5060(sm_120) 등 신형 GPU 에서 ctranslate2 가 hang/크래시하면 cpu 로 강제.
_DEVICE = os.environ.get("WHISPER_DEVICE", "cuda")


def _norm(s: str) -> str:
    """공백·문장부호 제거 + NFC 정규화 → 음운 글자열만 비교."""
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"[\s\W_]+", "", s)


def _levenshtein(a: str, b: str) -> int:
    m, n = len(a), len(b)
    if m == 0:
        return n
    if n == 0:
        return m
    prev = list(range(n + 1))
    for i in range(1, m + 1):
        cur = [i] + [0] * n
        ai = a[i - 1]
        for j in range(1, n + 1):
            cost = 0 if ai == b[j - 1] else 1
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost)
        prev = cur
    return prev[n]


def _cer(ref: str, hyp: str) -> float:
    r, h = _norm(ref), _norm(hyp)
    if not r:
        return 0.0
    return _levenshtein(r, h) / len(r)


def _load_model():
    from faster_whisper import WhisperModel

    if _DEVICE == "cpu":
        model = WhisperModel(_MODEL, device="cpu", compute_type="int8")
        print(f"모델 {_MODEL} (CPU/int8) 로드", flush=True)
        return model
    try:
        model = WhisperModel(_MODEL, device="cuda", compute_type="float16")
        print(f"모델 {_MODEL} (GPU/float16) 로드", flush=True)
        return model
    except Exception as exc:
        print(f"[warn] GPU 로드 실패 → CPU 폴백: {exc}", flush=True)
        model = WhisperModel(_MODEL, device="cpu", compute_type="int8")
        print(f"모델 {_MODEL} (CPU/int8) 로드", flush=True)
        return model


def _transcribe(model, path: str) -> str:
    segments, _info = model.transcribe(path, language="ko", beam_size=5)
    return "".join(seg.text for seg in segments).strip()


def main() -> None:
    files: list[tuple[str, str]] = []
    for p in sorted(glob.glob(os.path.join(_COMPARE_DIR, "el_*.mp3"))):
        files.append(("ElevenLabs", p))
    for p in sorted(glob.glob(os.path.join(_OUTPUT_DIR, "compare_google_*.mp3"))):
        files.append(("Google", p))

    if not files:
        print("분석할 mp3 없음 → 먼저 `python -m ai.tts.compare_elevenlabs` 실행")
        return

    print(f"원문: {_SAMPLE_TEXT}\n")
    model = _load_model()
    print()

    rows = []
    for engine, path in files:
        name = os.path.basename(path)
        try:
            hyp = _transcribe(model, path)
            cer = _cer(_SAMPLE_TEXT, hyp)
            rows.append((engine, name, cer, hyp))
            print(f"[{engine}] {name}  CER={cer:.1%}\n   받아쓰기: {hyp}")
        except Exception as exc:
            print(f"[warn] {name} 분석 실패: {exc}")

    rows.sort(key=lambda r: r[2])
    print("\n== 발음 명료도 순위 (CER 낮을수록 또렷) ==")
    for engine, name, cer, _ in rows:
        print(f"  {cer:6.1%}  [{engine:10}] {name}")


if __name__ == "__main__":
    main()
