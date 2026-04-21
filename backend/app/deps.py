from typing import Annotated

from fastapi import Depends, Header

from app.database import get_db
from app.exceptions import BusinessError, ERR_UNAUTHORIZED, ERR_TOKEN_EXPIRED, ERR_FORBIDDEN
from app.utils.security import decode_access_token, TokenExpired, TokenInvalid


async def get_current_user(authorization: Annotated[str, Header()]) -> dict:
    if not authorization.startswith("Bearer "):
        raise BusinessError(ERR_UNAUTHORIZED, "未登录")
    token = authorization[7:]
    try:
        payload = decode_access_token(token)
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


async def get_db_session():
    async for session in get_db():
        yield session
