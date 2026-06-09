"""⑧-확장: 일상복귀 신호 — 정량 분석.

목표(피드백): "재생횟수·접속빈도·감정추이로 '앱 쓰니 일상복귀 빨라졌다'를 입증."
감정 점수 추이 + 미션 완료율 + (있으면) 접속/재생 빈도를 묶어 **일상복귀 신호**
(회복 중 / 유지 중 / 주의 필요)를 산출합니다.

설계: [report.py](report.py) 와 동일하게 **순수 함수** — DB 조회는 백엔드/호출부가 하고
여기엔 조회 결과(리스트)를 넣어 줍니다. 그래야 GPU/DB 없이 테스트·시뮬레이션이 됩니다.
`build_report` 통합·엔드포인트 노출은 정환주(report.py)와 합의 후.

데이터 출처(PR #158, 머지됨):
- 접속빈도: `access_logs` 컬렉션(로그인마다 `accessed_at`) → 기간별로 묶어 `access_counts` 로.
- 재생횟수: `MediaAsset.play_count`(누적 카운터). ⚠️ per-play 타임스탬프가 없어 '추세'를
  직접 못 냄 → 재생 이벤트 로그가 생기면 `play_counts`(기간별 시계열)로 연결.

핵심 통찰(피드백): "접속/재생이 줄면서 감정이 오르면 = 일상으로 돌아간 신호."
→ 빈도 '감소'는 감정이 '상승/유지'일 때만 회복 근거로 읽습니다(이탈·방치와 구분).
"""

from __future__ import annotations

from typing import Any, Iterable, Optional, Sequence

# 신호 라벨 — 백엔드 get_recovery 의 trend 와 동일 어휘로 맞춥니다(혼선 방지).
SIGNAL_RECOVERING = "회복 중"
SIGNAL_STABLE = "유지 중"
SIGNAL_AT_RISK = "주의 필요"
SIGNAL_INSUFFICIENT = "데이터 부족"

_MIN_CHECKINS = 3  # 신호를 내기 위한 최소 감정 체크인 수
_DELTA = 0.5  # 감정 추이 상승/하락 판정 폭(점) — get_recovery 와 동일


def _scores_oldest_first(checkins: Iterable[dict[str, Any]]) -> list[float]:
    """감정 체크인을 시간순(오래된→최근)으로 정렬해 점수만 뽑습니다."""
    rows = sorted(checkins, key=lambda c: str(c.get("created_at") or ""))
    return [float(c.get("score", 0) or 0) for c in rows]


def _split_avg(series: Sequence[float]) -> tuple[float, float]:
    """시계열을 앞(오래된)·뒤(최근) 절반으로 나눠 각 평균을 냅니다."""
    n = len(series)
    mid = n // 2  # 홀수면 최근 쪽을 한 칸 더 길게
    older = series[:mid] or series[:1]
    recent = series[mid:]
    return sum(older) / len(older), sum(recent) / len(recent)


def _completion_rate(missions: Iterable[dict[str, Any]]) -> Optional[float]:
    """미션 완료율(0~1). 미션이 없으면 None."""
    items = list(missions)
    if not items:
        return None
    done = sum(1 for m in items if m.get("done"))
    return round(done / len(items), 3)


def _freq_trend(counts: Optional[Sequence[float]]) -> Optional[dict[str, Any]]:
    """기간별 빈도 시계열 → 추세 dict. 데이터가 2개 미만이면 None(추세 판단 불가)."""
    if not counts or len(counts) < 2:
        return None
    series = [float(x) for x in counts]
    older, recent = _split_avg(series)
    delta = recent - older
    direction = "감소" if delta < 0 else "증가" if delta > 0 else "유지"
    return {
        "older": round(older, 2),
        "recent": round(recent, 2),
        "delta": round(delta, 2),
        "direction": direction,
    }


def compute_recovery_signal(
    emotion_checkins: Iterable[dict[str, Any]],
    missions: Iterable[dict[str, Any]] = (),
    *,
    access_counts: Optional[Sequence[float]] = None,
    play_counts: Optional[Sequence[float]] = None,
) -> dict[str, Any]:
    """일상복귀 신호를 산출합니다.

    Args:
        emotion_checkins: 감정 체크인 목록 ``[{score, created_at}, ...]``(순서 무관, 내부 정렬).
        missions: 미션 목록 ``[{done: bool}, ...]``. 없으면 완료율 생략.
        access_counts: 기간별 앱 접속 횟수(오래된→최근). `access_logs` 를 일/주 단위로
            묶어 넣습니다. 없으면 생략(graceful).
        play_counts: 기간별 영상 재생 횟수(오래된→최근). 재생 이벤트 로그가 있을 때만.
            ⚠️ `play_count` 누적 카운터만 있으면 시계열이 아니라 못 넣음 → None.

    Returns:
        ``{signal, recovery_index, emotion, mission_completion_rate, access_trend,
        play_trend, evidence, reason}`` — 발표/프론트 차트·요약용.
        ``evidence`` 는 그대로 보여줄 수 있는 근거 문장 목록.
    """
    scores = _scores_oldest_first(emotion_checkins)

    if len(scores) < _MIN_CHECKINS:
        return {
            "signal": SIGNAL_INSUFFICIENT,
            "recovery_index": None,
            "emotion": None,
            "mission_completion_rate": _completion_rate(missions),
            "access_trend": None,
            "play_trend": None,
            "evidence": [f"감정 체크인이 {len(scores)}회뿐이라 신호를 내기 어려워요(최소 {_MIN_CHECKINS}회)."],
            "reason": "아직 데이터가 적어요. 체크인이 쌓이면 회복 추이를 보여드릴게요.",
        }

    older, recent = _split_avg(scores)
    delta = recent - older
    avg = sum(scores) / len(scores)

    if delta > _DELTA:
        emo_dir, signal = "상승", SIGNAL_RECOVERING
    elif delta < -_DELTA:
        emo_dir, signal = "하락", SIGNAL_AT_RISK
    else:
        emo_dir, signal = "유지", SIGNAL_STABLE

    completion = _completion_rate(missions)
    access = _freq_trend(access_counts)
    play = _freq_trend(play_counts)

    # 근거 문장 — 발표/화면에 그대로 노출.
    evidence = [f"감정 점수 {round(older, 1)} → {round(recent, 1)} ({emo_dir})"]
    if completion is not None:
        evidence.append(f"미션 완료율 {round(completion * 100)}%")
    for label, trend in (("앱 접속", access), ("영상 재생", play)):
        if not trend:
            continue
        if trend["direction"] == "감소" and signal != SIGNAL_AT_RISK:
            evidence.append(
                f"{label} {trend['older']}→{trend['recent']}회 (감소 — 앱 의존이 줄어드는 회복 신호)"
            )
        else:
            evidence.append(f"{label} {trend['older']}→{trend['recent']}회 ({trend['direction']})")

    reason = {
        SIGNAL_RECOVERING: "감정이 오르고 있어요. 일상으로 돌아가는 신호입니다.",
        SIGNAL_STABLE: "큰 변화 없이 안정적으로 지내고 있어요.",
        SIGNAL_AT_RISK: "최근 감정이 가라앉고 있어요. 더 세심한 돌봄이 필요해요.",
    }[signal]

    return {
        "signal": signal,
        "recovery_index": round(avg * 10),  # 0~100, get_recovery 의 recovery_pct 와 동일 척도
        "emotion": {
            "older_avg": round(older, 1),
            "recent_avg": round(recent, 1),
            "delta": round(delta, 1),
            "direction": emo_dir,
        },
        "mission_completion_rate": completion,
        "access_trend": access,
        "play_trend": play,
        "evidence": evidence,
        "reason": reason,
    }
