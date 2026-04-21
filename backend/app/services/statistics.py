"""Statistics service."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ERR_NOT_FOUND, BusinessError
from app.models import (
    Iteration,
    Project,
    Requirement,
    Task,
    TestCase,
    TestExecutionRecord,
    TestExecutionRound,
)


async def get_requirement_test_statistics(db: AsyncSession, requirement_id: int) -> dict:
    req_stmt = select(Requirement).where(Requirement.id == requirement_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    tc_stmt = select(TestCase).where(
        TestCase.requirement_id == requirement_id,
        TestCase.is_deleted == False,
    )
    tc_result = await db.execute(tc_stmt)
    test_cases = tc_result.scalars().all()
    total_cases = len(test_cases)

    if total_cases == 0:
        return {
            "total_cases": 0,
            "latest_results": {"passed": 0, "failed": 0, "skipped": 0, "not_executed": 0},
            "pass_rate": 0,
        }

    task_stmt = select(Task).where(
        Task.requirement_id == requirement_id,
        Task.is_deleted == False,
    )
    task_result = await db.execute(task_stmt)
    tasks = task_result.scalars().all()
    task_ids = [t.id for t in tasks]

    tc_ids = [tc.id for tc in test_cases]

    latest_results = {"passed": 0, "failed": 0, "skipped": 0, "not_executed": total_cases}
    pass_rate = 0.0

    if task_ids:
        executed_tc_ids = set()
        for tid in task_ids:
            round_stmt = (
                select(TestExecutionRound)
                .where(TestExecutionRound.task_id == tid)
                .order_by(TestExecutionRound.created_at.desc())
                .limit(1)
            )
            round_result = await db.execute(round_stmt)
            latest_round = round_result.scalar_one_or_none()
            if latest_round is None:
                continue

            rec_stmt = select(TestExecutionRecord).where(TestExecutionRecord.round_id == latest_round.id)
            rec_result = await db.execute(rec_stmt)
            records = rec_result.scalars().all()

            for rec in records:
                if rec.test_case_id in tc_ids:
                    executed_tc_ids.add(rec.test_case_id)
                    if rec.status in ("passed", "failed", "skipped"):
                        latest_results[rec.status] += 1

        latest_results["not_executed"] = total_cases - len(executed_tc_ids)
        if total_cases > 0:
            pass_rate = latest_results["passed"] / total_cases

    return {
        "total_cases": total_cases,
        "latest_results": latest_results,
        "pass_rate": pass_rate,
    }


async def get_iteration_test_statistics(db: AsyncSession, iteration_id: int) -> dict:
    iter_stmt = select(Iteration).where(Iteration.id == iteration_id)
    iter_result = await db.execute(iter_stmt)
    iteration = iter_result.scalar_one_or_none()
    if iteration is None:
        raise BusinessError(ERR_NOT_FOUND, "迭代不存在")

    req_stmt = select(Requirement).where(
        Requirement.iteration_id == iteration_id,
        Requirement.is_deleted == False,
    )
    req_result = await db.execute(req_stmt)
    requirements = req_result.scalars().all()

    if not requirements:
        return {"total_cases": 0, "latest_pass_rate": 0, "by_requirement": []}

    total_cases = 0
    total_passed = 0
    by_requirement = []

    for req in requirements:
        tc_stmt = select(TestCase).where(
            TestCase.requirement_id == req.id,
            TestCase.is_deleted == False,
        )
        tc_result = await db.execute(tc_stmt)
        test_cases = tc_result.scalars().all()
        req_tc_count = len(test_cases)
        total_cases += req_tc_count

        task_stmt = select(Task).where(
            Task.requirement_id == req.id,
            Task.is_deleted == False,
        )
        task_result = await db.execute(task_stmt)
        tasks = task_result.scalars().all()

        latest_passed = 0
        latest_failed = 0
        tc_ids = {tc.id for tc in test_cases}

        for t in tasks:
            round_stmt = (
                select(TestExecutionRound)
                .where(TestExecutionRound.task_id == t.id)
                .order_by(TestExecutionRound.created_at.desc())
                .limit(1)
            )
            round_result = await db.execute(round_stmt)
            latest_round = round_result.scalar_one_or_none()
            if latest_round is None:
                continue

            rec_stmt = select(TestExecutionRecord).where(TestExecutionRecord.round_id == latest_round.id)
            rec_result = await db.execute(rec_stmt)
            records = rec_result.scalars().all()

            for rec in records:
                if rec.test_case_id in tc_ids:
                    if rec.status == "passed":
                        latest_passed += 1
                    elif rec.status == "failed":
                        latest_failed += 1

        total_passed += latest_passed

        by_requirement.append({
            "requirement_id": req.id,
            "requirement_title": req.title,
            "total_cases": req_tc_count,
            "latest_passed": latest_passed,
            "latest_failed": latest_failed,
        })

    latest_pass_rate = total_passed / total_cases if total_cases > 0 else 0

    return {
        "total_cases": total_cases,
        "latest_pass_rate": latest_pass_rate,
        "by_requirement": by_requirement,
    }


async def get_project_test_statistics(db: AsyncSession, project_id: int) -> dict:
    proj_stmt = select(Project).where(Project.id == project_id, Project.is_deleted == False)
    proj_result = await db.execute(proj_stmt)
    project = proj_result.scalar_one_or_none()
    if project is None:
        raise BusinessError(ERR_NOT_FOUND, "项目不存在")

    iter_stmt = select(Iteration).where(Iteration.project_id == project_id)
    iter_result = await db.execute(iter_stmt)
    iterations = iter_result.scalars().all()

    if not iterations:
        return {"iterations": []}

    iteration_stats = []
    for iteration in iterations:
        iter_stat = await get_iteration_test_statistics(db, iteration.id)
        iteration_stats.append({
            "iteration_id": iteration.id,
            "iteration_name": iteration.name,
            "total_cases": iter_stat["total_cases"],
            "pass_rate": iter_stat["latest_pass_rate"],
        })

    return {"iterations": iteration_stats}
