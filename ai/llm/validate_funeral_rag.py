"""장례 절차 RAG 있음/없음 비교 — 실제 Gemini 대상 수동 점검 도구.

note 있는 케이스에서 RAG 주입 전/후 출력 차이를 눈으로 확인합니다.

⚠️ 실제 API 호출 — .env 의 LLM_API_KEY 필요. CI 미포함.
사용: ai/ 디렉터리에서  python -m llm.validate_funeral_rag
"""

from __future__ import annotations

import time
import ai.llm.funeral as funeral_module
from .funeral import generate_funeral_guidance
from .provider import generate

_DELAY_SEC = 45.0  # 무료 티어 RPM 회피 (분당 5회 한도, retry 36s 기준)

PET = {"name": "봄이", "species": "고양이"}

_CASES = [
    ("immediate", "같이 있어주고 싶은데 내일 출근을 해야 해요. 어떡하죠."),
    ("method",    "저는 수목장이 좋은데 부모님이 화장을 원하셔서 의견이 달라요."),
    ("after",     "유골함을 집에 두는 게 저한테는 더 힘들 것 같아서 봉안당을 알아보고 싶어요."),
]


def _run(step: str, note: str, *, use_rag: bool) -> dict:
    if not use_rag:
        original = funeral_module._rag_retrieve
        funeral_module._rag_retrieve = lambda *a, **kw: None
    try:
        result = generate_funeral_guidance(step, PET, note=note, generate=generate)
        return result
    finally:
        if not use_rag:
            funeral_module._rag_retrieve = original


def main() -> None:
    print("=" * 70)
    print("장례 절차 RAG 있음/없음 비교 (실제 Gemini)")
    print("=" * 70)

    for step, note in _CASES:
        print(f"\n{'─' * 70}")
        print(f"[단계] {step}  |  [메모] {note}")
        print("─" * 70)

        print("\n[guidance — STEP_TEMPLATES, 항상 동일]")
        template = funeral_module.funeral_prompt.STEP_TEMPLATES.get(step, "").format(name=PET["name"])
        print(template)

        print("\n▶ note_response: RAG 없음")
        no_rag = _run(step, note, use_rag=False)
        print(no_rag.get("note_response", ""))
        time.sleep(_DELAY_SEC)

        print("\n▶ note_response: RAG 있음")
        with_rag = _run(step, note, use_rag=True)
        print(with_rag.get("note_response", ""))

        if (step, note) != _CASES[-1]:
            print(f"\n  (다음 케이스까지 {int(_DELAY_SEC)}초 대기...)")
            time.sleep(_DELAY_SEC)

    print("\n" + "=" * 70)
    print("완료")


if __name__ == "__main__":
    main()
