from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    ERR_FORBIDDEN,
    ERR_INVITATION_INVALID,
    ERR_NOT_FOUND,
)
from app.models import Invitation, TeamMember


async def get_pending_invitations(db: AsyncSession, user_id: int) -> list[dict]:
    stmt = select(Invitation).where(
        Invitation.invitee_id == user_id,
        Invitation.status == "pending",
    )
    result = await db.execute(stmt)
    invitations = result.scalars().all()

    items = []
    for inv in invitations:
        items.append({
            "id": inv.id,
            "team_id": inv.team_id,
            "inviter_id": inv.inviter_id,
            "invitee_id": inv.invitee_id,
            "status": inv.status,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
        })
    return items


async def handle_invitation(db: AsyncSession, invitation_id: int, user_id: int, action: str) -> dict:
    stmt = select(Invitation).where(Invitation.id == invitation_id)
    result = await db.execute(stmt)
    invitation = result.scalar_one_or_none()

    if invitation is None:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_NOT_FOUND, "邀请不存在")

    if invitation.invitee_id != user_id:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_FORBIDDEN, "无权限")

    if invitation.status != "pending":
        from app.exceptions import BusinessError
        raise BusinessError(ERR_INVITATION_INVALID, "邀请已处理")

    if action == "accept":
        invitation.status = "accepted"
        invitation.responded_at = datetime.now(timezone.utc)
        member = TeamMember(team_id=invitation.team_id, user_id=user_id)
        db.add(member)
    elif action == "reject":
        invitation.status = "rejected"
        invitation.responded_at = datetime.now(timezone.utc)

    await db.commit()

    return {
        "id": invitation.id,
        "status": invitation.status,
    }
