from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TestExecutionRound(Base):
    __tablename__ = "test_execution_rounds"
    __table_args__ = (
        Index("idx_task", "task_id"),
        Index("idx_executor", "executed_by"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("tasks.id"), nullable=False)
    executed_by: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class TestExecutionRecord(Base):
    __tablename__ = "test_execution_records"
    __table_args__ = (
        Index("idx_round", "round_id"),
        Index("idx_case", "test_case_id"),
        Index("idx_ter_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    round_id: Mapped[int] = mapped_column(ForeignKey("test_execution_rounds.id"), nullable=False)
    test_case_id: Mapped[int] = mapped_column(ForeignKey("test_cases.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    actual_result: Mapped[str | None] = mapped_column(Text, default=None)
    failure_reason: Mapped[str | None] = mapped_column(Text, default=None)
    log_output: Mapped[str | None] = mapped_column(Text, default=None)
    duration_ms: Mapped[int | None] = mapped_column(Integer, default=None)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
