import hashlib
import hmac
import json
import logging

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BusinessError, ERR_NOT_FOUND
from app.models.webhook import Webhook, WebhookDelivery

logger = logging.getLogger(__name__)

VALID_EVENTS = [
    "review.submitted",
    "review.approved",
    "review.rejected",
    "status.changed",
    "task.assigned",
    "task.completed",
]


async def create_webhook(
    db: AsyncSession,
    team_id: int,
    url: str,
    created_by: int,
    events: list[str] | None = None,
    secret: str | None = None,
) -> dict:
    wh = Webhook(
        team_id=team_id,
        url=url,
        secret=secret,
        events=events if events is not None else VALID_EVENTS,
        is_active=True,
        created_by=created_by,
    )
    db.add(wh)
    await db.commit()
    await db.refresh(wh)
    return _webhook_to_dict(wh)


async def list_webhooks(db: AsyncSession, team_id: int) -> list[dict]:
    stmt = select(Webhook).where(Webhook.team_id == team_id).order_by(Webhook.created_at.desc())
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [_webhook_to_dict(wh) for wh in rows]


async def update_webhook(
    db: AsyncSession,
    webhook_id: int,
    url: str | None = None,
    events: list[str] | None = None,
    secret: str | None = None,
    is_active: bool | None = None,
) -> dict:
    stmt = select(Webhook).where(Webhook.id == webhook_id)
    result = await db.execute(stmt)
    wh = result.scalar_one_or_none()
    if wh is None:
        raise BusinessError(ERR_NOT_FOUND, "Webhook 不存在")

    if url is not None:
        wh.url = url
    if events is not None:
        wh.events = events
    if secret is not None:
        wh.secret = secret
    if is_active is not None:
        wh.is_active = is_active

    await db.commit()
    await db.refresh(wh)
    return _webhook_to_dict(wh)


async def delete_webhook(db: AsyncSession, webhook_id: int) -> dict:
    stmt = select(Webhook).where(Webhook.id == webhook_id)
    result = await db.execute(stmt)
    wh = result.scalar_one_or_none()
    if wh is None:
        raise BusinessError(ERR_NOT_FOUND, "Webhook 不存在")

    await db.delete(wh)
    await db.commit()
    return {"id": wh.id}


async def list_deliveries(db: AsyncSession, webhook_id: int, limit: int = 20) -> list[dict]:
    stmt = (
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.delivered_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [_delivery_to_dict(d) for d in rows]


async def fire_event(db: AsyncSession, team_id: int, event: str, payload: dict) -> None:
    stmt = select(Webhook).where(
        Webhook.team_id == team_id,
        Webhook.is_active == True,
    )
    result = await db.execute(stmt)
    webhooks = result.scalars().all()

    for wh in webhooks:
        subscribed = wh.events if wh.events else VALID_EVENTS
        if event in subscribed:
            try:
                await _deliver(db, wh, event, payload)
            except Exception:
                logger.exception("Failed to deliver webhook %s", wh.id)


async def _deliver(db: AsyncSession, webhook: Webhook, event: str, payload: dict) -> None:
    body = json.dumps({"event": event, "payload": payload})
    headers = {"Content-Type": "application/json"}
    if webhook.secret:
        sig = hmac.new(
            webhook.secret.encode(), body.encode(), hashlib.sha256
        ).hexdigest()
        headers["X-Webhook-Signature"] = f"sha256={sig}"

    status_code = None
    error = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook.url, content=body, headers=headers)
            status_code = resp.status_code
    except Exception as exc:
        error = str(exc)

    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event=event,
        payload=payload,
        status_code=status_code,
        error=error,
    )
    db.add(delivery)
    await db.commit()


def _webhook_to_dict(wh: Webhook) -> dict:
    return {
        "id": wh.id,
        "team_id": wh.team_id,
        "url": wh.url,
        "secret": "***" if wh.secret else None,
        "events": wh.events,
        "is_active": wh.is_active,
        "created_by": wh.created_by,
        "created_at": wh.created_at.isoformat() if wh.created_at else None,
        "updated_at": wh.updated_at.isoformat() if wh.updated_at else None,
    }


def _delivery_to_dict(d: WebhookDelivery) -> dict:
    return {
        "id": d.id,
        "webhook_id": d.webhook_id,
        "event": d.event,
        "payload": d.payload,
        "status_code": d.status_code,
        "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
        "error": d.error,
    }
