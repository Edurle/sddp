# Plan 2: Webhook Notifications

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Add configurable webhooks that POST to external URLs on review events, with delivery history and CLI management.

**Spec section:** "2. Webhook Notifications" in `docs/superpowers/specs/2026-05-16-agent-collaboration-design.md`

**Depends on:** Plan 1 (review comments) must be complete.

---

### Task 2.1: Create Webhook + WebhookDelivery Models

**Files:**
- Create: `backend/app/models/webhook.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create the model file**

```python
# backend/app/models/webhook.py
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Webhook(Base):
    __tablename__ = "webhooks"
    __table_args__ = (
        Index("idx_webhook_team", "team_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    team_id: Mapped[int] = mapped_column(nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[str | None] = mapped_column(Text, default=None)
    events: Mapped[dict | None] = mapped_column(JSONB, default=None)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=lambda: datetime.now(timezone.utc)
    )


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"
    __table_args__ = (
        Index("idx_wd_webhook", "webhook_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    webhook_id: Mapped[int] = mapped_column(nullable=False)
    event: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSONB, default=None)
    status_code: Mapped[int | None] = mapped_column(default=None)
    delivered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    error: Mapped[str | None] = mapped_column(Text, default=None)
```

- [ ] **Step 2: Register in models/__init__.py**

Add to `backend/app/models/__init__.py`:

```python
from app.models.webhook import Webhook, WebhookDelivery
```

Add `"Webhook"` and `"WebhookDelivery"` to `__all__`.

- [ ] **Step 3: Verify import**

Run: `conda run -n sdd python -c "from app.models import Webhook, WebhookDelivery; print('OK')"`
Expected: `OK`

---

### Task 2.2: Create Alembic Migration

**Files:**
- Create: `backend/alembic/versions/xxxx_add_webhooks.py`

- [ ] **Step 1: Generate migration**

Run: `conda run -n sdd python -m alembic -c backend/alembic.ini revision --autogenerate -m "add webhooks tables"`

If autogenerate doesn't pick it up, write manually. The migration `down_revision` should point to the review_comments migration from Plan 1.

```python
def upgrade() -> None:
    op.create_table(
        'webhooks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('team_id', sa.Integer(), nullable=False),
        sa.Column('url', sa.Text(), nullable=False),
        sa.Column('secret', sa.Text(), nullable=True),
        sa.Column('events', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_webhook_team', 'webhooks', ['team_id'])

    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('webhook_id', sa.Integer(), nullable=False),
        sa.Column('event', sa.String(length=50), nullable=False),
        sa.Column('payload', sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('error', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_wd_webhook', 'webhook_deliveries', ['webhook_id'])


def downgrade() -> None:
    op.drop_index('idx_wd_webhook', table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')
    op.drop_index('idx_webhook_team', table_name='webhooks')
    op.drop_table('webhooks')
```

- [ ] **Step 2: Run migration**

Run: `conda run -n sdd python -m alembic -c backend/alembic.ini upgrade head`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add backend/app/models/webhook.py backend/app/models/__init__.py backend/alembic/versions/
git commit -m "feat: add Webhook and WebhookDelivery models and migration"
```

---

### Task 2.3: Webhook Service

**Files:**
- Create: `backend/app/services/webhook.py`

- [ ] **Step 1: Create service with CRUD + delivery logic**

```python
# backend/app/services/webhook.py
import hashlib
import hmac
import json
import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Webhook, WebhookDelivery

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
    if events is None:
        events = VALID_EVENTS[:]
    wh = Webhook(
        team_id=team_id,
        url=url,
        secret=secret,
        events=events,
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
    return [_webhook_to_dict(w) for w in result.scalars().all()]


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
        from app.exceptions import BusinessError, ERR_NOT_FOUND
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
        from app.exceptions import BusinessError, ERR_NOT_FOUND
        raise BusinessError(ERR_NOT_FOUND, "Webhook 不存在")
    await db.delete(wh)
    await db.commit()
    return {"id": webhook_id}


async def list_deliveries(db: AsyncSession, webhook_id: int, limit: int = 20) -> list[dict]:
    stmt = (
        select(WebhookDelivery)
        .where(WebhookDelivery.webhook_id == webhook_id)
        .order_by(WebhookDelivery.delivered_at.desc())
        .limit(limit)
    )
    result = await db.execute(stmt)
    return [_delivery_to_dict(d) for d in result.scalars().all()]


async def fire_event(
    db: AsyncSession,
    team_id: int,
    event: str,
    payload: dict,
) -> None:
    stmt = select(Webhook).where(
        Webhook.team_id == team_id,
        Webhook.is_active == True,
    )
    result = await db.execute(stmt)
    webhooks = result.scalars().all()

    for wh in webhooks:
        subscribed = wh.events or []
        if event not in subscribed:
            continue
        await _deliver(db, wh, event, payload)


async def _deliver(
    db: AsyncSession,
    webhook: Webhook,
    event: str,
    payload: dict,
) -> None:
    body = json.dumps({"event": event, "timestamp": datetime.now(timezone.utc).isoformat(), "data": payload}, ensure_ascii=False)
    headers = {"Content-Type": "application/json"}
    if webhook.secret:
        sig = hmac.new(webhook.secret.encode(), body.encode(), hashlib.sha256).hexdigest()
        headers["X-SDD-Signature"] = f"sha256={sig}"

    delivery = WebhookDelivery(
        webhook_id=webhook.id,
        event=event,
        payload={"event": event, "data": payload},
    )

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(webhook.url, content=body, headers=headers)
            delivery.status_code = resp.status_code
    except Exception as e:
        delivery.status_code = 0
        delivery.error = str(e)[:500]

    db.add(delivery)
    await db.commit()


def _webhook_to_dict(wh: Webhook) -> dict:
    return {
        "id": wh.id,
        "team_id": wh.team_id,
        "url": wh.url,
        "secret": "***" if wh.secret else None,
        "events": wh.events or [],
        "is_active": wh.is_active,
        "created_by": wh.created_by,
        "created_at": wh.created_at.isoformat() if wh.created_at else None,
    }


def _delivery_to_dict(d: WebhookDelivery) -> dict:
    return {
        "id": d.id,
        "webhook_id": d.webhook_id,
        "event": d.event,
        "status_code": d.status_code,
        "error": d.error,
        "delivered_at": d.delivered_at.isoformat() if d.delivered_at else None,
    }
```

- [ ] **Step 2: Verify import**

Run: `conda run -n sdd python -c "from app.services.webhook import fire_event; print('OK')"`
Expected: `OK`

---

### Task 2.4: Webhook API Routes

**Files:**
- Create: `backend/app/api/webhooks.py`
- Modify: `backend/app/api/router.py`

- [ ] **Step 1: Create webhook API routes**

```python
# backend/app/api/webhooks.py
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db_session, require_permission
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
    user: Annotated[dict, Depends(require_permission("member:invite"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
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
    user: Annotated[dict, Depends(require_permission("member:invite"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await wh_svc.update_webhook(
        db, webhook_id,
        url=body.url, events=body.events, secret=body.secret, is_active=body.is_active,
    )
    return {"code": 0, "message": "success", "data": data}


@teams_nested_router.delete("/{teamId}/webhooks/{webhook_id}")
async def delete_webhook(
    teamId: int,
    webhook_id: int,
    user: Annotated[dict, Depends(require_permission("member:invite"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
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
```

- [ ] **Step 2: Register routes in router.py**

In `backend/app/api/router.py`:

Add import:
```python
from app.api import webhooks
```

Add route (after the teams router line):
```python
router.include_router(webhooks.teams_nested_router, prefix="/teams", tags=["webhooks"])
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/webhooks.py backend/app/api/router.py backend/app/services/webhook.py
git commit -m "feat: add webhook CRUD API routes"
```

---

### Task 2.5: Fire Webhook Events from Review Actions

**Files:**
- Modify: `backend/app/services/requirement.py`

- [ ] **Step 1: Add webhook firing to review_requirement**

In `backend/app/services/requirement.py`, in the `review_requirement` function, after the `await db.commit()` line (the final commit), add webhook event firing.

Add import at top:
```python
from app.services import webhook as wh_svc
```

Add a helper function:

```python
async def _fire_review_event(db: AsyncSession, req: Requirement, event: str, user_id: int, comment: str | None = None):
    iteration = await _get_iteration(db, req.iteration_id)
    if iteration is None:
        return
    project = await _get_project(db, iteration.project_id)
    if project is None:
        return
    await wh_svc.fire_event(
        db, project.team_id, event,
        {
            "requirement_id": req.id,
            "requirement_title": req.title,
            "reviewer_id": user_id,
            "comment": comment,
        },
    )
```

In `review_requirement`, after `await db.commit()` (the final line before `return`), add:

```python
    if action == "approve":
        await _fire_review_event(db, req, "review.approved", user_id, comment)
    elif action == "reject":
        await _fire_review_event(db, req, "review.rejected", user_id, comment)
```

- [ ] **Step 2: Add webhook firing to submit_review**

In the `submit_review` function, after `await db.commit()`, add:

```python
    await _fire_review_event(db, req, "review.submitted", user_id)
```

- [ ] **Step 3: Verify import**

Run: `conda run -n sdd python -c "from app.services.requirement import review_requirement; print('OK')"`
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add backend/app/services/requirement.py
git commit -m "feat: fire webhook events on review submit/approve/reject"
```

---

### Task 2.5b: Fire Webhook Events for Task Events

**Files:**
- Modify: `backend/app/services/task.py`

- [ ] **Step 1: Add webhook firing to task creation and completion**

In `backend/app/services/task.py`, add import at top:

```python
from app.services import webhook as wh_svc
```

Find the task creation function (likely `create_task`). After the commit, resolve the requirement to get the team_id and fire `task.assigned`:

```python
    from app.models import Requirement as ReqModel, Iteration as IterModel, Project as ProjModel
    req_stmt = select(ReqModel).where(ReqModel.id == task.requirement_id)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req:
        iter_stmt = select(IterModel).where(IterModel.id == req.iteration_id)
        iter_result = await db.execute(iter_stmt)
        iteration = iter_result.scalar_one_or_none()
        if iteration:
            proj_stmt = select(ProjModel).where(ProjModel.id == iteration.project_id)
            proj_result = await db.execute(proj_stmt)
            project = proj_result.scalar_one_or_none()
            if project and task.assignee_id:
                await wh_svc.fire_event(db, project.team_id, "task.assigned", {
                    "task_id": task.id,
                    "task_title": task.title,
                    "assignee_id": task.assignee_id,
                    "requirement_id": req.id,
                })
```

Find the task completion/update function. When a task status changes to `completed`, fire `task.completed` with the same pattern:

```python
                await wh_svc.fire_event(db, project.team_id, "task.completed", {
                    "task_id": task.id,
                    "task_title": task.title,
                    "assignee_id": task.assignee_id,
                    "requirement_id": req.id,
                })
```

- [ ] **Step 2: Verify import**

Run: `conda run -n sdd python -c "from app.services.task import create_task; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/task.py
git commit -m "feat: fire webhook events on task assign and complete"
```

---

### Task 2.6: Webhook Tests

**Files:**
- Create: `backend/tests/test_webhooks.py`
- Modify: `backend/tests/conftest.py`

- [ ] **Step 1: Update conftest TRUNCATE**

Add `webhook_deliveries, webhooks,` before `review_comments` in the `_TRUNCATE_SQL`.

- [ ] **Step 2: Write tests**

Create `backend/tests/test_webhooks.py`:

```python
import pytest
from tests.conftest import auth_headers


class TestWebhookCRUD:
    @pytest.mark.asyncio
    async def test_create_webhook(self, client, normal_user, owner_role):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id, permissions=["member:invite"])
        resp = await client.post(
            f"/api/v1/teams/{team.id}/webhooks",
            json={"url": "https://example.com/hook", "events": ["review.submitted"]},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["url"] == "https://example.com/hook"
        assert body["data"]["is_active"] is True

    @pytest.mark.asyncio
    async def test_list_webhooks(self, client, normal_user, owner_role):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id, permissions=["member:invite"])
        await client.post(
            f"/api/v1/teams/{team.id}/webhooks",
            json={"url": "https://example.com/hook1"},
            headers=headers,
        )
        resp = await client.get(
            f"/api/v1/teams/{team.id}/webhooks",
            headers=auth_headers(normal_user.id),
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert len(body["data"]) >= 1

    @pytest.mark.asyncio
    async def test_update_webhook(self, client, normal_user, owner_role):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id, permissions=["member:invite"])
        create_resp = await client.post(
            f"/api/v1/teams/{team.id}/webhooks",
            json={"url": "https://example.com/hook"},
            headers=headers,
        )
        wh_id = create_resp.json()["data"]["id"]
        resp = await client.put(
            f"/api/v1/teams/{team.id}/webhooks/{wh_id}",
            json={"url": "https://example.com/hook2", "is_active": False},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["url"] == "https://example.com/hook2"
        assert resp.json()["data"]["is_active"] is False

    @pytest.mark.asyncio
    async def test_delete_webhook(self, client, normal_user, owner_role):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id, permissions=["member:invite"])
        create_resp = await client.post(
            f"/api/v1/teams/{team.id}/webhooks",
            json={"url": "https://example.com/hook"},
            headers=headers,
        )
        wh_id = create_resp.json()["data"]["id"]
        resp = await client.delete(
            f"/api/v1/teams/{team.id}/webhooks/{wh_id}",
            headers=headers,
        )
        assert resp.status_code == 200

        list_resp = await client.get(
            f"/api/v1/teams/{team.id}/webhooks",
            headers=auth_headers(normal_user.id),
        )
        assert all(w["id"] != wh_id for w in list_resp.json()["data"])


class TestWebhookDelivery:
    @pytest.mark.asyncio
    async def test_deliveries_list_empty(self, client, normal_user, owner_role):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id, permissions=["member:invite"])
        create_resp = await client.post(
            f"/api/v1/teams/{team.id}/webhooks",
            json={"url": "https://example.com/hook"},
            headers=headers,
        )
        wh_id = create_resp.json()["data"]["id"]
        resp = await client.get(
            f"/api/v1/teams/{team.id}/webhooks/{wh_id}/deliveries",
            headers=auth_headers(normal_user.id),
        )
        assert resp.status_code == 200
        assert resp.json()["data"] == []
```

- [ ] **Step 3: Run webhook tests**

Run: `conda run -n sdd python -m pytest backend/tests/test_webhooks.py -v`
Expected: All tests pass

- [ ] **Step 4: Run full suite**

Run: `conda run -n sdd python -m pytest backend/tests/ -v --timeout=60`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add backend/tests/test_webhooks.py backend/tests/conftest.py
git commit -m "feat: add webhook tests"
```

---

### Task 2.7: CLI Webhook Commands

**Files:**
- Create: `cli/sdd_cli/webhooks.py`
- Modify: `cli/sdd_cli/main.py`

- [ ] **Step 1: Create CLI module**

```python
# cli/sdd_cli/webhooks.py
from __future__ import annotations

from typing import Optional

import typer

from sdd_cli.client import APIError, get_client
from sdd_cli.output import print_response

app = typer.Typer(help="Webhook management")


@app.command("list")
def list_webhooks(
    team_id: int = typer.Option(..., "--team-id", "-t"),
) -> None:
    try:
        client = get_client()
        data = client.get(f"/teams/{team_id}/webhooks")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("create")
def create_webhook(
    team_id: int = typer.Option(..., "--team-id", "-t"),
    url: str = typer.Option(..., "--url", "-u"),
    events: Optional[str] = typer.Option(None, "--events", "-e"),
    secret: Optional[str] = typer.Option(None, "--secret", "-s"),
) -> None:
    try:
        client = get_client()
        payload: dict = {"url": url}
        if events:
            payload["events"] = [e.strip() for e in events.split(",")]
        if secret:
            payload["secret"] = secret
        data = client.post(f"/teams/{team_id}/webhooks", json=payload)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("update")
def update_webhook(
    team_id: int = typer.Option(..., "--team-id", "-t"),
    webhook_id: int = typer.Option(..., "--id"),
    url: Optional[str] = typer.Option(None, "--url", "-u"),
    events: Optional[str] = typer.Option(None, "--events", "-e"),
    is_active: Optional[bool] = typer.Option(None, "--is-active"),
) -> None:
    try:
        client = get_client()
        payload: dict = {}
        if url:
            payload["url"] = url
        if events:
            payload["events"] = [e.strip() for e in events.split(",")]
        if is_active is not None:
            payload["is_active"] = is_active
        data = client.put(f"/teams/{team_id}/webhooks/{webhook_id}", json=payload)
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("delete")
def delete_webhook(
    team_id: int = typer.Option(..., "--team-id", "-t"),
    webhook_id: int = typer.Option(..., "--id"),
) -> None:
    try:
        client = get_client()
        data = client.delete(f"/teams/{team_id}/webhooks/{webhook_id}")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


@app.command("deliveries")
def list_deliveries(
    team_id: int = typer.Option(..., "--team-id", "-t"),
    webhook_id: int = typer.Option(..., "--id"),
) -> None:
    try:
        client = get_client()
        data = client.get(f"/teams/{team_id}/webhooks/{webhook_id}/deliveries")
        print_response(data)
    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)
```

- [ ] **Step 2: Register in main.py**

In `cli/sdd_cli/main.py`:

Add import:
```python
from sdd_cli import webhooks
```

Add:
```python
app.add_typer(webhooks.app, name="webhooks")
```

- [ ] **Step 3: Verify CLI loads**

Run: `conda run -n sdd python -m sdd_cli webhooks --help`
Expected: Help text showing list, create, update, delete, deliveries commands

- [ ] **Step 4: Commit**

```bash
git add cli/sdd_cli/webhooks.py cli/sdd_cli/main.py
git commit -m "feat: add webhook CLI commands"
```
