from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SpecTemplate(Base):
    __tablename__ = "spec_templates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("teams.id"), nullable=False, unique=True)
    sections: Mapped[dict] = mapped_column(JSONB, nullable=False)
    updated_by: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("users.id"), default=None)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=lambda: datetime.now(__import__("datetime").timezone.utc),
    )


class SpecDocument(Base):
    __tablename__ = "spec_documents"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    requirement_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("requirements.id"), nullable=False, unique=True)
    current_version: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    versions: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    draft_content: Mapped[dict | None] = mapped_column(JSONB, nullable=True, default=None)
    draft_base_version: Mapped[int | None] = mapped_column(Integer, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=lambda: datetime.now(__import__("datetime").timezone.utc),
    )
