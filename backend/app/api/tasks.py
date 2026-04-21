from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_current_user, get_db_session, require_permission
from app.services import task as task_svc
from app.services.test_execution import list_execution_rounds

router = APIRouter()


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
    user: Annotated[dict, Depends(require_permission("task:edit"))],
    db=Depends(get_db_session),
) -> dict:
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
    user: Annotated[dict, Depends(require_permission("task:delete"))],
    db=Depends(get_db_session),
) -> dict:
    data = await task_svc.delete_task(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/start-testing")
async def start_testing(
    id: int,
    user: Annotated[dict, Depends(require_permission("task:test"))],
    db=Depends(get_db_session),
) -> dict:
    data = await task_svc.start_testing(db, id, user_id=int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/complete")
async def complete_task(
    id: int,
    user: Annotated[dict, Depends(require_permission("task:complete"))],
    db=Depends(get_db_session),
) -> dict:
    data = await task_svc.complete_task(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{taskId}/test-executions")
async def get_task_test_executions(
    taskId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    data = await list_execution_rounds(db, taskId)
    return {"code": 0, "message": "success", "data": data}
