from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    ERR_ALREADY_MEMBER,
    ERR_CANNOT_REMOVE_OWNER,
    ERR_FORBIDDEN,
    ERR_NOT_FOUND,
    ERR_VALIDATION,
)
from app.models import Team, TeamMember, Role, RolePermission, MemberRole
from app.models.user import User


async def create_team(db: AsyncSession, user_id: int, name: str, description: str | None) -> dict:
    team = Team(name=name, description=description, owner_id=user_id)
    db.add(team)
    await db.flush()

    member = TeamMember(team_id=team.id, user_id=user_id)
    db.add(member)
    await db.flush()

    role = Role(
        team_id=team.id,
        name="所有者",
        is_builtin=True,
        description="团队所有者，拥有全部权限",
    )
    db.add(role)
    await db.flush()

    all_permissions = [
        "project:create", "project:edit", "project:archive", "project:delete",
        "iteration:create", "iteration:edit", "iteration:start", "iteration:complete",
        "requirement:create", "requirement:edit", "requirement:delete",
        "requirement:submit_review_req", "requirement:submit_review_spec", "requirement:submit_review_tests",
        "requirement:review_req", "requirement:review_spec", "requirement:review_tests",
        "specification:edit",
        "test_case:create", "test_case:edit", "test_case:delete",
        "task:create", "task:edit", "task:delete", "task:test", "task:complete",
        "member:invite", "member:remove", "member:assign_role",
        "spec_template:edit",
    ]
    for p in all_permissions:
        db.add(RolePermission(role_id=role.id, permission=p))
    await db.flush()

    db.add(MemberRole(member_id=member.id, role_id=role.id))
    await db.commit()
    await db.refresh(team)

    return _team_to_dict(team)


async def get_team(db: AsyncSession, team_id: int, user_id: int) -> dict:
    team = await _get_team_or_fail(db, team_id)
    await _check_member(db, team_id, user_id)

    owner_user = await _get_user(db, team.owner_id)
    member_count = await _count_members(db, team_id)

    result = _team_to_dict(team)
    result["owner"] = _user_to_dict(owner_user) if owner_user else None
    result["member_count"] = member_count
    return result


async def update_team(db: AsyncSession, team_id: int, name: str | None, description: str | None) -> dict:
    if name is not None and name.strip() == "":
        from app.exceptions import BusinessError
        raise BusinessError(ERR_VALIDATION, "团队名称不能为空")

    team = await _get_team_or_fail(db, team_id)
    if name is not None:
        team.name = name
    if description is not None:
        team.description = description
    await db.commit()
    await db.refresh(team)
    return _team_to_dict(team)


async def dissolve_team(db: AsyncSession, team_id: int, user_id: int, confirm_name: str | None = None) -> dict:
    if confirm_name:
        try:
            confirm_name = confirm_name.encode("latin-1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass

    team = await _get_team_or_fail(db, team_id)
    if team.owner_id != user_id:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_FORBIDDEN, "无权限")
    if confirm_name and confirm_name != team.name:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_VALIDATION, "确认名称不匹配")

    team.is_deleted = True
    team.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return _team_to_dict(team)


async def transfer_team(db: AsyncSession, team_id: int, user_id: int, new_owner_id: int) -> dict:
    team = await _get_team_or_fail(db, team_id)
    if team.owner_id != user_id:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_FORBIDDEN, "无权限")
    if new_owner_id == user_id:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_VALIDATION, "不能转让给自己")

    new_owner_member = await _find_member(db, team_id, new_owner_id)
    if new_owner_member is None:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_NOT_FOUND, "新所有者不是团队成员")

    team.owner_id = new_owner_id
    await db.commit()
    await db.refresh(team)
    return _team_to_dict(team)


async def get_members(db: AsyncSession, team_id: int, role_id: int | None = None) -> list[dict]:
    from app.models.role import MemberRole, Role as RoleModel, RolePermission
    team = await _get_team_or_fail(db, team_id)

    if role_id is not None:
        stmt = (
            select(TeamMember)
            .join(MemberRole, MemberRole.member_id == TeamMember.id)
            .where(
                TeamMember.team_id == team_id,
                TeamMember.is_deleted == False,
                MemberRole.role_id == role_id,
            )
        )
    else:
        stmt = select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.is_deleted == False,
        )

    result = await db.execute(stmt)
    members = result.scalars().all()

    items = []
    for m in members:
        user = await _get_user(db, m.user_id)

        mr_stmt = select(MemberRole).where(MemberRole.member_id == m.id)
        mr_result = await db.execute(mr_stmt)
        member_roles = mr_result.scalars().all()

        role_ids = []
        role_names = []
        for mr in member_roles:
            role_stmt = select(RoleModel).where(RoleModel.id == mr.role_id, RoleModel.is_deleted == False)
            role_result = await db.execute(role_stmt)
            role = role_result.scalar_one_or_none()
            if role:
                role_ids.append(role.id)
                role_names.append(role.name)

        items.append({
            "id": m.id,
            "team_id": m.team_id,
            "user_id": m.user_id,
            "joined_at": m.joined_at.isoformat() if m.joined_at else None,
            "user": _user_to_dict(user) if user else None,
            "is_owner": m.user_id == team.owner_id,
            "role_ids": role_ids,
            "role_names": role_names,
        })
    return items


async def invite_member(db: AsyncSession, team_id: int, inviter_id: int, identifier: str) -> dict:
    from app.models.invitation import Invitation

    stmt = select(User).where(User.email == identifier)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()

    if target_user is None:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_NOT_FOUND, "用户不存在")

    existing_member = await _find_member(db, team_id, target_user.id)
    if existing_member is not None:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_ALREADY_MEMBER, "该用户已是团队成员")

    stmt = select(Invitation).where(
        Invitation.team_id == team_id,
        Invitation.invitee_id == target_user.id,
        Invitation.status == "pending",
    )
    result = await db.execute(stmt)
    existing_inv = result.scalar_one_or_none()
    if existing_inv is not None:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_VALIDATION, "已存在待处理的邀请")

    invitation = Invitation(
        team_id=team_id,
        inviter_id=inviter_id,
        invitee_id=target_user.id,
        status="pending",
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return {
        "id": invitation.id,
        "team_id": invitation.team_id,
        "inviter_id": invitation.inviter_id,
        "invitee_id": invitation.invitee_id,
        "status": invitation.status,
        "created_at": invitation.created_at.isoformat() if invitation.created_at else None,
    }


async def remove_member(db: AsyncSession, team_id: int, user_id: int) -> dict:
    team = await _get_team_or_fail(db, team_id)
    if team.owner_id == user_id:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_CANNOT_REMOVE_OWNER, "不能移除团队所有者")

    member = await _find_member(db, team_id, user_id)
    if member is None:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_NOT_FOUND, "成员不存在")

    member.is_deleted = True
    member.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": member.id}


async def assign_roles(db: AsyncSession, team_id: int, user_id: int, role_ids: list[int]) -> dict:
    member = await _find_member(db, team_id, user_id)
    if member is None:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_NOT_FOUND, "成员不存在")

    for rid in role_ids:
        stmt = select(Role).where(Role.id == rid, Role.is_deleted == False)
        result = await db.execute(stmt)
        role = result.scalar_one_or_none()
        if role is None:
            from app.exceptions import BusinessError
            raise BusinessError(ERR_NOT_FOUND, "角色不存在")

    stmt = select(MemberRole).where(MemberRole.member_id == member.id)
    result = await db.execute(stmt)
    existing = result.scalars().all()
    for mr in existing:
        await db.delete(mr)
    await db.flush()

    for rid in role_ids:
        db.add(MemberRole(member_id=member.id, role_id=rid))

    await db.commit()
    return {"member_id": member.id, "role_ids": role_ids}


async def _get_team_or_fail(db: AsyncSession, team_id: int) -> Team:
    stmt = select(Team).where(Team.id == team_id, Team.is_deleted == False)
    result = await db.execute(stmt)
    team = result.scalar_one_or_none()
    if team is None:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_NOT_FOUND, "团队不存在")
    return team


async def _check_member(db: AsyncSession, team_id: int, user_id: int):
    member = await _find_member(db, team_id, user_id)
    if member is None:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_FORBIDDEN, "无权限")


async def _find_member(db: AsyncSession, team_id: int, user_id: int) -> TeamMember | None:
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
        TeamMember.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_user(db: AsyncSession, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _count_members(db: AsyncSession, team_id: int) -> int:
    stmt = select(func.count()).select_from(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one()


def _team_to_dict(team: Team) -> dict:
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "owner_id": team.owner_id,
        "is_deleted": team.is_deleted,
        "created_at": team.created_at.isoformat() if team.created_at else None,
        "updated_at": team.updated_at.isoformat() if team.updated_at else None,
    }


def _user_to_dict(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "is_admin": user.is_admin,
    }
