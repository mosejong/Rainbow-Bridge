"""회복 추이(recovery_trend) 반영 검증 — 미션 난이도 보정 + 메시지 톤 캘리브레이션.

백엔드 get_recovery 의 trend("회복 중"·"유지 중"·"주의 필요"·"데이터 없음")가
⑤ 미션 난이도와 ③ 메시지 톤에 제대로 반영되는지 확인하는 수동 점검 도구.

기본 모드는 **가짜 generate** 로 동작 → API 키·Redis·실제 LLM 없이 즉시 검증되며,
백엔드 경로 통합(협의 중)과 무관하게 지금 돌릴 수 있습니다.

사용 (레포 루트에서):
    python -m ai.llm.validate_recovery_trend          # 결정적 검증(빠름, API 불필요)
    python -m ai.llm.validate_recovery_trend --llm    # 실제 LLM 톤 비교(.env 필요)

결과는 ai/llm/validate_recovery_trend_result.txt 에도 저장됩니다.
"""

from __future__ import annotations

import io
import sys
import time

import ai.llm.memorial as memorial_module
from .memorial import generate_message
from .mission import _apply_trend, _difficulty, recommend
from .prompts import memorial as memorial_prompt
from .prompts import mission as mission_prompt

# Windows 터미널 인코딩 문제 우회 — UTF-8 강제
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

_RESULT_FILE = "ai/llm/validate_recovery_trend_result.txt"
_DELAY_SEC = 45.0

# 백엔드 trend 값 4종 + None. 띄어쓰기 포함 형태로 그대로 검증.
_TRENDS: tuple[str | None, ...] = ("회복 중", "유지 중", "주의 필요", "데이터 없음", None)

# 같은 점수에서 추이만 달라질 때 기대 난이도(점수 5 → base small).
#   회복 중 → 한 단계 ↑(active) · 주의 필요 → 한 단계 ↓(gentle) · 그 외 → 유지(small)
_EXPECT_DIFFICULTY: dict[str | None, str] = {
    "회복 중": "active",
    "유지 중": "small",
    "주의 필요": "gentle",
    "데이터 없음": "small",
    None: "small",
}


def _echo_generate(prompt: str, **_: object) -> str:
    """가짜 LLM — 프롬프트에 회복 추이 줄이 들어왔는지 표시해 돌려줍니다."""
    has_trend = "회복 추이" in prompt
    return f"[추이주입={has_trend}] 봄이는 늘 곁에서 환하게 웃어주었죠. 그 따뜻함은 잊지 않을게요."


def _check_difficulty(out, fails: list[str]) -> None:
    out("\n" + "=" * 70)
    out("[1] 미션 난이도 보정 — 같은 점수(5)에서 추이만 변경")
    out("=" * 70)
    base = _difficulty(5)
    out(f"  점수 5 기준 base 난이도: {base}")
    for trend in _TRENDS:
        got = _apply_trend(base, trend)
        want = _EXPECT_DIFFICULTY[trend]
        ok = got == want
        mark = "PASS" if ok else "FAIL"
        out(f"  [{mark}] trend={str(trend):8} → {got:7} (기대 {want})")
        if not ok:
            fails.append(f"난이도 보정: trend={trend} got={got} want={want}")

    # 천장·바닥 클램프
    out("  -- 경계(클램프) --")
    for difficulty, trend, want in (
        ("active", "회복 중", "active"),
        ("gentle", "주의 필요", "gentle"),
    ):
        got = _apply_trend(difficulty, trend)
        ok = got == want
        out(f"  [{'PASS' if ok else 'FAIL'}] {difficulty}+{trend} → {got} (기대 {want})")
        if not ok:
            fails.append(f"클램프: {difficulty}+{trend} got={got} want={want}")


def _check_mission_prompt(out, fails: list[str]) -> None:
    out("\n" + "=" * 70)
    out("[2] 미션 프롬프트 — 추이 주입 / 데이터없음·None 생략")
    out("=" * 70)
    for trend in _TRENDS:
        prompt = mission_prompt.build_prompt(
            emotion_score=5, difficulty="small", recovery_trend=trend
        )
        injected = "회복 추이" in prompt
        # "데이터 없음"·None 은 생략(graceful), 나머지는 주입돼야 함.
        want = trend not in ("데이터 없음", None)
        ok = injected == want
        out(f"  [{'PASS' if ok else 'FAIL'}] trend={str(trend):8} → 주입={injected} (기대 {want})")
        if not ok:
            fails.append(f"미션 프롬프트 주입: trend={trend} injected={injected} want={want}")


def _check_memorial_prompt(out, fails: list[str]) -> None:
    out("\n" + "=" * 70)
    out("[3] 메시지 프롬프트 — 추이 주입(톤 캘리브레이션) / 생략")
    out("=" * 70)
    for trend in _TRENDS:
        up = memorial_prompt.build_user_prompt(
            name="봄이", species="강아지", period="12년", score=5, recovery_trend=trend
        )
        line = next((ln for ln in up.splitlines() if "회복 추이" in ln), "")
        injected = bool(line)
        want = trend not in ("데이터 없음", None)
        ok = injected == want
        out(f"  [{'PASS' if ok else 'FAIL'}] trend={str(trend):8} → 주입={injected} (기대 {want})")
        if line:
            out(f"        {line.strip()}")
        if not ok:
            fails.append(f"메시지 프롬프트 주입: trend={trend} injected={injected} want={want}")


def _check_crisis_priority(out, fails: list[str]) -> None:
    """🚨 위기 신호가 있으면 추이가 '회복 중'이어도 1393 안내가 우선이어야 함."""
    out("\n" + "=" * 70)
    out("[4] 🚨 위기 우선순위 — 추이가 '회복 중'이어도 위기면 1393 우선")
    out("=" * 70)
    result = generate_message(
        {"name": "봄이", "species": "강아지", "period": "12년"},
        {"emotion_score": 5, "note": "더는 못 살겠어요. 저도 따라가고 싶어요."},
        generate=_echo_generate,
        recovery_trend="회복 중",
    )
    is_safety = result.get("source") == "safety"
    out(f"  [{'PASS' if is_safety else 'FAIL'}] source={result.get('source')} "
        f"(기대 safety — 추이보다 위기 선체크가 우선)")
    if not is_safety:
        fails.append("위기 우선순위: 회복중 추이가 위기 안내를 덮음")


def _check_backward_compat(out, fails: list[str]) -> None:
    out("\n" + "=" * 70)
    out("[5] 하위호환 — recovery_trend 없이 호출 시 기존대로 동작")
    out("=" * 70)
    msg = generate_message(
        {"name": "봄이", "species": "강아지", "period": "12년"},
        {"emotion_score": 5},
        generate=lambda p, **k: "봄이는 좋은 친구였어요. 늘 기억할게요.",
    )
    missions = recommend(5, generate=None, count=3)
    ok = msg.get("source") == "local" and len(missions) == 3
    out(f"  [{'PASS' if ok else 'FAIL'}] 메시지 source={msg.get('source')}, 미션 {len(missions)}개")
    if not ok:
        fails.append("하위호환 실패")


def _llm_tone_compare(out) -> None:
    """실제 LLM 으로 같은 케이스를 회복중 vs 주의필요로 생성해 톤 차이를 눈으로 비교.

    한 케이스가 실패(레이트리밋·타임아웃 등)해도 전체를 죽이지 않고 사유만 남기고
    다음 케이스로 넘어갑니다(graceful — ../CLAUDE.md §4 추론 실패 흡수).
    """
    from .provider import LLMError, generate as real_generate

    out("\n" + "=" * 70)
    out("[LLM] 실제 톤 비교 — 같은 케이스, 추이만 변경 (실제 API 호출)")
    out("=" * 70)
    pet = {"name": "봄이", "species": "강아지", "period": "12년",
           "memories": ["매일 현관에서 기다려준 것"]}
    emotion = {"emotion_score": 5, "note": "요즘 마음이 좀 달라요"}
    trends = ("회복 중", "주의 필요")
    for i, trend in enumerate(trends):
        out(f"\n▶ recovery_trend = {trend}")
        try:
            res = generate_message(pet, emotion, "warm",
                                   generate=real_generate, recovery_trend=trend)
            out(res.get("content", ""))
        except LLMError as e:
            # 무료 등급 일일 할당량(429) 등 — 코드 결함 아님. 사유만 남기고 계속.
            out(f"  (건너뜀 — LLM 호출 실패: {str(e).splitlines()[0]})")
        if i < len(trends) - 1:
            time.sleep(_DELAY_SEC)


def main() -> None:
    lines: list[str] = []

    def out(s: str = "") -> None:
        print(s)
        lines.append(s)

    fails: list[str] = []
    out("회복 추이(recovery_trend) 반영 검증 — 결정적(API 불필요)")

    _check_difficulty(out, fails)
    _check_mission_prompt(out, fails)
    _check_memorial_prompt(out, fails)
    _check_crisis_priority(out, fails)
    _check_backward_compat(out, fails)

    out("\n" + "=" * 70)
    if fails:
        out(f"실패 {len(fails)}건:")
        for f in fails:
            out(f"  - {f}")
    else:
        out("전체 통과 ✓")
    out("=" * 70)

    if "--llm" in sys.argv:
        _llm_tone_compare(out)

    with open(_RESULT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
