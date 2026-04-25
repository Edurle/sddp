import secrets
from datetime import datetime, timedelta, timezone

def _utcnow():
    return datetime.utcnow()

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import config
from app.exceptions import BusinessError, ERR_EMAIL_EXISTS, ERR_CREDENTIALS, ERR_EMAIL_UNVERIFIED, ERR_NOT_FOUND
from app.models.password_reset_token import PasswordResetToken
from app.models.role import MemberRole, Role, RolePermission
from app.models.team import TeamMember
from app.models.user import User
from app.utils.email import send_verification_email, send_password_reset_email
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


async def register(db: AsyncSession, email: str, password: str, nickname: str) -> dict:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise BusinessError(ERR_EMAIL_EXISTS, "邮箱已注册")

    user = User(
        email=email,
        nickname=nickname,
        password_hash=hash_password(password),
        email_verified=True,
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    await db.flush()

    token = secrets.token_urlsafe(32)
    reset_token = PasswordResetToken(
        user_id=user.id,
        token=token,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(reset_token)
    await db.commit()

    send_verification_email(email, token)

    return {"message": "注册成功", "user": {"id": user.id, "email": user.email, "nickname": user.nickname}}


async def verify_email(db: AsyncSession, token: str) -> dict:
    stmt = select(PasswordResetToken).where(PasswordResetToken.token == token)
    result = await db.execute(stmt)
    reset_token = result.scalar_one_or_none()

    if reset_token is None:
        raise BusinessError(ERR_NOT_FOUND, "无效的验证链接")
    if reset_token.used:
        raise BusinessError(ERR_NOT_FOUND, "验证链接已使用")
    expires = reset_token.expires_at
    if expires.tzinfo is not None:
        expires = expires.replace(tzinfo=None)
    if expires < _utcnow():
        raise BusinessError(ERR_NOT_FOUND, "验证链接已过期")

    reset_token.used = True

    stmt = select(User).where(User.id == reset_token.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.email_verified = True

    await db.commit()

    return {"message": "邮箱验证成功"}


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


async def forgot_password(db: AsyncSession, email: str) -> dict:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is not None:
        token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db.add(reset_token)
        await db.commit()
        send_password_reset_email(email, token)

    return {"message": "重置邮件已发送"}


async def reset_password(db: AsyncSession, token: str, new_password: str) -> dict:
    stmt = select(PasswordResetToken).where(PasswordResetToken.token == token)
    result = await db.execute(stmt)
    reset_token = result.scalar_one_or_none()

    if reset_token is None:
        raise BusinessError(ERR_NOT_FOUND, "无效的重置链接")
    if reset_token.used:
        raise BusinessError(ERR_NOT_FOUND, "重置链接已使用")
    expires = reset_token.expires_at
    if expires.tzinfo is not None:
        expires = expires.replace(tzinfo=None)
    if expires < _utcnow():
        raise BusinessError(ERR_NOT_FOUND, "重置链接已过期")

    reset_token.used = True

    stmt = select(User).where(User.id == reset_token.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        user.password_hash = hash_password(new_password)

    await db.commit()

    return {"message": "密码重置成功"}
