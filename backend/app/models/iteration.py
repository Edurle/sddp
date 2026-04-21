from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Index, String, types
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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(nullable=False)  # FK -> projects.id
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    goal: Mapped[str | None] = mapped_column(String, default=None)
    start_date: Mapped[date] = mapped_column(FlexibleDate, nullable=False)
    end_date: Mapped[date] = mapped_column(FlexibleDate, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="planned",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
