from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Requirement(Base):
    __tablename__ = "requirements"
    __table_args__ = (
        Index("idx_req_iter", "iteration_id"),
        Index("idx_req_type", "req_type"),
        Index("idx_req_status", "status"),
        Index("idx_req_creator", "created_by"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    iteration_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("iterations.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    req_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(nullable=False, default=0)
    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="drafting_req",
    )
    description: Mapped[str | None] = mapped_column(Text, default=None)
    type_detail: Mapped[dict | None] = mapped_column(JSONB, default=None)
    prototype_html: Mapped[str | None] = mapped_column(Text, default=None)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc)
    )
