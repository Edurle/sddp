from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import require_permission

router = APIRouter()


class UpdateTestCaseRequest(BaseModel):
    title: str | None = None
    case_type: str | None = None
    precondition: str | None = None
    steps: str | None = None
    expected_result: str | None = None
    related_api: str | None = None
    related_element: str | None = None


@router.put("/{id}")
async def update_test_case(
    id: int,
    body: UpdateTestCaseRequest,
    user: Annotated[dict, Depends(require_permission("requirement:edit"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.delete("/{id}")
async def delete_test_case(
    id: int,
    user: Annotated[dict, Depends(require_permission("requirement:delete"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")
