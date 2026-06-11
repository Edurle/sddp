from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select

from app.deps import get_current_user, get_db_session, check_team_permission, _team_id_from_requirement, _team_id_from_task
from app.exceptions import BusinessError, ERR_NOT_FOUND, ERR_REQUIREMENT_STATUS, ERR_VALIDATION
from app.services import task as task_svc
from app.services import task_commit as tc_svc
from app.services.test_execution import list_execution_rounds

router = APIRouter()


class DirectCreateTaskRequest(BaseModel):
    title: str
    description: str | None = None
    requirement_id: int
    assignee_id: int | None = None


class PatchTaskRequest(BaseModel):
    status: str | None = None
    title: str | None = None
    description: str | None = None


@router.post("")
async def direct_create_task(
    body: DirectCreateTaskRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    from app.models import Requirement, Task
    req_stmt = select(Requirement).where(Requirement.id == body.requirement_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    await check_team_permission(db, user, await _team_id_from_requirement(db, body.requirement_id), "task:create")
    if req.status != "approved":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "需求未通过审核，无法创建任务")
    task = Task(
        requirement_id=body.requirement_id,
        title=body.title,
        description=body.description,
        assignee_id=body.assignee_id,
        status="pending",
        created_by=int(user["sub"]),
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    data = task_svc._task_to_dict(task)
    return {"code": 0, "message": "success", "data": data}


VALID_TRANSITIONS = {
    "pending": {"coding"},
    "coding": {"testing", "pending"},
    "testing": {"completed", "coding"},
    "completed": set(),
}


@router.patch("/{id}")
async def patch_task(
    id: int,
    body: PatchTaskRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_task(db, id), "task:edit")
    task = await task_svc._get_task_or_fail(db, id)
    if body.status is not None and body.status != task.status:
        if body.status not in VALID_TRANSITIONS.get(task.status, set()):
            raise BusinessError(ERR_VALIDATION, f"不允许从 {task.status} 转换到 {body.status}")
        task.status = body.status
    if body.title is not None:
        task.title = body.title
    if body.description is not None:
        task.description = body.description
    await db.commit()
    await db.refresh(task)
    result = task_svc._task_to_dict(task)
    return {"code": 0, "message": "success", "data": result}


@router.post("/{id}/test-records")
async def create_test_record(
    id: int,
    body: dict,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_task(db, id), "task:test")
    from app.models import TestExecutionRound, TestExecutionRecord
    task = await task_svc._get_task_or_fail(db, id)

    round_stmt = select(TestExecutionRound).where(
        TestExecutionRound.task_id == id,
    ).order_by(TestExecutionRound.created_at.desc())
    round_result = await db.execute(round_stmt)
    latest_round = round_result.scalar_one_or_none()
    if latest_round is None:
        latest_round = TestExecutionRound(task_id=id, executed_by=int(user["sub"]))
        db.add(latest_round)
        await db.flush()

    test_case_id = body.get("test_case_id")
    status = body.get("status", "pending")
    actual_result = body.get("actual_result")
    failure_reason = body.get("failure_reason")

    existing_stmt = select(TestExecutionRecord).where(
        TestExecutionRecord.round_id == latest_round.id,
        TestExecutionRecord.test_case_id == test_case_id,
    )
    existing_result = await db.execute(existing_stmt)
    existing_rec = existing_result.scalar_one_or_none()

    if existing_rec:
        existing_rec.status = status
        existing_rec.actual_result = actual_result
        existing_rec.failure_reason = failure_reason
        await db.commit()
        await db.refresh(existing_rec)
        return {"code": 0, "message": "success", "data": {"id": existing_rec.id, "status": existing_rec.status, "round_id": latest_round.id}}

    rec = TestExecutionRecord(
        round_id=latest_round.id,
        test_case_id=test_case_id,
        status=status,
        actual_result=actual_result,
        failure_reason=failure_reason,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(rec)
    return {"code": 0, "message": "success", "data": {"id": rec.id, "status": rec.status, "round_id": latest_round.id}}


@router.post("/{id}/test-rounds")
async def create_test_round(
    id: int,
    body: dict,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_task(db, id), "task:test")
    from app.models import TestExecutionRound, TestExecutionRecord
    from sqlalchemy import select as sel

    task = await task_svc._get_task_or_fail(db, id)

    round_ = TestExecutionRound(task_id=id, executed_by=int(user["sub"]))
    db.add(round_)
    await db.flush()

    test_case_id = body.get("test_case_id")
    status = body.get("status", "pending")
    actual_result = body.get("actual_result")
    failure_reason = body.get("failure_reason")

    rec = TestExecutionRecord(
        round_id=round_.id,
        test_case_id=test_case_id,
        status=status,
        actual_result=actual_result,
        failure_reason=failure_reason,
    )
    db.add(rec)
    await db.commit()
    await db.refresh(round_)
    await db.refresh(rec)
    return {"code": 0, "message": "success", "data": {"id": round_.id, "round_id": round_.id}}


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None


@router.get("/{id}")
async def get_task(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    data = await task_svc.get_task_detail(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.put("/{id}")
async def update_task(
    id: int,
    body: UpdateTaskRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_task(db, id), "task:edit")
    data = await task_svc.update_task(
        db, id,
        title=body.title,
        description=body.description,
        assignee_id=body.assignee_id,
    )
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{id}")
async def delete_task(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_task(db, id), "task:delete")
    data = await task_svc.delete_task(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/start-testing")
async def start_testing(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_task(db, id), "task:test")
    data = await task_svc.start_testing(db, id, user_id=int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/complete")
async def complete_task(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_task(db, id), "task:complete")
    data = await task_svc.complete_task(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/start-coding")
async def start_coding(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_task(db, id), "task:edit")
    data = await task_svc.start_coding(db, id)
    return {"code": 0, "message": "success", "data": data}


class GitInfoRequest(BaseModel):
    git_branch: str | None = None
    commit_sha: str | None = None
    pr_url: str | None = None
    artifact_url: str | None = None
    message: str | None = None
    author: str | None = None
    committed_at: str | None = None


@router.patch("/{id}/git-info")
async def update_git_info(
    id: int,
    body: GitInfoRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_task(db, id), "task:edit")
    data = await task_svc.update_git_info(db, id, **body.model_dump(exclude_none=True))

    if body.commit_sha:
        try:
            await tc_svc.add_commit(
                db, id,
                commit_sha=body.commit_sha,
                message=body.message,
                author=body.author,
                committed_at=body.committed_at,
            )
        except BusinessError:
            pass

    return {"code": 0, "message": "success", "data": data}


class AddCommitRequest(BaseModel):
    commit_sha: str
    message: str | None = None
    author: str | None = None
    committed_at: str | None = None


@router.post("/{id}/commits")
async def add_task_commit(
    id: int,
    body: AddCommitRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_task(db, id), "task:edit")
    data = await tc_svc.add_commit(
        db, id,
        commit_sha=body.commit_sha,
        message=body.message,
        author=body.author,
        committed_at=body.committed_at,
    )
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}/commits")
async def list_task_commits(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    data = await tc_svc.list_task_commits(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{taskId}/test-executions")
async def get_task_test_executions(
    taskId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    data = await list_execution_rounds(db, taskId)
    return {"code": 0, "message": "success", "data": data}
