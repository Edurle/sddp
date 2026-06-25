from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Task(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("idx_task_req", "requirement_id"),
        Index("idx_assignee", "assignee_id"),
        Index("idx_task_status", "status"),
        Index("idx_task_creator", "created_by"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    requirement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("requirements.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, default=None)
    assignee_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), default=None)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    git_branch: Mapped[str | None] = mapped_column(String(255), default=None)
    commit_sha: Mapped[str | None] = mapped_column(String(40), default=None)
    task_type: Mapped[str | None] = mapped_column(String(20), default=None)
    source_section: Mapped[str | None] = mapped_column(String(50), default=None)
    spec_reference: Mapped[dict | None] = mapped_column(JSONB, default=None)
    pr_url: Mapped[str | None] = mapped_column(String(500), default=None)
    artifact_url: Mapped[str | None] = mapped_column(String(500), default=None)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc)
    )
