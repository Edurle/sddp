import hashlib
from typing import Annotated

from fastapi import Cookie, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import BusinessError, ERR_UNAUTHORIZED, ERR_TOKEN_EXPIRED, ERR_FORBIDDEN
from app.models.api_key import ApiKey
from app.models.user import User
from app.services.auth import _collect_user_permissions
from app.utils.security import decode_access_token, TokenExpired, TokenInvalid


async def get_db_session():
    async for session in get_db():
        yield session


async def _authenticate_api_key(x_api_key: str, db: AsyncSession) -> dict:
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    stmt = select(ApiKey).where(ApiKey.key_hash == key_hash)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise BusinessError(ERR_UNAUTHORIZED, "无效的 API Key")

    if not api_key.is_active:
        raise BusinessError(ERR_UNAUTHORIZED, "API Key 已被撤销")

    if api_key.expires_at is not None:
        expires = api_key.expires_at
        if expires.tzinfo is not None:
            from datetime import timezone
            expires = expires.replace(tzinfo=None)
        from datetime import datetime
        if expires < datetime.utcnow():
            raise BusinessError(ERR_UNAUTHORIZED, "API Key 已过期")

    stmt = select(User).where(User.id == api_key.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise BusinessError(ERR_UNAUTHORIZED, "API Key 关联的用户不可用")

    permissions = await _collect_user_permissions(db, user.id)

    return {
        "sub": str(user.id),
        "is_admin": user.is_admin,
        "permissions": permissions,
    }


async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    token: str | None = Cookie(default=None),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    if x_api_key:
        return await _authenticate_api_key(x_api_key, db)

    auth_token = None
    if authorization and authorization.startswith("Bearer "):
        auth_token = authorization[7:]
    elif token:
        auth_token = token
    else:
        raise BusinessError(ERR_UNAUTHORIZED, "未登录")
    try:
        payload = decode_access_token(auth_token)
    except TokenExpired:
        raise BusinessError(ERR_TOKEN_EXPIRED, "Token 已过期")
    except TokenInvalid:
        raise BusinessError(ERR_UNAUTHORIZED, "未登录")
    return payload


async def require_admin(user: Annotated[dict, Depends(get_current_user)]) -> dict:
    if not user.get("is_admin"):
        raise BusinessError(ERR_FORBIDDEN, "无权限")
    return user


def require_permission(permission: str):
    async def _check(
        user: Annotated[dict, Depends(get_current_user)],
    ) -> dict:
        user_permissions: list[str] = user.get("permissions", [])
        if permission not in user_permissions and not user.get("is_admin"):
            raise BusinessError(ERR_FORBIDDEN, "无权限")
        return user

    return _check
