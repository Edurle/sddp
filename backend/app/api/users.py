import hashlib
import secrets
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db_session
from app.exceptions import BusinessError, ERR_NOT_FOUND, ERR_VALIDATION
from app.models.api_key import ApiKey
from app.services import user as user_service
from app.services import task as task_service

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=2, max_length=32)
    avatar: str | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UpdateProfileRequest":
        if self.nickname is None and self.avatar is None:
            raise ValueError("At least one of nickname or avatar must be provided")
        return self


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=64)


class CreateUserApiKeyRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    expires_at: str | None = None


@router.get("")
async def list_users_endpoint(
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
    page_size: int = 100,
) -> dict:
    data = await user_service.list_users(db, 1, page_size, "")
    return {"code": 0, "message": "success", "data": data}


@router.get("/me")
async def get_current_user_info(
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = int(user["sub"])
    data = await user_service.get_user_info(db, user_id)
    return {"code": 0, "message": "success", "data": data}


@router.put("/me")
async def update_profile(
    body: UpdateProfileRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = int(user["sub"])
    data = await user_service.update_profile(db, user_id, body.nickname, body.avatar)
    return {"code": 0, "message": "success", "data": data}


@router.put("/me/password")
async def change_password(
    body: ChangePasswordRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = int(user["sub"])
    result = await user_service.change_password(db, user_id, body.old_password, body.new_password)
    return {"code": 0, "message": result["message"], "data": None}


@router.get("/me/pending")
async def get_pending_items(
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = int(user["sub"])
    data = await user_service.get_pending_items(db, user_id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/me/tasks")
async def get_my_tasks(
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
    status: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1),
) -> dict:
    user_id = int(user["sub"])
    if offset < 0:
        offset = 0
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200
    data = await task_service.list_tasks_by_assignee(db, user_id, status=status, offset=offset, limit=limit)
    return {"code": 0, "message": "success", "data": data}


@router.get("/me/pending-reviews")
async def get_my_pending_reviews(
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = int(user["sub"])
    data = await user_service.get_pending_reviews(db, user_id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/me/projects-tree")
async def get_projects_tree(
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = int(user["sub"])
    data = await user_service.get_projects_tree(db, user_id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/me/work")
async def get_my_work(
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = int(user["sub"])
    data = await user_service.get_user_work(db, user_id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/me/api-keys")
async def create_user_api_key(
    body: CreateUserApiKeyRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = int(user["sub"])

    raw_key = f"sdd_{secrets.token_urlsafe(32)}"
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[:8]

    expires_at = None
    if body.expires_at:
        try:
            expires_at = datetime.fromisoformat(body.expires_at)
        except (ValueError, TypeError):
            raise BusinessError(ERR_VALIDATION, "无效的过期时间格式")

    api_key = ApiKey(
        name=body.name,
        key_hash=key_hash,
        key_prefix=key_prefix,
        user_id=user_id,
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "id": api_key.id,
            "name": api_key.name,
            "raw_key": raw_key,
            "key_prefix": key_prefix,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
        },
    }


@router.get("/me/api-keys")
async def list_user_api_keys(
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = int(user["sub"])
    stmt = select(ApiKey).where(ApiKey.user_id == user_id).order_by(ApiKey.created_at.desc())
    result = await db.execute(stmt)
    keys = result.scalars().all()

    items = []
    for k in keys:
        items.append({
            "id": k.id,
            "name": k.name,
            "key_prefix": k.key_prefix,
            "is_active": k.is_active,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None,
            "created_at": k.created_at.isoformat() if k.created_at else None,
        })

    return {"code": 0, "message": "success", "data": items}


@router.delete("/me/api-keys/{id}")
async def revoke_user_api_key(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = int(user["sub"])
    stmt = select(ApiKey).where(ApiKey.id == id, ApiKey.user_id == user_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise BusinessError(ERR_NOT_FOUND, "API Key 不存在")

    api_key.is_active = False
    await db.commit()

    return {"code": 0, "message": "success", "data": {"id": api_key.id, "is_active": False}}
