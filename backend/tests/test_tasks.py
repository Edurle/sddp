import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_list_tasks_success(client, db, sample_task, normal_user):
    headers = auth_headers(normal_user.id)
    req_id = sample_task.requirement_id
    resp = await client.get(f"/api/v1/requirements/{req_id}/tasks", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert isinstance(body["data"], dict)
    assert "items" in body["data"]
    assert len(body["data"]["items"]) >= 1
    task = body["data"]["items"][0]
    assert "id" in task
    assert "title" in task
    assert "status" in task


@pytest.mark.asyncio
async def test_list_tasks_filter_by_status(client, db, sample_task, normal_user):
    headers = auth_headers(normal_user.id)
    req_id = sample_task.requirement_id
    resp = await client.get(
        f"/api/v1/requirements/{req_id}/tasks",
        params={"status": "pending"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    for task in body["data"]["items"]:
        assert task["status"] == "pending"


@pytest.mark.asyncio
async def test_list_tasks_filter_by_assignee(client, db, sample_task, normal_user):
    headers = auth_headers(normal_user.id)
    req_id = sample_task.requirement_id
    from app.models import Task

    sample_task.assignee_id = normal_user.id
    await db.commit()

    resp = await client.get(
        f"/api/v1/requirements/{req_id}/tasks",
        params={"assignee_id": normal_user.id},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    for task in body["data"]["items"]:
        assert task["assignee"] is not None
        assert task["assignee"]["id"] == normal_user.id


@pytest.mark.asyncio
async def test_list_tasks_excludes_soft_deleted(client, db, sample_task, normal_user):
    from app.models import Task

    sample_task.is_deleted = True
    await db.commit()

    headers = auth_headers(normal_user.id)
    req_id = sample_task.requirement_id
    resp = await client.get(f"/api/v1/requirements/{req_id}/tasks", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    for task in body["data"]["items"]:
        assert task["id"] != sample_task.id


@pytest.mark.asyncio
async def test_create_task_success(client, db, approved_requirement, normal_user, owner_role):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(
        f"/api/v1/requirements/{approved_requirement.id}/tasks",
        json={
            "title": "实现用户API",
            "description": "开发登录注册接口",
            "assignee_id": None,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert "id" in body["data"]


@pytest.mark.asyncio
async def test_create_task_requirement_not_approved(client, db, sample_requirement, normal_user, owner_role):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(
        f"/api/v1/requirements/{sample_requirement.id}/tasks",
        json={
            "title": "实现用户API",
            "description": "...",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


@pytest.mark.asyncio
async def test_create_task_empty_title(client, db, approved_requirement, normal_user, owner_role):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(
        f"/api/v1/requirements/{approved_requirement.id}/tasks",
        json={"title": ""},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40001


@pytest.mark.asyncio
async def test_create_task_no_permission(client, db, approved_requirement, normal_user):
    headers = auth_headers(normal_user.id, permissions=[])
    resp = await client.post(
        f"/api/v1/requirements/{approved_requirement.id}/tasks",
        json={"title": "test", "description": "test"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40300


@pytest.mark.asyncio
async def test_get_task_detail_success(client, db, sample_task, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.get(f"/api/v1/tasks/{sample_task.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["id"] == sample_task.id
    assert "requirement" in data
    assert "test_cases" in data


@pytest.mark.asyncio
async def test_get_task_detail_with_latest_execution(client, db, sample_task, sample_test_case, normal_user):
    from app.models import TestExecutionRound, TestExecutionRecord

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    record = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=sample_test_case.id,
        status="passed",
        actual_result="OK",
    )
    db.add(record)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(f"/api/v1/tasks/{sample_task.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    latest = body["data"]["latest_execution"]
    assert latest is not None
    assert latest["total"] >= 1
    assert "passed" in latest
    assert "failed" in latest
    assert "skipped" in latest


@pytest.mark.asyncio
async def test_get_task_detail_no_execution(client, db, sample_task, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.get(f"/api/v1/tasks/{sample_task.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["latest_execution"] is None


@pytest.mark.asyncio
async def test_get_task_not_found(client, db, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.get("/api/v1/tasks/999", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40400


@pytest.mark.asyncio
async def test_update_task_pending_success(client, db, sample_task, normal_user, owner_role):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.put(
        f"/api/v1/tasks/{sample_task.id}",
        json={"title": "更新标题"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_update_task_coding_success(client, db, sample_task, normal_user, owner_role):
    sample_task.status = "coding"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.put(
        f"/api/v1/tasks/{sample_task.id}",
        json={"description": "更新描述"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_update_task_testing_forbidden(client, db, sample_task, normal_user, owner_role):
    sample_task.status = "testing"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.put(
        f"/api/v1/tasks/{sample_task.id}",
        json={"title": "不应成功"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


@pytest.mark.asyncio
async def test_update_task_completed_forbidden(client, db, sample_task, normal_user, owner_role):
    sample_task.status = "completed"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.put(
        f"/api/v1/tasks/{sample_task.id}",
        json={"title": "不应成功"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


@pytest.mark.asyncio
async def test_delete_task_pending_success(client, db, sample_task, normal_user, owner_role):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.delete(f"/api/v1/tasks/{sample_task.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_delete_task_coding_success(client, db, sample_task, normal_user, owner_role):
    sample_task.status = "coding"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.delete(f"/api/v1/tasks/{sample_task.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_delete_task_testing_forbidden(client, db, sample_task, normal_user, owner_role):
    sample_task.status = "testing"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.delete(f"/api/v1/tasks/{sample_task.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


@pytest.mark.asyncio
async def test_delete_task_completed_forbidden(client, db, sample_task, normal_user, owner_role):
    sample_task.status = "completed"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.delete(f"/api/v1/tasks/{sample_task.id}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


@pytest.mark.asyncio
async def test_start_testing_coding_to_testing(client, db, sample_task, sample_test_case, normal_user, owner_role):
    sample_task.status = "coding"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(f"/api/v1/tasks/{sample_task.id}/start-testing", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert "round_id" in data
    assert "records" in data
    assert len(data["records"]) >= 1
    record = data["records"][0]
    assert record["status"] == "pending"


@pytest.mark.asyncio
async def test_start_testing_creates_records_for_all_cases(
    client, db, approved_requirement, sample_task, sample_test_case, normal_user, owner_role
):
    from app.models import TestCase

    tc2 = TestCase(
        requirement_id=approved_requirement.id,
        case_number=f"TC-{approved_requirement.id}-02",
        title="测试用例2",
        case_type="e2e",
        steps="步骤",
        expected_result="结果",
    )
    db.add(tc2)
    await db.commit()

    sample_task.status = "coding"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(f"/api/v1/tasks/{sample_task.id}/start-testing", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]["records"]) == 2


@pytest.mark.asyncio
async def test_start_testing_pending_forbidden(client, db, sample_task, normal_user, owner_role):
    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(f"/api/v1/tasks/{sample_task.id}/start-testing", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


@pytest.mark.asyncio
async def test_start_testing_already_testing(client, db, sample_task, normal_user, owner_role):
    sample_task.status = "testing"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(f"/api/v1/tasks/{sample_task.id}/start-testing", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


@pytest.mark.asyncio
async def test_complete_task_success(client, db, sample_task, sample_test_case, normal_user, owner_role):
    from app.models import TestExecutionRound, TestExecutionRecord

    sample_task.status = "testing"
    await db.flush()

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    record = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=sample_test_case.id,
        status="passed",
        actual_result="OK",
    )
    db.add(record)
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(f"/api/v1/tasks/{sample_task.id}/complete", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_complete_task_has_failed_tests(client, db, sample_task, sample_test_case, normal_user, owner_role):
    from app.models import TestExecutionRound, TestExecutionRecord

    sample_task.status = "testing"
    await db.flush()

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    record = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=sample_test_case.id,
        status="failed",
        actual_result="Error",
        failure_reason="bug",
    )
    db.add(record)
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(f"/api/v1/tasks/{sample_task.id}/complete", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40401


@pytest.mark.asyncio
async def test_complete_task_no_execution_records(client, db, sample_task, normal_user, owner_role):
    sample_task.status = "testing"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(f"/api/v1/tasks/{sample_task.id}/complete", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40402


@pytest.mark.asyncio
async def test_complete_task_wrong_status_coding(client, db, sample_task, normal_user, owner_role):
    sample_task.status = "coding"
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.post(f"/api/v1/tasks/{sample_task.id}/complete", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40204


class TestTaskDirectCreateStatusCheck:
    @pytest.mark.asyncio
    async def test_cannot_create_task_for_drafting_requirement(self, client, normal_user, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=["task:create"])
        resp = await client.post(
            "/api/v1/tasks",
            json={
                "title": "should fail",
                "requirement_id": sample_requirement.id,
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] != 0

    @pytest.mark.asyncio
    async def test_can_create_task_for_approved_requirement(self, client, normal_user, approved_requirement):
        headers = auth_headers(normal_user.id, permissions=["task:create"])
        resp = await client.post(
            "/api/v1/tasks",
            json={
                "title": "valid task",
                "requirement_id": approved_requirement.id,
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
