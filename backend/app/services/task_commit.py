from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BusinessError, ERR_NOT_FOUND, ERR_VALIDATION
from app.models import Task, TaskCommit


async def add_commit(
    db: AsyncSession,
    task_id: int,
    commit_sha: str,
    message: str | None = None,
    author: str | None = None,
    committed_at: str | None = None,
) -> dict:
    stmt = select(Task).where(Task.id == task_id, Task.is_deleted == False)
    result = await db.execute(stmt)
    task = result.scalar_one_or_none()
    if task is None:
        raise BusinessError(ERR_NOT_FOUND, "任务不存在")

    dup = select(TaskCommit).where(
        TaskCommit.task_id == task_id,
        TaskCommit.commit_sha == commit_sha,
    )
    if (await db.execute(dup)).scalar_one_or_none():
        raise BusinessError(ERR_VALIDATION, "该 commit 已存在")

    from datetime import datetime, timezone
    parsed_at = None
    if committed_at:
        try:
            parsed_at = datetime.fromisoformat(committed_at).replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            parsed_at = None

    tc = TaskCommit(
        task_id=task_id,
        commit_sha=commit_sha,
        message=message,
        author=author,
        committed_at=parsed_at,
    )
    db.add(tc)

    task.commit_sha = commit_sha
    if task.git_branch is None:
        pass

    await db.commit()
    await db.refresh(tc)
    return _tc_to_dict(tc)


async def list_task_commits(db: AsyncSession, task_id: int) -> list[dict]:
    stmt = (
        select(TaskCommit)
        .where(TaskCommit.task_id == task_id)
        .order_by(TaskCommit.committed_at.desc(), TaskCommit.created_at.desc())
    )
    result = await db.execute(stmt)
    return [_tc_to_dict(tc) for tc in result.scalars().all()]


async def list_requirement_commits(db: AsyncSession, requirement_id: int) -> list[dict]:
    task_stmt = select(Task.id).where(
        Task.requirement_id == requirement_id,
        Task.is_deleted == False,
    )
    task_result = await db.execute(task_stmt)
    task_ids = [row[0] for row in task_result.all()]

    if not task_ids:
        return []

    stmt = (
        select(TaskCommit)
        .where(TaskCommit.task_id.in_(task_ids))
        .order_by(TaskCommit.committed_at.desc(), TaskCommit.created_at.desc())
    )
    result = await db.execute(stmt)
    items = []
    for tc in result.scalars().all():
        d = _tc_to_dict(tc)
        d["task_id"] = tc.task_id
        items.append(d)
    return items


def _tc_to_dict(tc: TaskCommit) -> dict:
    return {
        "id": tc.id,
        "task_id": tc.task_id,
        "commit_sha": tc.commit_sha,
        "message": tc.message,
        "author": tc.author,
        "committed_at": tc.committed_at.isoformat() if tc.committed_at else None,
        "created_at": tc.created_at.isoformat() if tc.created_at else None,
    }
