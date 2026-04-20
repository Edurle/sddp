from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RequirementReview(Base):
    __tablename__ = "requirement_reviews"
    __table_args__ = (
        Index("idx_requirement", "requirement_id"),
        Index("idx_type", "review_type"),
        Index("idx_reviewer", "reviewer_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    requirement_id: Mapped[int] = mapped_column(nullable=False)  # FK -> requirements.id
    review_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    reviewer_id: Mapped[int] = mapped_column(nullable=False)  # FK -> users.id
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )
    comment: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
