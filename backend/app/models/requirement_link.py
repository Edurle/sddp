from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RequirementLink(Base):
    __tablename__ = "requirement_links"
    __table_args__ = (
        UniqueConstraint("source_id", "target_id", "link_type", name="uq_req_link"),
        Index("idx_link_source", "source_id"),
        Index("idx_link_target", "target_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    source_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("requirements.id"), nullable=False)
    target_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("requirements.id"), nullable=False)
    link_type: Mapped[str] = mapped_column(String(20), nullable=False)
    created_by: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
