from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.team import TeamBriefResponse


class ProjectCreateRequest(BaseModel):
    name: str
    description: str | None = None
    start_date: date | None = None


class ProjectUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    start_date: date | None = None


class ActiveIteration(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    status: str


class ProjectListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str
    active_iteration: ActiveIteration | None = None
    created_at: datetime


class ProjectStatistics(BaseModel):
    total_requirements: int = 0
    completed_requirements: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    test_pass_rate: float = 0.0


class ProjectDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: str
    team: TeamBriefResponse
    statistics: ProjectStatistics
