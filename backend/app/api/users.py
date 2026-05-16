from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db_session
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
