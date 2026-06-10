"""POST /messages/tts 라우트가 TTS 서비스로 위임하는지 확인(얇은 연결 테스트)."""

from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.endpoints import messages as ep
from app.schemas.tts import TtsCreate, TtsResponse


@pytest.mark.asyncio
async def test_messages_tts_forwards_body_to_generate_tts():
    body = TtsCreate(pet_id="pet1", text="보고 싶었어요", tone="warm")
    fake = TtsResponse(audio_url="/uploads/tts/x.mp3", duration=2.0, format="mp3")
    with patch.object(ep, "generate_tts", new=AsyncMock(return_value=fake)) as gen:
        result = await ep.synthesize_message_tts(body, user={"id": "u1"})

    gen.assert_awaited_once_with(body)
    assert result.audio_url == "/uploads/tts/x.mp3"
