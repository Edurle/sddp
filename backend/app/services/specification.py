from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache import cache_instance
from app.exceptions import (
    BusinessError,
    ERR_FORBIDDEN,
    ERR_NOT_FOUND,
    ERR_REQUIREMENT_STATUS,
    ERR_VALIDATION,
)
from app.models import Requirement, TeamMember
from app.mongo_models.spec_document import SpecDocument
from app.mongo_models.spec_template import SpecTemplate


async def get_spec_template(
    db: AsyncSession, team_id: int, user_id: int
) -> dict:
    await _check_team_member(db, team_id, user_id)

    key = f"spec_template:{team_id}"
    data = cache_instance.get(key)
    if data is None:
        default_sections = SpecTemplate().DEFAULT_SECTIONS
        return {"sections": default_sections}

    return {"sections": data.get("sections", [])}


async def update_spec_template(
    db: AsyncSession, team_id: int, user_id: int, sections: list[dict]
) -> dict:
    await _check_team_member(db, team_id, user_id)

    template = SpecTemplate(team_id=team_id)
    template.sections = [
        SpecTemplate._section_from_dict(s) for s in sections
    ]
    template.updated_by = user_id
    from datetime import datetime
    template.updated_at = datetime.utcnow()

    doc = template.to_document()
    cache_instance.set(f"spec_template:{team_id}", doc)
    return {"sections": doc["sections"]}


async def get_spec_document(
    db: AsyncSession, req_id: int
) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    key = f"spec_document:{req_id}"
    data = cache_instance.get(key)
    if data is None:
        return {"current_version": 0, "content": None}

    doc = SpecDocument(
        requirement_id=req_id,
        current_version=data.get("current_version", 0),
    )
    return {
        "current_version": doc.current_version if doc.current_version > 0 else None,
        "content": _get_current_content(data) if doc.current_version > 0 else None,
    }


async def save_spec_document(
    db: AsyncSession, req_id: int, user_id: int, content: dict
) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    if req.status != "drafting_spec":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前状态不允许编辑规格说明")

    key = f"spec_document:{req_id}"
    data = cache_instance.get(key)
    if data is None:
        doc = SpecDocument(requirement_id=req_id)
    else:
        doc = SpecDocument(
            requirement_id=req_id,
            current_version=data.get("current_version", 0),
        )
        for v in data.get("versions", []):
            from app.mongo_models.spec_document import SpecDocumentVersion
            doc.versions.append(SpecDocumentVersion(
                version=v["version"],
                content=v["content"],
                created_at=v.get("created_at"),
                created_by=v.get("created_by"),
            ))

    new_version = doc.add_version(content, user_id)
    cache_instance.set(key, doc.to_document())
    return {"version": new_version.version}


async def list_spec_versions(
    db: AsyncSession, req_id: int
) -> list[dict]:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    key = f"spec_document:{req_id}"
    data = cache_instance.get(key)
    if data is None:
        return []

    versions = data.get("versions", [])
    return [
        {
            "version": v["version"],
            "content": v.get("content"),
            "created_by": v.get("created_by"),
            "created_at": v.get("created_at").isoformat() if v.get("created_at") else None,
        }
        for v in versions
    ]


async def get_spec_version_detail(
    db: AsyncSession, req_id: int, version: int
) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    key = f"spec_document:{req_id}"
    data = cache_instance.get(key)
    if data is None:
        raise BusinessError(ERR_NOT_FOUND, "版本不存在")

    for v in data.get("versions", []):
        if v["version"] == version:
            return {
                "version": v["version"],
                "content": v["content"],
                "created_by": v.get("created_by"),
                "created_at": v.get("created_at").isoformat() if v.get("created_at") else None,
            }

    raise BusinessError(ERR_NOT_FOUND, "版本不存在")


async def _check_team_member(db: AsyncSession, team_id: int, user_id: int):
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
        TeamMember.is_deleted == False,
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()
    if member is None:
        raise BusinessError(ERR_FORBIDDEN, "无权限")


async def _get_requirement(db: AsyncSession, req_id: int) -> Requirement | None:
    stmt = select(Requirement).where(
        Requirement.id == req_id,
        Requirement.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _get_current_content(data: dict) -> dict | None:
    versions = data.get("versions", [])
    if not versions:
        return None
    return versions[-1].get("content")
