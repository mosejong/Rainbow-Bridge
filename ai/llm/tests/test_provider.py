"""provider 추상화 테스트 — 네트워크 없이 로직만 검증.

실제 LLM 호출(Gemini)은 .env 의 LLM_API_KEY 가 있어야 가능하므로, 여기서는
가짜 OpenAI 클라이언트를 끼워 **재시도·예외·json_mode·설정 적용**을 확인합니다.
"""

from __future__ import annotations

import httpx
import pytest
from openai import APITimeoutError

from .. import provider
from ..config import LLMConfig
from ..provider import LLMError, generate

# --- 가짜 OpenAI 클라이언트 ------------------------------------------------- #


class _FakeMessage:
    def __init__(self, content: str):
        self.content = content


class _FakeChoice:
    def __init__(self, content: str):
        self.message = _FakeMessage(content)


class _FakeResponse:
    def __init__(self, content: str):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    """script 순서대로: 문자열이면 응답, 예외면 raise."""

    def __init__(self, script):
        self._script = list(script)
        self.calls = 0
        self.last_kwargs: dict = {}

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        item = self._script[self.calls]
        self.calls += 1
        if isinstance(item, Exception):
            raise item
        return _FakeResponse(item)


class _FakeClient:
    def __init__(self, script):
        self.chat = type("C", (), {"completions": _FakeCompletions(script)})()


def _cfg(**override) -> LLMConfig:
    base = dict(
        provider="test",
        base_url="http://x",
        model="m",
        api_keys=("key",),
        timeout=5.0,
        max_retries=2,
        max_tokens=64,
        temperature=0.5,
        reasoning_effort="none",
    )
    base.update(override)
    return LLMConfig(**base)


@pytest.fixture
def patched(monkeypatch):
    """get_config·_client·sleep 을 통제 — script 로 응답/오류를 지정."""

    def _setup(script, **cfg_over):
        client = _FakeClient(script)
        monkeypatch.setattr(provider, "get_config", lambda: _cfg(**cfg_over))
        monkeypatch.setattr(provider, "_client", lambda *a, **kw: client)
        monkeypatch.setattr(provider, "_sleep_backoff", lambda attempt: None)
        return client

    return _setup


def _timeout() -> APITimeoutError:
    return APITimeoutError(request=httpx.Request("POST", "http://x"))


# --- 테스트 ----------------------------------------------------------------- #


def test_returns_text(patched):
    patched(["안녕하세요"])
    assert generate("hi") == "안녕하세요"


def test_strips_whitespace(patched):
    patched(["  여백 있음  \n"])
    assert generate("hi") == "여백 있음"


def test_applies_overrides(patched):
    client = patched(["ok"])
    generate("hi", max_tokens=123, temperature=0.1)
    kw = client.chat.completions.last_kwargs
    assert kw["max_tokens"] == 123
    assert kw["temperature"] == 0.1


def test_uses_config_defaults(patched):
    client = patched(["ok"])
    generate("hi")
    kw = client.chat.completions.last_kwargs
    assert kw["max_tokens"] == 64  # _cfg 기본
    assert kw["temperature"] == 0.5


def test_json_mode_sets_response_format(patched):
    client = patched(["{}"])
    generate("hi", json_mode=True)
    assert client.chat.completions.last_kwargs["response_format"] == {
        "type": "json_object"
    }


def test_reasoning_effort_sent_when_set(patched):
    client = patched(["ok"], reasoning_effort="none")
    generate("hi")
    assert client.chat.completions.last_kwargs["reasoning_effort"] == "none"


def test_reasoning_effort_omitted_when_empty(patched):
    client = patched(["ok"], reasoning_effort="")
    generate("hi")
    assert "reasoning_effort" not in client.chat.completions.last_kwargs


def test_retries_then_succeeds(patched):
    client = patched([_timeout(), "회복됨"], max_retries=2)
    assert generate("hi") == "회복됨"
    assert client.chat.completions.calls == 2  # 1회 실패 후 성공


def test_gives_up_after_retries(patched):
    patched([_timeout(), _timeout(), _timeout()], max_retries=2)
    with pytest.raises(LLMError):
        generate("hi")


def test_missing_api_key_raises(monkeypatch):
    monkeypatch.setattr(provider, "get_config", lambda: _cfg(api_keys=()))
    with pytest.raises(LLMError):
        generate("hi")


def test_key_rotation_on_rate_limit(monkeypatch):
    """첫 번째 키 429 → 두 번째 키로 전환해 성공."""
    from openai import RateLimitError as _RLE

    def _make_rate_limit():
        resp = httpx.Response(429, request=httpx.Request("POST", "http://x"))
        return _RLE(message="quota", response=resp, body=None)

    client_a = _FakeClient([_make_rate_limit()])
    client_b = _FakeClient(["두번째키 성공"])

    call_order: list[str] = []

    def _fake_client(api_key, base_url, timeout):
        call_order.append(api_key)
        return client_a if api_key == "key1" else client_b

    monkeypatch.setattr(provider, "get_config", lambda: _cfg(api_keys=("key1", "key2")))
    monkeypatch.setattr(provider, "_client", _fake_client)
    monkeypatch.setattr(provider, "_sleep_backoff", lambda attempt: None)

    result = generate("hi")
    assert result == "두번째키 성공"
    assert call_order == ["key1", "key2"]


def test_model_fallback_when_all_keys_exhausted(monkeypatch):
    """모든 키가 기본 모델에서 429 → 폴백 모델로 전환해 성공."""
    from openai import RateLimitError as _RLE

    def _make_rate_limit():
        resp = httpx.Response(429, request=httpx.Request("POST", "http://x"))
        return _RLE(message="quota", response=resp, body=None)

    # 단일 키: 기본 모델 호출 시 429, 폴백 모델 호출 시 성공.
    client = _FakeClient([_make_rate_limit(), "폴백 모델 성공"])
    monkeypatch.setattr(
        provider,
        "get_config",
        lambda: _cfg(model="gemini-2.5-flash", fallback_model="gemini-1.5-flash"),
    )
    monkeypatch.setattr(provider, "_client", lambda *a, **kw: client)
    monkeypatch.setattr(provider, "_sleep_backoff", lambda attempt: None)

    result = generate("hi")
    assert result == "폴백 모델 성공"
    # 두 번째(성공) 호출은 폴백 모델로 갔는지 확인
    assert client.chat.completions.last_kwargs["model"] == "gemini-1.5-flash"


def test_no_fallback_model_raises_after_keys(monkeypatch):
    """폴백 모델 미설정 시, 전 키 429면 그냥 LLMError."""
    from openai import RateLimitError as _RLE

    def _make_rate_limit():
        resp = httpx.Response(429, request=httpx.Request("POST", "http://x"))
        return _RLE(message="quota", response=resp, body=None)

    client = _FakeClient([_make_rate_limit(), _make_rate_limit()])
    monkeypatch.setattr(
        provider, "get_config", lambda: _cfg(api_keys=("k1", "k2"), fallback_model="")
    )
    monkeypatch.setattr(provider, "_client", lambda *a, **kw: client)
    monkeypatch.setattr(provider, "_sleep_backoff", lambda attempt: None)

    with pytest.raises(LLMError):
        generate("hi")
