import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_requirement_test_statistics_success(client, db, approved_requirement, sample_test_case, sample_task, normal_user):
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
    resp = await client.get(
        f"/api/v1/requirements/{approved_requirement.id}/test-statistics",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert "total_cases" in data
    assert "latest_results" in data
    assert "pass_rate" in data
    results = data["latest_results"]
    assert "passed" in results
    assert "failed" in results
    assert "skipped" in results
    assert "not_executed" in results


@pytest.mark.asyncio
async def test_requirement_test_statistics_no_execution(client, db, approved_requirement, sample_test_case, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/requirements/{approved_requirement.id}/test-statistics",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["total_cases"] >= 1
    results = data["latest_results"]
    assert results["not_executed"] >= 1
    assert results["passed"] == 0
    assert results["failed"] == 0
    assert results["skipped"] == 0
    assert data["pass_rate"] == 0


@pytest.mark.asyncio
async def test_requirement_test_statistics_pass_rate_calculation(
    client, db, approved_requirement, sample_task, normal_user
):
    from app.models import TestCase, TestExecutionRound, TestExecutionRecord

    tc1 = TestCase(
        requirement_id=approved_requirement.id,
        case_number=f"TC-{approved_requirement.id}-10",
        title="用例A",
        case_type="api",
        steps="步骤",
        expected_result="结果",
    )
    tc2 = TestCase(
        requirement_id=approved_requirement.id,
        case_number=f"TC-{approved_requirement.id}-11",
        title="用例B",
        case_type="api",
        steps="步骤",
        expected_result="结果",
    )
    db.add_all([tc1, tc2])
    await db.flush()

    round_ = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round_)
    await db.flush()

    rec1 = TestExecutionRecord(
        round_id=round_.id, test_case_id=tc1.id, status="passed", actual_result="OK"
    )
    rec2 = TestExecutionRecord(
        round_id=round_.id, test_case_id=tc2.id, status="failed",
        actual_result="Error", failure_reason="bug",
    )
    db.add_all([rec1, rec2])
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/requirements/{approved_requirement.id}/test-statistics",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["total_cases"] >= 2
    assert data["latest_results"]["passed"] >= 1
    assert data["latest_results"]["failed"] >= 1
    assert data["pass_rate"] > 0


@pytest.mark.asyncio
async def test_iteration_test_statistics_success(client, db, sample_iteration, approved_requirement, sample_task, sample_test_case, normal_user):
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
    resp = await client.get(
        f"/api/v1/iterations/{sample_iteration.id}/test-statistics",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert "total_cases" in data
    assert "latest_pass_rate" in data
    assert "by_requirement" in data
    assert isinstance(data["by_requirement"], list)
    if len(data["by_requirement"]) > 0:
        req_stat = data["by_requirement"][0]
        assert "requirement_id" in req_stat
        assert "requirement_title" in req_stat
        assert "total_cases" in req_stat
        assert "latest_passed" in req_stat
        assert "latest_failed" in req_stat


@pytest.mark.asyncio
async def test_iteration_test_statistics_empty(client, db, sample_iteration, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/iterations/{sample_iteration.id}/test-statistics",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["total_cases"] == 0
    assert data["latest_pass_rate"] == 0
    assert data["by_requirement"] == []


@pytest.mark.asyncio
async def test_iteration_test_statistics_latest_round_only(client, db, sample_iteration, approved_requirement, sample_task, sample_test_case, normal_user):
    from app.models import TestExecutionRound, TestExecutionRecord

    round1 = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round1)
    await db.flush()

    rec1 = TestExecutionRecord(
        round_id=round1.id, test_case_id=sample_test_case.id,
        status="failed", actual_result="Error", failure_reason="bug",
    )
    db.add(rec1)
    await db.flush()

    round2 = TestExecutionRound(task_id=sample_task.id, executed_by=normal_user.id)
    db.add(round2)
    await db.flush()

    rec2 = TestExecutionRecord(
        round_id=round2.id, test_case_id=sample_test_case.id,
        status="passed", actual_result="OK",
    )
    db.add(rec2)
    await db.commit()

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/iterations/{sample_iteration.id}/test-statistics",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["latest_pass_rate"] > 0


@pytest.mark.asyncio
async def test_project_test_statistics_success(client, db, sample_project, sample_iteration, approved_requirement, sample_task, sample_test_case, normal_user):
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
    resp = await client.get(
        f"/api/v1/projects/{sample_project.id}/test-statistics",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert "iterations" in data
    assert isinstance(data["iterations"], list)
    assert len(data["iterations"]) >= 1
    iter_stat = data["iterations"][0]
    assert "iteration_id" in iter_stat
    assert "iteration_name" in iter_stat
    assert "total_cases" in iter_stat
    assert "pass_rate" in iter_stat


@pytest.mark.asyncio
async def test_project_test_statistics_no_iterations(client, db, sample_project, normal_user):
    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/projects/{sample_project.id}/test-statistics",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert data["iterations"] == []


@pytest.mark.asyncio
async def test_project_test_statistics_multiple_iterations(
    client, db, sample_project, approved_requirement, sample_task, sample_test_case, normal_user
):
    from app.models import Iteration, TestExecutionRound, TestExecutionRecord

    iter2 = Iteration(
        project_id=sample_project.id,
        name="Sprint 2",
        goal="第二个迭代",
        start_date="2026-04-16",
        end_date="2026-04-30",
        status="planned",
    )
    db.add(iter2)
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

    headers = auth_headers(normal_user.id)
    resp = await client.get(
        f"/api/v1/projects/{sample_project.id}/test-statistics",
        headers=headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    data = body["data"]
    assert len(data["iterations"]) >= 2
