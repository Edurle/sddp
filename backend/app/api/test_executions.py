from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.deps import get_current_user, require_permission

router = APIRouter()


class UpdateExecutionRecordRequest(BaseModel):
    status: str
    actual_result: str | None = None
    failure_reason: str | None = None


@router.get("/{roundId}/records")
async def get_execution_records(
    roundId: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


records_router = APIRouter()


@records_router.put("/{id}")
async def update_execution_record(
    id: int,
    body: UpdateExecutionRecordRequest,
    user: Annotated[dict, Depends(require_permission("task:test"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")
