from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SpecFieldDefinition(BaseModel):
    name: str
    display_name: str
    type: str
    required: bool = True
    description: str | None = None


class SpecSectionDefinition(BaseModel):
    name: str
    display_name: str
    required: bool = True
    fields: list[SpecFieldDefinition] = []


class SpecTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    team_id: int
    sections: list[SpecSectionDefinition] = []
    updated_at: datetime


class SpecTemplateUpdateRequest(BaseModel):
    sections: list[SpecSectionDefinition]


class SpecDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    requirement_id: int
    current_version: int
    content: dict
    updated_at: datetime


class SpecContentUpdateRequest(BaseModel):
    content: dict


class SpecVersionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version: int
    created_by: dict
    created_at: datetime


class SpecVersionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    version: int
    content: dict
    created_by: dict
    created_at: datetime
