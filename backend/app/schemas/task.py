from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.requirement import UserBrief
from app.schemas.test_case import TestCaseBrief


class TaskCreateRequest(BaseModel):
    title: str
    description: str
    assignee_id: int | None = None


class TaskUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    assignee_id: int | None = None


class TaskListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    assignee: UserBrief | None = None
    status: str
    created_at: datetime


class TaskRequirementBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    specification: dict | None = None


class TestExecutionBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    round_id: int
    total: int
    passed: int
    failed: int
    skipped: int


class TaskDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    status: str
    assignee: UserBrief | None = None
    requirement: TaskRequirementBrief
    test_cases: list[TestCaseBrief] = []
    latest_execution: TestExecutionBrief | None = None
    created_by: UserBrief
    created_at: datetime
    updated_at: datetime
