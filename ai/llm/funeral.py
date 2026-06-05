"""2단계 장례 절차 단계별 상담 — 로직.

보호자가 현재 어느 장례 단계에 있는지 입력하면, 해당 단계 안내 텍스트를 생성합니다.
프롬프트(대본)는 prompts/funeral.py 에, 위기 판단은 safety.py 에 분리돼 있고,
이 파일은 그 둘을 엮어 흐름을 담당합니다:

    입력 → (1) 보호자 위기 선체크 → (2) 프롬프트 조립 → (3) LLM 호출 → 결과 dict

🚨 장례 준비 시기는 보호자 감정이 극도로 예민한 시기입니다.
보호자 메모(note)에 위기 신호가 있으면 절차 안내보다 1393 안내를 우선합니다.
"""

from __future__ import annotations

from typing import Optional, Protocol

from ai.rag.retrieve import retrieve as _rag_retrieve
from .prompts import funeral as funeral_prompt
from .safety import CRISIS_HOTLINE, detect_crisis


class GenerateFn(Protocol):
    """provider.generate 와 맞춘 호출 시그니처 (주입용)."""

    def __call__(
        self,
        prompt: str,
        *,
        max_tokens: int = 350,
        temperature: float = 0.5,
        json_mode: bool = False,
    ) -> str: ...


# 절차 안내는 정확성이 중요해 temperature 를 낮게 설정.
_MAX_TOKENS: int = 350
_TEMPERATURE: float = 0.5

# 🚨 1393 은 CRISIS_HOTLINE 상수로만 — 하드코딩 금지(../CLAUDE.md §0).
_CRISIS_NOTICE: str = (
    "지금 많이 힘드신 것 같아요. 혼자 견디지 않으셔도 됩니다. "
    f"언제든 자살예방 상담전화 {CRISIS_HOTLINE}(24시간)으로 마음을 나눠 주세요."
)


def generate_funeral_guidance(
    step: str,
    pet: dict,
    *,
    note: str = "",
    choice: str = "",
    generate: GenerateFn,
    source: str = "local",
) -> dict:
    """장례 절차 단계별 안내를 생성합니다.

    Args:
        step: 현재 장례 단계 키(funeral_prompt.STEP_ORDER 중 하나).
        pet: 반려동물 정보 ``{name, species}``.
        note: 보호자 감정 메모 또는 질문 (선택). 위기 선체크에도 사용.
        choice: 보호자가 선택한 장례 방식 (선택, method 단계에서 주로 사용).
        generate: LLM 호출 함수(provider.generate 또는 테스트용 가짜). **주입 필수.**
        source: 결과 출처 표기(local·perso 등).

    Returns:
        ``{guidance, step, next_step, source}``.
        보호자 위기 감지 시 ``crisis_message`` 와 ``risk_level`` 포함.
    """
    # (1) 보호자 메모에 위기 신호가 있으면 절차 안내보다 1393 우선.
    if note:
        crisis = detect_crisis(note)
        if crisis.hotline_required:
            return {
                "guidance": _CRISIS_NOTICE,
                "step": step,
                "next_step": None,
                "source": "safety",
                "crisis_message": _CRISIS_NOTICE,
                "risk_level": int(crisis.risk_level),
            }

    # (2) note 없으면 DB 템플릿 반환 — Gemini 호출 없음.
    if not note:
        template = funeral_prompt.STEP_TEMPLATES.get(step, "")
        guidance = template.format(name=pet.get("name", "반려동물"))
        return {
            "guidance": guidance,
            "step": step,
            "next_step": funeral_prompt.next_step(step),
            "source": "template",
        }

    # (3) RAG 검색 — 현재 단계 안내글 top-3 검색. 실패 시 graceful fallback.
    rag_hits = None
    try:
        query_parts: list[str] = [note]
        step_focus = funeral_prompt.STEP_FOCUS.get(step, "")
        if step_focus:
            query_parts.append(step_focus)
        rag_hits = _rag_retrieve(" ".join(query_parts), k=3)
    except Exception:
        rag_hits = None

    # (4) note 있으면 Gemini 호출 (질문에 맞춤 답변).
    messages = funeral_prompt.build_messages(
        step,
        name=pet.get("name", ""),
        species=pet.get("species", ""),
        choice=choice,
        note=note,
        rag_hits=rag_hits,
    )
    prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"
    guidance = generate(prompt, max_tokens=_MAX_TOKENS, temperature=_TEMPERATURE).strip()

    return {
        "guidance": guidance,
        "step": step,
        "next_step": funeral_prompt.next_step(step),
        "source": source,
    }
