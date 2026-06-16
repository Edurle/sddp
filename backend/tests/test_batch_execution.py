import pytest
from tests.conftest import auth_headers


@pytest.fixture
async def setup_round_with_records(db, sample_task, normal_user):
    from app.models import TestExecutionRound, TestExecutionRecord, TestCase

    tc1 = TestCase(
        requirement_id=sample_task.requirement_id,
        case_number="TC-BATCH-01",
        title="批量测试用例1",
        case_type="happy_path",
        steps="步骤1",
        expected_result="结果1",
    )
    tc2 = TestCase(
        requirement_id=sample_task.requirement_id,
        case_number="TC-BATCH-02",
        title="批量测试用例2",
        case_type="happy_path",
        steps="步骤2",
        expected_result="结果2",
    )
    db.add_all([tc1, tc2])
    await db.flush()

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    rec1 = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=tc1.id,
        status="pending",
    )
    rec2 = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=tc2.id,
        status="pending",
    )
    db.add_all([rec1, rec2])
    await db.commit()

    return {
        "round": round_,
        "test_cases": [tc1, tc2],
        "records": [rec1, rec2],
    }


@pytest.mark.asyncio
async def test_batch_submit_passed_results(client, db, setup_round_with_records, normal_user):
    data = setup_round_with_records
    round_id = data["round"].id
    tc1, tc2 = data["test_cases"]

    headers = auth_headers(normal_user.id)
    resp = await client.put(
        f"/api/v1/test-executions/{round_id}/batch",
        json={
            "records": [
                {"test_case_id": tc1.id, "status": "passed", "actual_result": "OK"},
                {"test_case_id": tc2.id, "status": "passed", "actual_result": "OK"},
            ]
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["updated"] == 2
    assert len(body["data"]["records"]) == 2
    for r in body["data"]["records"]:
        assert r["status"] == "passed"


@pytest.mark.asyncio
async def test_batch_mixed_pass_fail_with_log_and_duration(client, db, setup_round_with_records, normal_user):
    data = setup_round_with_records
    round_id = data["round"].id
    tc1, tc2 = data["test_cases"]

    headers = auth_headers(normal_user.id)
    resp = await client.put(
        f"/api/v1/test-executions/{round_id}/batch",
        json={
            "records": [
                {
                    "test_case_id": tc1.id,
                    "status": "passed",
                    "actual_result": "返回200",
                    "log_output": "GET /api OK",
                    "duration_ms": 120,
                },
                {
                    "test_case_id": tc2.id,
                    "status": "failed",
                    "actual_result": "返回500",
                    "failure_reason": "超时",
                    "log_output": "TimeoutError",
                    "duration_ms": 5000,
                },
            ]
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["updated"] == 2

    from app.models import TestExecutionRecord
    from sqlalchemy import select

    stmt = select(TestExecutionRecord).where(
        TestExecutionRecord.round_id == round_id,
        TestExecutionRecord.test_case_id == tc1.id,
    )
    result = await db.execute(stmt)
    rec1 = result.scalar_one()
    assert rec1.status == "passed"
    assert rec1.log_output == "GET /api OK"
    assert rec1.duration_ms == 120

    stmt2 = select(TestExecutionRecord).where(
        TestExecutionRecord.round_id == round_id,
        TestExecutionRecord.test_case_id == tc2.id,
    )
    result2 = await db.execute(stmt2)
    rec2 = result2.scalar_one()
    assert rec2.status == "failed"
    assert rec2.failure_reason == "超时"
    assert rec2.log_output == "TimeoutError"
    assert rec2.duration_ms == 5000


@pytest.mark.asyncio
async def test_batch_round_not_found(client, db, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.put(
        "/api/v1/test-executions/99999/batch",
        json={
            "records": [
                {"test_case_id": 1, "status": "passed"},
            ]
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 40400


@pytest.mark.asyncio
async def test_batch_empty_records(client, db, sample_task, normal_user):
    from app.models import TestExecutionRound

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.put(
        f"/api/v1/test-executions/{round_.id}/batch",
        json={"records": []},
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["updated"] == 0


@pytest.mark.asyncio
async def test_batch_records_contain_log_output_and_duration_ms(client, db, setup_round_with_records, normal_user):
    data = setup_round_with_records
    round_id = data["round"].id
    tc1 = data["test_cases"][0]

    headers = auth_headers(normal_user.id)
    resp = await client.put(
        f"/api/v1/test-executions/{round_id}/batch",
        json={
            "records": [
                {
                    "test_case_id": tc1.id,
                    "status": "passed",
                    "log_output": "line1\nline2\nline3",
                    "duration_ms": 350,
                },
            ]
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["updated"] == 1

    from app.models import TestExecutionRecord
    from sqlalchemy import select

    stmt = select(TestExecutionRecord).where(
        TestExecutionRecord.round_id == round_id,
        TestExecutionRecord.test_case_id == tc1.id,
    )
    result = await db.execute(stmt)
    rec = result.scalar_one()
    assert rec.log_output == "line1\nline2\nline3"
    assert rec.duration_ms == 350


@pytest.mark.asyncio
async def test_single_put_supports_new_fields(client, db, sample_task, sample_test_case, normal_user, owner_role):
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
            "status": "passed",
            "actual_result": "返回200",
            "log_output": "执行成功日志",
            "duration_ms": 200,
        },
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["data"]["log_output"] == "执行成功日志"
    assert body["data"]["duration_ms"] == 200
