"""⑤ 미션 추천 테스트 — LLM 없이 규칙·폴백·주입 경로를 검증.

  1. 규칙 기반(LLM 미주입) — 난이도 매핑·개수·중복 회피·구조
  2. LLM 주입 — 정상 JSON 사용 / 깨진 출력·실패 시 폴백
  3. 가드 — 부활 표현 미션 제외
"""

from __future__ import annotations

import json

from ..mission import recommend
from ..prompts import mission as mission_prompt


# --- 1. 규칙 기반 (generate 미주입) ----------------------------------------- #


def test_rule_based_returns_count():
    result = recommend(emotion_score=2, count=3)
    assert len(result) == 3
    for m in result:
        assert set(m) == {"title", "description", "category", "rationale"}
        assert m["category"] in mission_prompt.CATEGORIES
        # 근거는 카테고리별 회복 근거와 정확히 일치(코드 부착).
        assert m["rationale"] == mission_prompt.CATEGORY_RATIONALE[m["category"]]


def test_low_score_gives_gentle_missions():
    """감정 점수가 낮으면(무기력) gentle 풀에서 나온다."""
    result = recommend(emotion_score=1, count=5)
    titles = {m["title"] for m in result}
    assert "물 한 잔 마시기" in titles or "창문 열고 바람 쐬기" in titles


def test_high_score_gives_active_missions():
    result = recommend(emotion_score=9, count=5)
    titles = {m["title"] for m in result}
    assert "친구와 짧은 통화" in titles or "가까운 곳 다녀오기" in titles


def test_none_score_defaults_to_small():
    result = recommend(emotion_score=None, count=3)
    assert len(result) == 3


# --- 1-b. 논문 재설정: 난이도 × 권장 카테고리 정합 -------------------------- #


def test_gentle_surfaces_diverse_prescribed_categories():
    """재설정: gentle 은 rest 도배가 아니라 기록·추모·자기돌봄이 '고루' 나온다(라운드로빈)."""
    result = recommend(emotion_score=1, count=3)
    cats = [m["category"] for m in result]
    prescribed = set(mission_prompt.DIFFICULTY_CATEGORIES["gentle"])
    assert all(c in prescribed for c in cats)
    assert len(set(cats)) >= 2  # 한 분류 도배 방지(이전 버그: rest 3개)
    assert "record" in cats or "remembrance" in cats  # 글쓰기/추모 최소 1개


def test_small_surfaces_prescribed_categories():
    """재설정: small 은 행동활성화·사회적지지(activity·connection)가 먼저 노출된다."""
    result = recommend(emotion_score=5, count=5)
    prescribed = set(mission_prompt.DIFFICULTY_CATEGORIES["small"])
    assert all(m["category"] in prescribed for m in result)


def test_prompt_includes_category_hint():
    """LLM 프롬프트에 난이도별 권장 분류가 명시된다(텍스트 권유 → 분류 제약)."""
    prompt = mission_prompt.build_prompt(emotion_score=2, difficulty="gentle", count=3)
    assert "권장 분류" in prompt
    assert "record" in prompt and "remembrance" in prompt


def test_history_avoided():
    """history 에 있는 미션은 추천에서 제외된다."""
    first = recommend(emotion_score=2, count=2)
    avoid = [first[0]["title"]]
    again = recommend(emotion_score=2, history=avoid, count=2)
    assert avoid[0] not in {m["title"] for m in again}


# --- 2. LLM 주입 ------------------------------------------------------------ #


def _fake_llm(missions):
    payload = json.dumps({"missions": missions}, ensure_ascii=False)

    def gen(prompt, *, max_tokens=512, temperature=0.8, json_mode=False):
        assert json_mode is True  # 미션은 JSON 강제
        return payload

    return gen


def test_llm_output_used_when_valid():
    fake = _fake_llm(
        [
            {
                "title": "편지 한 줄 쓰기",
                "description": "짧게 적어보세요.",
                "category": "record",
            },
            {
                "title": "창밖 보기",
                "description": "잠시 바깥을 보세요.",
                "category": "rest",
            },
            {"title": "차 한 잔", "description": "따뜻하게.", "category": "rest"},
        ]
    )
    result = recommend(emotion_score=5, generate=fake, count=3)
    assert {m["title"] for m in result} == {"편지 한 줄 쓰기", "창밖 보기", "차 한 잔"}


def test_rationale_attached_to_llm_missions():
    """LLM 이 만든 미션에도 카테고리 기준 근거가 붙는다(환각 아닌 큐레이션 근거)."""
    fake = _fake_llm(
        [
            {
                "title": "편지 한 줄 쓰기",
                "description": "짧게 적어보세요.",
                "category": "record",
            }
        ]
    )
    result = recommend(emotion_score=5, generate=fake, count=1)
    assert result[0]["rationale"] == mission_prompt.CATEGORY_RATIONALE["record"]


def test_llm_broken_output_falls_back_to_rule():
    def bad_gen(prompt, *, max_tokens=512, temperature=0.8, json_mode=False):
        return "이건 JSON 이 아닙니다"

    result = recommend(emotion_score=2, generate=bad_gen, count=3)
    assert len(result) == 3  # 폴백으로 채워짐


def test_llm_failure_falls_back_to_rule():
    def boom(prompt, *, max_tokens=512, temperature=0.8, json_mode=False):
        raise RuntimeError("LLM 다운")

    result = recommend(emotion_score=2, generate=boom, count=3)
    assert len(result) == 3


def test_llm_short_output_topped_up_by_rule():
    """LLM 이 1개만 주면 나머지는 규칙 풀로 보충해 count 를 채운다."""
    fake = _fake_llm(
        [{"title": "딱 하나", "description": "유일한 미션.", "category": "rest"}]
    )
    result = recommend(emotion_score=2, generate=fake, count=3)
    assert len(result) == 3
    assert result[0]["title"] == "딱 하나"


# --- 3. 가드 ---------------------------------------------------------------- #


def test_resurrection_mission_filtered():
    fake = _fake_llm(
        [
            {
                "title": "봄이 부활시키기",
                "description": "다시 살아나길.",
                "category": "rest",
            },
            {"title": "산책 가기", "description": "5분만.", "category": "activity"},
        ]
    )
    result = recommend(emotion_score=5, generate=fake, count=3)
    assert all("부활" not in m["title"] for m in result)
