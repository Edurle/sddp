from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_current_user

router = APIRouter()


class UpdateProfileRequest(BaseModel):
    nickname: str | None = None
    avatar: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.get("/me")
async def get_current_user_info(
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/me")
async def update_profile(
    body: UpdateProfileRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/me/password")
async def change_password(
    body: ChangePasswordRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/me/pending")
async def get_pending_items(
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")
