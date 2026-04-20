from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class IterationCreateRequest(BaseModel):
    name: str
    goal: str
    start_date: date
    end_date: date


class IterationUpdateRequest(BaseModel):
    name: str | None = None
    goal: str | None = None
    end_date: date | None = None


class ProjectBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class IterationStatistics(BaseModel):
    total_requirements: int = 0
    approved_requirements: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    test_pass_rate: float = 0.0


class IterationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    goal: str
    start_date: date
    end_date: date
    status: str
    requirement_count: int = 0
    task_count: int = 0
    created_at: datetime


class IterationDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    goal: str
    start_date: date
    end_date: date
    status: str
    project: ProjectBrief
    statistics: IterationStatistics
    created_at: datetime


class KanbanRequirementItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    req_type: str
    priority: int = 0
    created_by: dict


class KanbanColumn(BaseModel):
    status: str
    display_name: str
    requirements: list[KanbanRequirementItem] = []


class KanbanResponse(BaseModel):
    columns: list[KanbanColumn] = []
