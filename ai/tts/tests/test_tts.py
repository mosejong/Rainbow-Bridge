"""④ TTS 골격 테스트 — 키·외부 호출 없이 순수 로직만 검증.

(Google Cloud TTS 실제 합성은 인증 필요 → 여기서는 호출하지 않음)
"""

from __future__ import annotations

import os

import pytest

from .. import tts as tts_mod
from ..tts import (
    _VOICE_NAME,
    _VOICES,
    AVAILABLE_VOICES,
    TtsTone,
    _TONE_MAP,
    _estimate_duration,
    _fallback_path,
    _probe_duration,
    _resolve_voice,
    _split_text,
    synthesize,
)


def test_tone_map_covers_all_tones():
    """모든 톤에 음성 파라미터가 정의돼 있어야 함."""
    for tone in TtsTone:
        assert tone in _TONE_MAP


def test_soft_tone_accepted():
    """프론트가 보내는 'soft'가 유효한 톤이어야 함(이전엔 warm으로 폴백)."""
    assert TtsTone("soft") is TtsTone.SOFT
    assert TtsTone.SOFT in _TONE_MAP


def test_resolve_voice_default_is_current():
    """voice 미지정(None)이면 현재 기본 목소리를 써야 함(하위호환)."""
    assert _resolve_voice(None) == _VOICE_NAME


def test_resolve_voice_known_key():
    """알려진 키는 해당 Google voice 이름으로 변환돼야 함."""
    assert _resolve_voice("male_c") == _VOICES["male_c"]
    assert all(_resolve_voice(k) == _VOICES[k] for k in AVAILABLE_VOICES)


def test_resolve_voice_unknown_raises():
    """미지원 키는 ValueError."""
    with pytest.raises(ValueError):
        _resolve_voice("robot_x")


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


def test_fallback_path_none_when_empty(tmp_path, monkeypatch):
    """샘플이 없으면 폴백 경로 없음(None)."""
    monkeypatch.setattr(tts_mod, "_SAMPLE_DIR", str(tmp_path))
    assert _fallback_path(TtsTone.WARM) is None


def test_fallback_path_prefers_per_tone(tmp_path, monkeypatch):
    """톤별 샘플이 공통 샘플보다 우선."""
    monkeypatch.setattr(tts_mod, "_SAMPLE_DIR", str(tmp_path))
    (tmp_path / "fallback.mp3").write_bytes(b"generic")
    assert _fallback_path(TtsTone.WARM).endswith("fallback.mp3")
    (tmp_path / "fallback_warm.mp3").write_bytes(b"warm")
    assert _fallback_path(TtsTone.WARM).endswith("fallback_warm.mp3")


def test_synthesize_falls_back_on_error(tmp_path, monkeypatch):
    """합성 실패 + 샘플 있으면 → 샘플 mp3로 폴백(fallback=True)."""
    monkeypatch.setattr(tts_mod, "_SAMPLE_DIR", str(tmp_path))
    monkeypatch.setattr(tts_mod, "_OUTPUT_DIR", str(tmp_path / "out"))
    (tmp_path / "fallback.mp3").write_bytes(b"ID3 fake-audio")

    def boom(*a, **k):
        raise RuntimeError("인증 없음")

    monkeypatch.setattr(tts_mod, "_synthesize_google", boom)
    result = synthesize("안녕하세요", TtsTone.WARM)
    assert result["fallback"] is True
    assert result["format"] == "mp3"
    assert os.path.exists(result["audio_path"])


def test_synthesize_reraises_without_fallback(tmp_path, monkeypatch):
    """합성 실패 + 샘플 없으면 → 원래 에러 그대로 올림."""
    monkeypatch.setattr(tts_mod, "_SAMPLE_DIR", str(tmp_path))  # 비어 있음
    monkeypatch.setattr(tts_mod, "_OUTPUT_DIR", str(tmp_path / "out"))

    def boom(*a, **k):
        raise RuntimeError("인증 없음")

    monkeypatch.setattr(tts_mod, "_synthesize_google", boom)
    with pytest.raises(RuntimeError):
        synthesize("안녕하세요", TtsTone.WARM)


def test_synthesize_success_has_fallback_false(monkeypatch, tmp_path):
    """정상 합성이면 fallback=False."""
    monkeypatch.setattr(tts_mod, "_OUTPUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(tts_mod, "_synthesize_google", lambda *a, **k: b"ID3 ok")
    monkeypatch.setattr(tts_mod, "_probe_duration", lambda p: None)
    result = synthesize("안녕하세요", TtsTone.CALM)
    assert result["fallback"] is False
    assert os.path.exists(result["audio_path"])
