from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Webhook(Base):
    __tablename__ = "webhooks"
    __table_args__ = (
        Index("idx_webhook_team", "team_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str | None] = mapped_column(Text, default=None)
    events: Mapped[dict | None] = mapped_column(JSONB, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc)
    )


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        Index("idx_wd_webhook", "webhook_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    webhook_id: Mapped[int] = mapped_column(nullable=False)
    event: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, default=None)
    status_code: Mapped[int | None] = mapped_column(default=None)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    error: Mapped[str | None] = mapped_column(Text, default=None)
