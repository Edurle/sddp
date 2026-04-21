from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db_session
from app.services import invitation as inv_svc

router = APIRouter()


class HandleInvitationRequest(BaseModel):
    action: str


@router.get("/pending")
async def get_pending_invitations(
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await inv_svc.get_pending_invitations(db, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.put("/{id}")
async def handle_invitation(
    id: int,
    body: HandleInvitationRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await inv_svc.handle_invitation(db, id, int(user["sub"]), body.action)
    return {"code": 0, "message": "success", "data": data}
