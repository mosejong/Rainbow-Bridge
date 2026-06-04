"""⑤ 미션 추천 — 프롬프트 템플릿.

보호자의 감정 상태·경과일에 맞춰 **작고 부담 없는 회복 미션**을 제안하기 위한
프롬프트입니다. 로직은 ../mission.py, 이 파일은 프롬프트만 분리·버전 관리합니다.

🚫 경계 (../CLAUDE.md §0): 반려동물 부활/1인칭 금지, 위험하거나 큰 부담을 주는
미션 금지. 우리는 보호자가 '지금 당장' 할 수 있는 작은 활동만 권합니다.
"""

from __future__ import annotations

from typing import Final, Optional

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
- 반려동물을 떠나보낸 지: {day_since_text}
- 최근 받은 미션(겹치지 않게 피하세요): {recent}

[요청]
위 상태에 맞는 회복 미션 {count}개를 JSON 으로 제안하세요.
"""


def build_prompt(
    *,
    emotion_score: int,
    difficulty: str,
    day_since: Optional[int] = None,
    recent_titles: Optional[list[str]] = None,
    count: int = 3,
) -> str:
    """미션 추천용 전체 프롬프트(system+user)를 만듭니다.

    Args:
        emotion_score: 보호자 감정 점수(1~10, 낮을수록 힘듦).
        difficulty: 난이도 키(gentle·small·active). DIFFICULTY_GUIDE 참조.
        day_since: 반려동물을 떠나보낸 뒤 경과일(모르면 None).
        recent_titles: 최근 추천/완료한 미션 제목(중복 회피용).
        count: 추천 개수.

    Returns:
        provider.generate 에 넘길 프롬프트 문자열.
    """
    recent = ", ".join(recent_titles) if recent_titles else "(없음)"
    day_text = f"{day_since}일" if day_since is not None else "(모름)"
    user = _USER_TEMPLATE.format(
        score=emotion_score,
        difficulty_guide=DIFFICULTY_GUIDE.get(difficulty, DIFFICULTY_GUIDE["small"]),
        day_since_text=day_text,
        recent=recent,
        count=count,
    )
    return f"{SYSTEM_PROMPT}\n\n{user}"
