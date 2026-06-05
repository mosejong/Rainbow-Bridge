"""HHHHHMM 삶의 질(QoL) 척도 — 1단계(아플 때) 보호자 보조 지표.

반려동물의 삶의 질을 7개 항목으로 점수화해(각 0~10), 총점과 해석·수의사
상담 안내를 돌려주는 **순수 함수**입니다. (Villalobos 박사 HHHHHMM Scale 기반)

⚠️ 윤리 경계 (필수):
  - 이 모듈은 **보호자에게 참고 정보를 제공하는 보조 지표**일 뿐입니다.
  - 🚫 안락사 같은 결정을 AI가 대신 내리지 않습니다. 결과엔 항상 면책 문구를 답니다.
  - 결과엔 항상 **수의사 상담 안내**를 함께 넣습니다.
  - 보호자의 정서 위기(자해·극단 선택 등)는 이 모듈이 아니라 ⑦ 위기 감지(`ai/llm/safety`)가
    별도로 다룹니다. QoL 점수로 1393을 임의 연계하지 않습니다(오탐 방지).

설계: DB·LLM·GPU 없음. 같은 입력 → 항상 같은 출력(ai/evaluation 순수함수 패턴).
"""

from __future__ import annotations

from typing import Any, Final

# HHHHHMM 7개 항목(각 0~10, 10이 가장 좋음). 키 순서 고정.
QOL_CRITERIA: Final[tuple[str, ...]] = (
    "hurt",  # 통증 조절(아프지 않게 다뤄지는가)
    "hunger",  # 식사(잘 먹는가)
    "hydration",  # 수분(충분히 마시는가)
    "hygiene",  # 위생(청결 유지가 되는가)
    "happiness",  # 행복(관심·반응·기쁨이 있는가)
    "mobility",  # 거동(움직일 수 있는가)
    "more_good_days",  # 좋은 날이 나쁜 날보다 많은가
)

# 항목별 한글 라벨(해석 표시용).
CRITERIA_LABELS: Final[dict[str, str]] = {
    "hurt": "통증 조절",
    "hunger": "식사",
    "hydration": "수분",
    "hygiene": "위생",
    "happiness": "행복·반응",
    "mobility": "거동",
    "more_good_days": "좋은 날 비중",
}

_MIN_SCORE: Final[int] = 0
_MAX_SCORE: Final[int] = 10
_MAX_TOTAL: Final[int] = _MAX_SCORE * len(QOL_CRITERIA)  # 70

# 원 척도 권고: 항목 합이 35 이상이면 삶의 질 유지가 받아들일 만함.
_ACCEPTABLE_TOTAL: Final[int] = 35

_VET_REFERRAL: Final[str] = (
    "이 점수는 참고용입니다. 실제 상태 판단과 치료·완화 계획은 반드시 "
    "수의사와 상담하세요."
)
_DISCLAIMER: Final[str] = (
    "AI는 안락사를 결정하지 않습니다. 참고용 보조 지표입니다."
)


def score_qol(scores: dict[str, int]) -> dict[str, Any]:
    """7개 항목 점수를 받아 총점·등급·해석·안내를 돌려줍니다.

    Args:
        scores: `QOL_CRITERIA` 7개 키 전부 포함. 각 값은 0~10 정수.

    Returns:
        {
          "criteria": {항목키: 점수},
          "labels": {항목키: 한글라벨},
          "total": int(0~70),
          "max": 70,
          "tier": "maintainable" | "declining",
          "interpretation": str,        # 보호자용 한 줄 해석
          "low_items": [항목키, ...],    # 5점 미만(주의가 필요한 항목)
          "vet_referral": str,          # 항상 포함
          "disclaimer": str,            # 항상 포함(안락사 결정 ❌)
        }

    Raises:
        ValueError: 항목 누락·여분, 또는 점수가 정수 0~10 범위를 벗어난 경우.
    """
    missing = [k for k in QOL_CRITERIA if k not in scores]
    if missing:
        raise ValueError(f"누락된 항목: {', '.join(missing)}")
    extra = [k for k in scores if k not in QOL_CRITERIA]
    if extra:
        raise ValueError(f"알 수 없는 항목: {', '.join(extra)}")

    clean: dict[str, int] = {}
    for k in QOL_CRITERIA:
        v = scores[k]
        if isinstance(v, bool) or not isinstance(v, int):
            raise ValueError(f"{k} 점수는 정수여야 합니다: {v!r}")
        if not _MIN_SCORE <= v <= _MAX_SCORE:
            raise ValueError(f"{k} 점수는 0~10 범위여야 합니다: {v}")
        clean[k] = v

    total = sum(clean.values())
    maintainable = total >= _ACCEPTABLE_TOTAL
    low_items = [k for k in QOL_CRITERIA if clean[k] < 5]

    if maintainable:
        interpretation = (
            f"총점 {total}/{_MAX_TOTAL} — 현재 삶의 질을 유지할 만한 수준입니다. "
            "꾸준히 관찰하며 낮은 항목을 돌봐 주세요."
        )
    else:
        interpretation = (
            f"총점 {total}/{_MAX_TOTAL} — 삶의 질이 낮아진 신호일 수 있습니다. "
            "수의사와 상태·완화 방법을 상의하시길 권합니다."
        )

    return {
        "criteria": clean,
        "labels": dict(CRITERIA_LABELS),
        "total": total,
        "max": _MAX_TOTAL,
        "tier": "maintainable" if maintainable else "declining",
        "interpretation": interpretation,
        "low_items": low_items,
        "vet_referral": _VET_REFERRAL,
        "disclaimer": _DISCLAIMER,
    }
