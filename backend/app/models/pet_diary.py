from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.rdb import Base


class PetDiary(Base):
    """보호자가 앱에서 작성하는 반려동물 일기 (1단계 건강관리).

    pet_id는 MongoDB의 pets 컬렉션 ObjectId(24자 hex 문자열)를 참조.
    """

    __tablename__ = "pet_diaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pet_id: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    record_date: Mapped[date] = mapped_column(Date, nullable=False)

    # 식사
    meal_amount: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # 0.0~1.0 (1/3 = 0.33)
    meal_note: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # 증상 (콤마 구분 문자열 또는 JSON)
    symptoms: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 산책
    walked: Mapped[bool] = mapped_column(Boolean, default=False)
    walk_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # 체중·메모
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class VetAdvice(Base):
    """수의사가 일기 기록에 달아주는 처방·조언 (웹 대시보드에서 작성)."""

    __tablename__ = "vet_advice"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    diary_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("pet_diaries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    vet_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("vets.id", ondelete="CASCADE"), nullable=False
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    prescription: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
