from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_current_user, require_permission

router = APIRouter()


class UpdateTaskRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None


@router.get("/{id}")
async def get_task(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/{id}")
async def update_task(
    id: int,
    body: UpdateTaskRequest,
    user: Annotated[dict, Depends(require_permission("task:edit"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.delete("/{id}")
async def delete_task(
    id: int,
    user: Annotated[dict, Depends(require_permission("task:delete"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/{id}/start-testing")
async def start_testing(
    id: int,
    user: Annotated[dict, Depends(require_permission("task:test"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/{id}/complete")
async def complete_task(
    id: int,
    user: Annotated[dict, Depends(require_permission("task:complete"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{taskId}/test-executions")
async def get_task_test_executions(
    taskId: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")
