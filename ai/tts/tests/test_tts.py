"""④ TTS 골격 테스트 — 키·외부 호출 없이 순수 로직만 검증.

(Google Cloud TTS 실제 합성은 인증 필요 → 여기서는 호출하지 않음)
"""

from __future__ import annotations

import pytest

from ..tts import (
    TtsTone,
    _TONE_MAP,
    _estimate_duration,
    _probe_duration,
    _split_text,
    synthesize,
)


def test_tone_map_covers_all_tones():
    """모든 톤에 음성 파라미터가 정의돼 있어야 함."""
    for tone in TtsTone:
        assert tone in _TONE_MAP


def test_split_short_text_single_chunk():
    assert _split_text("한 문장입니다.") == ["한 문장입니다."]


def test_split_long_text_respects_max_chars():
    text = " ".join(f"문장{i}." for i in range(50))
    chunks = _split_text(text, max_chars=30)
    assert len(chunks) > 1
    assert all(len(c) <= 30 for c in chunks)


def test_synthesize_empty_text_raises():
    with pytest.raises(ValueError):
        synthesize("")


def test_estimate_duration_positive():
    assert _estimate_duration("안녕하세요 반갑습니다") > 0


def test_probe_duration_missing_file_returns_none():
    """없는 파일은 측정 불가 → None (호출부는 추정값으로 폴백)."""
    assert _probe_duration("ai/tts/_output/__no_such_file__.mp3") is None
