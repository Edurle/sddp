from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.deps import get_current_user, require_permission

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
    status: str | None = Query(default=None),
    req_type: str | None = Query(default=None),
    sort_by: str | None = Query(default=None),
    sort_order: str | None = Query(default=None),
) -> dict:
    raise NotImplementedError("Not implemented yet")


@iterations_nested_router.post("/{iterationId}/requirements")
async def create_iteration_requirement(
    iterationId: int,
    body: CreateRequirementRequest,
    user: Annotated[dict, Depends(require_permission("requirement:create"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{id}")
async def get_requirement(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/{id}")
async def update_requirement(
    id: int,
    body: UpdateRequirementRequest,
    user: Annotated[dict, Depends(require_permission("requirement:edit"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.delete("/{id}")
async def delete_requirement(
    id: int,
    user: Annotated[dict, Depends(require_permission("requirement:delete"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/{id}/submit-review")
async def submit_review(
    id: int,
    body: SubmitReviewRequest,
    user: Annotated[dict, Depends(require_permission("requirement:edit"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/{id}/review")
async def review_requirement(
    id: int,
    body: ReviewRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{id}/test-statistics")
async def get_requirement_test_statistics(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{reqId}/test-cases")
async def list_test_cases(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    case_type: str | None = Query(default=None),
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/{reqId}/test-cases")
async def create_test_case(
    reqId: int,
    body: CreateTestCaseRequest,
    user: Annotated[dict, Depends(require_permission("requirement:edit"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{reqId}/tasks")
async def list_tasks(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    status: str | None = Query(default=None),
    assignee_id: int | None = Query(default=None),
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/{reqId}/tasks")
async def create_task(
    reqId: int,
    body: CreateTaskRequest,
    user: Annotated[dict, Depends(require_permission("task:create"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{reqId}/specification")
async def get_specification(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/{reqId}/specification")
async def update_specification(
    reqId: int,
    body: UpdateSpecificationRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{reqId}/specification/versions")
async def list_specification_versions(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{reqId}/specification/versions/{version}")
async def get_specification_version(
    reqId: int,
    version: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")
