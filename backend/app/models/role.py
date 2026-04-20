from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Role(Base):
    __tablename__ = "roles"
    __table_args__ = (
        UniqueConstraint("team_id", "name", name="uniq_team_role_name"),
        Index("idx_team", "team_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(nullable=False)  # FK -> teams.id
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    is_builtin: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(String(255), default=None)
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (
        UniqueConstraint("role_id", "permission", name="uniq_role_permission"),
        Index("idx_role", "role_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(nullable=False)  # FK -> roles.id
    permission: Mapped[str] = mapped_column(String(100), nullable=False)


class MemberRole(Base):
    __tablename__ = "member_roles"
    __table_args__ = (
        UniqueConstraint("member_id", "role_id", name="uniq_member_role"),
        Index("idx_member", "member_id"),
        Index("idx_role", "role_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    member_id: Mapped[int] = mapped_column(nullable=False)  # FK -> team_members.id
    role_id: Mapped[int] = mapped_column(nullable=False)  # FK -> roles.id
