from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.deps import get_current_user, get_db_session, require_permission
from app.services import iteration as iteration_service

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
    start_date: str | None = None


projects_nested_router = APIRouter()


@projects_nested_router.get("/{projectId}/iterations")
async def list_project_iterations(
    projectId: int,
    user: Annotated[dict, Depends(get_current_user)],
    status: str | None = Query(default=None),
    db=Depends(get_db_session),
) -> dict:
    data = await iteration_service.list_iterations(
        db, projectId, int(user["sub"]), status
    )
    return {"code": 0, "message": "ok", "data": data}


@projects_nested_router.post("/{projectId}/iterations")
async def create_project_iteration(
    projectId: int,
    body: CreateIterationRequest,
    user: Annotated[dict, Depends(require_permission("iteration:create"))],
    db=Depends(get_db_session),
) -> dict:
    data = await iteration_service.create_iteration(
        db,
        projectId,
        int(user["sub"]),
        body.name,
        body.goal,
        body.start_date,
        body.end_date,
    )
    return {"code": 0, "message": "ok", "data": data}


@router.get("/{id}")
async def get_iteration(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    data = await iteration_service.get_iteration_detail(db, id, int(user["sub"]))
    return {"code": 0, "message": "ok", "data": data}


@router.put("/{id}")
async def update_iteration(
    id: int,
    body: UpdateIterationRequest,
    user: Annotated[dict, Depends(require_permission("iteration:edit"))],
    db=Depends(get_db_session),
) -> dict:
    data = await iteration_service.update_iteration(
        db,
        id,
        int(user["sub"]),
        body.name,
        body.goal,
        body.end_date,
        body.start_date,
    )
    return {"code": 0, "message": "ok", "data": data}


@router.post("/{id}/start")
async def start_iteration(
    id: int,
    user: Annotated[dict, Depends(require_permission("iteration:start"))],
    db=Depends(get_db_session),
) -> dict:
    data = await iteration_service.start_iteration(db, id, int(user["sub"]))
    return {"code": 0, "message": "ok", "data": data}


@router.post("/{id}/complete")
async def complete_iteration(
    id: int,
    user: Annotated[dict, Depends(require_permission("iteration:complete"))],
    db=Depends(get_db_session),
) -> dict:
    data = await iteration_service.complete_iteration(db, id, int(user["sub"]))
    return {"code": 0, "message": "ok", "data": data}


@router.get("/{id}/kanban")
async def get_iteration_kanban(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    data = await iteration_service.get_iteration_kanban(db, id, int(user["sub"]))
    return {"code": 0, "message": "ok", "data": data}


@router.get("/{id}/statistics")
async def get_iteration_statistics(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    data = await iteration_service.get_iteration_statistics_detail(
        db, id, int(user["sub"])
    )
    return {"code": 0, "message": "ok", "data": data}


@router.get("/{id}/test-statistics")
async def get_iteration_test_statistics(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    data = await iteration_service.get_iteration_test_statistics(
        db, id, int(user["sub"])
    )
    return {"code": 0, "message": "ok", "data": data}
