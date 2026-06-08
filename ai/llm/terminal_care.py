"""시한부 케어 안내 — 고정 콘텐츠 제공(로직).

반려동물이 시한부 판정을 받은 보호자에게, 앞으로 나타날 수 있는 일반적인 신호와
보호자가 해줄 수 있는 케어를 **고정 안내문**으로 제공합니다.

🚫 triage(③ RAG+LLM 생성)와 정반대 설계입니다:
  - 임종 과정 정보는 정확성·일관성이 생명이라 **LLM 생성 금지**, 검수된 고정 텍스트만.
  - AI가 아이의 상태를 진단하거나 남은 시간을 예측하지 **않습니다**(disclaimer 명시).
  - 내용은 data/terminal_care.json 에 두고(반소람이 관리), 이 모듈은 로드만 합니다.

🚨 임종 임박 신호를 보는 보호자는 위기 감정 가능성이 높습니다. 안내에 자살예방
   상담전화(CRISIS_HOTLINE)를 함께 노출합니다. 번호는 상수에서만 참조(하드코딩 금지).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from .safety import CRISIS_HOTLINE

_DATA_PATH = Path(__file__).parent / "data" / "terminal_care.json"

# 보호자 정서 지지 안내 — 위기 안내 번호는 CRISIS_HOTLINE 상수에서만.
_SUPPORT_NOTE = (
    "이 시간을 혼자 견디지 않으셔도 됩니다. 많이 힘드실 땐 언제든 "
    f"자살예방 상담전화 {CRISIS_HOTLINE}(24시간)으로 마음을 나눠 주세요."
)


@lru_cache(maxsize=1)
def _load() -> dict:
    """JSON 콘텐츠를 한 번 읽어 캐시합니다."""
    return json.loads(_DATA_PATH.read_text(encoding="utf-8"))


def get_terminal_care_info() -> dict:
    """시한부 케어 안내 콘텐츠를 반환합니다(고정).

    백엔드는 이 함수만 호출하면 됩니다. 반환 dict 는 그대로 API 응답으로 내려
    프론트가 단계별 섹션으로 렌더링하도록 합니다.

    Returns:
        ``{title, disclaimer, stages[], care{}, closing, support_note,
           crisis_hotline, sources[]}``.
        - stages: 초기~중기 / 말기~임종 직전 두 단계, 각 group(증상 묶음) 포함.
        - support_note·crisis_hotline: 보호자 위기 대비 안내(상수 주입).
    """
    data = _load()
    return {
        **data,
        "support_note": _SUPPORT_NOTE,
        "crisis_hotline": CRISIS_HOTLINE,
    }
