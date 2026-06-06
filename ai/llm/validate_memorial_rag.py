"""추모 메시지 RAG 있음/없음 비교 — 실제 Gemini 대상 수동 점검 도구.

⚠️ 실제 API 호출 — .env 의 LLM_API_KEY 필요. CI 미포함.
사용: ai/ 디렉터리에서  python -m llm.validate_memorial_rag
결과는 ai/llm/validate_memorial_rag_result.txt 에도 저장됩니다.
"""

from __future__ import annotations

import io
import sys
import time
import ai.llm.memorial as memorial_module
from .memorial import generate_message
from .provider import generate

# Windows 터미널 인코딩 문제 우회 — UTF-8 강제
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_DELAY_SEC = 45.0

_CASES = [
    {
        "label": "강아지 / 감정 2 / 따뜻한 톤 / 추억 있음",
        "pet": {"name": "뭉이", "species": "강아지", "period": "14년",
                "memories": ["새벽마다 발 위에 올라와 잠들던 것", "산책할 때 꼭 내 그림자를 밟고 다녔던 것"]},
        "emotion": {"emotion_score": 2, "note": "자꾸 뭉이 밥그릇을 치우지 못하겠어요"},
        "tone": "warm",
    },
    {
        "label": "고양이 / 감정 5 / 차분한 톤 / 추억 있음",
        "pet": {"name": "나비", "species": "고양이", "period": "9년",
                "memories": ["책 읽을 때 항상 무릎에 올라왔던 것", "창가에서 해바라기 하던 것"]},
        "emotion": {"emotion_score": 5, "note": "나비가 좋아하던 창가 자리가 이제 비어 있어요"},
        "tone": "calm",
    },
    {
        "label": "고양이 / 감정 7 / 희망 톤 / 추억 있음",
        "pet": {"name": "콩이", "species": "고양이", "period": "6년",
                "memories": ["간식 봉지 소리만 나면 어디서든 달려오던 것"]},
        "emotion": {"emotion_score": 7, "note": "조금씩 일상으로 돌아가려고 해요"},
        "tone": "hopeful",
    },
]


def _run(case: dict, *, use_rag: bool) -> dict:
    if not use_rag:
        original = memorial_module._rag_retrieve
        memorial_module._rag_retrieve = lambda *a, **kw: None
    try:
        return generate_message(
            case["pet"], case["emotion"], case["tone"], generate=generate
        )
    finally:
        if not use_rag:
            memorial_module._rag_retrieve = original


_RESULT_FILE = "ai/llm/validate_memorial_rag_result.txt"


def main() -> None:
    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    out("=" * 70)
    out("추모 메시지 RAG 있음/없음 비교 (실제 Gemini)")
    out("=" * 70)

    for i, case in enumerate(_CASES):
        out(f"\n{'─' * 70}")
        out(f"[케이스] {case['label']}")
        out(f"  추억: {case['pet'].get('memories')}")
        out(f"  메모: {case['emotion'].get('note')}")
        out("─" * 70)

        out("\n▶ RAG 없음")
        no_rag = _run(case, use_rag=False)
        out(no_rag.get("content", ""))
        time.sleep(_DELAY_SEC)

        out("\n▶ RAG 있음")
        with_rag = _run(case, use_rag=True)
        out(with_rag.get("content", ""))

        if i < len(_CASES) - 1:
            out(f"\n  (다음 케이스까지 {int(_DELAY_SEC)}초 대기...)")
            time.sleep(_DELAY_SEC)

    out("\n" + "=" * 70)
    out("완료")

    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    main()
