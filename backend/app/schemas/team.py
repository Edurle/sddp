from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ApiResponse


class TeamBriefResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TeamCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=500)


class TeamUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=64)
    description: str | None = Field(default=None, max_length=500)


class OwnerBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str


class TeamDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None
    owner: OwnerBrief
    member_count: int
    created_at: datetime


class RoleBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    nickname: str
    email: str
    avatar: str | None = None
    roles: list[RoleBrief] = []
    joined_at: datetime


class TransferRequest(BaseModel):
    new_owner_id: int
