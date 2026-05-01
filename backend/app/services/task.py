"""Task service."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    ERR_NOT_FOUND,
    ERR_NO_EXECUTION,
    ERR_REQUIREMENT_STATUS,
    ERR_TEST_NOT_PASSED,
    ERR_VALIDATION,
    BusinessError,
)
from app.models import Requirement, Task, TestCase, TestExecutionRecord, TestExecutionRound


async def list_tasks(
    db: AsyncSession,
    requirement_id: int,
    status: str | None = None,
    assignee_id: int | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict:
    base_where = [
        Task.requirement_id == requirement_id,
        Task.is_deleted == False,
    ]
    if status:
        base_where.append(Task.status == status)
    if assignee_id is not None:
        base_where.append(Task.assignee_id == assignee_id)

    count_stmt = select(func.count()).select_from(Task).where(*base_where)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = select(Task).where(*base_where).order_by(Task.created_at.desc())
    stmt = stmt.offset(offset).limit(limit + 1)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = []
    for t in rows:
        d = _task_to_dict(t)
        if assignee_id is not None and t.assignee_id is not None:
            d["assignee"] = {"id": t.assignee_id}
        items.append(d)
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
    }


async def create_task(
    db: AsyncSession,
    requirement_id: int,
    user_id: int,
    title: str,
    description: str | None = None,
    assignee_id: int | None = None,
) -> dict:
    if not title or not title.strip():
        raise BusinessError(ERR_VALIDATION, "任务标题不能为空")

    req_stmt = select(Requirement).where(Requirement.id == requirement_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    if req.status != "approved":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "需求未通过审核")

    task = Task(
        requirement_id=requirement_id,
        title=title,
        description=description,
        assignee_id=assignee_id,
        status="pending",
        created_by=user_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return _task_to_dict(task)


async def get_task_detail(db: AsyncSession, task_id: int) -> dict:
    from app.models import User
    task = await _get_task_or_fail(db, task_id)

    req_stmt = select(Requirement).where(Requirement.id == task.requirement_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()

    tc_stmt = select(TestCase).where(
        TestCase.requirement_id == task.requirement_id,
        TestCase.is_deleted == False,
    )
    tc_result = await db.execute(tc_stmt)
    test_cases = tc_result.scalars().all()

    latest_execution = await _get_latest_execution_stats(db, task_id)

    assignee = None
    if task.assignee_id:
        user_stmt = select(User).where(User.id == task.assignee_id)
        user_result = await db.execute(user_stmt)
        user = user_result.scalar_one_or_none()
        if user:
            assignee = {"id": user.id, "nickname": user.nickname, "email": user.email}

    result = _task_to_dict(task)
    result["requirement"] = {
        "id": req.id,
        "title": req.title,
        "status": req.status,
    } if req else None
    result["assignee"] = assignee
    result["test_cases"] = [
        {"id": tc.id, "title": tc.title, "case_type": tc.case_type}
        for tc in test_cases
    ]
    result["latest_execution"] = latest_execution
    return result


async def update_task(
    db: AsyncSession,
    task_id: int,
    title: str | None = None,
    description: str | None = None,
    assignee_id: int | None = None,
) -> dict:
    task = await _get_task_or_fail(db, task_id)
    if task.status not in ("pending", "coding"):
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前任务状态不允许编辑")

    if title is not None:
        task.title = title
    if description is not None:
        task.description = description
    if assignee_id is not None:
        task.assignee_id = assignee_id

    await db.commit()
    await db.refresh(task)
    return _task_to_dict(task)


async def delete_task(db: AsyncSession, task_id: int) -> dict:
    task = await _get_task_or_fail(db, task_id)
    if task.status not in ("pending", "coding"):
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前任务状态不允许删除")

    task.is_deleted = True
    task.deleted_at = datetime.utcnow()
    await db.commit()
    return {"id": task.id}


async def start_testing(db: AsyncSession, task_id: int, user_id: int) -> dict:
    task = await _get_task_or_fail(db, task_id)
    if task.status != "coding":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "只有编码中的任务才能开始测试")

    tc_stmt = select(TestCase).where(
        TestCase.requirement_id == task.requirement_id,
        TestCase.is_deleted == False,
    )
    tc_result = await db.execute(tc_stmt)
    test_cases = tc_result.scalars().all()

    round_ = TestExecutionRound(task_id=task_id, executed_by=user_id)
    db.add(round_)
    await db.flush()

    records = []
    for tc in test_cases:
        rec = TestExecutionRecord(
            round_id=round_.id,
            test_case_id=tc.id,
            status="pending",
        )
        db.add(rec)
        records.append(rec)
    await db.flush()

    task.status = "testing"
    await db.commit()
    await db.refresh(round_)
    for rec in records:
        await db.refresh(rec)

    return {
        "round_id": round_.id,
        "records": [
            {
                "id": r.id,
                "test_case_id": r.test_case_id,
                "status": r.status,
            }
            for r in records
        ],
    }


async def complete_task(db: AsyncSession, task_id: int) -> dict:
    task = await _get_task_or_fail(db, task_id)
    if task.status != "testing":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "只有测试中的任务才能完成")

    latest_round_stmt = (
        select(TestExecutionRound)
        .where(TestExecutionRound.task_id == task_id)
        .order_by(TestExecutionRound.created_at.desc())
        .limit(1)
    )
    lr_result = await db.execute(latest_round_stmt)
    latest_round = lr_result.scalar_one_or_none()

    if latest_round is None:
        raise BusinessError(ERR_NO_EXECUTION, "没有测试执行记录")

    rec_stmt = select(TestExecutionRecord).where(TestExecutionRecord.round_id == latest_round.id)
    rec_result = await db.execute(rec_stmt)
    records = rec_result.scalars().all()

    if not records:
        raise BusinessError(ERR_NO_EXECUTION, "没有测试执行记录")

    for rec in records:
        if rec.status in ("failed", "fail"):
            raise BusinessError(ERR_TEST_NOT_PASSED, "存在未通过的测试用例")

    task.status = "completed"
    await db.commit()
    return _task_to_dict(task)


async def start_coding(db: AsyncSession, task_id: int) -> dict:
    task = await _get_task_or_fail(db, task_id)
    if task.status != "pending":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "只有待处理的任务才能开始编码")
    task.status = "coding"
    await db.commit()
    await db.refresh(task)
    return _task_to_dict(task)


async def update_git_info(db: AsyncSession, task_id: int, **kwargs) -> dict:
    task = await _get_task_or_fail(db, task_id)
    for key in ("git_branch", "commit_sha", "pr_url", "artifact_url"):
        if key in kwargs:
            setattr(task, key, kwargs[key])
    await db.commit()
    await db.refresh(task)
    return _task_to_dict(task)


async def _get_task_or_fail(db: AsyncSession, task_id: int) -> Task:
    stmt = select(Task).where(Task.id == task_id, Task.is_deleted == False)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise BusinessError(ERR_NOT_FOUND, "任务不存在")
    return task


async def _get_latest_execution_stats(db: AsyncSession, task_id: int) -> dict | None:
    round_stmt = (
        select(TestExecutionRound)
        .where(TestExecutionRound.task_id == task_id)
        .order_by(TestExecutionRound.created_at.desc())
        .limit(1)
    )
    round_result = await db.execute(round_stmt)
    latest_round = round_result.scalar_one_or_none()
    if latest_round is None:
        return None

    rec_stmt = select(TestExecutionRecord).where(TestExecutionRecord.round_id == latest_round.id)
    rec_result = await db.execute(rec_stmt)
    records = rec_result.scalars().all()

    if not records:
        return None

    return {
        "total": len(records),
        "passed": sum(1 for r in records if r.status == "passed"),
        "failed": sum(1 for r in records if r.status == "failed"),
        "skipped": sum(1 for r in records if r.status == "skipped"),
    }


async def list_tasks_by_assignee(
    db: AsyncSession, user_id: int, status: str | None = None,
    offset: int = 0, limit: int = 50,
) -> dict:
    base_where = [Task.assignee_id == user_id, Task.is_deleted == False]
    if status:
        base_where.append(Task.status == status)

    count_stmt = select(func.count()).select_from(Task).where(*base_where)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = select(Task).where(*base_where).order_by(Task.updated_at.desc())
    stmt = stmt.offset(offset).limit(limit + 1)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = []
    for t in rows:
        d = _task_to_dict(t)
        req_stmt = select(Requirement).where(Requirement.id == t.requirement_id)
        req_result = await db.execute(req_stmt)
        req = req_result.scalar_one_or_none()
        if req:
            d["requirement_title"] = req.title
        items.append(d)
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
    }


def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "requirement_id": task.requirement_id,
        "title": task.title,
        "description": task.description,
        "assignee_id": task.assignee_id,
        "status": task.status,
        "created_by": task.created_by,
        "git_branch": task.git_branch,
        "commit_sha": task.commit_sha,
        "pr_url": task.pr_url,
        "artifact_url": task.artifact_url,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
