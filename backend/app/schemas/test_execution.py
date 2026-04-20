from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.requirement import UserBrief
from app.schemas.test_case import TestCaseBrief


class ExecutionRoundListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    round_id: int
    executed_by: UserBrief
    total: int
    passed: int
    failed: int
    skipped: int
    created_at: datetime


class ExecutionRecordItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_case: TestCaseBrief
    status: str
    actual_result: str | None = None
    failure_reason: str | None = None
    executed_at: datetime | None = None


class ExecutionRecordUpdate(BaseModel):
    status: str = Field(pattern=r"^(passed|failed|skipped)$")
    actual_result: str | None = None
    failure_reason: str | None = None


class RequirementTestStatistics(BaseModel):
    total_cases: int = 0
    latest_results: dict = {}
    pass_rate: float = 0.0


class IterationTestStatItem(BaseModel):
    requirement_id: int
    requirement_title: str
    total_cases: int = 0
    latest_passed: int = 0
    latest_failed: int = 0


class IterationTestStatistics(BaseModel):
    total_cases: int = 0
    latest_pass_rate: float = 0.0
    by_requirement: list[IterationTestStatItem] = []


class ProjectIterationTestStat(BaseModel):
    iteration_id: int
    iteration_name: str
    total_cases: int = 0
    pass_rate: float = 0.0


class ProjectTestStatistics(BaseModel):
    iterations: list[ProjectIterationTestStat] = []
