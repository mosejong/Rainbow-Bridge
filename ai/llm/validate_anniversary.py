"""3단계 기념일 케어 알림 품질 검증 — 실제 Gemini 대상 수동 점검 도구.

D+30·D+100 케이스 + 위기 차단 케이스로 generate_anniversary_care 를 호출해
출력 품질을 눈으로 확인합니다.

체크 항목:
  1. 기념일 메시지가 해당 시점에 맞는지 (D+30: 일상 복귀, D+100: 100일 회고)
  2. 반려동물 이름이 자연스럽게 들어가는지
  3. "이제 괜찮아야 해" 식의 강요·말줄임표(...)·부활/1인칭 없는지
  4. note 있을 때 Gemini 가 보호자 감정을 반영하는지
  5. 위기 메모 → 1393 안내로 차단되는지

⚠️ 실제 API 호출 — .env 의 LLM_API_KEY 필요. CI 미포함.
사용: ai/ 디렉터리에서  python -m llm.validate_anniversary
"""

from __future__ import annotations

import time

from .anniversary import generate_anniversary_care
from .provider import generate

_DELAY_SEC = 4.0  # 무료 티어 RPM 회피

PET = {"name": "봄이", "species": "고양이", "memories": ["매일 아침 같이 일어났어요"]}

# (days_since, note)
_CASES = [
    (30,  ""),
    (100, ""),
    (30,  "한 달이 지났는데 아직도 너무 힘들어요. 밥도 못 먹고 있어요."),
    (100, "100일이 지났어요. 조금은 나아진 것 같은데 아직도 보고 싶네요."),
    # 위기 차단 — LLM 호출 없이 1393 으로 막혀야 함
    (30,  "봄이 곁으로 나도 따라가고 싶어요"),
]


def main() -> None:
    print("=" * 70)
    print("3단계 기념일 케어 알림 품질 검증 (실제 Gemini)")
    print("=" * 70)

    from .prompts.anniversary import MILESTONE_LABELS

    for days_since, note in _CASES:
        is_crisis = note and "따라가고" in note
        label = "CRISIS" if is_crisis else f"D+{days_since}"
        milestone = MILESTONE_LABELS.get(days_since, f"{days_since}일")
        print(f"\n[{label}] 무지개다리 {milestone} 기념일")
        print(f"  반려동물: {PET['name']}({PET['species']})")
        if note:
            print(f"  보호자 메모: {note}")

        try:
            result = generate_anniversary_care(
                PET, days_since, note=note, generate=generate
            )
            crisis = result.get("crisis_message")

            if crisis:
                print(f"  [위기차단] {crisis}")
            else:
                src = result.get("source", "")
                print(f"  출처: {src}")
                print(f"  {result['message']}")
        except Exception as e:
            print(f"  [오류] {e}")

        time.sleep(_DELAY_SEC)

    print("\n" + "=" * 70)
    print("검증 완료. 출력을 눈으로 확인해주세요.")
    print("  - D+30: 일상 복귀 격려, 잊는 게 아님을 담았는지")
    print("  - D+100: 100일 버텨온 보호자 위로, 기억이 함께함을 담았는지")
    print("  - note 반영: 보호자 감정에 맞춤 응답인지")
    print("  - 말줄임표·부활·1인칭 반려동물 화법 없는지")
    print("=" * 70)


if __name__ == "__main__":
    main()
