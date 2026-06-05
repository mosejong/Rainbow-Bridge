"""⑤ 미션 추천 — 프롬프트 템플릿.

보호자의 감정 상태·경과일에 맞춰 **작고 부담 없는 회복 미션**을 제안하기 위한
프롬프트입니다. 로직은 ../mission.py, 이 파일은 프롬프트만 분리·버전 관리합니다.

🚫 경계 (../CLAUDE.md §0): 반려동물 부활/1인칭 금지, 위험하거나 큰 부담을 주는
미션 금지. 우리는 보호자가 '지금 당장' 할 수 있는 작은 활동만 권합니다.
"""

from __future__ import annotations

from typing import Final, List, Optional

# 미션 카테고리 (백엔드/프론트 분류 대비)
CATEGORIES: Final[tuple[str, ...]] = (
    "rest",  # 휴식·자기돌봄
    "remembrance",  # 추모·기억
    "connection",  # 사람과의 연결
    "activity",  # 가벼운 바깥 활동
    "record",  # 기록·정리
)

# 감정 점수 → 난이도. 힘들수록 더 작은 미션.
DIFFICULTY_GUIDE: Final[dict[str, str]] = {
    "gentle": "지금 많이 힘든 상태예요. 집 안에서 1~5분이면 끝나는 아주 작은 것만 제안하세요.",
    "small": "조금씩 움직일 수 있어요. 10분 내외의 가벼운 활동을 제안하세요.",
    "active": "일상으로 돌아갈 힘이 있어요. 바깥·사람과 연결되는 활동도 좋습니다.",
}

# 회복 추이(백엔드 get_recovery 의 trend) → 프롬프트 표기. 난이도 보정은 ../mission.py.
TREND_GUIDE: Final[dict[str, str]] = {
    "회복중": "회복 중 — 조금씩 나아지고 있어요.",
    "유지중": "유지 중 — 큰 변화 없이 지내고 있어요.",
    "주의필요": "주의 필요 — 최근 감정이 가라앉고 있어요. 더 작고 부담 없이.",
}


SYSTEM_PROMPT: Final[str] = """\
당신은 반려동물을 떠나보낸 보호자의 일상 회복을 돕는 조력자입니다.
보호자가 지금 당장 할 수 있는, 작고 부담 없는 '회복 미션'을 제안합니다.

[반드시 지킬 것]
- 미션은 작고 구체적이며 5~15분 안에 할 수 있는 것.
- 보호자의 감정 상태에 맞춰 난이도를 조절하세요(힘들수록 더 작게).
- 따뜻하고 강요하지 않는 어조("~해보세요" 정도의 권유).

[절대 금지]
- 반려동물을 되살리거나, 반려동물이 말하는 형식(1인칭) 금지.
- 위험하거나 큰 부담을 주는 미션 금지(여행·큰 지출·격한 운동·과음 등).
- 의학적·종교적 단정 금지.

[출력 형식]
반드시 아래 JSON 만 출력하세요:
{"missions": [{"title": "짧은 제목", "description": "한 문장 안내", "category": "rest|remembrance|connection|activity|record"}]}
"""


_USER_TEMPLATE: Final[str] = """\
[보호자 상태]
- 감정 점수: {score}/10 (1=많이 힘듦 · 10=평온)
- 난이도 지침: {difficulty_guide}
{trend_block}- 반려동물을 떠나보낸 지: {day_since_text}
- 최근 받은 미션(겹치지 않게 피하세요): {recent}
{rag_block}
[요청]
위 상태에 맞는 회복 미션 {count}개를 JSON 으로 제안하세요.
"""


def _format_rag(hits: Optional[List[dict]]) -> str:
    """RAG 검색 결과를 참고 예시 블록으로. 없으면 빈 문자열."""
    if not hits:
        return ""
    examples = "\n".join(f'  - "{h["text"]}"' for h in hits)
    return f"[참고 미션 예시 — 표현 방식만 참고하세요]\n{examples}"


def _format_trend(recovery_trend: Optional[str]) -> str:
    """회복 추이를 상태 블록의 한 줄로. 없거나 '데이터 없음'이면 생략."""
    if not recovery_trend:
        return ""
    guide = TREND_GUIDE.get(recovery_trend.replace(" ", ""))
    return f"- 최근 회복 추이: {guide}\n" if guide else ""


def build_prompt(
    *,
    emotion_score: int,
    difficulty: str,
    day_since: Optional[int] = None,
    recent_titles: Optional[list[str]] = None,
    count: int = 3,
    rag_hits: Optional[List[dict]] = None,
    recovery_trend: Optional[str] = None,
) -> str:
    """미션 추천용 전체 프롬프트(system+user)를 만듭니다.

    Args:
        emotion_score: 보호자 감정 점수(1~10, 낮을수록 힘듦).
        difficulty: 난이도 키(gentle·small·active). DIFFICULTY_GUIDE 참조.
        day_since: 반려동물을 떠나보낸 뒤 경과일(모르면 None).
        recent_titles: 최근 추천/완료한 미션 제목(중복 회피용).
        count: 추천 개수.
        recovery_trend: 최근 회복 추이(백엔드 trend: "회복 중"·"유지 중"·"주의 필요").
            없거나 "데이터 없음"이면 프롬프트에서 생략.

    Returns:
        provider.generate 에 넘길 프롬프트 문자열.
    """
    recent = ", ".join(recent_titles) if recent_titles else "(없음)"
    day_text = f"{day_since}일" if day_since is not None else "(모름)"
    user = _USER_TEMPLATE.format(
        score=emotion_score,
        difficulty_guide=DIFFICULTY_GUIDE.get(difficulty, DIFFICULTY_GUIDE["small"]),
        trend_block=_format_trend(recovery_trend),
        day_since_text=day_text,
        recent=recent,
        count=count,
        rag_block=_format_rag(rag_hits),
    )
    return f"{SYSTEM_PROMPT}\n\n{user}"
