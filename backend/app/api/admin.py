import hashlib
import secrets
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import require_admin, get_db_session
from app.exceptions import BusinessError, ERR_VALIDATION, ERR_NOT_FOUND
from app.models.api_key import ApiKey
from app.models.user import User
from app.services import user as user_service

router = APIRouter()


class CreateUserRequest(BaseModel):
    email: EmailStr
    nickname: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=8, max_length=64)


class UpdateUserStatusRequest(BaseModel):
    is_active: bool

    @field_validator("is_active", mode="before")
    @classmethod
    def validate_is_active(cls, v):
        if not isinstance(v, bool):
            raise ValueError("is_active must be a boolean")
        return v


class ResetUserPasswordRequest(BaseModel):
    new_password: str = Field(min_length=8, max_length=64)


class CreateApiKeyRequest(BaseModel):
    user_id: int
    name: str = Field(min_length=1, max_length=100)
    expires_at: str | None = None


@router.get("/users")
async def list_users(
    user: Annotated[dict, Depends(require_admin)],
    db: AsyncSession = Depends(get_db_session),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str = Query(default=""),
) -> dict:
    data = await user_service.list_users(db, page, page_size, search)
    return {"code": 0, "message": "success", "data": data}


@router.post("/users")
async def create_user(
    body: CreateUserRequest,
    user: Annotated[dict, Depends(require_admin)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    data = await user_service.create_user_by_admin(db, body.email, body.nickname, body.password)
    return {"code": 0, "message": "success", "data": data}


@router.put("/users/{id}/status")
async def update_user_status(
    id: int,
    body: UpdateUserStatusRequest,
    user: Annotated[dict, Depends(require_admin)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    admin_user_id = int(user["sub"])
    data = await user_service.toggle_user_status(db, id, body.is_active, admin_user_id)
    return {"code": 0, "message": "success", "data": data}


@router.put("/users/{id}/password")
async def reset_user_password(
    id: int,
    body: ResetUserPasswordRequest,
    user: Annotated[dict, Depends(require_admin)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    data = await user_service.reset_user_password(db, id, body.new_password)
    return {"code": 0, "message": data["message"], "data": None}


@router.post("/api-keys")
async def create_api_key(
    body: CreateApiKeyRequest,
    admin: Annotated[dict, Depends(require_admin)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    stmt = select(User).where(User.id == body.user_id)
    result = await db.execute(stmt)
    target_user = result.scalar_one_or_none()
    if target_user is None:
        raise BusinessError(ERR_NOT_FOUND, "用户不存在")

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
        user_id=body.user_id,
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
            "user_id": api_key.user_id,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "created_at": api_key.created_at.isoformat() if api_key.created_at else None,
        },
    }


@router.get("/users/{id}/api-keys")
async def list_user_api_keys(
    id: int,
    admin: Annotated[dict, Depends(require_admin)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    stmt = select(ApiKey).where(ApiKey.user_id == id).order_by(ApiKey.created_at.desc())
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


@router.delete("/api-keys/{id}")
async def revoke_api_key(
    id: int,
    admin: Annotated[dict, Depends(require_admin)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    stmt = select(ApiKey).where(ApiKey.id == id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if api_key is None:
        raise BusinessError(ERR_NOT_FOUND, "API Key 不存在")

    api_key.is_active = False
    await db.commit()

    return {"code": 0, "message": "success", "data": {"id": api_key.id, "is_active": False}}
