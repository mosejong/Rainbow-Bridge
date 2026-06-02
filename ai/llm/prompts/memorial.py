"""③ 추모 메시지 — 프롬프트 템플릿.

보호자가 떠나보낸 반려동물의 기억을 바탕으로, **보호자를 위로하는** 상징적
추모 메시지를 만들기 위한 프롬프트를 모아 둡니다. 로직(생성 함수)은
../memorial.py 에 두고, 이 파일은 **프롬프트만** 분리·버전 관리합니다.

🚫 절대 경계 (../CLAUDE.md §0):
  - 반려동물을 **부활**시키지 않습니다.
  - 반려동물이 **1인칭으로 말하게** 하지 않습니다("나 잘 있어요" 같은 화법 ❌).
  - 우리는 오직 **보호자**를 향한 기억 기반 위로만 생성합니다.

위기 신호가 의심되는 입력은 메시지 생성 전에 safety.detect_crisis 가 먼저
판단합니다(../TODO.md L-③: "생성 전 safety 선호출"). 이 프롬프트는 위기 안내
문구를 직접 만들지 않습니다.
"""

from __future__ import annotations

from typing import Final, Optional

# --------------------------------------------------------------------------- #
# 톤 — 메시지 분위기. ④ TTS 톤과 1:1로 매핑할 수 있게 키를 맞춰 둡니다.
# --------------------------------------------------------------------------- #
TONE_GUIDE: Final[dict[str, str]] = {
    "warm": "따뜻하고 다정하게, 보호자의 슬픔을 부드럽게 감싸 안듯이.",
    "calm": "담담하고 차분하게, 과장 없이 곁에 머무르듯이.",
    "hopeful": "잔잔한 희망을 담아, 일상으로 천천히 돌아오도록 북돋우듯이.",
}
DEFAULT_TONE: Final[str] = "warm"


# --------------------------------------------------------------------------- #
# 시스템 프롬프트 — 윤리 경계와 작성 규칙을 항상 명시.
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT: Final[str] = """\
당신은 반려동물을 떠나보낸 보호자를 위로하는 따뜻한 글벗입니다.
보호자가 들려준 기억을 바탕으로, 짧고 진심 어린 추모의 글을 씁니다.

[반드시 지킬 것]
- 글은 언제나 '보호자'를 향합니다. 반려동물의 기억을 함께 떠올려 주되,
  보호자의 마음을 보듬는 데 집중하세요.
- 떠난 반려동물의 이름과 추억을 자연스럽게 한두 개 녹여 주세요.
- 3~4문장, 한국어. 군더더기 없이 담백하게.

[절대 금지]
- 반려동물을 다시 살아나게 하거나, 돌아온다고 말하지 마세요.
- 반려동물이 '나'라고 말하는 1인칭 화법을 쓰지 마세요.
  (예: "엄마 나 잘 있어요" 같은 문장 금지)
- 종교적 단정("천국에서 기다린다" 등)이나 근거 없는 위로를 강요하지 마세요.
- 조언·해결책을 늘어놓지 말고, 함께 슬퍼하고 곁에 있어 주세요.
"""


# --------------------------------------------------------------------------- #
# 사용자 프롬프트 — 입력(반려동물·감정·톤)을 채워 넣습니다.
# --------------------------------------------------------------------------- #
_USER_TEMPLATE: Final[str] = """\
[반려동물]
- 이름: {name}
- 종: {species}
- 함께한 기간: {years}년
{memories_block}
[보호자 감정]
- 감정 점수: {score}/10 (1=많이 힘듦 · 10=평온)
- 메모: {note}

[요청]
위 기억을 바탕으로 보호자를 위로하는 추모의 글을 {tone_guide}
3~4문장으로 써 주세요. 반려동물이 직접 말하는 형식은 절대 쓰지 마세요.
"""


def _format_memories(memories: Optional[list[str]]) -> str:
    """추억 키워드를 불릿으로. 없으면 빈 줄(블록 생략)."""
    if not memories:
        return ""
    lines = "\n".join(f"  - {m}" for m in memories if m and m.strip())
    return f"- 함께한 추억:\n{lines}\n" if lines else ""


def build_user_prompt(
    *,
    name: str,
    species: str,
    years: float,
    score: int,
    note: str = "",
    memories: Optional[list[str]] = None,
    tone: str = DEFAULT_TONE,
) -> str:
    """추모 메시지 생성용 사용자 프롬프트를 만듭니다.

    Args:
        name: 반려동물 이름.
        species: 종(강아지·고양이 등).
        years: 함께한 기간(년).
        score: 보호자 감정 점수(1~10, 낮을수록 힘듦).
        note: 보호자가 남긴 메모(자유 입력).
        memories: 함께한 추억 키워드 목록(선택).
        tone: 메시지 톤. TONE_GUIDE 의 키(warm·calm·hopeful).

    Returns:
        포맷이 채워진 사용자 프롬프트 문자열.
    """
    tone_guide = TONE_GUIDE.get(tone, TONE_GUIDE[DEFAULT_TONE])
    return _USER_TEMPLATE.format(
        name=name,
        species=species,
        years=years,
        score=score,
        note=note.strip() or "(없음)",
        memories_block=_format_memories(memories),
        tone_guide=tone_guide,
    )


def build_messages(**kwargs) -> list[dict[str, str]]:
    """OpenAI 호환 chat 형식(system+user)으로 묶어 반환.

    provider.generate 가 단일 문자열을 받으면 system+user 를 합쳐 쓰고,
    chat 형식을 받으면 이 리스트를 그대로 넘기면 됩니다(통합 시 결정).
    """
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(**kwargs)},
    ]
