"""⑤ 미션 추천 — 로직.

보호자의 감정 점수·경과일에 맞춰 **작은 회복 미션**을 추천합니다. 난이도는 규칙으로
정하고(안전·일관성), 문구는 LLM 으로 개인화하되 실패하면 큐레이션된 규칙 풀로
폴백합니다(graceful). memorial 과 같은 '주입(generate) + 가드 + 폴백' 패턴.

흐름:
    emotion_score → 난이도 결정 → (LLM 생성 시도 → 검증·중복제거)
                  → 부족하면 규칙 풀로 보충/폴백 → count 개 반환

🚫 경계(../CLAUDE.md §0): 반려동물 부활/1인칭·위험한 미션 금지. 규칙 풀과 LLM
가드 양쪽에 적용합니다.
"""

from __future__ import annotations

import json
from typing import Optional, Protocol

from .prompts import mission as mission_prompt


class GenerateFn(Protocol):
    """provider.generate 와 맞춘 호출 시그니처 (주입용)."""

    def __call__(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
        json_mode: bool = False,
    ) -> str: ...


# 생성 파라미터 (잠정).
_MAX_TOKENS: int = 512
_TEMPERATURE: float = 0.8  # 미션은 다양성이 좋아 약간 높게

# 부활/되살림 표현 — 미션에 섞이면 제외(2차 가드).
_FORBIDDEN: tuple[str, ...] = ("부활", "환생", "되살", "다시살아")


# --------------------------------------------------------------------------- #
# 규칙 풀 — LLM 폴백/보충용. 난이도별 (제목, 설명, 카테고리).
# --------------------------------------------------------------------------- #
_RULE_POOL: dict[str, tuple[tuple[str, str, str], ...]] = {
    "gentle": (
        ("물 한 잔 마시기", "천천히 물 한 잔을 마시며 숨을 고르세요.", "rest"),
        ("창문 열고 바람 쐬기", "잠시 창문을 열어 바깥 공기를 느껴보세요.", "rest"),
        ("햇빛 1분 쬐기", "창가나 문 앞에서 잠깐 햇빛을 쬐어보세요.", "rest"),
        ("좋아하는 음악 한 곡", "마음이 편해지는 음악을 한 곡 들어보세요.", "rest"),
        ("사진 한 장 바라보기", "함께한 사진 한 장을 천천히 바라보세요.", "remembrance"),
        ("눈 감고 숨 세 번", "눈을 감고 천천히 깊게 숨을 세 번 쉬어보세요.", "rest"),
        ("담요 덮고 쉬기", "따뜻한 담요를 덮고 잠시 몸을 쉬게 해주세요.", "rest"),
        ("좋아하는 간식 하나", "좋아하는 간식을 천천히 먹으며 잠시 쉬어가세요.", "rest"),
        ("이름 한 번 불러보기", "반려동물의 이름을 조용히 한 번 불러보세요.", "remembrance"),
        ("오늘 감정 한 줄", "지금 느끼는 감정을 한 줄로만 적어보세요.", "record"),
    ),
    "small": (
        ("집 앞 5분 산책", "집 근처를 5분만 천천히 걸어보세요.", "activity"),
        ("따뜻한 차 한 잔", "따뜻한 차를 우려 천천히 마셔보세요.", "rest"),
        ("추억 한 가지 적기", "함께한 기억 하나를 짧게 적어보세요.", "record"),
        ("물건 하나 정리하기", "반려동물의 물건 하나를 천천히 정리해보세요.", "remembrance"),
        ("안부 한 줄 보내기", "가족이나 친구에게 짧게 안부를 전해보세요.", "connection"),
        ("좋아했던 장소 떠올리기", "함께 자주 갔던 곳을 떠올리며 잠시 머물러보세요.", "remembrance"),
        ("10분 가볍게 스트레칭", "몸을 가볍게 풀어주며 일상의 감각을 되찾아보세요.", "activity"),
        ("오늘 잘한 일 하나", "오늘 스스로 잘했다고 느낀 일 하나를 적어보세요.", "record"),
        ("창밖 풍경 바라보기", "창밖을 5분만 바라보며 지금 이 순간에 머물러보세요.", "rest"),
        ("고마운 것 세 가지", "오늘 고마웠던 것 세 가지를 짧게 적어보세요.", "record"),
    ),
    "active": (
        ("산책길 다시 걷기", "둘이 함께 걷던 길을 천천히 걸어보세요.", "remembrance"),
        ("친구와 짧은 통화", "편한 사람과 잠시 통화해보세요.", "connection"),
        ("추억 사진 정리하기", "함께한 사진을 모아 앨범으로 정리해보세요.", "record"),
        ("가까운 곳 다녀오기", "가보고 싶던 가까운 곳에 잠시 들러보세요.", "activity"),
        ("작은 화분 돌보기", "식물 하나를 돌보며 일상의 리듬을 찾아보세요.", "activity"),
        ("편지 한 통 쓰기", "반려동물에게 전하고 싶은 말을 편지로 써보세요.", "record"),
        ("새로운 산책 코스", "한 번도 안 가본 길을 30분 걸어보세요.", "activity"),
        ("맛있는 식사 차리기", "스스로를 위해 좋아하는 음식을 차려보세요.", "activity"),
        ("가족 모임 제안하기", "가족이나 친한 친구와 만남을 잡아보세요.", "connection"),
        ("추억 영상 만들기", "함께한 사진들로 짧은 슬라이드를 만들어보세요.", "record"),
    ),
}


def _difficulty(emotion_score: Optional[int]) -> str:
    """감정 점수 → 난이도. 점수가 없으면 중간(small)."""
    if emotion_score is None:
        return "small"
    if emotion_score <= 3:
        return "gentle"
    if emotion_score <= 6:
        return "small"
    return "active"


def _is_safe(mission: dict) -> bool:
    """미션 문구에 금지 표현(부활 등)이 없는지."""
    text = (mission.get("title", "") + mission.get("description", "")).replace(" ", "")
    return not any(bad in text for bad in _FORBIDDEN)


def _rule_missions(difficulty: str, exclude: set[str], count: int) -> list[dict]:
    """규칙 풀에서 exclude 를 제외하고 count 개를 뽑습니다."""
    out: list[dict] = []
    for title, desc, category in _RULE_POOL[difficulty]:
        if title in exclude:
            continue
        out.append({"title": title, "description": desc, "category": category})
        if len(out) >= count:
            break
    return out


def _parse_llm(raw: str) -> list[dict]:
    """LLM JSON 출력을 미션 리스트로 파싱(형식이 깨지면 빈 리스트)."""
    data = json.loads(raw)
    items = data.get("missions") if isinstance(data, dict) else data
    if not isinstance(items, list):
        return []
    result: list[dict] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        title = str(it.get("title", "")).strip()
        if not title:
            continue
        category = it.get("category")
        result.append(
            {
                "title": title,
                "description": str(it.get("description", "")).strip(),
                "category": (
                    category if category in mission_prompt.CATEGORIES else "activity"
                ),
            }
        )
    return result


def recommend(
    emotion_score: Optional[int],
    day_since: Optional[int] = None,
    history: Optional[list[str]] = None,
    *,
    generate: Optional[GenerateFn] = None,
    count: int = 3,
) -> list[dict]:
    """회복 미션을 추천합니다.

    Args:
        emotion_score: 보호자 감정 점수(1~10, 낮을수록 힘듦). None 이면 중간 난이도.
        day_since: 반려동물을 떠나보낸 뒤 경과일(선택).
        history: 최근 추천/완료한 미션 제목(중복 회피).
        generate: LLM 호출 함수(provider.generate). None 이면 규칙 기반만 사용.
        count: 추천 개수.

    Returns:
        ``[{title, description, category}, ...]`` (최대 count 개).
    """
    difficulty = _difficulty(emotion_score)
    recent: set[str] = set(history or [])
    score = emotion_score if emotion_score is not None else 5

    missions: list[dict] = []

    # LLM 개인화 시도 — 실패/이상 출력이면 조용히 폴백.
    if generate is not None:
        try:
            prompt = mission_prompt.build_prompt(
                emotion_score=score,
                difficulty=difficulty,
                day_since=day_since,
                recent_titles=sorted(recent),
                count=count,
            )
            raw = generate(
                prompt,
                max_tokens=_MAX_TOKENS,
                temperature=_TEMPERATURE,
                json_mode=True,
            )
            for m in _parse_llm(raw):
                if m["title"] not in recent and _is_safe(m):
                    missions.append(m)
        except Exception:  # noqa: BLE001 — 추론 실패는 폴백으로 흡수(graceful)
            missions = []

    # 부족분은 규칙 풀로 보충(=LLM 미사용 시 전량 규칙 폴백).
    if len(missions) < count:
        used = recent | {m["title"] for m in missions}
        missions += _rule_missions(difficulty, used, count - len(missions))

    return missions[:count]
