"""⑧ llm_logs 스키마 테스트 — total_tokens 정합 + 원문 미저장(PII)."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from ..logs import (
    KIND_CRISIS,
    KIND_MESSAGE,
    LLMLog,
    alog_llm_call,
    log_llm_call,
    measure_latency,
)


def test_total_tokens_sum():
    log = LLMLog(
        kind=KIND_MESSAGE,
        provider="gemini",
        model="gemini-2.5-flash",
        tokens_in=100,
        tokens_out=40,
    )
    assert log.total_tokens == 140


def test_to_doc_has_total_tokens_and_no_prompt():
    log = LLMLog(
        kind=KIND_MESSAGE, provider="gemini", model="m", tokens_in=10, tokens_out=5
    )
    doc = log.to_doc()
    assert doc["total_tokens"] == 15  # admin/usage $sum:total_tokens 와 정합
    assert "prompt" not in doc  # 대화 원문 미저장(개인정보 최소화)
    assert doc["kind"] == KIND_MESSAGE
    assert doc["model"] == "m"


def _fake_resp(prompt_tokens=9, completion_tokens=3, model="gemini-2.5-flash"):
    """OpenAI 호환 응답 흉내(usage·model 만)."""
    return SimpleNamespace(
        model=model,
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens
        ),
    )


def test_from_openai_extracts_tokens_and_model():
    log = LLMLog.from_openai(_fake_resp(), kind=KIND_MESSAGE, pet_id="p1")
    assert log.tokens_in == 9
    assert log.tokens_out == 3
    assert log.model == "gemini-2.5-flash"
    assert log.pet_id == "p1"
    assert log.ok is True
    doc = log.to_doc()
    assert doc["total_tokens"] == 12  # admin/usage 와 정합
    assert "prompt" not in doc  # 원문 미저장


def test_from_openai_guards_missing_usage():
    # usage 없는 응답 → 토큰 0 (가드)
    log = LLMLog.from_openai(SimpleNamespace(model="m"), kind=KIND_MESSAGE)
    assert log.tokens_in == 0
    assert log.tokens_out == 0
    assert log.model == "m"


def test_from_openai_failure_no_response():
    # 호출 실패(resp=None) → ok=False, 토큰 0, 인자 model 사용
    log = LLMLog.from_openai(
        None, kind=KIND_MESSAGE, model="gemini-2.5-flash", ok=False
    )
    assert log.ok is False
    assert log.tokens_in == 0
    assert log.model == "gemini-2.5-flash"


def test_measure_latency_records_ms():
    with measure_latency() as t:
        pass
    assert isinstance(t.ms, int)
    assert t.ms >= 0


def test_log_llm_call_inserts_one_doc():
    # 가짜 컬렉션(mongo 불필요) — insert_one 이 to_doc() 1건으로 호출되는지 검증
    inserted = []

    class _StubCollection:
        def insert_one(self, doc):
            inserted.append(doc)
            return SimpleNamespace(inserted_id="stub-id")

    result = log_llm_call(
        _StubCollection(),
        _fake_resp(),
        kind=KIND_MESSAGE,
        latency_ms=42,
        pet_id="p1",
    )
    assert result.inserted_id == "stub-id"
    assert len(inserted) == 1
    doc = inserted[0]
    assert doc["kind"] == KIND_MESSAGE
    assert doc["total_tokens"] == 12
    assert doc["latency_ms"] == 42
    assert "prompt" not in doc  # 원문 미저장


def test_alog_llm_call_lite_inserts_one_doc():
    # motor(async) 버전 — resp 없이 라이트 로깅(토큰 0). asyncio.run 으로 plugin 불필요.
    inserted = []

    class _StubAsyncCollection:
        async def insert_one(self, doc):
            inserted.append(doc)
            return SimpleNamespace(inserted_id="stub-id")

    result = asyncio.run(
        alog_llm_call(
            _StubAsyncCollection(),
            kind=KIND_CRISIS,
            latency_ms=7,
            pet_id="p1",
            model="gemini-2.5-flash",
            risk_level=2,
        )
    )
    assert result.inserted_id == "stub-id"
    assert len(inserted) == 1
    doc = inserted[0]
    assert doc["kind"] == KIND_CRISIS
    assert doc["pet_id"] == "p1"
    assert doc["latency_ms"] == 7
    assert doc["risk_level"] == 2
    assert doc["total_tokens"] == 0  # resp 없음 → 토큰 0 (라이트 로깅)
    assert doc["model"] == "gemini-2.5-flash"
    assert "prompt" not in doc  # 원문 미저장
