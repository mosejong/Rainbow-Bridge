"""⑦ 위기 감지 L1(LLM) 골든셋 검증 — 실제 Gemini 대상 수동 점검 도구.

골든 케이스를 규칙(L0)·LLM(L1)·융합(max)으로 돌려 비교하고, **미탐(심각등급 누락)**·
**오탐(L0 과탐)** 을 집계합니다. 융합이 max라 미탐은 규칙이 보장(0이어야 정상)하고,
이 검증의 핵심은 L1이 함정/정상 문장을 과하게 올리지 않는지(오탐) 보는 것입니다.

⚠️ 실제 API 호출이라 .env 의 LLM_API_KEY 필요. CI 미포함(비결정적·비용·레이트리밋).
사용: ai/ 디렉터리에서  python -m llm.validate_crisis_llm
"""

from __future__ import annotations

import time

from .provider import generate
from .safety import RiskLevel, classify_with_llm, detect_crisis
from .tests.golden_crisis import GOLDEN_CASES

_DELAY_SEC = 4.0  # 무료 티어 RPM 회피


def main() -> None:
    miss = 0  # 미탐: 융합 < 기대
    over = 0  # 오탐: 기대 L0 인데 융합 > L0
    llm_ok = 0  # L1 실제 응답 성공 수

    print(f"{'id':24}{'기대':>4}{'규칙':>5}{'L1':>4}{'융합':>5}  플래그 / 문장")
    print("-" * 92)
    for case in GOLDEN_CASES:
        rule = detect_crisis(case.text)
        verdict = classify_with_llm(case.text, generate)
        if verdict is None:
            l1_disp = "—"
            fused = rule.risk_level
        else:
            llm_ok += 1
            l1_disp = str(int(verdict.risk_level))
            fused = max(rule.risk_level, verdict.risk_level)

        flag = ""
        if fused < case.expected_level:
            miss += 1
            flag += "❌미탐 "
        if case.expected_level == RiskLevel.L0_NORMAL and fused > RiskLevel.L0_NORMAL:
            over += 1
            flag += "⚠️과탐 "

        print(
            f"{case.id:24}{int(case.expected_level):>4}{int(rule.risk_level):>5}"
            f"{l1_disp:>4}{int(fused):>5}  {flag}{case.text}"
        )
        time.sleep(_DELAY_SEC)

    print("-" * 92)
    total = len(GOLDEN_CASES)
    print(f"L1 실제 호출 성공: {llm_ok}/{total} (나머지는 레이트리밋 등 → 규칙 폴백)")
    print(f"미탐(심각등급 누락): {miss}   오탐(L0 과탐): {over}")
    print("→ 미탐 0이면 안전 기준 통과. 오탐은 L1 프롬프트 보정 후보.")


if __name__ == "__main__":
    main()
