"""레인보우브릿지 Google Cloud TTS 튜닝 데모 — voice/속도/피치 직접 조절.

3인칭(메시지 읽어주기)용 성인 목소리를 직접 돌려보며 음색을 고른다.
Qwen3 어린아이 데모(qwen3_webui.py, 8000)와 별개. Google은 클라우드라 GPU 무관
→ Qwen3 데모와 동시에 띄워도 VRAM 영향 없음.

실행:
    conda run --no-capture-output -n qwen3-tts python ai/tts/google_webui.py
→ 브라우저 http://127.0.0.1:8002
필요: GOOGLE_APPLICATION_CREDENTIALS (.env, 인증키 json). 상대경로면 자동 보정.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# .env 의 GOOGLE_APPLICATION_CREDENTIALS 로드 + 상대경로 → 절대경로 보정.
_ROOT = Path(__file__).resolve().parents[2]
try:
    from dotenv import load_dotenv

    load_dotenv(_ROOT / ".env")
except Exception:
    pass
_cred = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if _cred and not os.path.isabs(_cred):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str((_ROOT / _cred).resolve())

import gradio as gr  # noqa: E402
from google.cloud import texttospeech  # noqa: E402

_OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_output", "google_webui")
_DEFAULT_TEXT = "오늘 하루도 정말 수고 많으셨어요. 천천히, 편안하게 쉬어도 괜찮아요."

print("[로딩] Google TTS 클라이언트 + ko-KR 보이스 목록…")
_client = texttospeech.TextToSpeechClient()


def _list_ko_voices() -> list[str]:
    """ko-KR 보이스 동적 수집 (Neural2/Wavenet/Standard/Chirp3-HD …)."""
    try:
        resp = _client.list_voices(language_code="ko-KR")
        return sorted(v.name for v in resp.voices)
    except Exception as e:  # 네트워크/인증 실패 시 기본 목록
        print("[warn] list_voices 실패:", e)
        return ["ko-KR-Neural2-A", "ko-KR-Neural2-B", "ko-KR-Neural2-C"]


_VOICES = _list_ko_voices()
_DEFAULT_VOICE = "ko-KR-Neural2-A" if "ko-KR-Neural2-A" in _VOICES else _VOICES[0]
print(f"[완료] ko-KR 보이스 {len(_VOICES)}종 — http://127.0.0.1:8002")

# 톤 프리셋 (tts.py _TONE_MAP 과 동일 값) — 누르면 속도·피치 채움.
_PRESETS: dict[str, tuple[float, float]] = {
    "warm 따뜻": (0.92, -1.0),
    "calm 담담": (0.95, 0.0),
    "hopeful 희망": (1.0, 1.0),
    "soft 나직이": (0.88, -2.0),
}


def _slow_down(in_path: str, factor: float) -> str:
    """ffmpeg atempo 로 전체 속도 늦춤(음정 유지). factor=0.7 → 70% 속도(느려짐).

    Chirp3-HD 처럼 speaking_rate 가 안 먹는 보이스의 전체 속도를 확실히 제어.
    실패 시 원본 경로 그대로 반환(데모 안 끊기게).
    """
    if factor >= 0.999:
        return in_path
    import subprocess

    out = in_path[:-4] + f"_t{factor}.mp3"
    try:
        r = subprocess.run(
            ["ffmpeg", "-y", "-i", in_path, "-filter:a", f"atempo={factor}", out],
            capture_output=True,
            timeout=30,
        )
        return out if (r.returncode == 0 and os.path.exists(out)) else in_path
    except Exception:
        return in_path


def _synth(text, voice, rate, pitch, gain, post_rate):
    text = (text or "").strip()
    if not text:
        return None, "❌ 읽을 문장을 입력하세요."
    # Chirp3-HD 계열은 pitch 파라미터 미지원(400 에러) → pitch 생략.
    pitch_ok = "chirp" not in voice.lower()
    try:
        vp = texttospeech.VoiceSelectionParams(language_code="ko-KR", name=voice)
        ac_kwargs = dict(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=float(rate),
            volume_gain_db=float(gain),
        )
        if pitch_ok:
            ac_kwargs["pitch"] = float(pitch)
        ac = texttospeech.AudioConfig(**ac_kwargs)
        resp = _client.synthesize_speech(
            input=texttospeech.SynthesisInput(text=text),
            voice=vp,
            audio_config=ac,
        )
        os.makedirs(_OUT_DIR, exist_ok=True)
        p_tag = f"p{pitch}" if pitch_ok else "pNA"
        label = f"{voice}_r{rate}_{p_tag}_g{gain}"
        safe = re.sub(r"[^0-9a-zA-Z._-]", "_", label)[:80]
        path = os.path.join(_OUT_DIR, f"g_{safe}.mp3")
        with open(path, "wb") as f:
            f.write(resp.audio_content)
        path = _slow_down(path, float(post_rate))  # 전체 속도 후처리(음정 유지)
        pitch_note = f"pitch {pitch}" if pitch_ok else "pitch 미지원(Chirp3-HD)"
        post_note = "" if float(post_rate) >= 0.999 else f" · 후처리 {post_rate}x"
        return path, f"✅ 완료 — {voice} | rate {rate} {pitch_note} gain {gain}{post_note}"
    except Exception as e:  # UI 안 죽게
        return None, f"❌ 오류: {type(e).__name__}: {str(e)[:200]}"


def _fill_preset(name):
    r, p = _PRESETS.get(name, (1.0, 0.0))
    return r, p


with gr.Blocks(title="레인보우브릿지 Google TTS 튜닝") as demo:
    gr.Markdown(
        "# 🌈 Google Cloud TTS 튜닝 — 3인칭 낭독용 목소리\n"
        "성인 목소리를 **voice·속도·피치**로 직접 돌려 음색(섬뜩/부자연) 잡기. "
        "결과는 플레이어 **⬇** 로 다운로드. (클라우드·GPU 무관 → Qwen3 데모와 동시 가능)"
    )
    with gr.Row():
        with gr.Column():
            text = gr.Textbox(label="읽을 문장 (한국어)", value=_DEFAULT_TEXT, lines=3)
            voice = gr.Dropdown(
                _VOICES, value=_DEFAULT_VOICE, label=f"목소리 (ko-KR {len(_VOICES)}종)"
            )
            preset = gr.Radio(
                list(_PRESETS), value=None, label="톤 프리셋 (누르면 속도·피치 자동)"
            )
            rate = gr.Slider(
                0.25, 2.0, value=0.95, step=0.01,
                label="속도 speaking_rate (1.0 기본 · 낮을수록 느림)",
            )
            pitch = gr.Slider(
                -10, 10, value=0.0, step=0.5,
                label="피치 pitch (0 기본 · 낮을수록 굵고 차분 / Chirp3-HD는 미적용)",
            )
            post_rate = gr.Slider(
                0.6, 1.0, value=1.0, step=0.05,
                label="전체 속도 후처리 (1.0=안함 · 낮출수록 전체 느림, 음정 유지 / Chirp3-HD 속도 안 먹을 때 사용)",
            )
            with gr.Accordion("고급 (선택)", open=False):
                gain = gr.Slider(
                    -16, 16, value=0.0, step=1.0, label="볼륨 volume_gain_db"
                )
            go = gr.Button("🔊 합성", variant="primary")
        with gr.Column():
            audio = gr.Audio(label="결과 음성 (⬇ 다운로드)", type="filepath", autoplay=True)
            status = gr.Textbox(label="상태", lines=2, interactive=False)

    preset.change(_fill_preset, inputs=preset, outputs=[rate, pitch])
    go.click(
        _synth,
        inputs=[text, voice, rate, pitch, gain, post_rate],
        outputs=[audio, status],
    )


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=8002, inbrowser=False)
