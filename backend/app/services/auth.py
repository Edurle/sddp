from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import config
from app.exceptions import BusinessError, ERR_CREDENTIALS, ERR_EMAIL_UNVERIFIED, ERR_FORBIDDEN
from app.models.role import MemberRole, Role, RolePermission
from app.models.team import TeamMember
from app.models.user import User
from app.utils.security import hash_password, verify_password, create_access_token


async def _collect_user_permissions(db: AsyncSession, user_id: int) -> list[str]:
    stmt = select(TeamMember).where(
        TeamMember.user_id == user_id, TeamMember.is_deleted == False,
    )
    result = await db.execute(stmt)
    members = result.scalars().all()

    all_perms: set[str] = set()
    for member in members:
        mr_stmt = select(MemberRole).where(MemberRole.member_id == member.id)
        mr_result = await db.execute(mr_stmt)
        member_roles = mr_result.scalars().all()

        for mr in member_roles:
            rp_stmt = select(RolePermission).where(RolePermission.role_id == mr.role_id)
            rp_result = await db.execute(rp_stmt)
            role_perms = rp_result.scalars().all()
            for rp in role_perms:
                all_perms.add(rp.permission)

    return sorted(all_perms)


async def _collect_team_permissions(db: AsyncSession, user_id: int, team_id: int) -> list[str]:
    stmt = select(TeamMember).where(
        TeamMember.user_id == user_id,
        TeamMember.team_id == team_id,
        TeamMember.is_deleted == False,
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()
    if member is None:
        return []

    perms: set[str] = set()
    mr_stmt = select(MemberRole).where(MemberRole.member_id == member.id)
    mr_result = await db.execute(mr_stmt)
    member_roles = mr_result.scalars().all()

    for mr in member_roles:
        rp_stmt = select(RolePermission).where(RolePermission.role_id == mr.role_id)
        rp_result = await db.execute(rp_stmt)
        role_perms = rp_result.scalars().all()
        for rp in role_perms:
            perms.add(rp.permission)

    return sorted(perms)


async def login(db: AsyncSession, email: str, password: str, remember: bool = False) -> dict:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise BusinessError(ERR_CREDENTIALS, "邮箱或密码错误")
    if not verify_password(password, user.password_hash):
        raise BusinessError(ERR_CREDENTIALS, "邮箱或密码错误")
    if not user.email_verified:
        raise BusinessError(ERR_EMAIL_UNVERIFIED, "邮箱未验证")
    if not user.is_active:
        raise BusinessError(ERR_FORBIDDEN, "账号已被禁用")

    permissions = await _collect_user_permissions(db, user.id)

    if remember:
        expires_delta = timedelta(days=config.REMEMBER_TOKEN_EXPIRE_DAYS)
    else:
        expires_delta = timedelta(hours=config.ACCESS_TOKEN_EXPIRE_HOURS)

    token = create_access_token(
        {"sub": str(user.id), "is_admin": user.is_admin, "permissions": permissions},
        expires_delta=expires_delta,
    )

    return {
        "token": token,
        "user": {
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "avatar": user.avatar,
            "is_admin": user.is_admin,
        },
    }
