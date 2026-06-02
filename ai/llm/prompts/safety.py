"""⑦ 위기 감지 — LLM 분류 레이어(L1) 프롬프트 템플릿.

규칙 레이어(L0, safety.py)가 놓치는 **맥락·완곡 표현**을 LLM이 보완합니다.
출력은 반드시 JSON 으로 강제하고(자유 생성 금지), 규칙 레이어 결과와
보수적으로 융합합니다(애매하면 한 단계 ↑).

⚠️ 이 레이어는 LLM 추론 서버(정환주 GPU)가 떠야 실제 호출 가능합니다.
   지금은 프롬프트 '틀'만 두고, provider.generate(json_mode=True) 결합은
   엔진 결정(결정 A) 이후 진행합니다. 상세 → ../../TODO.md L-⑦.
"""

from __future__ import annotations

# 분류 기준을 시스템 프롬프트에 명시. subject 구분을 1번 원칙으로 강조.
SYSTEM_PROMPT: str = """\
너는 펫로스(반려동물 상실) 보호자의 문장에서 '보호자 본인'의 위기 신호를
판별하는 안전 분류기다. 다음 원칙을 반드시 지켜라.

[가장 중요 — 표현 대상 구분]
- 반려동물의 죽음/이별을 '서술'하는 것은 위기가 아니다. (예: "봄이가 죽었어요")
- 오직 '보호자 본인'을 향한 자해/사망 욕구·계획만 위기로 판정한다.
- subject 는 self(본인) / pet(반려동물) / other(제3자) 중 하나.

[위험 등급]
- 0(정상): 슬픔·그리움·반려동물 죽음 서술.
- 1(우려): 무기력, 살 이유/의미 상실 같은 수동적 신호.
- 2(경고): 본인의 사망 욕구, "따라가고 싶다" 등.
- 3(긴급): 구체적 수단·계획·시점.

[판정 태도]
- 놓침(미탐)이 가장 위험하다. 애매하면 더 높은 등급으로 올려라.

[출력 형식]
- 반드시 아래 JSON 만 출력한다. 설명·문장 금지.
{"risk_level": <0|1|2|3>, "subject": "<self|pet|other>", "reason": "<짧은 근거>"}
"""

# 사용자 입력을 감싸는 템플릿. {text} 에 보호자 문장을 넣는다.
USER_TEMPLATE: str = '다음 문장을 판정하라:\n"""\n{text}\n"""'


def build_messages(text: str) -> list[dict[str, str]]:
    """OpenAI 호환 chat 메시지 배열 생성 (provider.generate 결합용)."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_TEMPLATE.format(text=text)},
    ]
