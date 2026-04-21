from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_current_user, get_db_session
from app.services import test_case as tc_svc

router = APIRouter()


class DirectCreateTestCaseRequest(BaseModel):
    title: str
    case_type: str
    requirement_id: int
    precondition: str | None = None
    steps: str | None = None
    expected: str | None = None
    related_api: str | None = None
    related_element: str | None = None


@router.post("")
async def direct_create_test_case(
    body: DirectCreateTestCaseRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    from app.models import TestCase as TCModel
    from sqlalchemy import func, select

    if not body.title or not body.title.strip():
        from app.exceptions import BusinessError, ERR_VALIDATION
        raise BusinessError(ERR_VALIDATION, "用例标题不能为空")

    count_stmt = select(func.count()).select_from(TCModel)
    count_result = await db.execute(count_stmt)
    count = count_result.scalar_one()
    case_number = f"TC-{count + 1}"

    tc = TCModel(
        requirement_id=body.requirement_id,
        case_number=case_number,
        title=body.title,
        case_type=body.case_type,
        precondition=body.precondition or "",
        steps=body.steps or "",
        expected_result=body.expected or "",
        related_api=body.related_api,
        related_element=body.related_element,
    )
    db.add(tc)
    await db.commit()
    await db.refresh(tc)
    data = {
        "id": tc.id,
        "requirement_id": tc.requirement_id,
        "case_number": tc.case_number,
        "title": tc.title,
        "case_type": tc.case_type,
        "precondition": tc.precondition,
        "steps": tc.steps,
        "expected_result": tc.expected_result,
        "related_api": tc.related_api,
        "related_element": tc.related_element,
        "created_at": tc.created_at.isoformat() if tc.created_at else None,
    }
    return {"code": 0, "message": "success", "data": data, **data}


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
    user: Annotated[dict, Depends(get_current_user)],
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
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated = Depends(get_db_session),
) -> dict:
    data = await tc_svc.delete_test_case(db, id)
    return {"code": 0, "message": "success", "data": data}
