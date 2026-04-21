from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Invitation(Base):
    __tablename__ = "invitations"
    __table_args__ = (
        Index("idx_inv_team", "team_id"),
        Index("idx_inv_inviter", "inviter_id"),
        Index("idx_inv_invitee", "invitee_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(nullable=False)  # FK -> teams.id
    inviter_id: Mapped[int] = mapped_column(nullable=False)  # FK -> users.id
    invitee_id: Mapped[int] = mapped_column(nullable=False)  # FK -> users.id
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    responded_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
