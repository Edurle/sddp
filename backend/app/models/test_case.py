from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TestCase(Base):
    __tablename__ = "test_cases"
    __table_args__ = (
        Index("idx_tc_req", "requirement_id"),
        Index("idx_tc_type", "case_type"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    requirement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("requirements.id"), nullable=False)
    case_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    case_type: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    precondition: Mapped[str | None] = mapped_column(Text, default=None)
    steps: Mapped[str] = mapped_column(Text, nullable=False)
    expected_result: Mapped[str] = mapped_column(Text, nullable=False)
    related_api: Mapped[str | None] = mapped_column(String(500), default=None)
    related_element: Mapped[str | None] = mapped_column(String(200), default=None)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
