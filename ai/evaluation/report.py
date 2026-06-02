"""⑧ 평가 리포트 집계 (골격).

지표(초안, 팀 합의): 사용 횟수 · 감정 변화 추이 · 미션 완료율 · 재방문.

설계 원칙: 집계 함수는 **순수 함수**로 둡니다. DB 조회는 백엔드(김윤한)가 하고,
여기엔 조회 결과(리스트)를 넣어 줍니다. 그래야 GPU/DB 없이도 테스트 가능합니다.
(`build_report` 가 데이터를 인자로 받는 이유)

🚧 감정 추이·재방문 등 일부 지표는 백엔드 스키마(②감정체크인·⑥타임라인) 확정 후
   필드명을 맞춰야 합니다 — TODO 표시.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Iterable, Optional


def _completion_rate(missions: Iterable[dict[str, Any]]) -> Optional[float]:
    """미션 완료율(0~1). 미션이 없으면 None."""
    items = list(missions)
    if not items:
        return None
    done = sum(1 for m in items if m.get("done"))
    return round(done / len(items), 3)


def _emotion_trend(checkins: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    """감정 체크인을 시간순으로 정리한 추이 데이터(프론트 차트용).

    🚧 mood 필드 표현(점수/카테고리)은 ② 감정 체크인 스키마 확정 후 맞춤.
    지금은 {created_at, mood} 를 그대로 시간순 정렬해 넘깁니다.
    """
    rows = [
        {"created_at": c.get("created_at"), "mood": c.get("mood")}
        for c in checkins
    ]
    return sorted(rows, key=lambda r: str(r["created_at"]))


def build_report(
    pet_id: str,
    period: Optional[str] = None,
    *,
    llm_logs: Iterable[dict[str, Any]] = (),
    emotion_checkins: Iterable[dict[str, Any]] = (),
    missions: Iterable[dict[str, Any]] = (),
) -> dict[str, Any]:
    """반려동물별 사용 데이터를 리포트로 집계합니다.

    Args:
        pet_id: 대상 반려동물.
        period: 집계 기간 라벨(예: "2026-06"). 필터링은 호출부(백엔드)에서.
        llm_logs: `llm_logs` 조회 결과(이미 pet_id·기간으로 필터됨).
        emotion_checkins: 감정 체크인 조회 결과.
        missions: 미션 조회 결과.

    Returns:
        프론트 차트/요약 UI 용 리포트 dict.
        (출력 스키마는 민경이와 확정 후 고정 — TODO)
    """
    logs = list(llm_logs)
    kind_counts = Counter(log.get("kind") for log in logs)

    return {
        "pet_id": pet_id,
        "period": period,
        "usage": {
            "total_calls": len(logs),
            "by_kind": dict(kind_counts),
        },
        "emotion_trend": _emotion_trend(emotion_checkins),
        "mission_completion_rate": _completion_rate(missions),
        # 🚧 재방문(revisit): 세션/접속 로그 스키마 확정 후 추가 (백엔드 합의)
        "revisit": None,
    }
