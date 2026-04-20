from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel

from app.deps import get_current_user, require_permission

router = APIRouter()


class CreateTeamRequest(BaseModel):
    name: str
    description: str | None = None


class UpdateTeamRequest(BaseModel):
    name: str | None = None
    description: str | None = None


class TransferTeamRequest(BaseModel):
    new_owner_id: int


class InviteMemberRequest(BaseModel):
    identifier: str


class AssignRolesRequest(BaseModel):
    role_ids: list[int]


class CreateRoleRequest(BaseModel):
    name: str
    description: str | None = None
    permissions: list[str]


class UpdateRoleRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    permissions: list[str] | None = None


class UpdateSpecTemplateRequest(BaseModel):
    sections: list[dict]


@router.post("/")
async def create_team(
    body: CreateTeamRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{id}")
async def get_team(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/{id}")
async def update_team(
    id: int,
    body: UpdateTeamRequest,
    user: Annotated[dict, Depends(require_permission("member:assign_role"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.delete("/{id}")
async def dissolve_team(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    x_confirm_delete: Annotated[str, Header()],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/{id}/transfer")
async def transfer_team(
    id: int,
    body: TransferTeamRequest,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{id}/members")
async def get_team_members(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    role_id: int | None = Query(default=None),
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/{id}/invitations")
async def invite_member(
    id: int,
    body: InviteMemberRequest,
    user: Annotated[dict, Depends(require_permission("member:invite"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.delete("/{teamId}/members/{userId}")
async def remove_member(
    teamId: int,
    userId: int,
    user: Annotated[dict, Depends(require_permission("member:remove"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/{teamId}/members/{userId}/roles")
async def assign_roles(
    teamId: int,
    userId: int,
    body: AssignRolesRequest,
    user: Annotated[dict, Depends(require_permission("member:assign_role"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{teamId}/roles")
async def list_roles(
    teamId: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.post("/{teamId}/roles")
async def create_role(
    teamId: int,
    body: CreateRoleRequest,
    user: Annotated[dict, Depends(require_permission("member:assign_role"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/{teamId}/roles/{roleId}")
async def update_role(
    teamId: int,
    roleId: int,
    body: UpdateRoleRequest,
    user: Annotated[dict, Depends(require_permission("member:assign_role"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.delete("/{teamId}/roles/{roleId}")
async def delete_role(
    teamId: int,
    roleId: int,
    user: Annotated[dict, Depends(require_permission("member:assign_role"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.get("/{teamId}/spec-template")
async def get_spec_template(
    teamId: int,
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    raise NotImplementedError("Not implemented yet")


@router.put("/{teamId}/spec-template")
async def update_spec_template(
    teamId: int,
    body: UpdateSpecTemplateRequest,
    user: Annotated[dict, Depends(require_permission("spec_template:edit"))],
) -> dict:
    raise NotImplementedError("Not implemented yet")
