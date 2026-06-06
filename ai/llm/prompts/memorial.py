"""③ 추모 메시지 — 프롬프트 템플릿.

보호자가 떠나보낸 반려동물의 기억을 바탕으로, **보호자를 위로하는** 상징적
추모 메시지를 만들기 위한 프롬프트를 모아 둡니다. 로직(생성 함수)은
../memorial.py 에 두고, 이 파일은 **프롬프트만** 분리·버전 관리합니다.

🚫 절대 경계 (../CLAUDE.md §0):
  - 반려동물을 **부활**시키지 않습니다.
  - 반려동물 1인칭 화법은 **기본값 금지**. (first_person=True 는 §1.5 조건 충족 후에만)
  - 우리는 오직 **보호자**를 향한 기억 기반 위로만 생성합니다.

✅ 1인칭 편지 모드 (first_person=True):
  - 보호자 명시 동의 + 경고 문구 표시 + risk_level 0~1 검증을 **호출자**가 보장해야 합니다.
  - SYSTEM_PROMPT_FIRST_PERSON 과 _USER_TEMPLATE_FIRST_PERSON 을 사용합니다.
  - 부활/환생 단정 표현은 1인칭 모드에서도 여전히 금지입니다.

위기 신호가 의심되는 입력은 메시지 생성 전에 safety.detect_crisis 가 먼저
판단합니다(../TODO.md L-③: "생성 전 safety 선호출"). 이 프롬프트는 위기 안내
문구를 직접 만들지 않습니다.
"""

from __future__ import annotations

from typing import Final, List, Optional

# --------------------------------------------------------------------------- #
# 톤 — 메시지 분위기. ④ TTS 톤과 1:1로 매핑할 수 있게 키를 맞춰 둡니다.
# --------------------------------------------------------------------------- #
TONE_GUIDE: Final[dict[str, str]] = {
    "warm": "따뜻하고 다정하게, 보호자의 슬픔을 부드럽게 감싸 안듯이.",
    "calm": "담담하고 차분하게, 과장 없이 곁에 머무르듯이.",
    "hopeful": "잔잔한 희망을 담아, 일상으로 천천히 돌아오도록 북돋우듯이.",
}
DEFAULT_TONE: Final[str] = "warm"

# 회복 추이(백엔드 get_recovery 의 trend) → 톤 캘리브레이션용 한 줄 지침.
# 톤(tone)을 덮어쓰지 않고, 같은 톤 안에서 결을 맞추도록 모델에 신호만 줍니다.
TREND_GUIDE: Final[dict[str, str]] = {
    "회복중": "보호자가 조금씩 회복 중이에요. 무기력하게 가라앉히지 말고 잔잔한 온기를 더하세요.",
    "유지중": "보호자가 큰 변화 없이 지내고 있어요. 담담하게 곁에 머무르세요.",
    "주의필요": "보호자의 감정이 최근 가라앉고 있어요. 밝게 띄우지 말고 더 조심스럽게 보듬으세요.",
}


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
- 반려동물이 말하는 1인칭 화법을 절대 쓰지 마세요.
  "나는", "내가", "저는", "제가"를 반려동물의 시점으로 쓰면 안 됩니다.
  (예: "나는 잘 있어요", "내가 곁에 있을게요", "저 행복해요" 같은 문장 금지)
  글 전체에서 반려동물은 반드시 3인칭("봄이는", "봄이가")으로만 표현하세요.
- 종교적 단정("천국에서 기다린다" 등)이나 근거 없는 위로를 강요하지 마세요.
- 조언·해결책을 늘어놓지 말고, 함께 슬퍼하고 곁에 있어 주세요.
"""

# 1인칭 편지 모드 — §1.5 조건(보호자 동의+경고 문구+risk_level 0~1) 충족 후에만 사용.
SYSTEM_PROMPT_FIRST_PERSON: Final[str] = """\
당신은 반려동물을 떠나보낸 보호자가 꿈 속에서 나누는 작별 대화를 쓰는 따뜻한 글벗입니다.
보호자가 들려준 기억을 바탕으로, 반려동물의 시점에서 보호자에게 마지막 인사를 건넵니다.

[반드시 지킬 것]
- 이것은 "꿈 속 작별 대화"입니다. 반려동물이 실제로 돌아온 것이 아님을 전제로 씁니다.
- 반려동물의 1인칭("나는", "내가", "저는")으로 보호자에게 따뜻하게 말을 건네세요.
- 보호자가 들려준 기억·추억을 한두 개 자연스럽게 녹여 주세요.
- 3~4문장, 한국어. 담백하고 따뜻하게.

[절대 금지]
- "살아 돌아왔어요", "다시 만날 수 있어요" 등 부활·환생을 단정하지 마세요.
- "지금 곁에 있어요" 등 현재 존재감을 단정하는 연출은 피하세요.
- 종교적 단정("천국에서 기다린다" 등)이나 근거 없는 확언을 하지 마세요.
- 말줄임표(...)를 절대 사용하지 마세요. 문장은 반드시 완전하게 끝맺으세요.
"""


# --------------------------------------------------------------------------- #
# 사용자 프롬프트 — 입력(반려동물·감정·톤)을 채워 넣습니다.
# --------------------------------------------------------------------------- #
_USER_TEMPLATE: Final[str] = """\
[반려동물]
- 이름: {name}
- 종: {species}
- 함께한 기간: {period}
{memories_block}
[보호자 감정]
- 감정 점수: {score}/10 (1=많이 힘듦 · 10=평온)
- 메모: {note}
{recovery_block}{rag_block}
[요청]
위 기억을 바탕으로 보호자를 위로하는 추모의 글을 {tone_guide}
3~4문장으로 써 주세요.
반려동물은 반드시 3인칭({name}는/{name}가)으로만 쓰고, 절대 1인칭("나는", "저는")으로 말하게 하지 마세요.
"""

# 1인칭 편지 모드 — SYSTEM_PROMPT_FIRST_PERSON 과 함께 사용.
_USER_TEMPLATE_FIRST_PERSON: Final[str] = """\
[반려동물]
- 이름: {name}
- 종: {species}
- 함께한 기간: {period}
{memories_block}
[보호자 감정]
- 감정 점수: {score}/10 (1=많이 힘듦 · 10=평온)
- 메모: {note}
{recovery_block}{rag_block}
[요청]
꿈 속 작별 대화입니다. 반려동물 {name}의 1인칭("나는", "내가")으로 보호자에게 마지막 인사를 건네는 3~4문장을 {tone_guide}
써 주세요. 부활·환생을 단정하는 표현("살아 돌아왔어요" 등)은 쓰지 마세요.
"""


def _format_memories(memories: Optional[list[str]]) -> str:
    """추억 키워드를 불릿으로. 없으면 빈 줄(블록 생략)."""
    if not memories:
        return ""
    lines = "\n".join(f"  - {m}" for m in memories if m and m.strip())
    return f"- 함께한 추억:\n{lines}\n" if lines else ""


def _format_rag(hits: Optional[List[dict]]) -> str:
    """RAG 검색 결과를 few-shot 예시 블록으로. 없으면 빈 문자열."""
    if not hits:
        return ""
    examples = "\n".join(f'  - "{h["text"]}"' for h in hits)
    return f"\n[참고 위로글 예시 — 톤과 표현 방식만 참고하고 내용은 직접 작성하세요]\n{examples}\n"


def _format_recovery(recovery_trend: Optional[str]) -> str:
    """회복 추이를 톤 캘리브레이션 한 줄로. 없거나 '데이터 없음'이면 생략."""
    if not recovery_trend:
        return ""
    guide = TREND_GUIDE.get(recovery_trend.replace(" ", ""))
    return f"- 최근 회복 추이: {guide}\n" if guide else ""


def build_user_prompt(
    *,
    name: str,
    species: str,
    period: str,
    score: int,
    note: str = "",
    memories: Optional[list[str]] = None,
    tone: str = DEFAULT_TONE,
    rag_hits: Optional[List[dict]] = None,
    recovery_trend: Optional[str] = None,
    first_person: bool = False,
) -> str:
    """추모 메시지 생성용 사용자 프롬프트를 만듭니다.

    Args:
        name: 반려동물 이름.
        species: 종(강아지·고양이 등).
        period: 함께한 기간(백엔드 pet.period 문자열, 예 "12년"/"2018~2026").
        score: 보호자 감정 점수(1~10, 낮을수록 힘듦).
        note: 보호자가 남긴 메모(자유 입력).
        memories: 함께한 추억 키워드 목록(선택).
        tone: 메시지 톤. TONE_GUIDE 의 키(warm·calm·hopeful).
        rag_hits: RAG 검색 결과(retrieve() 반환값). 없으면 few-shot 생략.
        recovery_trend: 최근 회복 추이(백엔드 trend: "회복 중"·"유지 중"·"주의 필요").
            톤을 덮어쓰지 않고 같은 톤 안에서 결을 맞추도록 신호만 줍니다.
            없거나 "데이터 없음"이면 생략.
        first_person: True 이면 반려동물 1인칭 편지 모드. §1.5 조건 충족 후에만 사용.

    Returns:
        포맷이 채워진 사용자 프롬프트 문자열.
    """
    tone_guide = TONE_GUIDE.get(tone, TONE_GUIDE[DEFAULT_TONE])
    template = _USER_TEMPLATE_FIRST_PERSON if first_person else _USER_TEMPLATE
    return template.format(
        name=name,
        species=species,
        period=period,
        score=score,
        note=note.strip() or "(없음)",
        memories_block=_format_memories(memories),
        recovery_block=_format_recovery(recovery_trend),
        rag_block=_format_rag(rag_hits),
        tone_guide=tone_guide,
    )


def build_messages(*, first_person: bool = False, **kwargs) -> list[dict[str, str]]:
    """OpenAI 호환 chat 형식(system+user)으로 묶어 반환.

    provider.generate 가 단일 문자열을 받으면 system+user 를 합쳐 쓰고,
    chat 형식을 받으면 이 리스트를 그대로 넘기면 됩니다(통합 시 결정).

    Args:
        first_person: True 이면 1인칭 편지 모드 프롬프트 사용. §1.5 조건 충족 후에만 전달.
    """
    system = SYSTEM_PROMPT_FIRST_PERSON if first_person else SYSTEM_PROMPT
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": build_user_prompt(first_person=first_person, **kwargs)},
    ]
