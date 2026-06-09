"""레인보우브릿지 한국어 TTS 웹 UI — Qwen3 VoiceDesign (라벨 전부 한국어).

기본 qwen-tts-demo 는 화면이 영어·중국어라 불편 → 같은 모델을 한국어 UI 로 감쌈.
language 는 'korean' 고정. 두 가지 입력 방식:
  ① 다이얼 — 슬라이더(나이/다정/밝기/피치/감정/또렷/속도/안정성/seed + 고급)로 미세조정 (추천).
  ② 프리셋·직접설명 — 빠른 음색 버튼 또는 영어 instruct 직접 입력.
모든 결과는 플레이어 ⬇ 버튼으로 다운로드 + 설정별 파일로 _output 폴더에 자동 누적 저장.

실행:
    conda run --no-capture-output -n qwen3-tts python ai/tts/qwen3_webui.py
→ 브라우저에서 http://127.0.0.1:8000 접속.
"""

from __future__ import annotations

import os
import re
import sys

# anaconda libiomp5 중복 크래시 우회 (torch import 전).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

# 같은 폴더 qwen3_emotion 의 다이얼 로직 재사용 (ai/tts/__init__ 안 거침 → google-cloud 회피).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from qwen3_emotion import _OUT_DIR, build_instruct  # noqa: E402
from tone_down import high_shelf  # noqa: E402  # 쨍함(고역) 톤다운 후처리 재사용

import gradio as gr  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402

from qwen_tts import Qwen3TTSModel  # noqa: E402

_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"

_PRESETS: dict[str, str] = {
    "발랄한 여자아이": "A bright, cheerful, lively and playful little girl voice",
    "귀여운 여자아이": "A cute, sweet, adorable soft young girl voice",
    "발랄한 남자아이": "A bright, energetic, playful and cheerful little boy voice",
    "차분한 남자아이": "A soft, gentle, calm and innocent little boy voice",
    "밝은 성인 여성": "A bright, cheerful, upbeat young woman voice",
    "따뜻한 성인 여성": "A warm, gentle, soothing young woman voice",
    "차분한 성인 남성": "A calm, warm, gentle adult man voice",
    "활기찬 성인 남성": "A bright, energetic, friendly young man voice",
}

_DEFAULT_TEXT = "오늘 하루도 정말 수고 많으셨어요. 천천히, 편안하게 쉬어도 괜찮아요."

print("[로딩] 모델 불러오는 중… (처음 한 번 수십 초)")
_model = Qwen3TTSModel.from_pretrained(_MODEL_ID, device_map="cuda:0", dtype=torch.bfloat16)
_CUDA = torch.cuda.is_available()
print("[완료] 모델 준비됨 — 브라우저에서 http://127.0.0.1:8000 여세요")


def _save(wav, sr, label: str) -> None:
    try:
        import soundfile as sf

        os.makedirs(_OUT_DIR, exist_ok=True)
        safe = re.sub(r"[^0-9a-zA-Z._-]", "_", label)[:80]
        sf.write(os.path.join(_OUT_DIR, f"qwen3em_{safe}.wav"), wav, sr)
    except Exception:
        pass


def _run(text, instruct, temp, seed, label, top_p, rep_pen, eq_db=0.0, eq_fc=4000.0):
    """공통 합성: seed 고정 → temperature/top_p/repetition_penalty → 정규화 → (쨍함 EQ) → 저장."""
    text = (text or "").strip()
    instruct = (instruct or "").strip()
    if not text:
        return None, "❌ 읽을 문장을 입력하세요."
    if not instruct:
        return None, "❌ 목소리 설명이 비었습니다."
    try:
        if seed is not None:
            torch.manual_seed(int(seed))
            if _CUDA:
                torch.cuda.manual_seed_all(int(seed))
        gk = {"temperature": float(temp)}
        if top_p is not None and float(top_p) > 0:
            gk["top_p"] = float(top_p)
        if rep_pen is not None and float(rep_pen) > 0:
            gk["repetition_penalty"] = float(rep_pen)
        wavs, sr = _model.generate_voice_design(
            text=text, instruct=instruct, language="korean", **gk
        )
        wav = np.asarray(wavs[0], dtype=np.float32)
        peak = float(np.max(np.abs(wav)))
        if peak > 0:  # 목소리 작음 보정
            wav = wav / peak * 0.95
        if eq_db and float(eq_db) > 0:  # 쨍함(날카로운 고역) 톤다운 — high-shelf 감쇠
            wav = high_shelf(wav, sr, float(eq_fc), -float(eq_db)).astype(np.float32)
        _save(wav, sr, label)
        return (sr, wav), "✅ 완료 — 재생/다운로드(⬇) 하세요."
    except Exception as e:  # 합성 실패해도 UI 안 죽게
        return None, f"❌ 오류: {type(e).__name__}: {str(e)[:200]}"


def _synth_dial(text, gender, age, warmth, bright, pitch, emotion, clarity, pace, temp, seed, top_p, rep_pen, eq_db, eq_fc):
    instruct = build_instruct(
        gender, int(warmth), int(bright), pace, age=age, pitch=pitch, emotion=emotion, clarity=int(clarity)
    )
    label = f"dial_{gender}_{age}_w{int(warmth)}_b{int(bright)}_{pitch}_{emotion}_c{int(clarity)}_{pace}_t{temp}_s{int(seed)}"
    if eq_db and float(eq_db) > 0:  # 파일명에 EQ 기록 → 어느 강도였는지 추적
        label += f"_eq{int(eq_db)}@{int(eq_fc)}"
    audio, status = _run(text, instruct, temp, seed, label, top_p, rep_pen, eq_db, eq_fc)
    return audio, status, instruct


def _synth_free(text, instruct, temp, seed, top_p, rep_pen):
    return _run(text, instruct, temp, seed, "free", top_p, rep_pen)


def _fill_preset(name: str) -> str:
    return _PRESETS.get(name, "")


def _rand_seed() -> int:
    import random

    return random.randint(0, 99999)


with gr.Blocks(title="레인보우브릿지 한국어 TTS") as demo:
    gr.Markdown(
        "# 🌈 레인보우브릿지 — 한국어 목소리 만들기\n"
        "**① 다이얼** 탭에서 슬라이더만 돌리면 어린아이 목소리가 미세조정됩니다. "
        "여아/남아 둘 다 됨 · 결과는 플레이어 **⬇** 로 다운로드. (무료·로컬)"
    )

    with gr.Tab("① 다이얼 (추천)"):
        with gr.Row():
            with gr.Column():
                d_text = gr.Textbox(label="읽을 문장 (한국어)", value=_DEFAULT_TEXT, lines=3)
                with gr.Row():
                    d_gender = gr.Radio(["boy", "girl"], value="boy", label="성별")
                    d_age = gr.Radio(
                        ["younger", "child", "older"], value="child",
                        label="나이 (younger 5세 / child 7세 / older 10세)",
                    )
                d_warmth = gr.Slider(0, 3, value=1, step=1, label="다정함 (0 담백 ↔ 3 다정·느끼위험)")
                d_bright = gr.Slider(0, 3, value=2, step=1, label="밝기 (0 쳐짐 ↔ 3 들뜸)")
                d_pitch = gr.Radio(["low", "normal", "high"], value="normal", label="피치(높낮이)")
                d_emotion = gr.Radio(
                    ["none", "calm", "sad", "comfort"], value="none",
                    label="감정 결 (없음 / 차분 / 슬픔 / 위로)",
                )
                d_clarity = gr.Slider(0, 2, value=1, step=1, label="또렷함 (속삭임 반대 · 발음 분명)")
                d_eq = gr.Slider(0, 9, value=0, step=1, label="쨍함 줄이기 (고역 컷 dB · 0=안함 / girl 날카로움 보정)")
                d_pace = gr.Radio(["slow", "normal", "fast"], value="normal", label="속도")
                d_temp = gr.Slider(0.5, 1.0, value=0.7, step=0.05, label="안정성 temp (낮을수록 또박·흔들림↓)")
                with gr.Row():
                    d_seed = gr.Number(value=7, precision=0, label="seed (같은 설정 다른 목소리)")
                    d_dice = gr.Button("🎲 새 목소리", scale=0)
                with gr.Accordion("고급 (선택)", open=False):
                    d_top_p = gr.Slider(0.0, 1.0, value=0.0, step=0.05, label="top_p (0=미사용)")
                    d_rep = gr.Slider(0.0, 2.0, value=0.0, step=0.05, label="repetition_penalty (0=미사용)")
                    d_eq_fc = gr.Slider(2000, 7000, value=4000, step=500, label="쨍함 고역 시작 fc(Hz · 낮을수록 넓게 깎음)")
                d_go = gr.Button("🔊 합성", variant="primary")
            with gr.Column():
                d_audio = gr.Audio(label="결과 음성 (⬇ 다운로드)", type="numpy", autoplay=True)
                d_status = gr.Textbox(label="상태", lines=1, interactive=False)
                d_instruct = gr.Textbox(label="이번에 들어간 설명 (참고)", lines=4, interactive=False)

        d_dice.click(_rand_seed, outputs=d_seed)
        d_go.click(
            _synth_dial,
            inputs=[d_text, d_gender, d_age, d_warmth, d_bright, d_pitch, d_emotion,
                    d_clarity, d_pace, d_temp, d_seed, d_top_p, d_rep, d_eq, d_eq_fc],
            outputs=[d_audio, d_status, d_instruct],
        )

    with gr.Tab("② 프리셋·직접 설명"):
        with gr.Row():
            with gr.Column():
                text_in = gr.Textbox(label="읽을 문장 (한국어)", value=_DEFAULT_TEXT, lines=3)
                preset_in = gr.Radio(
                    label="빠른 목소리 선택 (누르면 아래 설명 자동 입력)",
                    choices=list(_PRESETS.keys()),
                    value=None,
                )
                instruct_in = gr.Textbox(
                    label="목소리 설명 (직접 수정 가능 · 영어가 더 정확)",
                    lines=2,
                    placeholder="예: bright cheerful little girl voice",
                )
                f_temp = gr.Slider(0.5, 1.0, value=0.7, step=0.05, label="안정성 temp")
                f_seed = gr.Number(value=7, precision=0, label="seed")
                with gr.Accordion("고급 (선택)", open=False):
                    f_top_p = gr.Slider(0.0, 1.0, value=0.0, step=0.05, label="top_p (0=미사용)")
                    f_rep = gr.Slider(0.0, 2.0, value=0.0, step=0.05, label="repetition_penalty (0=미사용)")
                btn = gr.Button("🎙️ 목소리 생성", variant="primary")
            with gr.Column():
                audio_out = gr.Audio(label="결과 음성 (⬇ 다운로드)", type="numpy", autoplay=True)
                status_out = gr.Textbox(label="상태", lines=2, interactive=False)

        preset_in.change(_fill_preset, inputs=preset_in, outputs=instruct_in)
        btn.click(
            _synth_free,
            inputs=[text_in, instruct_in, f_temp, f_seed, f_top_p, f_rep],
            outputs=[audio_out, status_out],
        )


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=8000, inbrowser=False)
