from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.deps import get_current_user, get_db_session, check_team_permission, _team_id_from_project
from app.services import project as project_service

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
    db=Depends(get_db_session),
) -> dict:
    data = await project_service.list_team_projects(db, teamId, int(user["sub"]), status)
    return {"code": 0, "message": "success", "data": data}


@teams_nested_router.post("/{teamId}/projects")
async def create_team_project(
    teamId: int,
    body: CreateProjectRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, teamId, "project:create")
    data = await project_service.create_project(
        db, teamId, int(user["sub"]), body.name, body.description, body.start_date
    )
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}")
async def get_project(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    data = await project_service.get_project_detail(db, id, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.put("/{id}")
async def update_project(
    id: int,
    body: UpdateProjectRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_project(db, id), "project:edit")
    data = await project_service.update_project(
        db, id, int(user["sub"]), body.name, body.description, body.start_date
    )
    return {"code": 0, "message": "success", "data": data}


@router.put("/{id}/archive")
async def archive_project(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_project(db, id), "project:archive")
    data = await project_service.archive_project(db, id, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{id}")
async def delete_project(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_project(db, id), "project:delete")
    data = await project_service.delete_project(db, id, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}/test-statistics")
async def get_project_test_statistics(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    data = await project_service.get_project_test_statistics(db, id, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}
