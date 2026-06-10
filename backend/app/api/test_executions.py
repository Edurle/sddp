from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_current_user, get_db_session, check_team_permission, _team_id_from_execution_record, _team_id_from_execution_round
from app.services.test_execution import (
    batch_update_records,
    get_execution_records,
    update_execution_record,
)

router = APIRouter()


class UpdateExecutionRecordRequest(BaseModel):
    status: str
    actual_result: str | None = None
    failure_reason: str | None = None
    log_output: str | None = None
    duration_ms: int | None = None


class BatchRecordItem(BaseModel):
    test_case_id: int
    status: str
    actual_result: str | None = None
    failure_reason: str | None = None
    log_output: str | None = None
    duration_ms: int | None = None


class BatchUpdateRequest(BaseModel):
    records: list[BatchRecordItem]


@router.get("/{roundId}/records")
async def get_records(
    roundId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated = Depends(get_db_session),
) -> dict:
    data = await get_execution_records(db, roundId)
    return {"code": 0, "message": "success", "data": data}


@router.put("/{roundId}/batch")
async def batch_update(
    roundId: int,
    body: BatchUpdateRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated = Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_execution_round(db, roundId), "task:test")
    data = await batch_update_records(db, roundId, body.records)
    return {"code": 0, "message": "success", "data": data}


records_router = APIRouter()


@records_router.put("/{id}")
async def update_record(
    id: int,
    body: UpdateExecutionRecordRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated = Depends(get_db_session),
) -> dict:
    await check_team_permission(db, user, await _team_id_from_execution_record(db, id), "task:test")
    data = await update_execution_record(
        db, id,
        status=body.status,
        actual_result=body.actual_result,
        failure_reason=body.failure_reason,
        log_output=body.log_output,
        duration_ms=body.duration_ms,
    )
    return {"code": 0, "message": "success", "data": data}
