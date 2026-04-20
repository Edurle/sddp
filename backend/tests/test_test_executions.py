import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_list_execution_rounds_success(client, db, sample_task, sample_test_case, normal_user):
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
    resp = await client.get(f"/api/v1/tasks/{sample_task.id}/test-executions", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1
    r = body["data"][0]
    assert "round_id" in r
    assert "total" in r
    assert "passed" in r
    assert "failed" in r
    assert "skipped" in r
    assert "executed_by" in r
    assert "created_at" in r


@pytest.mark.asyncio
async def test_list_execution_rounds_empty(client, db, sample_task, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.get(f"/api/v1/tasks/{sample_task.id}/test-executions", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"] == []


@pytest.mark.asyncio
async def test_list_execution_rounds_multiple(client, db, sample_task, sample_test_case, normal_user):
    from app.models import TestExecutionRound, TestExecutionRecord

    for i in range(2):
        round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
        db.add(round_)
        await db.flush()

        rec = TestExecutionRecord(
            round_id=round_.id,
            test_case_id=sample_test_case.id,
            status="passed" if i == 0 else "failed",
            actual_result="OK",
            failure_reason=None if i == 0 else "error",
        )
        db.add(rec)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(f"/api/v1/tasks/{sample_task.id}/test-executions", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert len(body["data"]) == 2


@pytest.mark.asyncio
async def test_get_execution_records_success(client, db, sample_task, sample_test_case, normal_user):
    from app.models import TestExecutionRound, TestExecutionRecord

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    record = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=sample_test_case.id,
        status="passed",
        actual_result="返回200和token",
    )
    db.add(record)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(f"/api/v1/test-executions/{round_.id}/records", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert isinstance(body["data"], list)
    assert len(body["data"]) >= 1
    rec = body["data"][0]
    assert "id" in rec
    assert "test_case" in rec
    assert rec["test_case"]["id"] == sample_test_case.id
    assert rec["status"] == "passed"


@pytest.mark.asyncio
async def test_get_execution_records_pending_status(client, db, sample_task, sample_test_case, normal_user):
    from app.models import TestExecutionRound, TestExecutionRecord

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    record = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=sample_test_case.id,
        status="pending",
    )
    db.add(record)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(f"/api/v1/test-executions/{round_.id}/records", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"][0]["status"] == "pending"


@pytest.mark.asyncio
async def test_update_record_mark_passed(client, db, sample_task, sample_test_case, normal_user, owner_role):
    from app.models import TestExecutionRound, TestExecutionRecord

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    record = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=sample_test_case.id,
        status="pending",
    )
    db.add(record)
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.put(
        f"/api/v1/test-execution-records/{record.id}",
        json={"status": "passed", "actual_result": "返回200和token"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_update_record_mark_failed_with_reason(client, db, sample_task, sample_test_case, normal_user, owner_role):
    from app.models import TestExecutionRound, TestExecutionRecord

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    record = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=sample_test_case.id,
        status="pending",
    )
    db.add(record)
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.put(
        f"/api/v1/test-execution-records/{record.id}",
        json={
            "status": "failed",
            "actual_result": "返回500",
            "failure_reason": "数据库连接失败",
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_update_record_failed_without_reason(client, db, sample_task, sample_test_case, normal_user, owner_role):
    from app.models import TestExecutionRound, TestExecutionRecord

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    record = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=sample_test_case.id,
        status="pending",
    )
    db.add(record)
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.put(
        f"/api/v1/test-execution-records/{record.id}",
        json={"status": "failed", "failure_reason": ""},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40403


@pytest.mark.asyncio
async def test_update_record_mark_skipped(client, db, sample_task, sample_test_case, normal_user, owner_role):
    from app.models import TestExecutionRound, TestExecutionRecord

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    record = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=sample_test_case.id,
        status="pending",
    )
    db.add(record)
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
    resp = await client.put(
        f"/api/v1/test-execution-records/{record.id}",
        json={"status": "skipped", "actual_result": "依赖接口不可用"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0


@pytest.mark.asyncio
async def test_update_record_no_permission(client, db, sample_task, sample_test_case, normal_user):
    from app.models import TestExecutionRound, TestExecutionRecord

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    record = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=sample_test_case.id,
        status="pending",
    )
    db.add(record)
    await db.commit()

    headers = auth_headers(normal_user.id, permissions=[])
    resp = await client.put(
        f"/api/v1/test-execution-records/{record.id}",
        json={"status": "passed", "actual_result": "OK"},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40300
