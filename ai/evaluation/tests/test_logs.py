"""⑧ llm_logs 스키마 테스트 — total_tokens 정합 + 원문 미저장(PII)."""

from __future__ import annotations

from ..logs import KIND_MESSAGE, LLMLog


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
