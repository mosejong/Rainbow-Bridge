from app.schemas.tts import TtsCreate, TtsResponse

# TODO: 정환주님 ai/tts/tts.py 연동 후 실제 합성으로 교체
# from ai.tts import synthesize, TtsTone

_STUB_AUDIO_URL = "/uploads/tts/stub_warm.mp3"
_STUB_DURATION = 8.0


async def generate_tts(data: TtsCreate) -> TtsResponse:
    """TTS 합성 스텁 — 정환주님 Google Cloud TTS 인증 완료 후 실 합성으로 교체."""
    # TODO: 아래 주석 해제 후 stub 반환 제거
    # result = synthesize(data.text, TtsTone(data.tone))
    # return TtsResponse(
    #     audio_url=result["audio_path"],
    #     duration=result["duration"],
    #     format=result["format"],
    # )

    return TtsResponse(
        audio_url=_STUB_AUDIO_URL,
        duration=_STUB_DURATION,
        format="mp3",
    )
