from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db_session, require_permission
from app.services import team as team_svc
from app.services import role as role_svc
from app.services import specification as spec_svc

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
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    if not body.name or body.name.strip() == "":
        from app.exceptions import BusinessError, ERR_VALIDATION
        raise BusinessError(ERR_VALIDATION, "团队名称不能为空")
    data = await team_svc.create_team(db, int(user["sub"]), body.name, body.description)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}")
async def get_team(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await team_svc.get_team(db, id, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.put("/{id}")
async def update_team(
    id: int,
    body: UpdateTeamRequest,
    user: Annotated[dict, Depends(require_permission("member:assign_role"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await team_svc.update_team(db, id, body.name, body.description)
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{id}")
async def dissolve_team(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    x_confirm_delete: Annotated[str, Header()],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await team_svc.dissolve_team(db, id, int(user["sub"]), x_confirm_delete)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/transfer")
async def transfer_team(
    id: int,
    body: TransferTeamRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await team_svc.transfer_team(db, id, int(user["sub"]), body.new_owner_id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}/members")
async def get_team_members(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    role_id: int | None = Query(default=None),
) -> dict:
    data = await team_svc.get_members(db, id, role_id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/invitations")
async def invite_member(
    id: int,
    body: InviteMemberRequest,
    user: Annotated[dict, Depends(require_permission("member:invite"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await team_svc.invite_member(db, id, int(user["sub"]), body.identifier)
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{teamId}/members/{userId}")
async def remove_member(
    teamId: int,
    userId: int,
    user: Annotated[dict, Depends(require_permission("member:remove"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await team_svc.remove_member(db, teamId, userId)
    return {"code": 0, "message": "success", "data": data}


@router.put("/{teamId}/members/{userId}/roles")
async def assign_roles(
    teamId: int,
    userId: int,
    body: AssignRolesRequest,
    user: Annotated[dict, Depends(require_permission("member:assign_role"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await team_svc.assign_roles(db, teamId, userId, body.role_ids)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{teamId}/roles")
async def list_roles(
    teamId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await role_svc.list_roles(db, teamId)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{teamId}/roles")
async def create_role(
    teamId: int,
    body: CreateRoleRequest,
    user: Annotated[dict, Depends(require_permission("member:assign_role"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await role_svc.create_role(db, teamId, body.name, body.description, body.permissions)
    return {"code": 0, "message": "success", "data": data}


@router.put("/{teamId}/roles/{roleId}")
async def update_role(
    teamId: int,
    roleId: int,
    body: UpdateRoleRequest,
    user: Annotated[dict, Depends(require_permission("member:assign_role"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await role_svc.update_role(db, teamId, roleId, body.name, body.description, body.permissions)
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{teamId}/roles/{roleId}")
async def delete_role(
    teamId: int,
    roleId: int,
    user: Annotated[dict, Depends(require_permission("member:assign_role"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await role_svc.delete_role(db, teamId, roleId)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{teamId}/spec-template")
async def get_spec_template(
    teamId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await spec_svc.get_spec_template(db, teamId, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.put("/{teamId}/spec-template")
async def update_spec_template(
    teamId: int,
    body: UpdateSpecTemplateRequest,
    user: Annotated[dict, Depends(require_permission("spec_template:edit"))],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await spec_svc.update_spec_template(db, teamId, int(user["sub"]), body.sections)
    return {"code": 0, "message": "success", "data": data}
