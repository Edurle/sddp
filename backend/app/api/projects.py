from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.deps import get_current_user, require_permission

router = APIRouter()


class CreateProjectRequest(BaseModel):
    name: str
    description: str | None = None
    start_date: str | None = None


class UpdateProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    start_date: str | None = None


teams_nested_router = APIRouter()


@teams_nested_router.get("/{teamId}/projects")
async def list_team_projects(
    teamId: int,
    user: Annotated[dict, Depends(get_current_user)],
    status: str | None = Query(default=None),
) -> dict:
    raise NotImplementedError("Not implemented yet")


@teams_nested_router.post("/{teamId}/projects")
async def create_team_project(
    teamId: int,
    body: CreateProjectRequest,
    user: Annotated[dict, Depends(require_permission("project:create"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{id}")
async def get_project(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/{id}")
async def update_project(
    id: int,
    body: UpdateProjectRequest,
    user: Annotated[dict, Depends(require_permission("project:edit"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/{id}/archive")
async def archive_project(
    id: int,
    user: Annotated[dict, Depends(require_permission("project:archive"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.delete("/{id}")
async def delete_project(
    id: int,
    user: Annotated[dict, Depends(require_permission("project:delete"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{id}/test-statistics")
async def get_project_test_statistics(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")
