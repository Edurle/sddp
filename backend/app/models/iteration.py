from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, String, func, types
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FlexibleDate(types.TypeDecorator):
    impl = Date
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if isinstance(value, str):
            return date.fromisoformat(value)
        return value


class Iteration(Base):
    __tablename__ = "iterations"
    __table_args__ = (
        Index("idx_project", "project_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    goal: Mapped[str | None] = mapped_column(String, default=None)
    start_date: Mapped[date] = mapped_column(FlexibleDate, nullable=False)
    end_date: Mapped[date] = mapped_column(FlexibleDate, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="planned",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc)
    )
