from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db_session, check_team_permission
from app.services import webhook as wh_svc

router = APIRouter()

teams_nested_router = APIRouter()


class CreateWebhookRequest(BaseModel):
    url: str
    events: list[str] | None = None
    secret: str | None = None


class UpdateWebhookRequest(BaseModel):
    url: str | None = None
    events: list[str] | None = None
    secret: str | None = None
    is_active: bool | None = None


@teams_nested_router.post("/{teamId}/webhooks")
async def create_webhook(
    teamId: int,
    body: CreateWebhookRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, teamId, "member:invite")
    data = await wh_svc.create_webhook(
        db, teamId, body.url, int(user["sub"]),
        events=body.events, secret=body.secret,
    )
    return {"code": 0, "message": "success", "data": data}


@teams_nested_router.get("/{teamId}/webhooks")
async def list_webhooks(
    teamId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await wh_svc.list_webhooks(db, teamId)
    return {"code": 0, "message": "success", "data": data}


@teams_nested_router.put("/{teamId}/webhooks/{webhook_id}")
async def update_webhook(
    teamId: int,
    webhook_id: int,
    body: UpdateWebhookRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, teamId, "member:invite")
    data = await wh_svc.update_webhook(
        db, webhook_id,
        url=body.url, events=body.events, secret=body.secret, is_active=body.is_active,
    )
    return {"code": 0, "message": "success", "data": data}


@teams_nested_router.delete("/{teamId}/webhooks/{webhook_id}")
async def delete_webhook(
    teamId: int,
    webhook_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, teamId, "member:invite")
    data = await wh_svc.delete_webhook(db, webhook_id)
    return {"code": 0, "message": "success", "data": data}


@teams_nested_router.get("/{teamId}/webhooks/{webhook_id}/deliveries")
async def list_deliveries(
    teamId: int,
    webhook_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await wh_svc.list_deliveries(db, webhook_id)
    return {"code": 0, "message": "success", "data": data}
