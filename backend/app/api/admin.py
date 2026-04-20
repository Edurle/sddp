from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, EmailStr

from app.deps import require_admin

router = APIRouter()


class CreateUserRequest(BaseModel):
    email: EmailStr
    nickname: str
    password: str


class UpdateUserStatusRequest(BaseModel):
    is_active: bool


@router.get("/users")
async def list_users(
    user: Annotated[dict, Depends(require_admin)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    search: str = Query(default=""),
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/users")
async def create_user(
    body: CreateUserRequest,
    user: Annotated[dict, Depends(require_admin)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/users/{id}/status")
async def update_user_status(
    id: int,
    body: UpdateUserStatusRequest,
    user: Annotated[dict, Depends(require_admin)],
) -> dict:
    raise NotImplementedError("Not implemented yet")
