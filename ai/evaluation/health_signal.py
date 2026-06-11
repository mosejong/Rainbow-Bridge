"""⑧-확장: 수면·활동 객관데이터 → 회복점수 반영 (프로토타입).

⑧ 평가 확장: 삼성헬스(→Health Connect 경유)에서 받은 **수면·활동 객관데이터**를
회복점수에 더하고, 주관 감정 체크인과 **교차검증**한다.

설계: [recovery_signal.py](recovery_signal.py) 와 동일하게 **순수 함수** — 데이터 소스
(삼성헬스/더미/수동입력)와 분리. 입력만 넣으면 점수가 나온다. 그래서 GPU/DB/실연동
없이도 더미로 바로 테스트된다. (삼성헬스 실연동은 개발 빌드에서 같은 입력에 꽂으면 끝)

⚠️ 기존 `recovery_score()` 함수 자체는 **안 건드린다.** `compute_recovery_signal()` 이
수면·활동 인자가 들어올 때만 `blend_recovery_score`(35/25/15/15/10)로 교체 호출한다
(미제공 시 기존 40/35/25 산식 그대로 — 하위호환). 가중치는 설계 판단이라 자유 조정.

가중치·임계값은 논문이 정해주는 값이 아니라 **설계 판단**(주석에 표시). 숫자는 자유롭게 조정.
"""

from __future__ import annotations

from typing import Any, Optional

# ── 가중치(합 100) — 수면·활동을 넣으려고 감정·미션·꾸준함에서 떼옴. 조정 가능. ──
W_EMOTION = 35.0  # 주관 감정 평균
W_MISSION = 25.0  # 미션 누적(천장)
W_CONSISTENCY = 15.0  # 체크인 꾸준함
W_SLEEP = 15.0  # 수면 객관
W_ACTIVITY = 10.0  # 활동 객관
# 합 = 100
_MISSION_CAP = 25.0  # 미션 만점 기준(개수) — 가중치 W_MISSION 과 별개로 정규화에 사용

# ── 교차검증 임계값(설계 판단) ──
_SLEEP_BAD = 40.0  # 수면점수 이 미만이면 '나쁨'
_SLEEP_GOOD = 70.0  # 이 이상이면 '좋음'
_EMOTION_GOOD = 6.0  # 감정 평균(1~10) 이 이상이면 '좋음'
_EMOTION_BAD = 4.0  # 이 이하면 '나쁨'

# ── 활동량 정규화 기준(설계 판단) ──
_STEPS_TARGET = 8000  # 이 걸음수를 100점으로


def sleep_to_score(
    sleep_score: Optional[float] = None, sleep_hours: Optional[float] = None
) -> Optional[float]:
    """수면 → 0~100 점수.

    - 삼성헬스 **수면점수(0~100)** 가 있으면 그대로 사용(가장 정확).
    - 없고 **수면시간** 만 있으면 7~9시간을 최적(100)으로 보고 환산.
    - 둘 다 없으면 None(graceful — 점수에서 수면 항 0 취급).
    """
    if sleep_score is not None:
        return max(0.0, min(100.0, float(sleep_score)))
    if sleep_hours is not None:
        h = float(sleep_hours)
        # 8h 중심, ±1h 까지 만점, 멀어질수록 감점(설계 판단).
        if 7.0 <= h <= 9.0:
            return 100.0
        gap = 7.0 - h if h < 7.0 else h - 9.0
        return max(0.0, 100.0 - gap * 20.0)  # 1시간 벗어날 때마다 20점
    return None


def activity_to_score(steps: Optional[int] = None) -> Optional[float]:
    """활동(걸음수) → 0~100 점수. 목표 걸음(_STEPS_TARGET)을 100으로 선형 환산.

    ⚠️ steps=0 은 "실제 0걸음"으로 보고 0점 반환(None 아님). "측정 안 됨"은 None 으로
    구분해 호출부에서 넘긴다(어댑터 `total_steps` 는 레코드 없으면 None).
    """
    if steps is None:
        return None
    return max(0.0, min(100.0, float(steps) / _STEPS_TARGET * 100.0))


def blend_recovery_score(
    emotion_avg: float,
    completed_missions: int = 0,
    consistency_pct: Optional[float] = None,
    sleep_score: Optional[float] = None,
    activity_score: Optional[float] = None,
) -> int:
    """회복점수(0~100) — 감정·미션·꾸준함 + **수면·활동** 가중합.

    옵션 A(재정규화): 빠진 **외부 신호(수면·활동)** 는 분모에서 제외한다 → 데이터가
    없다고 점수가 깎이지 않는다. 핵심 항(감정·미션·꾸준함)은 항상 분모에 포함.
    각 항은 0~1 비율 × 가중치, 최종 = 포함된 가중치 합으로 나눠 0~100 정규화.
    """
    parts: list[tuple[float, float]] = [
        (max(0.0, min(1.0, (emotion_avg - 1) / 9)), W_EMOTION),
        (min(float(completed_missions), _MISSION_CAP) / _MISSION_CAP, W_MISSION),
        (max(0.0, min(1.0, (consistency_pct or 0.0) / 100)), W_CONSISTENCY),
    ]
    if sleep_score is not None:  # 외부 신호 — 있을 때만 분모에 포함
        parts.append((max(0.0, min(1.0, sleep_score / 100)), W_SLEEP))
    if activity_score is not None:
        parts.append((max(0.0, min(1.0, activity_score / 100)), W_ACTIVITY))
    total_w = sum(w for _, w in parts)
    if total_w == 0:
        return 0
    return max(0, min(100, round(sum(frac * w for frac, w in parts) / total_w * 100)))


def cross_check(
    sleep_score: Optional[float], emotion_avg: Optional[float]
) -> dict[str, Any]:
    """객관(수면) vs 주관(감정) 교차검증. 점수는 안 깎고 **플래그+근거문장**만.

    "센서는 나쁘다는데 본인은 괜찮다더라"(주관·객관 불일치) 케이스를 잡는다.
    """
    if sleep_score is None or emotion_avg is None:
        return {"status": "unknown", "mismatch": False, "note": None}

    sleep_bad = sleep_score < _SLEEP_BAD
    sleep_good = sleep_score >= _SLEEP_GOOD
    emo_good = emotion_avg >= _EMOTION_GOOD
    emo_bad = emotion_avg <= _EMOTION_BAD

    if sleep_bad and emo_good:
        return {
            "status": "mismatch_high_risk",
            "mismatch": True,
            "note": "수면은 낮은데 기분은 양호 — 숨기는 중일 수 있어요. 추가 관찰 필요.",
        }
    if sleep_good and emo_bad:
        return {
            "status": "mismatch",
            "mismatch": True,
            "note": "수면은 괜찮은데 기분은 가라앉음 — 수면 외 요인일 수 있어요.",
        }
    if sleep_bad and emo_bad:
        return {
            "status": "agree_low",
            "mismatch": False,
            "note": "수면·기분 모두 낮음 — 위험 신호의 신뢰도가 높아요.",
        }
    return {"status": "agree_ok", "mismatch": False, "note": None}


def health_signal(
    emotion_avg: float,
    *,
    completed_missions: int = 0,
    consistency_pct: Optional[float] = None,
    sleep_score: Optional[float] = None,
    sleep_hours: Optional[float] = None,
    steps: Optional[int] = None,
) -> dict[str, Any]:
    """수면·활동까지 묶은 회복 신호 한 방. 화면/발표에 그대로 쓸 dict 반환."""
    s_score = sleep_to_score(sleep_score, sleep_hours)
    a_score = activity_to_score(steps)
    index = blend_recovery_score(
        emotion_avg, completed_missions, consistency_pct, s_score, a_score
    )
    check = cross_check(s_score, emotion_avg)

    evidence: list[str] = [f"감정 평균 {round(emotion_avg, 1)}/10"]
    if s_score is not None:
        evidence.append(f"수면점수 {round(s_score)}/100")
    if a_score is not None:
        evidence.append(f"활동 {round(a_score)}/100 ({steps}걸음)")
    if check["note"]:
        evidence.append(f"⚠ {check['note']}")

    return {
        "recovery_index": index,
        "sleep_score": s_score,
        "activity_score": a_score,
        "cross_check": check,
        "evidence": evidence,
    }


if __name__ == "__main__":
    import sys

    # Windows 기본 콘솔(cp949)에서 ⚠ 등 유니코드 출력 크래시 방지.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # 더미 시나리오 — 삼성헬스 없이 로직 검증.
    scenarios = [
        (
            "좋음 일치",
            dict(
                emotion_avg=8,
                completed_missions=10,
                consistency_pct=80,
                sleep_score=82,
                steps=9000,
            ),
        ),
        (
            "나쁨 일치",
            dict(
                emotion_avg=3,
                completed_missions=2,
                consistency_pct=30,
                sleep_score=35,
                steps=1500,
            ),
        ),
        (
            "센서 나쁨·본인 좋다",
            dict(
                emotion_avg=8,
                completed_missions=5,
                consistency_pct=50,
                sleep_score=32,
                steps=2000,
            ),
        ),
        ("수면시간만 있음", dict(emotion_avg=6, sleep_hours=5.5, steps=6000)),
    ]
    for name, kw in scenarios:
        out = health_signal(**kw)
        print(f"\n[{name}]  회복점수 = {out['recovery_index']}")
        print(f"  교차검증: {out['cross_check']['status']}")
        for e in out["evidence"]:
            print(f"  - {e}")
