"""③ 추모 메시지 생성 — 로직.

보호자가 들려준 기억을 바탕으로 **보호자를 위로하는** 추모 메시지를 만듭니다.
프롬프트(대본)는 prompts/memorial.py 에, 위기 판단은 safety.py 에 분리돼 있고,
이 파일은 그 둘을 엮어 **흐름**을 담당합니다:

    입력 → (1) 위기 선체크 → (2) 프롬프트 조립 → (3) LLM 호출
         → (4) 후처리 가드(1인칭/부활 차단) → 결과 dict

🚫 윤리 경계 (../CLAUDE.md §0):
  - 반려동물 부활/1인칭 화법 금지 → 출력에서도 후처리로 한 번 더 거릅니다.
  - 위기 신호가 강하면(L2↑) 메시지 생성보다 1393 안내가 **우선**입니다.

LLM 호출(provider.generate)은 **주입(generate 인자)** 받습니다. 덕분에 엔진이
확정되기 전에도 가짜 generate 로 흐름·가드를 테스트할 수 있고, 확정 후에는
provider.generate 를 그대로 넘기면 됩니다(결정 A/B).
"""

from __future__ import annotations

from typing import Optional, Protocol

from .prompts import memorial as memorial_prompt
from .safety import CRISIS_HOTLINE, detect_crisis


class GenerateFn(Protocol):
    """provider.generate 와 맞춘 호출 시그니처 (주입용)."""

    def __call__(
        self,
        prompt: str,
        *,
        max_tokens: int = 400,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str: ...


# 생성 파라미터 기본값 (config 확정 전 잠정값).
_MAX_TOKENS: int = 400
_TEMPERATURE: float = 0.7

# 위기 안내가 필요할 때 메시지 대신 내보내는 안내문.
# 🚨 1393 은 CRISIS_HOTLINE 상수로만 — 하드코딩 금지(../CLAUDE.md §0).
_CRISIS_NOTICE: str = (
    "지금 많이 힘드신 것 같아요. 혼자 견디지 않으셔도 됩니다. "
    f"언제든 자살예방 상담전화 {CRISIS_HOTLINE}(24시간)으로 마음을 나눠 주세요."
)


class GuardrailViolation(Exception):
    """생성 결과가 윤리 경계(1인칭/부활)를 넘었을 때."""


# --------------------------------------------------------------------------- #
# 후처리 가드 — LLM이 경계를 넘으면 잡아냅니다(2차 안전망).
# --------------------------------------------------------------------------- #
# 부활/환생 등 "돌아온다"는 단정 표현.
_RESURRECTION_MARKERS: tuple[str, ...] = (
    "다시살아",
    "다시태어",
    "되살아",
    "부활",
    "환생",
    "돌아올거",
    "돌아온다",
    "다시만날수있어",
)


def _violates_guardrail(content: str) -> Optional[str]:
    """경계 위반 사유를 반환(없으면 None).

    - 부활/환생 단정 표현
    - 반려동물 1인칭 화법(예: "<이름>이가: ..." 또는 따옴표로 반려동물이 말함)

    1인칭은 형태가 다양해 규칙만으로 완벽히 못 잡습니다. 여기서는 **명백한**
    경우만 차단하고, 정교한 판별은 향후 LLM 검수 단계로 미룹니다(보수적 2차망).
    """
    normalized = content.replace(" ", "")

    for marker in _RESURRECTION_MARKERS:
        if marker in normalized:
            return f"부활/환생 표현 감지: '{marker}'"

    # 반려동물이 보호자를 부르며 1인칭으로 말하는 전형적 패턴.
    first_person_hints = ("엄마나", "아빠나", "보호자님나")
    if any(hint in normalized for hint in first_person_hints):
        return "반려동물 1인칭 화법으로 의심되는 표현 감지"

    return None


def generate_message(
    pet: dict,
    emotion: dict,
    tone: str = memorial_prompt.DEFAULT_TONE,
    *,
    generate: GenerateFn,
    source: str = "local",
    max_retries: int = 1,
) -> dict:
    """추모 메시지를 생성합니다.

    Args:
        pet: 반려동물 정보 ``{name, species, period, memories?}`` (백엔드 pet 스키마).
        emotion: 보호자 감정 ``{emotion_score, note?}`` (emotion_score 1~10, 낮을수록 힘듦).
        tone: 메시지 톤(warm·calm·hopeful). prompts.TONE_GUIDE 키.
        generate: LLM 호출 함수(provider.generate 또는 테스트용 가짜). **주입 필수.**
        source: 결과 출처 표기(local·perso 등).
        max_retries: 가드 위반 시 재생성 횟수(소진되면 안내문으로 대체).

    Returns:
        ``{content, tone, source}``. 위기 시에는 ``crisis_message`` 와 ``risk_level`` 포함.
    """
    note = str(emotion.get("note", "") or "")

    # (1) 위기 선체크 — 본인 위기 신호가 강하면 메시지보다 안내 우선.
    crisis = detect_crisis(note)
    if crisis.hotline_required:
        return {
            "content": _CRISIS_NOTICE,
            "tone": tone,
            "source": "safety",
            "crisis_message": _CRISIS_NOTICE,
            "risk_level": int(crisis.risk_level),
        }

    # (2) 프롬프트 조립 — 키 이름은 백엔드 스키마와 합의(pet.period, emotion_score).
    prompt_kwargs = dict(
        name=pet.get("name", ""),
        species=pet.get("species", ""),
        period=pet.get("period", ""),
        score=int(emotion.get("emotion_score", 5)),
        note=note,
        memories=pet.get("memories"),
        tone=tone,
    )
    messages = memorial_prompt.build_messages(**prompt_kwargs)
    prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"

    # (3)+(4) 호출 후 가드 검사, 위반 시 재생성.
    last_violation = ""
    for _ in range(max_retries + 1):
        content = generate(
            prompt, max_tokens=_MAX_TOKENS, temperature=_TEMPERATURE
        ).strip()
        violation = _violates_guardrail(content)
        if violation is None:
            return {"content": content, "tone": tone, "source": source}
        last_violation = violation

    # 재시도까지 실패 → 위험한 출력을 내보내지 않고 차단.
    raise GuardrailViolation(
        f"생성 결과가 윤리 경계를 반복해서 위반했습니다 ({last_violation})."
    )
