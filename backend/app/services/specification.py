import jsonschema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    BusinessError,
    ERR_FORBIDDEN,
    ERR_NOT_FOUND,
    ERR_REQUIREMENT_STATUS,
    ERR_VALIDATION,
)
from app.models import Requirement, TeamMember
from app.mongo_database import get_spec_templates_collection, get_spec_documents_collection
from app.mongo_models.spec_document import SpecDocument
from app.mongo_models.spec_template import SpecTemplate


async def _get_template_sections(team_id: int) -> list[dict]:
    data = await get_spec_templates_collection().find_one({"team_id": team_id})
    if data is not None:
        return data.get("sections", [])
    return SpecTemplate().DEFAULT_SECTIONS


async def _validate_spec_content(content: dict, team_id: int) -> list[dict]:
    sections = await _get_template_sections(team_id)
    errors = []

    for section in sections:
        section_name = section["name"]
        section_required = section.get("required", True)
        section_fields = section.get("fields", [])

        if section_name not in content:
            if section_required:
                errors.append({
                    "section": section_name,
                    "message": f"缺少必填章节: {section.get('display_name', section_name)}",
                })
            continue

        section_content = content[section_name]
        if not isinstance(section_content, dict):
            errors.append({
                "section": section_name,
                "message": f"章节 {section.get('display_name', section_name)} 的内容必须是对象",
            })
            continue

        for field_def in section_fields:
            field_name = field_def["name"]
            field_required = field_def.get("required", True)
            field_schema = field_def.get("json_schema")
            field_display = field_def.get("display_name", field_name)

            if field_name not in section_content:
                if field_required:
                    errors.append({
                        "section": section_name,
                        "field": field_name,
                        "message": f"缺少必填字段: {field_display}",
                    })
                continue

            if field_schema is not None:
                try:
                    jsonschema.validate(section_content[field_name], field_schema)
                except jsonschema.ValidationError as e:
                    errors.append({
                        "section": section_name,
                        "field": field_name,
                        "message": f"字段 {field_display} 格式不正确: {e.message}",
                        "path": list(e.absolute_path) if e.absolute_path else [],
                    })

    return errors


async def _get_team_id_by_requirement(db: AsyncSession, req_id: int) -> int:
    from sqlalchemy import select as sel
    from app.models import Iteration as IterModel, Project as ProjModel
    req = await _get_requirement(db, req_id)
    if req is None:
        return 0
    stmt = sel(IterModel).where(IterModel.id == req.iteration_id)
    result = await db.execute(stmt)
    iteration = result.scalar_one_or_none()
    if iteration is None:
        return 0
    stmt2 = sel(ProjModel).where(ProjModel.id == iteration.project_id)
    result2 = await db.execute(stmt2)
    project = result2.scalar_one_or_none()
    if project is None:
        return 0
    return project.team_id


async def get_spec_template(
    db: AsyncSession, team_id: int, user_id: int
) -> dict:
    await _check_team_member(db, team_id, user_id)

    data = await get_spec_templates_collection().find_one({"team_id": team_id})
    if data is None:
        default_sections = SpecTemplate().DEFAULT_SECTIONS
        return {"sections": default_sections}

    return {"sections": data.get("sections", [])}


async def get_agent_guide(
    db: AsyncSession, team_id: int, user_id: int
) -> dict:
    return await get_spec_template(db, team_id, user_id)


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
    await get_spec_templates_collection().update_one(
        {"team_id": team_id},
        {"$set": doc},
        upsert=True,
    )
    return {"sections": doc["sections"]}


async def get_spec_document(
    db: AsyncSession, req_id: int
) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    data = await get_spec_documents_collection().find_one({"requirement_id": req_id})
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

    team_id = await _get_team_id_by_requirement(db, req_id)
    errors = await _validate_spec_content(content, team_id)
    if errors:
        raise BusinessError(ERR_VALIDATION, "规范内容校验失败", errors=errors)

    data = await get_spec_documents_collection().find_one({"requirement_id": req_id})
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
    await get_spec_documents_collection().update_one(
        {"requirement_id": req_id},
        {"$set": doc.to_document()},
        upsert=True,
    )
    return {"version": new_version.version}


async def list_spec_versions(
    db: AsyncSession, req_id: int
) -> list[dict]:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    data = await get_spec_documents_collection().find_one({"requirement_id": req_id})
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

    data = await get_spec_documents_collection().find_one({"requirement_id": req_id})
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
