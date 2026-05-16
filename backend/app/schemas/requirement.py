from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RequirementCreateRequest(BaseModel):
    title: str
    req_type: str
    priority: int = 0
    description: str
    type_detail: dict | None = None
    prototype_html: str | None = None


class RequirementUpdateRequest(BaseModel):
    title: str | None = None
    req_type: str | None = None
    priority: str | None = None
    description: str | None = None
    type_detail: dict | None = None
    prototype_html: str | None = None


class RequirementUpdateRequest(BaseModel):
    title: str | None = None
    req_type: str | None = None
    priority: int | None = None
    description: str | None = None
    type_detail: dict | None = None


class UserBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str


class RequirementListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    req_type: str
    priority: int = 0
    status: str
    task_count: int = 0
    created_by: UserBrief
    created_at: datetime


class IterationBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    review_type: str
    reviewer: UserBrief
    status: str
    comment: str | None = None
    created_at: datetime
    reviewed_at: datetime | None = None


class TaskBriefInRequirement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    assignee: UserBrief | None = None
    status: str


class RequirementDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    req_type: str
    priority: int = 0
    status: str
    description: str
    type_detail: dict | None = None
    prototype_html: str | None = None
    iteration: IterationBrief
    created_by: UserBrief
    current_step: str
    reviews: list[ReviewResponse] = []
    tasks: list[TaskBriefInRequirement] = []
    created_at: datetime
    updated_at: datetime


class ReviewSubmitRequest(BaseModel):
    reviewer_id: int


class ReviewActionRequest(BaseModel):
    action: str = Field(pattern=r"^(approve|reject)$")
    comment: str | None = None
