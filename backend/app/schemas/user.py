from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.schemas.common import ApiResponse


class TeamBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    role_names: list[str] = []


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nickname: str
    avatar: str | None = None
    is_admin: bool = False
    teams: list[TeamBrief] = []


class UserUpdateRequest(BaseModel):
    nickname: str | None = Field(default=None, min_length=2, max_length=32)
    avatar: str | None = None

    @model_validator(mode="after")
    def at_least_one_field(self) -> "UserUpdateRequest":
        if self.nickname is None and self.avatar is None:
            raise ValueError("At least one of nickname or avatar must be provided")
        return self


class PasswordChangeRequest(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=64)


class PendingReviewItem(BaseModel):
    id: int
    type: str
    title: str
    review_type: str
    project_name: str
    created_at: datetime


class PendingTaskItem(BaseModel):
    id: int
    title: str
    project_name: str
    iteration_name: str
    status: str
    due_date: datetime | None = None


class PendingInvitationItem(BaseModel):
    id: int
    team_id: int
    team_name: str
    inviter: dict
    created_at: datetime


class PendingItemsResponse(BaseModel):
    pending_reviews: list[PendingReviewItem] = []
    pending_tasks: list[PendingTaskItem] = []
    pending_invitations: list[PendingInvitationItem] = []


class AdminUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nickname: str
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime


class AdminUserCreateRequest(BaseModel):
    email: EmailStr
    nickname: str = Field(min_length=2, max_length=32)
    password: str = Field(min_length=8, max_length=64)


class AdminUserStatusRequest(BaseModel):
    is_active: bool
