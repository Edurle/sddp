from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.team import OwnerBrief


class InviteRequest(BaseModel):
    identifier: str


class InviteActionRequest(BaseModel):
    action: str = Field(pattern=r"^(accept|reject)$")


class InviteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    team_id: int
    team_name: str
    inviter: OwnerBrief
    created_at: datetime


class InviteResult(BaseModel):
    invitation_id: int
    user_id: int
    nickname: str
