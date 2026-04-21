from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_db_session, require_permission
from app.services import test_case as tc_svc

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
    db: Annotated = Depends(get_db_session),
) -> dict:
    data = await tc_svc.update_test_case(
        db, id,
        title=body.title,
        case_type=body.case_type,
        precondition=body.precondition,
        steps=body.steps,
        expected_result=body.expected_result,
        related_api=body.related_api,
        related_element=body.related_element,
    )
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{id}")
async def delete_test_case(
    id: int,
    user: Annotated[dict, Depends(require_permission("requirement:delete"))],
    db: Annotated = Depends(get_db_session),
) -> dict:
    data = await tc_svc.delete_test_case(db, id)
    return {"code": 0, "message": "success", "data": data}
