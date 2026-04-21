from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_current_user, get_db_session, require_permission
from app.services.test_execution import get_execution_records, update_execution_record

router = APIRouter()


class UpdateExecutionRecordRequest(BaseModel):
    status: str
    actual_result: str | None = None
    failure_reason: str | None = None


@router.get("/{roundId}/records")
async def get_records(
    roundId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated = Depends(get_db_session),
) -> dict:
    data = await get_execution_records(db, roundId)
    return {"code": 0, "message": "success", "data": data}


records_router = APIRouter()


@records_router.put("/{id}")
async def update_record(
    id: int,
    body: UpdateExecutionRecordRequest,
    user: Annotated[dict, Depends(require_permission("task:test"))],
    db: Annotated = Depends(get_db_session),
) -> dict:
    data = await update_execution_record(
        db, id,
        status=body.status,
        actual_result=body.actual_result,
        failure_reason=body.failure_reason,
    )
    return {"code": 0, "message": "success", "data": data}
