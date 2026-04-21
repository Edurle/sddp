from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import require_admin, get_db_session
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
