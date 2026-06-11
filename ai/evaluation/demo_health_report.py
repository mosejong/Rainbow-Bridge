"""수면·활동 객관데이터 → 회복점수 — 발표용 전체 파이프라인 데모.

⚠️ 여기 수치는 **실데이터가 아니라 가상 시나리오**입니다(발표에서 "시뮬레이션"이라 밝힐 것).
삼성헬스 실연동(개발 빌드)이 붙으면 같은 함수가 실데이터로 동작합니다.

보여주려는 이야기:
    "주관 감정 체크인뿐 아니라 삼성헬스의 객관적 수면·활동을 함께 반영해 상태를 추정한다.
     특히 '센서는 나쁜데 본인은 괜찮다'는 불일치도 잡아낸다."

흐름(실제 서비스 경로 그대로):
    삼성헬스 더미 JSON → from_health_connect → build_report(sleep/steps) → recovery_signal + cross_check

실행 (레포 루트에서):
    python -m ai.evaluation.demo_health_report
"""

from __future__ import annotations

import io
import sys

from .health_adapter import from_health_connect
from .report import build_report

# Windows 콘솔 한글/이모지 인코딩 우회
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def _checkins(scores: list[int]) -> list[dict]:
    """오래된→최근 감정 점수(1~10)를 체크인 목록으로."""
    return [
        {"created_at": f"2026-06-{i + 1:02d}", "score": s} for i, s in enumerate(scores)
    ]


def _hc(
    steps_records: list[tuple[int, str, str]], sleep_records: list[tuple[str, str]]
):
    """삼성헬스→Health Connect readRecords 응답(JSON) 모양 더미 생성."""
    steps = {
        "records": [
            {"count": c, "startTime": s, "endTime": e} for c, s, e in steps_records
        ]
    }
    sleep = {
        "records": [
            {"startTime": s, "endTime": e, "stages": []} for s, e in sleep_records
        ]
    }
    return steps, sleep


# ── 시나리오: (이름, 감정 점수열, 삼성헬스 더미 or None) ──
_GOOD_STEPS, _GOOD_SLEEP = _hc(
    [
        (5000, "2026-06-11T08:00:00Z", "2026-06-11T18:00:00Z"),
        (4000, "2026-06-11T18:00:00Z", "2026-06-11T22:00:00Z"),
    ],
    [("2026-06-11T00:00:00Z", "2026-06-11T08:00:00Z")],  # 8시간
)
_BAD_STEPS, _BAD_SLEEP = _hc(
    [(1500, "2026-06-11T10:00:00Z", "2026-06-11T20:00:00Z")],
    [("2026-06-11T03:30:00Z", "2026-06-11T07:00:00Z")],  # 3.5시간
)

SCENARIOS = [
    (
        "① 좋음 일치 (감정↑·수면 좋음·활동 많음)",
        [3, 4, 5, 6, 7, 8, 8, 9],
        (_GOOD_STEPS, _GOOD_SLEEP),
    ),
    (
        "② 센서 나쁨·본인 좋다 (감정↑·수면 나쁨)",
        [7, 8, 8, 8, 9, 8, 9, 9],
        (_BAD_STEPS, _BAD_SLEEP),
    ),
    ("③ 헬스 없음 (주관 체크인만 — 비교용)", [3, 4, 5, 6, 7, 8, 8, 9], None),
]


def _run(name: str, scores: list[int], hc) -> None:
    kwargs: dict = {}
    if hc is not None:
        steps_res, sleep_res = hc
        parsed = from_health_connect(steps_res, sleep_res)  # {steps, sleep_hours}
        kwargs.update(parsed)

    report = build_report("demo_pet", emotion_checkins=_checkins(scores), **kwargs)
    sig = report["recovery_signal"]

    print(f"\n{'=' * 56}\n{name}")
    print(f"  회복점수 = {sig['recovery_index']}   (산식: {sig['scoring']})")
    print(f"  신호 = {sig['signal']}")
    if sig["cross_check"]:
        print(f"  교차검증 = {sig['cross_check']['status']}")
    print("  근거:")
    for e in sig["evidence"]:
        print(f"    - {e}")


if __name__ == "__main__":
    print("수면·활동 객관데이터 → 회복점수 (가상 시뮬레이션)")
    for name, scores, hc in SCENARIOS:
        _run(name, scores, hc)
    print(
        "\n핵심: ②처럼 '본인은 좋다고 했지만 수면 센서가 나쁜' 경우를 mismatch 로 잡아낸다.\n"
        "      ③(헬스 없음)은 기존 산식(base) 그대로 — 하위호환."
    )
