from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BusinessError, ERR_NOT_FOUND, ERR_REQUIREMENT_STATUS, ERR_VALIDATION
from app.models import Requirement, RequirementLink


async def supersede_requirement(
    db: AsyncSession,
    req_id: int,
    user_id: int,
    title: str | None = None,
    description: str | None = None,
) -> dict:
    stmt = select(Requirement).where(
        Requirement.id == req_id,
        Requirement.is_deleted == False,
    )
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    if req.status != "approved":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "只有已通过审核的需求才能创建变更")

    new_title = title or f"{req.title}（变更）"
    new_req = Requirement(
        iteration_id=req.iteration_id,
        title=new_title,
        req_type=req.req_type,
        priority=req.priority,
        status="drafting_req",
        description=description or req.description,
        type_detail=req.type_detail,
        prototype_html=req.prototype_html,
        created_by=user_id,
    )
    db.add(new_req)
    await db.flush()

    req.status = "deprecated"

    link = RequirementLink(
        source_id=req.id,
        target_id=new_req.id,
        link_type="supersede",
        created_by=user_id,
    )
    db.add(link)
    await db.commit()
    await db.refresh(new_req)

    return {
        "old_requirement": _req_brief(req),
        "new_requirement": _req_brief(new_req),
    }


async def create_link(
    db: AsyncSession,
    req_id: int,
    target_id: int,
    link_type: str,
    user_id: int,
) -> dict:
    if link_type not in ("relates_to",):
        raise BusinessError(ERR_VALIDATION, "只允许手动创建 relates_to 类型的关联")

    if req_id == target_id:
        raise BusinessError(ERR_VALIDATION, "不能关联自身")

    stmt = select(Requirement).where(
        Requirement.id == req_id,
        Requirement.is_deleted == False,
    )
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is None:
        raise BusinessError(ERR_NOT_FOUND, "源需求不存在")

    stmt2 = select(Requirement).where(
        Requirement.id == target_id,
        Requirement.is_deleted == False,
    )
    result2 = await db.execute(stmt2)
    if result2.scalar_one_or_none() is None:
        raise BusinessError(ERR_NOT_FOUND, "目标需求不存在")

    existing = select(RequirementLink).where(
        or_(
            (RequirementLink.source_id == req_id) & (RequirementLink.target_id == target_id) & (RequirementLink.link_type == link_type),
            (RequirementLink.source_id == target_id) & (RequirementLink.target_id == req_id) & (RequirementLink.link_type == link_type),
        )
    )
    if (await db.execute(existing)).scalar_one_or_none():
        raise BusinessError(ERR_VALIDATION, "关联已存在")

    link = RequirementLink(
        source_id=req_id,
        target_id=target_id,
        link_type=link_type,
        created_by=user_id,
    )
    db.add(link)
    await db.commit()
    await db.refresh(link)

    return _link_to_dict(link)


async def list_links(
    db: AsyncSession,
    req_id: int,
) -> list[dict]:
    stmt = select(RequirementLink).where(
        or_(
            RequirementLink.source_id == req_id,
            RequirementLink.target_id == req_id,
        )
    ).order_by(RequirementLink.created_at.desc())
    result = await db.execute(stmt)
    links = result.scalars().all()

    items = []
    for link in links:
        d = _link_to_dict(link)
        if link.source_id == req_id:
            d["direction"] = "outgoing"
        else:
            d["direction"] = "incoming"
            d["related_req_id"] = link.source_id
        if link.source_id == req_id:
            d["related_req_id"] = link.target_id
        items.append(d)
    return items


async def delete_link(
    db: AsyncSession,
    req_id: int,
    link_id: int,
) -> dict:
    stmt = select(RequirementLink).where(RequirementLink.id == link_id)
    result = await db.execute(stmt)
    link = result.scalar_one_or_none()
    if link is None:
        raise BusinessError(ERR_NOT_FOUND, "关联不存在")

    if link.source_id != req_id and link.target_id != req_id:
        raise BusinessError(ERR_NOT_FOUND, "关联不存在")

    if link.link_type == "supersede":
        raise BusinessError(ERR_VALIDATION, "变更关联不可删除")

    await db.delete(link)
    await db.commit()
    return {"id": link.id}


def _link_to_dict(link: RequirementLink) -> dict:
    return {
        "id": link.id,
        "source_id": link.source_id,
        "target_id": link.target_id,
        "link_type": link.link_type,
        "created_by": link.created_by,
        "created_at": link.created_at.isoformat() if link.created_at else None,
    }


def _req_brief(req: Requirement) -> dict:
    return {
        "id": req.id,
        "iteration_id": req.iteration_id,
        "title": req.title,
        "req_type": req.req_type,
        "priority": req.priority,
        "status": req.status,
        "created_by": req.created_by,
    }
