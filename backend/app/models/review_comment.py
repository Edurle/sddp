from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ReviewComment(Base):
    __tablename__ = "review_comments"
    __table_args__ = (
        Index("idx_rc_requirement", "requirement_id"),
        Index("idx_rc_reviewer", "reviewer_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    requirement_id: Mapped[int] = mapped_column(nullable=False)
    reviewer_id: Mapped[int] = mapped_column(nullable=False)
    review_type: Mapped[str] = mapped_column(String(20), nullable=False)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
