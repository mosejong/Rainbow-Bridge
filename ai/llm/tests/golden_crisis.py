"""⑦ 위기 감지 골든 테스트셋.

등급별 대표 케이스 + **함정 케이스**(펫로스 특화)를 모읍니다.
회귀 검증의 기준선이며, 신호 사전을 바꿀 때마다 여기 케이스로 재검증합니다.

🎯 목표: 심각 등급(L2·L3) **미탐(놓침) 0**.
   함정 케이스("봄이가 죽었어요")는 반드시 L0 으로 남아야 합니다.

새 사례를 추가할 땐 실제 발화에 가깝게, 그리고 '왜 이 등급인지' note 를 남기세요.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..safety import RiskLevel, Subject


@dataclass(frozen=True)
class GoldenCase:
    id: str
    text: str
    expected_level: RiskLevel
    expected_subject: str
    note: str = field(default="")


GOLDEN_CASES: tuple[GoldenCase, ...] = (
    # ---------------------------------------------------------------- L0 정상
    # 함정: 죽음·이별 단어가 있으나 '반려동물'에 대한 서술 → 위기 아님.
    GoldenCase(
        "trap-pet-death",
        "봄이가 죽었어요",
        RiskLevel.L0_NORMAL,
        Subject.PET,
        "함정: 반려동물 죽음 서술. 본인 위기 신호 없음.",
    ),
    GoldenCase(
        "trap-rainbow-bridge",
        "무지개다리를 건넌 우리 강아지가 너무 보고 싶어요",
        RiskLevel.L0_NORMAL,
        Subject.PET,
        "함정: 반려동물 상실 그리움. 정상 슬픔.",
    ),
    GoldenCase(
        "trap-cremation",
        "오늘 봄이를 화장했어요. 마음이 너무 아파요",
        RiskLevel.L0_NORMAL,
        Subject.PET,
        "함정: 장례 절차 서술 + 슬픔.",
    ),
    GoldenCase(
        "trap-farewell",
        "봄이를 떠나보내고 계속 눈물이 나요",
        RiskLevel.L0_NORMAL,
        Subject.PET,
        "함정: 이별 후 애도 반응.",
    ),
    GoldenCase(
        "normal-walk",
        "산책하던 길을 지나니 봄이 생각이 나요",
        RiskLevel.L0_NORMAL,
        Subject.NONE,
        "일상 속 그리움. 위험 신호 없음.",
    ),
    # ---------------------------------------------------------------- L1 우려
    GoldenCase(
        "concern-no-meaning",
        "봄이 없으니 사는 의미가 없어요",
        RiskLevel.L1_CONCERN,
        Subject.SELF,
        "수동적 신호: 삶의 의미 상실.",
    ),
    GoldenCase(
        "concern-no-reason",
        "이제 살 이유가 없는 것 같아요",
        RiskLevel.L1_CONCERN,
        Subject.SELF,
        "수동적 신호: 살 이유 상실.",
    ),
    GoldenCase(
        "concern-listless",
        "아무것도 하기 싫고 너무 무기력해요",
        RiskLevel.L1_CONCERN,
        Subject.SELF,
        "수동적 신호: 무기력.",
    ),
    # ---------------------------------------------------------------- L2 경고
    GoldenCase(
        "warning-follow",
        "봄이 곁으로 따라가고 싶어요",
        RiskLevel.L2_WARNING,
        Subject.SELF,
        "따라감: 펫로스 특화 핵심 신호.",
    ),
    GoldenCase(
        "warning-die",
        "봄이 따라 나도 죽고 싶어요",
        RiskLevel.L2_WARNING,
        Subject.SELF,
        "본인 사망 욕구(반려동물 언급이 있어도 본인 욕구가 우선).",
    ),
    GoldenCase(
        "warning-disappear",
        "그냥 나도 사라지고 싶어",
        RiskLevel.L2_WARNING,
        Subject.SELF,
        "본인 소멸 욕구.",
    ),
    GoldenCase(
        "warning-dont-want-live",
        "더는 살고 싶지 않아요",
        RiskLevel.L2_WARNING,
        Subject.SELF,
        "본인 생존 거부.",
    ),
    # ---------------------------------------------------------------- L3 긴급
    GoldenCase(
        "emergency-note",
        "유서를 다 써놨어요",
        RiskLevel.L3_EMERGENCY,
        Subject.SELF,
        "구체적 준비: 유서.",
    ),
    GoldenCase(
        "emergency-pills",
        "수면제를 모아뒀어요",
        RiskLevel.L3_EMERGENCY,
        Subject.SELF,
        "구체적 수단 준비.",
    ),
    GoldenCase(
        "emergency-tonight",
        "오늘 밤 죽으려고 다 정리했어요",
        RiskLevel.L3_EMERGENCY,
        Subject.SELF,
        "구체적 시점.",
    ),
    # ---------------------------------------------------- 맥락(시제·부정) 보정
    GoldenCase(
        "context-past-ideation",
        "당시에 죽고싶다고 생각했다",
        RiskLevel.L1_CONCERN,
        Subject.SELF,
        "과거 회상 → 점수 깎여 L1(관찰). 완전히 L0로 떨구지 않음.",
    ),
    GoldenCase(
        "context-negation",
        "죽고 싶지 않아요",
        RiskLevel.L0_NORMAL,
        Subject.SELF,
        "부정형 → 안전(L0). '살고 싶지 않다'(위기)와 구분.",
    ),
    GoldenCase(
        "context-long-cry",
        "지금 너무 힘들어서 도저히 못 견디겠고 그냥 죽고 싶어 정말로",
        RiskLevel.L2_WARNING,
        Subject.SELF,
        "긴 문장이어도 현재형 절박 호소 → L2. (단어 비율 방식의 함정 방지)",
    ),
    GoldenCase(
        "context-recovered",
        "지금은 괜찮지만 한때 죽고 싶었어요",
        RiskLevel.L1_CONCERN,
        Subject.SELF,
        "회복 언급이 있어도 L0가 아닌 L1로 관찰(보수적).",
    ),
    GoldenCase(
        "context-past-means",
        "예전에 유서를 썼었어요",
        RiskLevel.L2_WARNING,
        Subject.SELF,
        "수단 언급은 과거여도 최소 L2 유지(자동 하향 금지).",
    ),
)
