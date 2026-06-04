"""Gemini 연결 확인용 스모크 테스트 (정환주, 2026-06-02).

목적: `.env` 의 Gemini 설정으로 실제 응답이 1회 오는지만 확인합니다.
※ 임시 연결 점검용입니다. 실제 LLM 추상화(`provider.py`)는 반소람 담당 —
   이 파일은 `provider.py` 를 import 하지 않고 독립 실행합니다.

사용:
  pip install openai python-dotenv
  python ai/llm/smoke_gemini.py
"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["LLM_API_KEY"],
    base_url=os.environ.get(
        "LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/"
    ),
)

resp = client.chat.completions.create(
    model=os.environ.get("LLM_MODEL", "gemini-2.5-flash"),
    messages=[{"role": "user", "content": "한국어로 한 문장만 답해 주세요: 잘 연결됐나요?"}],
    max_tokens=64,
)
print(resp.choices[0].message.content)
