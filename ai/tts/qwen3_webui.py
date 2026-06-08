"""레인보우브릿지 한국어 TTS 웹 UI — Qwen3 VoiceDesign (라벨 전부 한국어).

기본 qwen-tts-demo 는 화면이 영어·중국어라 불편 → 같은 모델을 한국어 UI 로 감쌈.
language 는 'korean' 고정, 자주 쓸 음색은 버튼(프리셋)으로 영어 instruct 자동 입력.

실행:
    conda run --no-capture-output -n qwen3-tts python ai/tts/qwen3_webui.py
→ 브라우저에서 http://127.0.0.1:8000 접속.
"""

from __future__ import annotations

import os

# anaconda libiomp5 중복 크래시 우회 (torch import 전).
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")

import gradio as gr
import torch

from qwen_tts import Qwen3TTSModel

_MODEL_ID = "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign"

# 빠른 목소리 프리셋: 한국어 라벨 → 영어 instruct(모델이 더 잘 알아들음). 직접 수정도 가능.
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
print("[완료] 모델 준비됨")


def _fill_preset(name: str) -> str:
    return _PRESETS.get(name, "")


def _synth(text: str, instruct: str):
    text = (text or "").strip()
    instruct = (instruct or "").strip()
    if not text:
        return None, "❌ 읽을 문장을 입력하세요."
    if not instruct:
        return None, "❌ 목소리 설명을 입력하거나 위에서 골라주세요."
    try:
        wavs, sr = _model.generate_voice_design(
            text=text, instruct=instruct, language="korean"
        )
        return (sr, wavs[0]), "✅ 완료 — 아래에서 재생하세요."
    except Exception as e:  # 합성 실패해도 UI 안 죽게
        return None, f"❌ 오류: {type(e).__name__}: {str(e)[:200]}"


with gr.Blocks(title="레인보우브릿지 한국어 TTS") as demo:
    gr.Markdown(
        "# 🌈 레인보우브릿지 — 한국어 목소리 만들기\n"
        "원하는 **목소리 느낌**을 고르거나 적고, **읽을 문장**을 넣은 뒤 *목소리 생성*을 누르세요.\n"
        "마음에 들 때까지 설명을 바꿔가며 여러 번 만들어 보세요. (전부 무료·로컬)"
    )
    with gr.Row():
        with gr.Column():
            text_in = gr.Textbox(
                label="① 읽을 문장 (한국어)",
                value=_DEFAULT_TEXT,
                lines=3,
                placeholder="여기에 한국어 문장을 입력하세요.",
            )
            preset_in = gr.Radio(
                label="② 빠른 목소리 선택 (누르면 아래 설명이 자동 입력됩니다)",
                choices=list(_PRESETS.keys()),
                value=None,
            )
            instruct_in = gr.Textbox(
                label="③ 목소리 설명 (직접 수정 가능 · 영어로 쓰면 더 정확)",
                lines=2,
                placeholder="예: 밝고 발랄한 여자아이 목소리 / bright cheerful little girl voice",
            )
            btn = gr.Button("🎙️ 목소리 생성", variant="primary")
        with gr.Column():
            audio_out = gr.Audio(label="결과 음성", type="numpy")
            status_out = gr.Textbox(label="상태", lines=2, interactive=False)

    preset_in.change(_fill_preset, inputs=preset_in, outputs=instruct_in)
    btn.click(_synth, inputs=[text_in, instruct_in], outputs=[audio_out, status_out])


if __name__ == "__main__":
    demo.launch(server_name="127.0.0.1", server_port=8000, inbrowser=False)
