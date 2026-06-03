import hashlib
from typing import Annotated

from fastapi import Cookie, Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exceptions import BusinessError, ERR_UNAUTHORIZED, ERR_TOKEN_EXPIRED, ERR_FORBIDDEN
from app.models.api_key import ApiKey
from app.models.user import User
from app.services.auth import _collect_user_permissions, _collect_team_permissions
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
        from datetime import datetime, timezone
        expires = api_key.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
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


async def check_team_permission(
    db: AsyncSession, user: dict, team_id: int, permission: str,
) -> dict:
    if user.get("is_admin"):
        return user
    user_id = int(user["sub"])
    perms = await _collect_team_permissions(db, user_id, team_id)
    if permission not in perms:
        raise BusinessError(ERR_FORBIDDEN, "无权限")
    return user


async def _team_id_from_project(db: AsyncSession, project_id: int) -> int:
    from app.models import Project
    stmt = select(Project).where(Project.id == project_id, Project.is_deleted == False)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise BusinessError(ERR_FORBIDDEN, "项目不存在")
    return project.team_id


async def _team_id_from_iteration(db: AsyncSession, iteration_id: int) -> int:
    from app.models import Iteration as IterModel
    stmt = select(IterModel).where(IterModel.id == iteration_id)
    result = await db.execute(stmt)
    iteration = result.scalar_one_or_none()
    if iteration is None:
        raise BusinessError(ERR_FORBIDDEN, "迭代不存在")
    return await _team_id_from_project(db, iteration.project_id)


async def _team_id_from_requirement(db: AsyncSession, req_id: int) -> int:
    from app.models import Requirement as ReqModel
    stmt = select(ReqModel).where(ReqModel.id == req_id, ReqModel.is_deleted == False)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_FORBIDDEN, "需求不存在")
    return await _team_id_from_iteration(db, req.iteration_id)


async def _team_id_from_task(db: AsyncSession, task_id: int) -> int:
    from app.models import Task as TaskModel
    stmt = select(TaskModel).where(TaskModel.id == task_id, TaskModel.is_deleted == False)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise BusinessError(ERR_FORBIDDEN, "任务不存在")
    return await _team_id_from_requirement(db, task.requirement_id)


async def _team_id_from_execution_record(db: AsyncSession, record_id: int) -> int:
    from app.models import TestExecutionRecord, TestExecutionRound
    stmt = select(TestExecutionRecord).where(TestExecutionRecord.id == record_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        raise BusinessError(ERR_FORBIDDEN, "执行记录不存在")
    round_stmt = select(TestExecutionRound).where(TestExecutionRound.id == record.round_id)
    round_result = await db.execute(round_stmt)
    round_obj = round_result.scalar_one_or_none()
    if round_obj is None:
        raise BusinessError(ERR_FORBIDDEN, "执行轮次不存在")
    return await _team_id_from_task(db, round_obj.task_id)
