"""Test execution service."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    ERR_FAILURE_REASON_REQUIRED,
    ERR_NOT_FOUND,
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
            "test_case": {"id": rec.test_case_id} if tc else None,
            "status": rec.status,
            "actual_result": rec.actual_result,
            "failure_reason": rec.failure_reason,
            "executed_at": rec.executed_at.isoformat() if rec.executed_at else None,
        })
    return items


async def update_execution_record(
    db: AsyncSession,
    record_id: int,
    status: str,
    actual_result: str | None = None,
    failure_reason: str | None = None,
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

    await db.commit()
    await db.refresh(record)
    return {
        "id": record.id,
        "status": record.status,
        "actual_result": record.actual_result,
        "failure_reason": record.failure_reason,
    }
