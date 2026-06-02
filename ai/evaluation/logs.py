"""LLM 호출 로그(`llm_logs`) 스키마 + 저장 헬퍼.

`GET /api/v1/admin/usage` 가 집계해 보여줄 원본 로그입니다. 지금은 실제 저장
구조가 없어서, 호출 한 건을 표준 형태로 적재하는 스키마/헬퍼를 정의합니다.

⚠️ 개인정보 최소화 (../CLAUDE.md, ../llm/CLAUDE.md §5):
   **대화 원문(프롬프트/응답 텍스트)은 저장하지 않습니다.** 위기 로그는 특히
   등급·신호 위주로만. 길이·토큰·지연 같은 비식별 지표만 남깁니다.

ℹ️ MongoDB 연결은 백엔드(김윤한) 담당입니다. 이 모듈은 컬렉션 핸들을
   **주입받아** 저장만 하므로 백엔드 db 모듈에 의존하지 않습니다.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Final, Optional

# 컬렉션 이름 — 백엔드와 합의해 고정.
COLLECTION: Final[str] = "llm_logs"

# 호출 종류 (어떤 기능에서 LLM을 불렀는지)
KIND_MESSAGE: Final[str] = "message"  # ③ 추모 메시지
KIND_MISSION: Final[str] = "mission"  # ⑤ 미션 추천
KIND_CRISIS: Final[str] = "crisis"  # ⑦ 위기 감지
KIND_FUNERAL: Final[str] = "funeral"  # 2단계 장례 상담
KIND_TRIAGE: Final[str] = "triage"  # 1단계 증상 진료 안내


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class LLMLog:
    """LLM 호출 한 건의 비식별 로그.

    원문 텍스트는 담지 않습니다(개인정보 최소화). 집계(build_report)와
    사용량 대시보드(admin/usage)의 단위가 됩니다.
    """

    kind: str  # KIND_* 중 하나
    provider: str  # gemini | perso | ollama
    model: str  # 예: gemini-2.5-flash
    pet_id: Optional[str] = None  # 반려동물별 집계용 (없으면 전체)
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    ok: bool = True  # 호출 성공 여부
    risk_level: Optional[int] = None  # ⑦ 위기 등급(L0~L3)만 — 원문은 저장 ❌
    created_at: datetime = field(default_factory=_now)

    def to_doc(self) -> dict[str, Any]:
        """MongoDB 저장용 dict. None 필드는 그대로 둬 스키마를 일정하게 유지."""
        return asdict(self)


def save_log(collection: Any, log: LLMLog) -> Any:
    """로그 한 건을 컬렉션에 저장하고 insert 결과를 돌려줍니다.

    Args:
        collection: pymongo/motor 컬렉션 핸들(백엔드가 주입).
        log: 저장할 LLMLog.

    Note:
        동기 pymongo 기준입니다. 백엔드가 motor(async)면 호출부에서
        `await collection.insert_one(log.to_doc())` 로 직접 쓰세요.
    """
    return collection.insert_one(log.to_doc())
