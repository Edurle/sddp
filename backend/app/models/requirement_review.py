from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RequirementReview(Base):
    __tablename__ = "requirement_reviews"
    __table_args__ = (
        Index("idx_review_req", "requirement_id"),
        Index("idx_review_type", "review_type"),
        Index("idx_reviewer", "reviewer_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    requirement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("requirements.id"), nullable=False)
    review_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    reviewer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )
    comment: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)
