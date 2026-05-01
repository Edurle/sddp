import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_iteration_requirements_pagination_offset_limit(
    client, db, sample_iteration, normal_user
):
    from app.models import Requirement

    for i in range(7):
        req = Requirement(
            iteration_id=sample_iteration.id,
            title=f"需求-{i}",
            req_type="feature",
            priority=1,
            status="drafting_req",
            created_by=normal_user.id,
        )
        db.add(req)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/iterations/{sample_iteration.id}/requirements",
        params={"offset": 2, "limit": 3},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert "items" in data
    assert "total" in data
    assert "offset" in data
    assert "limit" in data
    assert "has_more" in data
    assert data["offset"] == 2
    assert data["limit"] == 3
    assert data["total"] == 7
    assert len(data["items"]) == 3
    assert data["has_more"] is True


@pytest.mark.asyncio
async def test_iteration_requirements_has_more_false(
    client, db, sample_iteration, normal_user
):
    from app.models import Requirement

    for i in range(3):
        req = Requirement(
            iteration_id=sample_iteration.id,
            title=f"需求-{i}",
            req_type="feature",
            priority=1,
            status="drafting_req",
            created_by=normal_user.id,
        )
        db.add(req)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/iterations/{sample_iteration.id}/requirements",
        params={"offset": 0, "limit": 10},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["total"] == 3
    assert data["has_more"] is False
    assert len(data["items"]) == 3


@pytest.mark.asyncio
async def test_iteration_requirements_default_values(
    client, db, sample_iteration, normal_user
):
    from app.models import Requirement

    req = Requirement(
        iteration_id=sample_iteration.id,
        title="唯一需求",
        req_type="feature",
        priority=1,
        status="drafting_req",
        created_by=normal_user.id,
    )
    db.add(req)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/iterations/{sample_iteration.id}/requirements",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["offset"] == 0
    assert data["limit"] == 50
    assert data["total"] == 1
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_tasks_pagination_offset_limit(
    client, db, approved_requirement, normal_user
):
    from app.models import Task

    for i in range(6):
        task = Task(
            requirement_id=approved_requirement.id,
            title=f"任务-{i}",
            status="pending",
            created_by=normal_user.id,
        )
        db.add(task)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/requirements/{approved_requirement.id}/tasks",
        params={"offset": 1, "limit": 2},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert "items" in data
    assert data["total"] == 6
    assert data["offset"] == 1
    assert data["limit"] == 2
    assert len(data["items"]) == 2
    assert data["has_more"] is True


@pytest.mark.asyncio
async def test_test_cases_pagination(
    client, db, approved_requirement, normal_user
):
    from app.models import TestCase

    for i in range(5):
        tc = TestCase(
            requirement_id=approved_requirement.id,
            case_number=f"TC-{approved_requirement.id}-{i}",
            title=f"用例-{i}",
            case_type="api",
            steps="步骤",
            expected_result="结果",
        )
        db.add(tc)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/requirements/{approved_requirement.id}/test-cases",
        params={"offset": 0, "limit": 3},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert "items" in data
    assert data["total"] == 5
    assert data["offset"] == 0
    assert data["limit"] == 3
    assert len(data["items"]) == 3
    assert data["has_more"] is True


@pytest.mark.asyncio
async def test_my_tasks_pagination(
    client, db, approved_requirement, normal_user
):
    from app.models import Task

    for i in range(5):
        task = Task(
            requirement_id=approved_requirement.id,
            title=f"我的任务-{i}",
            status="pending",
            created_by=normal_user.id,
            assignee_id=normal_user.id,
        )
        db.add(task)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        "/api/v1/users/me/tasks",
        params={"offset": 0, "limit": 3},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert "items" in data
    assert data["total"] == 5
    assert data["offset"] == 0
    assert data["limit"] == 3
    assert len(data["items"]) == 3
    assert data["has_more"] is True


@pytest.mark.asyncio
async def test_global_requirements_pagination(
    client, db, sample_iteration, normal_user
):
    from app.models import Requirement

    for i in range(5):
        req = Requirement(
            iteration_id=sample_iteration.id,
            title=f"全局需求-{i}",
            req_type="feature",
            priority=1,
            status="drafting_req",
            created_by=normal_user.id,
        )
        db.add(req)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        "/api/v1/requirements",
        params={"offset": 1, "limit": 2},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert "items" in data
    assert data["total"] == 5
    assert data["offset"] == 1
    assert data["limit"] == 2
    assert len(data["items"]) == 2
    assert data["has_more"] is True


@pytest.mark.asyncio
async def test_limit_capped_at_200(
    client, db, sample_iteration, normal_user
):
    from app.models import Requirement

    req = Requirement(
        iteration_id=sample_iteration.id,
        title="需求",
        req_type="feature",
        priority=1,
        status="drafting_req",
        created_by=normal_user.id,
    )
    db.add(req)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/iterations/{sample_iteration.id}/requirements",
        params={"limit": 500},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["limit"] == 200


@pytest.mark.asyncio
async def test_pagination_empty_result(
    client, db, sample_iteration, normal_user
):
    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/iterations/{sample_iteration.id}/requirements",
        params={"offset": 0, "limit": 10},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["total"] == 0
    assert data["items"] == []
    assert data["has_more"] is False


@pytest.mark.asyncio
async def test_offset_beyond_total(
    client, db, sample_iteration, normal_user
):
    from app.models import Requirement

    req = Requirement(
        iteration_id=sample_iteration.id,
        title="需求",
        req_type="feature",
        priority=1,
        status="drafting_req",
        created_by=normal_user.id,
    )
    db.add(req)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/iterations/{sample_iteration.id}/requirements",
        params={"offset": 100, "limit": 10},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    data = body["data"]
    assert data["total"] == 1
    assert data["items"] == []
    assert data["has_more"] is False
