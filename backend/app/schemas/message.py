from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    pet_id: str = Field(..., description="반려동물 ID")
    tone: str = Field("warm", description="메시지 톤 (warm·calm·hopeful)")
    emotion_score: Optional[int] = Field(None, ge=1, le=10, description="감정 점수")
    note: Optional[str] = Field(None, description="보호자 메모")
    consent: bool = Field(
        False, description="(구) 1인칭 편지 동의 — request_first_person 으로 대체됨"
    )
    request_first_person: bool = Field(
        False,
        description="1인칭 편지 요청(보호자 명시 동의). 회복 게이트 통과 시에만 실제 적용",
    )
    guardian_nickname: Optional[str] = Field(
        None, description="로그인 유저 닉네임 (3인칭 글 머리에 표시)"
    )


class MessageResponse(BaseModel):
    id: str
    pet_id: str
    content: str = Field(..., description="생성된 추모 메시지")
    tone: str
    source: str = Field(..., description="생성 출처 (local·perso·stub)")
    first_person: bool = Field(
        False,
        description="이 편지가 실제 1인칭으로 생성됐는지 (요청 + 게이트 통과 시 True)",
    )
    content_unlocked: bool = Field(
        False, description="추모 컨텐츠 공개 여부 — 회복 게이트 통과 시 True"
    )
    allow_first_person: bool = Field(
        False,
        description="1인칭 편지 허용 여부 — content_unlocked + 창 내 위기 없음(risk=0)",
    )
    risk_level: int = Field(0, description="위기 수준 (0=정상, 2=위기 시 1393 우선)")
    crisis_message: Optional[str] = Field(None, description="위기 시 1393 안내")
    support_message: Optional[str] = Field(
        None, description="L1 우려 시 복지자원 안내 문구"
    )
    welfare_resources: Optional[list[dict]] = Field(
        None, description="L1 우려 시 심리상담 자원 목록"
    )
    created_at: datetime
