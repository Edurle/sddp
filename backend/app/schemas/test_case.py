from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TestCaseCreateRequest(BaseModel):
    title: str
    case_type: str
    precondition: str
    steps: str
    expected_result: str
    related_api: str | None = None
    related_element: str | None = None


class TestCaseUpdateRequest(BaseModel):
    title: str | None = None
    case_type: str | None = None
    precondition: str | None = None
    steps: str | None = None
    expected_result: str | None = None
    related_api: str | None = None
    related_element: str | None = None


class TestCaseListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    title: str
    case_type: str
    precondition: str
    steps: str
    expected_result: str
    related_api: str | None = None
    related_element: str | None = None
    created_at: datetime


class TestCaseBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    title: str
    case_type: str
