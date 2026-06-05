"""1단계 증상 진료 안내 — Gemini 프롬프트 템플릿.

보호자가 살아있는 반려동물의 증상을 입력하면, Gemini 가 어떤 진료가 필요한지
정보를 제공하고 동물병원 방문을 안내합니다.

톤 원칙:
  - 수의사가 아니므로 단정("분명히")을 피하고 "~듯합니다" 등 추정형을 씁니다.
  - 증상 심각도(severity)에 따라 마지막 문장을 다르게 구성합니다.
"""

from __future__ import annotations

from typing import Final, Optional

# 심각도별 마지막 안내 문장 (케이스마다 마지막 문장 다르게)
SEVERITY_CLOSINGS: Final[dict[str, str]] = {
    # 즉시 응급 처치가 필요한 증상 (경련, 호흡곤란, 대량 출혈 등)
    "emergency": "지금 바로 24시간 응급 동물병원에 데려가 주세요.",
    # 당일 진료가 필요한 증상 (구토·설사 반복, 식욕 완전 거부, 고열 등)
    "urgent": "오늘 안에 동물병원에서 진찰받아 보시는 게 좋을 듯합니다.",
    # 수일 내 진료 권장 증상 (간헐적 기침, 약한 식욕 저하 등)
    "soon": "며칠 내로 동물병원에 방문해 보시는 게 좋을 듯합니다.",
    # 관찰 후 지속 시 진료 권장
    "monitor": "증상이 하루 이상 계속된다면 동물병원에 방문해 보시는 게 좋을 듯합니다.",
}

# --------------------------------------------------------------------------- #
# 시스템 프롬프트
# --------------------------------------------------------------------------- #
SYSTEM_PROMPT: Final[str] = """\
당신은 반려동물 건강 정보를 안내하는 보조입니다.
보호자가 입력한 증상을 바탕으로, 어떤 진료과·검사가 필요할 수 있는지 정보를 제공합니다.

[톤 원칙]
- 수의사가 아니므로 진단을 단정하지 않습니다.
- "분명히", "확실히", "반드시 ~입니다" 같은 단정 표현을 피하고,
  "~일 수 있을 듯합니다", "~로 보일 수 있습니다", "~가 의심될 수 있습니다" 처럼
  추정형으로 씁니다.
- 3~4문장, 한국어. 전문 용어는 쉬운 말로 풀어 씁니다.
- 마지막 문장은 입력으로 주어지는 [병원 안내 문장]을 그대로 씁니다.

[절대 금지]
- 특정 질병명을 단정("이건 파보바이러스입니다")하지 마세요.
- 약 이름이나 투약량을 직접 안내하지 마세요.
- 병원 방문 없이 집에서 해결하라고 유도하지 마세요.
"""

_USER_TEMPLATE: Final[str] = """\
[반려동물 정보]
- 이름: {name}
- 종: {species}
- 나이: {age}

[증상]
{symptoms}

[병원 안내 문장]: {closing}

위 증상을 바탕으로 어떤 진료나 검사가 필요할 수 있는지 3~4문장으로 안내해 주세요.
마지막 문장은 반드시 [병원 안내 문장] 그대로 써 주세요.
"""


def _assess_severity(symptoms: str) -> str:
    """증상 텍스트에서 심각도를 추론합니다."""
    norm = symptoms.replace(" ", "")
    emergency_keywords = ("경련", "발작", "호흡곤란", "숨못쉬", "의식없", "대량출혈", "다량출혈", "쓰러졌")
    urgent_keywords = ("구토를반복", "설사를반복", "아무것도안먹", "먹지않", "고열", "피오줌", "피변", "혈변", "혈뇨")
    soon_keywords = ("기침", "재채기", "눈곱", "눈물", "절뚝", "다리를절")
    for kw in emergency_keywords:
        if kw in norm:
            return "emergency"
    for kw in urgent_keywords:
        if kw in norm:
            return "urgent"
    for kw in soon_keywords:
        if kw in norm:
            return "soon"
    return "monitor"


def build_messages(
    symptoms: str,
    *,
    name: str = "",
    species: str = "",
    age: str = "",
    severity: Optional[str] = None,
) -> list[dict[str, str]]:
    """증상 진료 안내 메시지 생성용 OpenAI 호환 chat 메시지 배열을 만듭니다.

    Args:
        symptoms: 보호자가 입력한 증상 텍스트.
        name: 반려동물 이름 (선택).
        species: 종 (강아지·고양이 등, 선택).
        age: 나이 (선택).
        severity: 심각도 키(emergency·urgent·soon·monitor). 미지정 시 자동 추론.

    Returns:
        [{"role": "system", ...}, {"role": "user", ...}] 형식의 리스트.
    """
    resolved = severity or _assess_severity(symptoms)
    closing = SEVERITY_CLOSINGS.get(resolved, SEVERITY_CLOSINGS["monitor"])
    user_content = _USER_TEMPLATE.format(
        name=name or "미입력",
        species=species or "미입력",
        age=age or "미입력",
        symptoms=symptoms.strip(),
        closing=closing,
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
