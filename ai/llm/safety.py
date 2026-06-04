"""⑦ 위기 감정 감지 — 규칙 레이어(L0).

펫로스 대화는 "죽음·이별" 단어가 정상적으로 가득합니다. 그래서 단순 키워드는
오탐이 폭발합니다. 이 모듈의 핵심은 **표현 대상(subject) 구분**과
**본인의 욕구 어법("~고 싶다")** 매칭입니다.

  - "봄이가 죽었어요"        → 반려동물(pet) 죽음 서술 → 위기 아님(L0)
  - "봄이 따라 나도 죽고싶어" → 본인(self) 사망 욕구    → 경고(L2)

즉 죽음 '명사'가 아니라 **본인을 주어로 하는 욕구 표현**을 잡습니다.

이 파일은 다층 구조의 첫 단계인 **규칙 레이어(L0)** 입니다.
강한 직접 표현을 빠르게 확정하고, 애매한 판단은 이후 LLM 레이어(L1)와
보수적으로 융합합니다(애매하면 한 단계 ↑). 상세 설계는 ../TODO.md L-⑦.

🚨 안내 번호 1393은 CRISIS_HOTLINE 상수로만 참조합니다(하드코딩 금지).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Final, Optional, Protocol

from .prompts import safety as safety_prompt

# 🚨 위기 안내 번호 — 어떤 경우에도 변경/누락 금지 (자살예방 상담전화).
CRISIS_HOTLINE: Final[str] = "1393"


class RiskLevel(IntEnum):
    """위험 등급 4단계 (숫자가 클수록 위험).

    다층 융합에서 max()·"애매하면 한 단계 ↑" 보정에 쓰려고 정수 비교가
    가능한 IntEnum 으로 둡니다.
    """

    L0_NORMAL = 0  # 정상 — 펫로스 슬픔/반려동물 죽음 언급 포함 (위기 아님)
    L1_CONCERN = 1  # 우려 — 무기력·"살 이유가 없다" 등 수동적 신호
    L2_WARNING = 2  # 경고 — 본인 사망 욕구·"따라가고 싶다" → 1393 우선
    L3_EMERGENCY = 3  # 긴급 — 구체적 계획·수단 → 생성 중단 + 1393 전면

    @property
    def label(self) -> str:
        return {
            RiskLevel.L0_NORMAL: "정상",
            RiskLevel.L1_CONCERN: "우려",
            RiskLevel.L2_WARNING: "경고",
            RiskLevel.L3_EMERGENCY: "긴급",
        }[self]


# L2(경고) 이상부터 1393 안내를 띄웁니다.
HOTLINE_REQUIRED_FROM: Final[RiskLevel] = RiskLevel.L2_WARNING


class Subject:
    """표현 대상 — 위험 신호가 '누구'에 대한 것인지.

    대상 구분이 오탐 방지의 1번 열쇠입니다. 반려동물(pet) 죽음 언급은
    위기로 보지 않습니다(L0).
    """

    SELF: Final[str] = "self"  # 보호자 본인 (위기 판단 대상)
    PET: Final[str] = "pet"  # 떠난 반려동물 (죽음 언급해도 위기 아님)
    OTHER: Final[str] = "other"  # 제3자
    NONE: Final[str] = "none"  # 위험 신호 없음


# --------------------------------------------------------------------------- #
# 펫로스 특화 위험 신호 사전
# --------------------------------------------------------------------------- #
# 패턴은 '공백을 제거한' 텍스트에 대해 부분일치로 검사합니다.
# (사용자가 "죽고 싶어" / "죽고싶어" 둘 다 입력하므로 공백차이를 흡수)
# 따라서 패턴은 공백 없이 적습니다.
#
# category 의미:
#   direct   : 직접적 자기 죽음 욕구
#   following : 따라감 — 떠난 반려동물을 따라가려는 욕구 (펫로스 특화 핵심 신호)
#   passive  : 수동적 — 살 이유/의미 상실, 무기력
#   means    : 긴급 — 구체적 수단·계획·시점


@dataclass(frozen=True)
class CrisisSignal:
    """매칭된 위험 신호 한 건."""

    pattern: str  # 사전에 등록된(공백 제거) 패턴
    category: str  # direct | following | passive | means
    level: RiskLevel  # 이 신호가 단독으로 시사하는 등급


# (pattern, category, level) — 공백 제거 기준
_SIGNAL_TABLE: Final[tuple[tuple[str, str, RiskLevel], ...]] = (
    # 🔴 긴급(L3) — 구체적 수단·계획·시점이 드러나는 표현
    ("유서", "means", RiskLevel.L3_EMERGENCY),
    ("목을매", "means", RiskLevel.L3_EMERGENCY),
    ("목매달", "means", RiskLevel.L3_EMERGENCY),
    ("뛰어내리", "means", RiskLevel.L3_EMERGENCY),
    ("투신", "means", RiskLevel.L3_EMERGENCY),
    ("번개탄", "means", RiskLevel.L3_EMERGENCY),
    ("수면제를모", "means", RiskLevel.L3_EMERGENCY),
    ("수면제모아", "means", RiskLevel.L3_EMERGENCY),
    ("약을모았", "means", RiskLevel.L3_EMERGENCY),
    ("약을모아", "means", RiskLevel.L3_EMERGENCY),
    ("오늘밤죽", "means", RiskLevel.L3_EMERGENCY),
    ("내일죽을", "means", RiskLevel.L3_EMERGENCY),
    # 🟠 경고(L2) — 본인의 사망 욕구 (따라감 포함)
    ("죽고싶", "direct", RiskLevel.L2_WARNING),
    ("죽어버리고싶", "direct", RiskLevel.L2_WARNING),
    ("죽어야겠", "direct", RiskLevel.L2_WARNING),
    ("죽었으면좋겠", "direct", RiskLevel.L2_WARNING),
    ("죽어버렸으면", "direct", RiskLevel.L2_WARNING),
    ("차라리죽", "direct", RiskLevel.L2_WARNING),
    ("사라지고싶", "direct", RiskLevel.L2_WARNING),
    ("없어지고싶", "direct", RiskLevel.L2_WARNING),
    ("끝내고싶", "direct", RiskLevel.L2_WARNING),
    ("살고싶지않", "direct", RiskLevel.L2_WARNING),
    ("살기싫", "direct", RiskLevel.L2_WARNING),
    ("따라가고싶", "following", RiskLevel.L2_WARNING),
    ("따라갈래", "following", RiskLevel.L2_WARNING),
    ("나도따라가", "following", RiskLevel.L2_WARNING),
    ("나도데려가", "following", RiskLevel.L2_WARNING),
    ("곁으로가고싶", "following", RiskLevel.L2_WARNING),
    # 🟡 우려(L1) — 수동적 신호: 살 이유/의미 상실, 무기력
    ("살이유가없", "passive", RiskLevel.L1_CONCERN),
    ("살이유없", "passive", RiskLevel.L1_CONCERN),
    ("사는이유가없", "passive", RiskLevel.L1_CONCERN),
    ("살의미가없", "passive", RiskLevel.L1_CONCERN),
    ("살의미없", "passive", RiskLevel.L1_CONCERN),
    ("사는의미가없", "passive", RiskLevel.L1_CONCERN),
    ("사는게의미없", "passive", RiskLevel.L1_CONCERN),
    ("다포기하고싶", "passive", RiskLevel.L1_CONCERN),
    ("무기력", "passive", RiskLevel.L1_CONCERN),
    ("아무것도하기싫", "passive", RiskLevel.L1_CONCERN),
    ("아무의욕이없", "passive", RiskLevel.L1_CONCERN),
)

# 반려동물 죽음·이별을 가리키는 단서(공백 제거 기준).
# 이런 표현만 있고 본인 욕구 신호가 없으면 대상은 pet → 위기 아님(L0).
_PET_DEATH_HINTS: Final[tuple[str, ...]] = (
    "무지개다리",
    "떠나보",
    "떠났",
    "보내줬",
    "보내주",
    "먼저갔",
    "하늘나라",
    "별이됐",
    "별이되",
    "묻어줬",
    "화장했",
    # 서술형 죽음 단어 — 본인 소망 어법(죽고싶/죽었으면)은 신호 사전에서
    # 먼저 걸러지므로, 이 단계에 도달하면 제3자/반려동물 죽음 '서술'이다.
    "죽었",
    "죽은",
    "죽고말",
    "숨졌",
    "숨을거뒀",
    "세상을떠",
    "곁을떠",
)

# --------------------------------------------------------------------------- #
# 맥락 점수(가중치) — 시제·부정·강도로 신호 점수를 보정
# --------------------------------------------------------------------------- #
# "죽고 싶어"(현재) 와 "당시에 죽고싶다고 생각했다"(과거 회상) 는 같은 단어라도
# 위험도가 다릅니다. 단어 '비율'이 아니라(긴 문장의 절박한 호소를 놓치므로),
# 신호의 기본 점수에서 맥락 표시어로 더하고/빼서 최종 등급을 정합니다.
#
# 🚨 안전 원칙(이 프로젝트): 미탐(놓침)이 가장 치명적. 그래서
#   - 깎이더라도 본인 죽음 욕구는 L0 로 완전히 떨구기보다 L1(관찰)로 남겨
#     LLM 레이어(L1)가 다시 보게 한다(애매하면 ↑).
#   - 구체적 수단·계획(means)은 어떤 맥락에서도 자동으로 크게 내리지 않는다.

# 신호 범주별 기본 점수
_CATEGORY_BASE: Final[dict[str, int]] = {
    "means": 100,  # 긴급 — 수단·계획
    "direct": 50,  # 본인 직접 사망 욕구
    "following": 50,  # 따라감
    "passive": 25,  # 수동적 신호
}

# 점수→등급 임계값 (널널하게: 애매하면 L1 로 남김)
_SCORE_L2: Final[int] = 45  # 이상이면 경고(L2)
_SCORE_L1: Final[int] = 15  # 이상이면 우려(L1)
_SCORE_MEANS_L3: Final[int] = 80  # means 가 이 이상이면 긴급(L3), 미만이면 L2 바닥

# 보정값
_DAMPEN_PAST: Final[int] = 25  # 과거·회상
_DAMPEN_SAFE: Final[int] = 30  # 현재 안전("지금은 괜찮")
_DAMPEN_NEGATION: Final[int] = 40  # 죽음 욕구의 부정("죽고 싶지 않아")
_BOOST_PRESENT: Final[int] = 15  # 현재성
_BOOST_INTENSITY: Final[int] = 10  # 강도

# 과거·회상 표시어 (공백 제거 기준) — 점수 깎기
_PAST_MARKERS: Final[tuple[str, ...]] = (
    "당시",
    "그때",
    "그땐",
    "예전",
    "한때",
    "옛날",
    "어렸을때",
    "었었",
    "았었",
    "던적",
    "었던",
    "았던",
    "생각했",
    "느꼈었",
)

# 현재 안전 표시어 — 점수 깎기 (회복·호전)
_SAFE_MARKERS: Final[tuple[str, ...]] = (
    "지금은괜찮",
    "이제는괜찮",
    "이제괜찮",
    "지금은아니",
    "이제는아니",
    "나아졌",
    "괜찮아졌",
    "극복",
    "다행",
)

# 죽음 욕구의 부정형 (안전) — "살고 싶지 않다"(위기)와 구분해 명시적으로 나열.
_NEGATED_DEATH_DESIRE: Final[tuple[str, ...]] = (
    "죽고싶지않",
    "죽고싶진않",
    "죽어버리고싶지않",
    "사라지고싶지않",
    "없어지고싶지않",
    "따라가고싶지않",
    "끝내고싶지않",
)

# 현재성 표시어 — 점수 더하기
_PRESENT_MARKERS: Final[tuple[str, ...]] = (
    "지금",
    "요즘",
    "요새",
    "자꾸",
    "계속",
    "매일",
    "오늘",
    "자주",
)

# 강도 표시어 — 점수 더하기
_INTENSITY_MARKERS: Final[tuple[str, ...]] = (
    "너무",
    "정말",
    "진짜",
    "도저히",
    "못견디",
    "미치겠",
    "더이상",
)

_WHITESPACE_RE: Final[re.Pattern[str]] = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """공백을 모두 제거 — '죽고 싶어'/'죽고싶어' 의 표기 차이를 흡수."""
    return _WHITESPACE_RE.sub("", text)


@dataclass(frozen=True)
class CrisisResult:
    """detect_crisis 결과.

    dict 변환(as_dict)으로 백엔드 응답 스키마(결정 C)와 맞춥니다.
    """

    risk_level: RiskLevel
    subject: str
    signals: list[CrisisSignal]
    hotline_required: bool
    reason: str
    score: int = 0  # 맥락 보정 후 위험 점수(투명성·튜닝용)
    context_markers: list[str] = field(default_factory=list)  # 감지된 시제·강도 표시어

    def as_dict(self) -> dict:
        return {
            "risk_level": int(self.risk_level),
            "risk_label": self.risk_level.label,
            "subject": self.subject,
            "signals": [
                {"pattern": s.pattern, "category": s.category, "level": int(s.level)}
                for s in self.signals
            ],
            "hotline_required": self.hotline_required,
            "hotline": CRISIS_HOTLINE if self.hotline_required else None,
            "score": self.score,
            "context_markers": self.context_markers,
            "reason": self.reason,
        }


def _collect_markers(normalized: str, table: tuple[str, ...]) -> list[str]:
    """표시어 사전에서 본문에 등장한 항목을 모읍니다."""
    return [m for m in table if m in normalized]


def _score_to_level(score: int, has_means: bool) -> RiskLevel:
    """맥락 보정 점수를 등급으로 매핑.

    means(수단·계획)가 있으면 자동으로 크게 못 내립니다(최소 L2). 그 외에는
    임계값으로 L0/L1/L2 를 정하되, 애매한 구간은 L1(관찰)로 남깁니다.
    """
    if has_means:
        return (
            RiskLevel.L3_EMERGENCY if score >= _SCORE_MEANS_L3 else RiskLevel.L2_WARNING
        )
    if score >= _SCORE_L2:
        return RiskLevel.L2_WARNING
    if score >= _SCORE_L1:
        return RiskLevel.L1_CONCERN
    return RiskLevel.L0_NORMAL


def detect_crisis(text: str, context: Optional[dict] = None) -> CrisisResult:
    """규칙 레이어(L0) 위기 감지 — 맥락 점수 방식.

    본인을 주어로 하는 욕구 표현(신호 사전)을 찾고, **시제·부정·강도** 표시어로
    점수를 보정해 등급을 정합니다. 같은 "죽고 싶다"라도 현재형은 확정하고,
    과거 회상("당시에 죽고싶다고 생각했다")은 점수를 깎아 L1(관찰)로 내립니다.

    Args:
        text: 보호자가 입력한 문장.
        context: 향후 확장용(이전 대화·반려동물 이름 등). 현재 규칙 레이어는
            미사용이지만 LLM 레이어(L1)·융합 단계와 시그니처를 맞춰 둡니다.

    Returns:
        CrisisResult — risk_level·subject·signals·hotline_required·score·reason 등.

    Note:
        **놓침(미탐)을 최악으로** 봅니다. 그래서 깎이더라도 본인 죽음 욕구는
        L0 로 완전히 떨구기보다 L1(관찰)로 남겨 LLM 레이어가 재확인하게 합니다.
    """
    del context  # 규칙 레이어 미사용 (시그니처 호환 목적)

    normalized = _normalize(text)

    matched: list[CrisisSignal] = []
    for pattern, category, level in _SIGNAL_TABLE:
        if pattern in normalized:
            matched.append(
                CrisisSignal(pattern=pattern, category=category, level=level)
            )

    # 신호가 없으면: 반려동물 죽음 언급일 수 있으나 위기는 아님(L0).
    if not matched:
        subject = (
            Subject.PET
            if any(hint in normalized for hint in _PET_DEATH_HINTS)
            else Subject.NONE
        )
        reason = (
            "반려동물과의 이별/죽음 서술로 보이며 본인 위기 신호는 없음 (정상)"
            if subject == Subject.PET
            else "위험 신호가 감지되지 않음 (정상)"
        )
        return CrisisResult(
            risk_level=RiskLevel.L0_NORMAL,
            subject=subject,
            signals=[],
            hotline_required=False,
            reason=reason,
        )

    # --- 기본 점수: 매칭된 신호 중 가장 높은 범주 점수 ---
    base = max(_CATEGORY_BASE[s.category] for s in matched)
    has_means = any(s.category == "means" for s in matched)

    # --- 맥락 보정 ---
    markers: list[str] = []
    score = base

    # 부정: "죽고 싶지 않아" 등 (살고 싶지 않다=위기 와는 구분된 명시 목록)
    negations = _collect_markers(normalized, _NEGATED_DEATH_DESIRE)
    if negations:
        score -= _DAMPEN_NEGATION
        markers += [f"-부정({n})" for n in negations]

    # 현재 안전("지금은 괜찮") 이 있으면 우선 적용하고 현재성 가산은 생략.
    safe = _collect_markers(normalized, _SAFE_MARKERS)
    past = _collect_markers(normalized, _PAST_MARKERS)
    if safe:
        score -= _DAMPEN_SAFE
        markers += [f"-안전({m})" for m in safe]
    elif past:
        score -= _DAMPEN_PAST
        markers += [f"-과거({m})" for m in past]
    else:
        present = _collect_markers(normalized, _PRESENT_MARKERS)
        if present:
            score += _BOOST_PRESENT
            markers += [f"+현재({m})" for m in present]

    # 강도 표시어 가산 (항상)
    intensity = _collect_markers(normalized, _INTENSITY_MARKERS)
    if intensity:
        score += _BOOST_INTENSITY
        markers += [f"+강도({m})" for m in intensity]

    score = max(0, score)
    level = _score_to_level(score, has_means)

    categories = sorted({s.category for s in matched})
    reason = (
        f"본인 위기 신호({', '.join(categories)}) 점수 {score} → "
        f"{level.label}({level.name})"
    )
    if markers:
        reason += f" / 맥락: {', '.join(markers)}"

    return CrisisResult(
        risk_level=level,
        subject=Subject.SELF,
        signals=matched,
        hotline_required=level >= HOTLINE_REQUIRED_FROM,
        reason=reason,
        score=score,
        context_markers=markers,
    )


# --------------------------------------------------------------------------- #
# LLM 분류 레이어(L1) — 규칙이 놓치는 완곡·맥락 표현 보완
# --------------------------------------------------------------------------- #
# 규칙(L0)과 **보수적으로 융합**(max)합니다. 미탐(놓침)이 가장 치명적이라,
# 융합은 등급을 절대 내리지 않습니다. LLM 호출은 주입(generate)받아, 엔진 미연결
# 이나 호출 실패 시 규칙 결과로 graceful 폴백합니다.


class GenerateFn(Protocol):
    """provider.generate 와 맞춘 호출 시그니처 (주입용)."""

    def __call__(
        self,
        prompt: str,
        *,
        max_tokens: int = 256,
        temperature: float = 0.0,
        json_mode: bool = False,
    ) -> str: ...


@dataclass(frozen=True)
class LLMVerdict:
    """L1 분류 결과."""

    risk_level: RiskLevel
    subject: str
    reason: str


_VALID_SUBJECTS: Final[frozenset[str]] = frozenset(
    {Subject.SELF, Subject.PET, Subject.OTHER, Subject.NONE}
)


def classify_with_llm(text: str, generate: GenerateFn) -> Optional[LLMVerdict]:
    """LLM(L1)으로 위기 등급을 분류합니다(JSON 강제).

    prompts/safety.py 의 분류 프롬프트로 generate 를 호출하고, JSON 을 파싱해
    LLMVerdict 로 돌려줍니다. 호출·파싱 실패는 None 으로 흡수(상위에서 규칙 폴백).

    Args:
        text: 보호자가 입력한 문장.
        generate: provider.generate 호환 함수(json_mode 지원).

    Returns:
        LLMVerdict 또는 None(실패 시).
    """
    messages = safety_prompt.build_messages(text)
    prompt = f"{messages[0]['content']}\n\n{messages[1]['content']}"
    try:
        raw = generate(prompt, max_tokens=256, temperature=0.0, json_mode=True)
        data = json.loads(raw)
        level = int(data.get("risk_level", 0))
        level = min(int(RiskLevel.L3_EMERGENCY), max(int(RiskLevel.L0_NORMAL), level))
        subject = data.get("subject", Subject.NONE)
        if subject not in _VALID_SUBJECTS:
            subject = Subject.NONE
        return LLMVerdict(
            risk_level=RiskLevel(level),
            subject=subject,
            reason=str(data.get("reason", "")),
        )
    except Exception:  # noqa: BLE001 — 호출·파싱 실패는 규칙 폴백으로 흡수(graceful)
        return None


def assess_crisis(
    text: str,
    context: Optional[dict] = None,
    *,
    generate: Optional[GenerateFn] = None,
) -> CrisisResult:
    """위기 감지 **공식 창구** — 백엔드는 이 함수만 호출하세요.

    백엔드가 의존하는 단 하나의 진입점입니다. 함수 이름과 반환 타입
    (CrisisResult / as_dict)을 고정해 두면, 내부 구현이 바뀌어도 백엔드
    코드는 그대로 둘 수 있습니다.

    - **generate 미주입(기본)**: 규칙 레이어(L0) `detect_crisis` 결과만 반환.
      (백엔드 현재 호출 `assess_crisis(note)` 는 이 경로 — 동작 그대로 유지.)
    - **generate 주입**: L0 + LLM 레이어(L1)를 **보수적 융합**(max — "애매하면 ↑").
      미탐 0은 규칙이 보장하므로 융합은 등급을 내리지 않습니다. L1 실패 시 규칙 폴백.

    Args:
        text: 보호자가 입력한 문장.
        context: 향후 확장용(이전 대화 등). 현재 미사용.
        generate: 주입 시 L1 활성화(provider.generate). None 이면 규칙만.

    Returns:
        CrisisResult — risk_level·hotline_required 등 (detect_crisis와 동일 타입).
    """
    rule = detect_crisis(text, context)
    if generate is None:
        return rule

    verdict = classify_with_llm(text, generate)
    if verdict is None:  # L1 실패 → 규칙 결과로 폴백
        return rule

    # 보수적 융합: 등급은 더 높은 쪽(절대 내리지 않음).
    fused = max(rule.risk_level, verdict.risk_level)
    # 대상(subject): L1이 등급을 올렸으면 L1 판단을, 아니면 규칙 판단을 따름.
    subject = verdict.subject if verdict.risk_level > rule.risk_level else rule.subject
    reason = (
        f"융합(L0={rule.risk_level.name}, L1={verdict.risk_level.name}) "
        f"→ {fused.name}; L1근거: {verdict.reason}"
    )
    return CrisisResult(
        risk_level=fused,
        subject=subject,
        signals=rule.signals,
        hotline_required=fused >= HOTLINE_REQUIRED_FROM,
        reason=reason,
        score=rule.score,
        context_markers=rule.context_markers,
    )
