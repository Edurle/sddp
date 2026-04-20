from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_current_user

router = APIRouter()


class HandleInvitationRequest(BaseModel):
    action: str


@router.get("/pending")
async def get_pending_invitations(
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/{id}")
async def handle_invitation(
    id: int,
    body: HandleInvitationRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")
