"""Test execution service."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    ERR_FAILURE_REASON_REQUIRED,
    ERR_NOT_FOUND,
    ERR_REQUIREMENT_STATUS,
    BusinessError,
)
from app.models import TestCase, TestExecutionRecord, TestExecutionRound


async def list_execution_rounds(db: AsyncSession, task_id: int) -> list[dict]:
    round_stmt = select(TestExecutionRound).where(
        TestExecutionRound.task_id == task_id,
    ).order_by(TestExecutionRound.created_at.asc())
    round_result = await db.execute(round_stmt)
    rounds = round_result.scalars().all()

    items = []
    for r in rounds:
        rec_stmt = select(TestExecutionRecord).where(TestExecutionRecord.round_id == r.id)
        rec_result = await db.execute(rec_stmt)
        records = rec_result.scalars().all()

        items.append({
            "id": r.id,
            "round_id": r.id,
            "total": len(records),
            "passed": sum(1 for rec in records if rec.status == "passed"),
            "failed": sum(1 for rec in records if rec.status == "failed"),
            "skipped": sum(1 for rec in records if rec.status == "skipped"),
            "executed_by": r.executed_by,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return items


async def get_execution_records(db: AsyncSession, round_id: int) -> list[dict]:
    rec_stmt = select(TestExecutionRecord).where(TestExecutionRecord.round_id == round_id)
    rec_result = await db.execute(rec_stmt)
    records = rec_result.scalars().all()

    items = []
    for rec in records:
        tc_stmt = select(TestCase).where(TestCase.id == rec.test_case_id)
        tc_result = await db.execute(tc_stmt)
        tc = tc_result.scalar_one_or_none()

        items.append({
            "id": rec.id,
            "test_case": {"id": rec.test_case_id, "title": tc.title} if tc else None,
            "status": rec.status,
            "actual_result": rec.actual_result,
            "failure_reason": rec.failure_reason,
            "log_output": rec.log_output,
            "duration_ms": rec.duration_ms,
            "executed_at": rec.executed_at.isoformat() if rec.executed_at else None,
        })
    return items


async def update_execution_record(
    db: AsyncSession,
    record_id: int,
    status: str,
    actual_result: str | None = None,
    failure_reason: str | None = None,
    log_output: str | None = None,
    duration_ms: int | None = None,
) -> dict:
    stmt = select(TestExecutionRecord).where(TestExecutionRecord.id == record_id)
    result = await db.execute(stmt)
    record = result.scalar_one_or_none()
    if record is None:
        raise BusinessError(ERR_NOT_FOUND, "执行记录不存在")

    if status == "failed" and not failure_reason:
        raise BusinessError(ERR_FAILURE_REASON_REQUIRED, "失败原因不能为空")

    record.status = status
    if actual_result is not None:
        record.actual_result = actual_result
    if status == "failed":
        record.failure_reason = failure_reason
    else:
        record.failure_reason = None
    if log_output is not None:
        record.log_output = log_output
    if duration_ms is not None:
        record.duration_ms = duration_ms

    await db.commit()
    await db.refresh(record)
    return {
        "id": record.id,
        "status": record.status,
        "actual_result": record.actual_result,
        "failure_reason": record.failure_reason,
        "log_output": record.log_output,
        "duration_ms": record.duration_ms,
    }


async def batch_update_records(
    db: AsyncSession,
    round_id: int,
    records: list,
) -> dict:
    round_stmt = select(TestExecutionRound).where(TestExecutionRound.id == round_id)
    round_result = await db.execute(round_stmt)
    if round_result.scalar_one_or_none() is None:
        raise BusinessError(ERR_NOT_FOUND, "执行轮次不存在")

    # 废弃用例不可再执行
    tc_ids = [item.test_case_id for item in records]
    if tc_ids:
        dep_stmt = select(TestCase.id).where(TestCase.id.in_(tc_ids), TestCase.status == "deprecated")
        if (await db.execute(dep_stmt)).first() is not None:
            raise BusinessError(ERR_REQUIREMENT_STATUS, "已废弃的测试用例不可再执行")

    updated = []
    for item in records:
        stmt = select(TestExecutionRecord).where(
            TestExecutionRecord.round_id == round_id,
            TestExecutionRecord.test_case_id == item.test_case_id,
        )
        result = await db.execute(stmt)
        rec = result.scalar_one_or_none()
        if rec is None:
            rec = TestExecutionRecord(
                round_id=round_id,
                test_case_id=item.test_case_id,
                status=item.status,
                actual_result=item.actual_result,
                failure_reason=item.failure_reason,
                log_output=item.log_output,
                duration_ms=item.duration_ms,
            )
            db.add(rec)
        else:
            rec.status = item.status
            if item.actual_result is not None:
                rec.actual_result = item.actual_result
            if item.failure_reason is not None:
                rec.failure_reason = item.failure_reason
            if item.log_output is not None:
                rec.log_output = item.log_output
            if item.duration_ms is not None:
                rec.duration_ms = item.duration_ms
        updated.append(rec)
    await db.commit()
    for r in updated:
        await db.refresh(r)
    return {
        "updated": len(updated),
        "records": [
            {"id": r.id, "test_case_id": r.test_case_id, "status": r.status}
            for r in updated
        ],
    }
