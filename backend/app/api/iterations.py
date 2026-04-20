from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.deps import get_current_user, require_permission

router = APIRouter()


class CreateIterationRequest(BaseModel):
    name: str
    goal: str | None = None
    start_date: str
    end_date: str


class UpdateIterationRequest(BaseModel):
    name: str | None = None
    goal: str | None = None
    end_date: str | None = None


projects_nested_router = APIRouter()


@projects_nested_router.get("/{projectId}/iterations")
async def list_project_iterations(
    projectId: int,
    user: Annotated[dict, Depends(get_current_user)],
    status: str | None = Query(default=None),
) -> dict:
    raise NotImplementedError("Not implemented yet")


@projects_nested_router.post("/{projectId}/iterations")
async def create_project_iteration(
    projectId: int,
    body: CreateIterationRequest,
    user: Annotated[dict, Depends(require_permission("iteration:create"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{id}")
async def get_iteration(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/{id}")
async def update_iteration(
    id: int,
    body: UpdateIterationRequest,
    user: Annotated[dict, Depends(require_permission("iteration:edit"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/{id}/start")
async def start_iteration(
    id: int,
    user: Annotated[dict, Depends(require_permission("iteration:start"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/{id}/complete")
async def complete_iteration(
    id: int,
    user: Annotated[dict, Depends(require_permission("iteration:complete"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{id}/kanban")
async def get_iteration_kanban(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{id}/statistics")
async def get_iteration_statistics(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{id}/test-statistics")
async def get_iteration_test_statistics(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")
