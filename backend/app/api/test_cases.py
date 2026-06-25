from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_current_user, get_db_session, check_team_permission, _team_id_from_requirement, _team_id_from_test_case
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
    await check_team_permission(db, user, await _team_id_from_requirement(db, body.requirement_id), "test_case:create")
    data = await tc_svc.create_test_case(
        db, body.requirement_id,
        title=body.title,
        case_type=body.case_type,
        precondition=body.precondition,
        steps=body.steps,
        expected_result=body.expected,
        related_api=body.related_api,
        related_element=body.related_element,
    )
    return {"code": 0, "message": "success", "data": data}


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
    await check_team_permission(db, user, await _team_id_from_test_case(db, id), "test_case:edit")
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
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_test_case(db, id), "test_case:delete")
    data = await tc_svc.delete_test_case(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/deprecate")
async def deprecate_test_case(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_test_case(db, id), "test_case:edit")
    data = await tc_svc.deprecate_test_case(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/requirement/{requirement_id}/execution-results")
async def get_test_case_execution_results(
    requirement_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db=Depends(get_db_session),
) -> dict:
    from sqlalchemy import select
    from app.models import TestCase as TCModel, TestExecutionRecord, TestExecutionRound

    tc_stmt = select(TCModel).where(
        TCModel.requirement_id == requirement_id,
        TCModel.is_deleted == False,
        TCModel.status != "deprecated",
    ).order_by(TCModel.id)
    tc_result = await db.execute(tc_stmt)
    test_cases = tc_result.scalars().all()

    items = []
    for tc in test_cases:
        rec_stmt = (
            select(TestExecutionRecord)
            .where(TestExecutionRecord.test_case_id == tc.id)
            .order_by(TestExecutionRecord.executed_at.desc())
        )
        rec_result = await db.execute(rec_stmt)
        records = rec_result.scalars().all()

        latest = None
        all_records = []
        for rec in records:
            round_stmt = select(TestExecutionRound).where(TestExecutionRound.id == rec.round_id)
            round_result = await db.execute(round_stmt)
            rnd = round_result.scalar_one_or_none()

            rec_data = {
                "id": rec.id,
                "status": rec.status,
                "actual_result": rec.actual_result,
                "failure_reason": rec.failure_reason,
                "log_output": rec.log_output,
                "duration_ms": rec.duration_ms,
                "executed_at": rec.executed_at.isoformat() if rec.executed_at else None,
                "round_id": rec.round_id,
                "executed_by": rnd.executed_by if rnd else None,
            }
            all_records.append(rec_data)
            if latest is None:
                latest = rec_data

        items.append({
            "test_case_id": tc.id,
            "title": tc.title,
            "latest_result": latest,
            "execution_count": len(all_records),
            "all_results": all_records,
        })

    return {"code": 0, "message": "success", "data": items}
