"""1단계 증상 진료 안내 — 로직.

보호자가 입력한 반려동물 증상을 바탕으로 진료 안내 텍스트를 생성합니다.
프롬프트(대본)는 prompts/triage.py 에, 위기 판단은 safety.py 에 분리돼 있고,
이 파일은 그 둘을 엮어 흐름을 담당합니다:

    입력 → (1) 보호자 위기 선체크 → (2) 프롬프트 조립 → (3) LLM 호출 → 결과 dict

🚨 1단계는 반려동물이 아직 살아있는 시점이지만, 보호자가 남긴 메모(note)에
위기 신호가 있으면 진료 안내보다 1393 안내를 우선합니다.

LLM 호출(provider.generate)은 주입(generate 인자) 받습니다.
엔진이 확정되기 전에도 가짜 generate 로 흐름을 테스트할 수 있습니다.
"""

from __future__ import annotations

from typing import Optional, Protocol

from .prompts import triage as triage_prompt
from .safety import (
    CrisisAction,
    EMPATHY_FOCUS_NOTE,
    WELFARE_INTRO,
    WELFARE_RESOURCES,
    crisis_notice,
    decide_action,
    detect_crisis,
)


class GenerateFn(Protocol):
    """provider.generate 와 맞춘 호출 시그니처 (주입용)."""

    def __call__(
        self,
        prompt: str,
        *,
        max_tokens: int = 300,
        temperature: float = 0.4,
        json_mode: bool = False,
    ) -> str: ...


# 의료 정보는 창의성보다 일관성이 중요해서 temperature 를 낮게 설정.
_MAX_TOKENS: int = 300
_TEMPERATURE: float = 0.4

def generate_triage(
    symptoms: str,
    pet: dict,
    *,
    note: str = "",
    generate: GenerateFn,
    source: str = "local",
) -> dict:
    """증상 진료 안내를 생성합니다.

    Args:
        symptoms: 보호자가 입력한 증상 텍스트.
        pet: 반려동물 정보 ``{name, species, age}``.
        note: 보호자 감정 메모 (선택). 위기 선체크에만 사용.
        generate: LLM 호출 함수(provider.generate 또는 테스트용 가짜). **주입 필수.**
        source: 결과 출처 표기(local·perso 등).

    Returns:
        ``{advice, severity, source}``.
        보호자 위기 감지 시 ``crisis_message`` 와 ``risk_level`` 포함.
    """
    # (1) 보호자 메모 위기 선체크 — 등급별 응답 정책(safety.decide_action).
    #     L2(경고)·L3(긴급)이면 진료 안내보다 1393 우선.
    action = CrisisAction.GENERATE
    crisis = None
    if note:
        crisis = detect_crisis(note)
        action = decide_action(crisis.risk_level)
        if action == CrisisAction.BLOCK:  # L3 — 안내 중단, 1393 만
            notice = crisis_notice()
            return {
                "advice": notice,
                "severity": "crisis",
                "source": "safety",
                "crisis_message": notice,
                "risk_level": int(crisis.risk_level),
            }

    # (2) 심각도 추론 + 프롬프트 조립.
    severity = triage_prompt._assess_severity(symptoms)
    messages = triage_prompt.build_messages(
        symptoms,
        name=pet.get("name", ""),
        species=pet.get("species", ""),
        age=pet.get("age", ""),
        severity=severity,
    )
    prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"
    # L1(우려)·L2(경고) — 진료 정보보다 공감을 먼저 하도록 지침 추가.
    if action in (CrisisAction.GENERATE_WITH_SUPPORT, CrisisAction.HOTLINE):
        prompt += EMPATHY_FOCUS_NOTE

    # (3) LLM 호출.
    advice = generate(prompt, max_tokens=_MAX_TOKENS, temperature=_TEMPERATURE).strip()

    result = {"advice": advice, "severity": severity, "source": source}
    # L1(우려) — 진료 안내는 하되 복지자원 안내를 함께.
    if action == CrisisAction.GENERATE_WITH_SUPPORT and crisis is not None:
        result["support_message"] = WELFARE_INTRO
        result["welfare_resources"] = list(WELFARE_RESOURCES)
        result["risk_level"] = int(crisis.risk_level)
    # L2(경고) — 진료 안내는 하되 1393 안내를 함께(우선 표시).
    elif action == CrisisAction.HOTLINE and crisis is not None:
        result["crisis_message"] = crisis_notice()
        result["risk_level"] = int(crisis.risk_level)
    return result
