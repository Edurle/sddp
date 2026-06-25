from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TaskCommit(Base):
    __tablename__ = "task_commits"
    __table_args__ = (
        Index("idx_tc_task", "task_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tasks.id"), nullable=False)
    commit_sha: Mapped[str] = mapped_column(String(40), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, default=None)
    author: Mapped[str | None] = mapped_column(String(100), default=None)
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
