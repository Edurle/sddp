# Plan 3: Agent Work Discovery

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Add a `GET /me/work` API and `sdd my-work` CLI command that returns a role-aware work queue for agents.

**Spec section:** "3. Agent Work Discovery" in `docs/superpowers/specs/2026-05-16-agent-collaboration-design.md`

**Depends on:** Nothing (fully independent).

---

### Task 3.1: Add `get_user_work()` Service Function

**Files:**
- Modify: `backend/app/services/user.py`

- [ ] **Step 1: Add the `get_user_work` function**

Add at the end of `backend/app/services/user.py`:

```python
async def get_user_work(db: AsyncSession, user_id: int) -> dict:
    pending_reviews = await _get_pending_reviews(db, user_id)

    from app.services.task import list_tasks_by_assignee
    assigned_result = await list_tasks_by_assignee(db, user_id)
    assigned_tasks = assigned_result["items"]

    teams = await _get_user_teams_detailed(db, user_id)
    team_ids = [t["id"] for t in teams]
    projects = await _get_user_projects(db, team_ids)
    project_ids = [p["id"] for p in projects]

    draftable_items = await _get_draftable_items(db, user_id, teams, project_ids)

    return {
        "pending_reviews": pending_reviews,
        "assigned_tasks": assigned_tasks,
        "draftable_items": draftable_items,
        "summary": {
            "reviews_waiting": len(pending_reviews),
            "tasks_in_progress": len([t for t in assigned_tasks if t.get("status") not in ("completed",)]),
            "items_to_draft": len(draftable_items),
        },
    }


async def _get_draftable_items(
    db: AsyncSession, user_id: int, teams: list[dict], project_ids: list[int],
) -> list[dict]:
    if not project_ids:
        return []

    from app.models import Iteration as IterModel, Requirement as ReqModel

    role_map = {}
    for t in teams:
        role_map[t["id"]] = t.get("role", "member").lower()

    iter_stmt = select(IterModel).where(IterModel.project_id.in_(project_ids))
    iter_result = await db.execute(iter_stmt)
    iterations = iter_result.scalars().all()
    if not iterations:
        return []

    iter_ids = [i.id for i in iterations]
    iter_project_map = {i.id: i.project_id for i in iterations}

    existing_projects = await _get_user_projects(db, list(set(t["id"] for t in teams)))
    project_team_map = {p["id"]: p["team_id"] for p in existing_projects}

    status_role_map = {
        "drafting_req": ["product_manager", "pm", "所有者"],
        "drafting_spec": ["developer", "开发", "所有者"],
        "drafting_tests": ["tester", "qa", "测试", "所有者"],
    }

    req_stmt = select(ReqModel).where(
        ReqModel.iteration_id.in_(iter_ids),
        ReqModel.is_deleted == False,
    )
    req_result = await db.execute(req_stmt)
    requirements = req_result.scalars().all()

    next_action_map = {
        "drafting_req": "write_requirement",
        "drafting_spec": "write_spec",
        "drafting_tests": "write_tests",
    }

    items = []
    for req in requirements:
        iter_obj = next((i for i in iterations if i.id == req.iteration_id), None)
        if iter_obj is None:
            continue

        team_id = project_team_map.get(iter_obj.project_id)
        if team_id is None:
            continue

        user_role = role_map.get(team_id, "")
        matching_roles = status_role_map.get(req.status, [])
        if not matching_roles:
            continue

        if user_role not in [r.lower() for r in matching_roles]:
            continue

        items.append({
            "id": req.id,
            "title": req.title,
            "status": req.status,
            "my_role": user_role,
            "next_action": next_action_map.get(req.status, "unknown"),
        })

    return items
```

- [ ] **Step 2: Verify import**

Run: `conda run -n sdd python -c "from app.services.user import get_user_work; print('OK')"`
Expected: `OK`

---

### Task 3.2: Add `GET /me/work` API Endpoint

**Files:**
- Modify: `backend/app/api/users.py`

- [ ] **Step 1: Add the endpoint**

In `backend/app/api/users.py`, add after the `get_projects_tree` endpoint (after line 118):

```python
@router.get("/me/work")
async def get_my_work(
    user: Annotated[dict, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    user_id = int(user["sub"])
    data = await user_service.get_user_work(db, user_id)
    return {"code": 0, "message": "success", "data": data}
```

**Important:** This must be placed BEFORE the `/{id}` catch-all route if one exists. In this file there is no such route, so placement after `get_projects_tree` is safe.

- [ ] **Step 2: Commit**

```bash
git add backend/app/services/user.py backend/app/api/users.py
git commit -m "feat: add GET /me/work API for agent work discovery"
```

---

### Task 3.3: Tests for Agent Work Discovery

**Files:**
- Create: `backend/tests/test_agent_work.py`

- [ ] **Step 1: Write tests**

```python
import pytest
from tests.conftest import auth_headers


class TestAgentWork:
    @pytest.mark.asyncio
    async def test_empty_work(self, client, normal_user, owner_role):
        headers = auth_headers(normal_user.id)
        resp = await client.get("/api/v1/users/me/work", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert "pending_reviews" in data
        assert "assigned_tasks" in data
        assert "draftable_items" in data
        assert "summary" in data
        assert data["summary"]["reviews_waiting"] == 0
        assert data["summary"]["tasks_in_progress"] == 0
        assert data["summary"]["items_to_draft"] == 0

    @pytest.mark.asyncio
    async def test_shows_pending_review(
        self, client, normal_user, another_user, sample_requirement, owner_role
    ):
        headers = auth_headers(normal_user.id, permissions=["requirement:review_req"])
        await client.post(
            f"/api/v1/requirements/{sample_requirement.id}/submit-review",
            json={"reviewer_id": another_user.id},
            headers=headers,
        )

        reviewer_headers = auth_headers(another_user.id)
        resp = await client.get("/api/v1/users/me/work", headers=reviewer_headers)
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["summary"]["reviews_waiting"] >= 1

    @pytest.mark.asyncio
    async def test_shows_assigned_task(
        self, client, normal_user, approved_requirement, owner_role
    ):
        headers = auth_headers(normal_user.id, permissions=["task:create"])
        await client.post(
            f"/api/v1/requirements/{approved_requirement.id}/tasks",
            json={"title": "Test task", "assignee_id": normal_user.id},
            headers=headers,
        )

        resp = await client.get("/api/v1/users/me/work", headers=auth_headers(normal_user.id))
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["summary"]["tasks_in_progress"] >= 1
```

- [ ] **Step 2: Run tests**

Run: `conda run -n sdd python -m pytest backend/tests/test_agent_work.py -v`
Expected: All 3 tests pass

- [ ] **Step 3: Run full suite**

Run: `conda run -n sdd python -m pytest backend/tests/ -v --timeout=60`
Expected: All tests pass

- [ ] **Step 4: Commit**

```bash
git add backend/tests/test_agent_work.py
git commit -m "feat: add tests for agent work discovery"
```

---

### Task 3.4: CLI `sdd my-work` Command

**Files:**
- Modify: `cli/sdd_cli/me.py`

- [ ] **Step 1: Add the my-work command**

In `cli/sdd_cli/me.py`, add after the `pending_reviews` command:

```python
@app.command(name="my-work")
def my_work(
    work_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter: reviews, tasks, drafts"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    try:
        client = get_client()
        data = client.get("/users/me/work")

        if json_output:
            print_response(data)
            return

        if work_type == "reviews":
            _print_reviews(data.get("pending_reviews", []))
        elif work_type == "tasks":
            _print_tasks(data.get("assigned_tasks", []))
        elif work_type == "drafts":
            _print_drafts(data.get("draftable_items", []))
        else:
            _print_reviews(data.get("pending_reviews", []))
            _print_tasks(data.get("assigned_tasks", []))
            _print_drafts(data.get("draftable_items", []))
            summary = data.get("summary", {})
            typer.echo(f"\n摘要: {summary.get('reviews_waiting', 0)}个审核 | {summary.get('tasks_in_progress', 0)}个任务 | {summary.get('items_to_draft', 0)}个待起草")

    except APIError as e:
        typer.echo(f"Error: {e.message}", err=True)
        raise typer.Exit(code=1)


def _print_reviews(items: list) -> None:
    if not items:
        return
    typer.echo(typer.style("\n📋 待审核", fg=typer.colors.CYAN, bold=True))
    for item in items:
        typer.echo(f"  #{item.get('requirement_id')} {item.get('requirement_title', '')} [{item.get('review_type', '')}]")


def _print_tasks(items: list) -> None:
    if not items:
        return
    typer.echo(typer.style("\n🔨 我的任务", fg=typer.colors.CYAN, bold=True))
    for item in items:
        status = item.get("status", "")
        req_title = item.get("requirement_title", "")
        typer.echo(f"  #{item.get('id')} {item.get('title', '')} [{status}]" + (f" → {req_title}" if req_title else ""))


def _print_drafts(items: list) -> None:
    if not items:
        return
    typer.echo(typer.style("\n✏️ 待起草", fg=typer.colors.CYAN, bold=True))
    for item in items:
        typer.echo(f"  #{item.get('id')} {item.get('title', '')} [{item.get('status', '')}] → {item.get('next_action', '')}")
```

- [ ] **Step 2: Verify CLI loads**

Run: `conda run -n sdd python -m sdd_cli me my-work --help`
Expected: Help text showing --type and --json options

- [ ] **Step 3: Commit**

```bash
git add cli/sdd_cli/me.py
git commit -m "feat: add 'sdd my-work' CLI command for agent work discovery"
```
