"""1셋 미완료 케이스 재실행 (cat-calm / rabbit-hopeful / cat-no-memories)."""
import time

from ai.llm.memorial import generate_message
from ai.llm.provider import generate

_DELAY_SEC = 15.0  # 분당 5회 한도 → 12초 이상 간격 필요

_CASES = [
    (
        "cat-calm",
        {"name": "나비", "species": "고양이", "period": "12년", "memories": ["무릎 위에서 잠들기", "창가 햇볕 쬐기"]},
        {"emotion_score": 5, "note": "나비가 항상 옆에 있었는데 이제 그 자리가 비어있어요."},
        "calm",
    ),
    (
        "rabbit-hopeful",
        {"name": "콩이", "species": "토끼", "period": "3년", "memories": ["채소 먹이기", "뛰어다니는 거 구경하기"]},
        {"emotion_score": 6, "note": "짧은 시간이었지만 행복했어요."},
        "hopeful",
    ),
    (
        "cat-no-memories",
        {"name": "몽이", "species": "고양이", "period": "2년", "memories": []},
        {"emotion_score": 5, "note": "갑작스럽게 떠나보내서 너무 힘들어요."},
        "calm",
    ),
]

_FORBIDDEN_1ST = ("나는", "내가", "내 이름", "나였", "나예요", "저는", "제가")
_FORBIDDEN_REVIVE = ("부활", "환생", "되살", "다시살아")


def _check(content):
    issues = []
    for w in _FORBIDDEN_1ST:
        if w in content:
            issues.append("1인칭 감지: " + w)
    for w in _FORBIDDEN_REVIVE:
        if w in content.replace(" ", ""):
            issues.append("부활 표현 감지: " + w)
    return issues


def main():
    print("=" * 70)
    print("1셋 (재실행) - 기본 모드 나머지 3케이스 (딜레이 15초)")
    print("=" * 70)

    for i, (case_id, pet, emotion, tone) in enumerate(_CASES):
        if i > 0:
            print("  (대기 15초...)")
            time.sleep(_DELAY_SEC)
        print(
            "\n[" + case_id + "]  "
            + pet["name"] + "(" + pet["species"] + ", " + pet["period"] + ")"
            + "  tone=" + tone
        )
        print("  입력: " + (emotion.get("note") or "(없음)"))
        try:
            result = generate_message(pet, emotion, tone, generate=generate)
            crisis = result.get("crisis_message")
            if crisis:
                print("  [위기차단] " + crisis)
            else:
                print("  출처: " + result.get("source", "?"))
                print("  메시지: " + result.get("content", ""))
                issues = _check(result.get("content", ""))
                if issues:
                    print("  [!문제] " + str(issues))
                else:
                    print("  [OK] 가드레일 통과")
        except Exception as e:
            print("  [오류] " + str(e))

    print()
    print("=" * 70)
    print("1셋 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()
