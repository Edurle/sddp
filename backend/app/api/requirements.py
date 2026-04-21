from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db_session, require_permission
from app.services import requirement as req_svc
from app.services import specification as spec_svc
from app.services import task as task_svc
from app.services import test_case as tc_svc
from app.services.statistics import get_requirement_test_statistics

router = APIRouter()


class CreateRequirementRequest(BaseModel):
    title: str
    req_type: str
    priority: int
    description: str | None = None
    type_detail: dict | None = None


class UpdateRequirementRequest(BaseModel):
    title: str | None = None
    req_type: str | None = None
    priority: int | None = None
    description: str | None = None
    type_detail: dict | None = None


class SubmitReviewRequest(BaseModel):
    reviewer_id: int


class ReviewRequest(BaseModel):
    action: str
    comment: str | None = None


class CreateTaskRequest(BaseModel):
    title: str
    description: str | None = None
    assignee_id: int | None = None


class CreateTestCaseRequest(BaseModel):
    title: str
    case_type: str
    precondition: str | None = None
    steps: str | None = None
    expected_result: str | None = None
    related_api: str | None = None
    related_element: str | None = None


class UpdateSpecificationRequest(BaseModel):
    content: dict


iterations_nested_router = APIRouter()


@iterations_nested_router.get("/{iterationId}/requirements")
async def list_iteration_requirements(
    iterationId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(default=None),
    req_type: str | None = Query(default=None),
    sort_by: str | None = Query(default=None),
    sort_order: str | None = Query(default=None),
) -> dict:
    data = await req_svc.list_requirements(
        db, iterationId, int(user["sub"]), status, req_type, sort_by, sort_order
    )
    return {"code": 0, "message": "success", "data": data}


@iterations_nested_router.post("/{iterationId}/requirements")
async def create_iteration_requirement(
    iterationId: int,
    body: CreateRequirementRequest,
    user: Annotated[dict, Depends(require_permission("requirement:create"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await req_svc.create_requirement(
        db, iterationId, int(user["sub"]),
        body.title, body.req_type, body.priority,
        body.description, body.type_detail,
    )
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}")
async def get_requirement(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await req_svc.get_requirement_detail(db, id, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.put("/{id}")
async def update_requirement(
    id: int,
    body: UpdateRequirementRequest,
    user: Annotated[dict, Depends(require_permission("requirement:edit"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await req_svc.update_requirement(
        db, id, int(user["sub"]),
        body.title, body.req_type, body.priority,
        body.description, body.type_detail,
    )
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{id}")
async def delete_requirement(
    id: int,
    user: Annotated[dict, Depends(require_permission("requirement:delete"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await req_svc.delete_requirement(db, id, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/submit-review")
async def submit_review(
    id: int,
    body: SubmitReviewRequest,
    user: Annotated[dict, Depends(require_permission("requirement:edit"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await req_svc.submit_review(db, id, int(user["sub"]), body.reviewer_id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/review")
async def review_requirement(
    id: int,
    body: ReviewRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await req_svc.review_requirement(
        db, id, int(user["sub"]), body.action, body.comment,
        user.get("permissions", []),
    )
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}/test-statistics")
async def get_req_test_stats(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await get_requirement_test_statistics(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{reqId}/test-cases")
async def list_test_cases(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    case_type: str | None = Query(default=None),
) -> dict:
    data = await tc_svc.list_test_cases(db, reqId, case_type=case_type)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{reqId}/test-cases")
async def create_test_case(
    reqId: int,
    body: CreateTestCaseRequest,
    user: Annotated[dict, Depends(require_permission("requirement:edit"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await tc_svc.create_test_case(
        db, reqId,
        title=body.title,
        case_type=body.case_type,
        precondition=body.precondition,
        steps=body.steps,
        expected_result=body.expected_result,
        related_api=body.related_api,
        related_element=body.related_element,
    )
    return {"code": 0, "message": "success", "data": data}


@router.get("/{reqId}/tasks")
async def list_tasks(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(default=None),
    assignee_id: int | None = Query(default=None),
) -> dict:
    data = await task_svc.list_tasks(db, reqId, status=status, assignee_id=assignee_id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{reqId}/tasks")
async def create_task(
    reqId: int,
    body: CreateTaskRequest,
    user: Annotated[dict, Depends(require_permission("task:create"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await task_svc.create_task(
        db, reqId, int(user["sub"]),
        title=body.title,
        description=body.description,
        assignee_id=body.assignee_id,
    )
    return {"code": 0, "message": "success", "data": data}


@router.get("/{reqId}/specification")
async def get_specification(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await spec_svc.get_spec_document(db, reqId)
    return {"code": 0, "message": "success", "data": data}


@router.put("/{reqId}/specification")
async def update_specification(
    reqId: int,
    body: UpdateSpecificationRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await spec_svc.save_spec_document(db, reqId, int(user["sub"]), body.content)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{reqId}/specification/versions")
async def list_specification_versions(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await spec_svc.list_spec_versions(db, reqId)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{reqId}/specification/versions/{version}")
async def get_specification_version(
    reqId: int,
    version: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await spec_svc.get_spec_version_detail(db, reqId, version)
    return {"code": 0, "message": "success", "data": data}
