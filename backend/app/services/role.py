from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.exceptions import (
    ERR_BUILTIN_ROLE,
    ERR_NOT_FOUND,
    ERR_ROLE_NAME_EXISTS,
    ERR_VALIDATION,
)
from app.models import Role, RolePermission, MemberRole
from app.utils.permissions import is_valid_permission


async def list_roles(db: AsyncSession, team_id: int) -> list[dict]:
    stmt = select(Role).where(Role.team_id == team_id, Role.is_deleted == False)
    result = await db.execute(stmt)
    roles = result.scalars().all()

    items = []
    for role in roles:
        perm_stmt = select(RolePermission).where(RolePermission.role_id == role.id)
        perm_result = await db.execute(perm_stmt)
        perms = perm_result.scalars().all()
        items.append({
            "id": role.id,
            "team_id": role.team_id,
            "name": role.name,
            "slug": role.slug,
            "is_builtin": role.is_builtin,
            "description": role.description,
            "permissions": [p.permission for p in perms],
            "created_at": role.created_at.isoformat() if role.created_at else None,
        })
    return items


async def create_role(db: AsyncSession, team_id: int, name: str, description: str | None, permissions: list[str]) -> dict:
    if not name or name.strip() == "":
        from app.exceptions import BusinessError
        raise BusinessError(ERR_VALIDATION, "角色名称不能为空")

    for p in permissions:
        if not is_valid_permission(p):
            from app.exceptions import BusinessError
            raise BusinessError(ERR_VALIDATION, f"无效权限: {p}")

    stmt = select(Role).where(
        Role.team_id == team_id,
        Role.name == name,
        Role.is_deleted == False,
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        perm_stmt = select(RolePermission).where(RolePermission.role_id == existing.id)
        perm_result = await db.execute(perm_stmt)
        existing_perms = [p.permission for p in perm_result.scalars().all()]
        if (existing.description or "") == (description or "") and set(permissions) == set(existing_perms):
            return {
                "id": existing.id,
                "team_id": existing.team_id,
                "name": existing.name,
                "slug": existing.slug,
                "is_builtin": existing.is_builtin,
                "description": existing.description,
                "permissions": existing_perms,
                "created_at": existing.created_at.isoformat() if existing.created_at else None,
            }
        from app.exceptions import BusinessError
        raise BusinessError(ERR_ROLE_NAME_EXISTS, "角色名称已存在")

    role = Role(team_id=team_id, name=name, is_builtin=False, description=description)
    db.add(role)
    await db.flush()

    for p in permissions:
        db.add(RolePermission(role_id=role.id, permission=p))
    await db.commit()
    await db.refresh(role)

    return {
        "id": role.id,
        "team_id": role.team_id,
        "name": role.name,
        "slug": role.slug,
        "is_builtin": role.is_builtin,
        "description": role.description,
        "permissions": permissions,
        "created_at": role.created_at.isoformat() if role.created_at else None,
    }


async def update_role(db: AsyncSession, team_id: int, role_id: int, name: str | None, description: str | None, permissions: list[str] | None) -> dict:
    role = await _get_role(db, team_id, role_id)
    if role is None:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_NOT_FOUND, "角色不存在")
    if role.is_builtin:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_BUILTIN_ROLE, "不能修改内置角色")

    if permissions is not None:
        for p in permissions:
            if not is_valid_permission(p):
                from app.exceptions import BusinessError
                raise BusinessError(ERR_VALIDATION, f"无效权限: {p}")

    if name is not None:
        if name.strip() == "":
            from app.exceptions import BusinessError
            raise BusinessError(ERR_VALIDATION, "角色名称不能为空")
        role.name = name
    if description is not None:
        role.description = description

    if permissions is not None:
        perm_stmt = select(RolePermission).where(RolePermission.role_id == role.id)
        perm_result = await db.execute(perm_stmt)
        existing_perms = perm_result.scalars().all()
        for ep in existing_perms:
            await db.delete(ep)
        await db.flush()
        for p in permissions:
            db.add(RolePermission(role_id=role.id, permission=p))

    await db.commit()
    await db.refresh(role)

    perm_stmt = select(RolePermission).where(RolePermission.role_id == role.id)
    perm_result = await db.execute(perm_stmt)
    current_perms = perm_result.scalars().all()

    return {
        "id": role.id,
        "team_id": role.team_id,
        "name": role.name,
        "is_builtin": role.is_builtin,
        "description": role.description,
        "permissions": [p.permission for p in current_perms],
        "created_at": role.created_at.isoformat() if role.created_at else None,
    }


async def delete_role(db: AsyncSession, team_id: int, role_id: int) -> dict:
    role = await _get_role(db, team_id, role_id)
    if role is None:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_NOT_FOUND, "角色不存在")
    if role.is_builtin:
        from app.exceptions import BusinessError
        raise BusinessError(ERR_BUILTIN_ROLE, "不能删除内置角色")

    role.is_deleted = True
    role.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": role.id}


async def _get_role(db: AsyncSession, team_id: int, role_id: int) -> Role | None:
    stmt = select(Role).where(
        Role.id == role_id,
        Role.team_id == team_id,
        Role.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
