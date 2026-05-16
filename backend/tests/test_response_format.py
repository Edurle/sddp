import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_direct_create_task_no_top_level_duplicate(client, db, approved_requirement, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.post(
        "/api/v1/tasks",
        json={
            "title": "格式测试任务",
            "description": "验证无重复键",
            "requirement_id": approved_requirement.id,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["message"] == "success"
    assert "data" in body
    top_level_keys = set(body.keys())
    assert top_level_keys == {"code", "message", "data"}


@pytest.mark.asyncio
async def test_direct_create_requirement_no_top_level_duplicate(client, db, normal_user, owner_role):
    headers = auth_headers(normal_user.id)
    resp = await client.post(
        "/api/v1/requirements",
        json={
            "title": "格式测试需求",
            "type": "feature",
            "priority": 1,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["message"] == "success"
    assert "data" in body
    top_level_keys = set(body.keys())
    assert top_level_keys == {"code", "message", "data"}


@pytest.mark.asyncio
async def test_direct_create_test_case_no_top_level_duplicate(client, db, approved_requirement, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.post(
        "/api/v1/test-cases",
        json={
            "title": "格式测试用例",
            "case_type": "api",
            "requirement_id": approved_requirement.id,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["message"] == "success"
    assert "data" in body
    top_level_keys = set(body.keys())
    assert top_level_keys == {"code", "message", "data"}


@pytest.mark.asyncio
async def test_patch_task_no_top_level_duplicate(client, db, sample_task, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.patch(
        f"/api/v1/tasks/{sample_task.id}",
        json={"title": "新标题"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["message"] == "success"
    assert "data" in body
    top_level_keys = set(body.keys())
    assert top_level_keys == {"code", "message", "data"}


@pytest.mark.asyncio
async def test_create_test_record_no_top_level_duplicate(client, db, sample_task, sample_test_case, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.post(
        f"/api/v1/tasks/{sample_task.id}/test-records",
        json={"test_case_id": sample_test_case.id, "status": "pending"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["message"] == "success"
    assert "data" in body
    top_level_keys = set(body.keys())
    assert top_level_keys == {"code", "message", "data"}


@pytest.mark.asyncio
async def test_create_test_round_no_top_level_duplicate(client, db, sample_task, sample_test_case, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.post(
        f"/api/v1/tasks/{sample_task.id}/test-rounds",
        json={"test_case_id": sample_test_case.id, "status": "pending"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["message"] == "success"
    assert "data" in body
    top_level_keys = set(body.keys())
    assert top_level_keys == {"code", "message", "data"}


@pytest.mark.asyncio
async def test_projects_use_success_message(client, normal_user, owner_role, sample_project):
    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/teams/{owner_role['team'].id}/projects",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "success"

    resp2 = await client.get(f"/api/v1/projects/{sample_project.id}", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["message"] == "success"


@pytest.mark.asyncio
async def test_iterations_use_success_message(client, normal_user, sample_project, sample_iteration):
    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/projects/{sample_project.id}/iterations",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["message"] == "success"

    resp2 = await client.get(f"/api/v1/iterations/{sample_iteration.id}", headers=headers)
    assert resp2.status_code == 200
    assert resp2.json()["message"] == "success"


@pytest.mark.asyncio
async def test_approve_requirement_not_found_uses_business_error(client, db, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.post("/api/v1/requirements/99999/approve", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] != 0
    assert body["code"] != 1
    assert "data" in body


@pytest.mark.asyncio
async def test_approve_spec_not_found_uses_business_error(client, db, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.post("/api/v1/requirements/99999/approve-spec", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] != 0
    assert body["code"] != 1
    assert "data" in body
