import pytest
from sqlalchemy import select

from app.models import (
    Team, TeamMember, Project, Iteration, Requirement,
    RequirementReview, Task, TestCase,
)
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_tc_agent_018_full_pending_overview(
    client, db, normal_user, another_user, owner_role, sample_project,
    sample_iteration, approved_requirement,
):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])

    task = Task(
        requirement_id=approved_requirement.id,
        title="Agent task",
        status="coding",
        assignee_id=normal_user.id,
        created_by=normal_user.id,
    )
    db.add(task)

    review = RequirementReview(
        requirement_id=approved_requirement.id,
        review_type="requirement",
        reviewer_id=normal_user.id,
        status="pending",
    )
    db.add(review)
    await db.commit()

    resp = await client.get("/api/v1/users/me/pending", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0

    data = body["data"]
    assert len(data["teams"]) >= 1
    assert data["teams"][0]["id"] == owner_role["team"].id
    assert len(data["projects"]) >= 1
    assert data["projects"][0]["id"] == sample_project.id
    assert len(data["active_iterations"]) >= 1
    assert len(data["assigned_tasks"]) >= 1
    assert data["assigned_tasks"][0]["title"] == "Agent task"
    assert data["assigned_tasks"][0]["requirement_title"] == approved_requirement.title
    assert len(data["pending_reviews"]) >= 1


@pytest.mark.asyncio
async def test_tc_agent_019_empty_pending_for_new_user(client, db, another_user):
    headers = auth_headers(another_user.id)

    resp = await client.get("/api/v1/users/me/pending", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["teams"] == []
    assert data["projects"] == []
    assert data["active_iterations"] == []
    assert data["assigned_tasks"] == []
    assert data["pending_reviews"] == []


@pytest.mark.asyncio
async def test_tc_agent_020_unauthorized_access(client):
    resp = await client.get("/api/v1/users/me/pending")
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40100


@pytest.mark.asyncio
async def test_tc_agent_021_list_my_tasks_with_requirement_title(
    client, db, normal_user, approved_requirement,
):
    headers = auth_headers(normal_user.id)

    task = Task(
        requirement_id=approved_requirement.id,
        title="My task",
        status="coding",
        assignee_id=normal_user.id,
        created_by=normal_user.id,
    )
    db.add(task)
    await db.commit()

    resp = await client.get("/api/v1/users/me/tasks", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    items = body["data"]["items"]
    assert len(items) >= 1
    found = [t for t in items if t["id"] == task.id]
    assert len(found) == 1
    assert found[0]["requirement_title"] == approved_requirement.title


@pytest.mark.asyncio
async def test_tc_agent_022_filter_tasks_by_status(
    client, db, normal_user, approved_requirement,
):
    headers = auth_headers(normal_user.id)

    t1 = Task(
        requirement_id=approved_requirement.id,
        title="Pending task",
        status="pending",
        assignee_id=normal_user.id,
        created_by=normal_user.id,
    )
    t2 = Task(
        requirement_id=approved_requirement.id,
        title="Coding task",
        status="coding",
        assignee_id=normal_user.id,
        created_by=normal_user.id,
    )
    db.add_all([t1, t2])
    await db.commit()

    resp = await client.get("/api/v1/users/me/tasks?status=coding", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    items = body["data"]["items"]
    assert all(t["status"] == "coding" for t in items)
    assert len(items) >= 1


@pytest.mark.asyncio
async def test_tc_agent_023_no_tasks_empty_array(client, db, another_user):
    headers = auth_headers(another_user.id)

    resp = await client.get("/api/v1/users/me/tasks", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["items"] == []


@pytest.mark.asyncio
async def test_tc_agent_024_pending_reviews_returned(
    client, db, normal_user, another_user, approved_requirement,
):
    headers = auth_headers(normal_user.id)

    review = RequirementReview(
        requirement_id=approved_requirement.id,
        review_type="specification",
        reviewer_id=normal_user.id,
        status="pending",
    )
    db.add(review)
    await db.commit()

    resp = await client.get("/api/v1/users/me/pending-reviews", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    items = body["data"]
    assert len(items) >= 1
    found = [r for r in items if r["review_id"] == review.id]
    assert len(found) == 1
    assert found[0]["requirement_id"] == approved_requirement.id
    assert found[0]["requirement_title"] == approved_requirement.title
    assert found[0]["review_type"] == "specification"
    assert found[0]["status"] == "pending"


@pytest.mark.asyncio
async def test_tc_agent_025_processed_reviews_excluded(
    client, db, normal_user, approved_requirement,
):
    headers = auth_headers(normal_user.id)

    from datetime import datetime, timezone
    review = RequirementReview(
        requirement_id=approved_requirement.id,
        review_type="requirement",
        reviewer_id=normal_user.id,
        status="approved",
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(review)
    await db.commit()

    resp = await client.get("/api/v1/users/me/pending-reviews", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    items = body["data"]
    found = [r for r in items if r["review_id"] == review.id]
    assert len(found) == 0


@pytest.mark.asyncio
async def test_tc_agent_026_global_requirements_filter_by_status(
    client, db, normal_user, owner_role, sample_iteration, approved_requirement,
):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])

    draft_req = Requirement(
        iteration_id=sample_iteration.id,
        title="Draft req",
        req_type="feature",
        priority=1,
        status="drafting_req",
        created_by=normal_user.id,
    )
    db.add(draft_req)
    await db.commit()

    resp = await client.get("/api/v1/requirements?status=approved", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    items = body["data"]["items"]
    assert all(r["status"] == "approved" for r in items)
    assert len(items) >= 1


@pytest.mark.asyncio
async def test_tc_agent_027_filter_by_iteration_id(
    client, db, normal_user, owner_role, sample_iteration, approved_requirement,
):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])

    resp = await client.get(
        f"/api/v1/requirements?iteration_id={sample_iteration.id}", headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    items = body["data"]["items"]
    assert len(items) >= 1
    assert all(r["iteration_id"] == sample_iteration.id for r in items)


@pytest.mark.asyncio
async def test_tc_agent_028_no_filter_returns_all(
    client, db, normal_user, owner_role, sample_iteration, approved_requirement,
):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])

    another_req = Requirement(
        iteration_id=sample_iteration.id,
        title="Another req",
        req_type="bug",
        priority=2,
        status="drafting_req",
        created_by=normal_user.id,
    )
    db.add(another_req)
    await db.commit()

    resp = await client.get("/api/v1/requirements", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    items = body["data"]["items"]
    assert len(items) >= 2


@pytest.mark.asyncio
async def test_tc_agent_029_full_context_with_all_data(
    client, db, normal_user, owner_role, approved_requirement,
):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])

    task = Task(
        requirement_id=approved_requirement.id,
        title="Context task",
        status="pending",
        created_by=normal_user.id,
    )
    db.add(task)

    tc = TestCase(
        requirement_id=approved_requirement.id,
        case_number=f"TC-{approved_requirement.id}-CTX",
        title="Context test case",
        case_type="happy_path",
        steps="do something",
        expected_result="works",
    )
    db.add(tc)
    await db.commit()

    resp = await client.get(
        f"/api/v1/requirements/{approved_requirement.id}/full-context", headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]

    assert data["requirement"]["id"] == approved_requirement.id
    assert data["requirement"]["title"] == approved_requirement.title
    assert len(data["tasks"]) >= 1
    assert len(data["test_cases"]) >= 1


@pytest.mark.asyncio
async def test_tc_agent_030_full_context_without_spec(
    client, db, normal_user, owner_role, approved_requirement,
):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])

    resp = await client.get(
        f"/api/v1/requirements/{approved_requirement.id}/full-context", headers=headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["spec"] is None or data["spec"]["content"] is None


@pytest.mark.asyncio
async def test_tc_agent_031_requirement_not_found(client, db, normal_user):
    headers = auth_headers(normal_user.id)

    resp = await client.get("/api/v1/requirements/99999/full-context", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40400
