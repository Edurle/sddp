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
from app.models.spec import SpecTemplate, SpecDocument
from app.mongo_models.spec_template import SpecTemplate as SpecTemplateDefaults


async def _get_template_sections(db: AsyncSession, team_id: int) -> list[dict]:
    stmt = select(SpecTemplate).where(SpecTemplate.team_id == team_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()
    if template is not None:
        return template.sections
    return SpecTemplateDefaults().DEFAULT_SECTIONS


async def _validate_spec_content(content: dict, db: AsyncSession, team_id: int) -> tuple[list[dict], list[dict]]:
    sections = await _get_template_sections(db, team_id)
    errors = []
    suggestions = []

    for section in sections:
        section_name = section["name"]
        section_display = section.get("display_name", section_name)
        section_fields = section.get("fields", [])

        if section_name not in content:
            suggestions.append({
                "section": section_name,
                "field": None,
                "message": f"章节「{section_display}」未填写，如涉及相关内容建议补充",
            })
            continue

        section_content = content[section_name]
        if not isinstance(section_content, dict):
            errors.append({
                "section": section_name,
                "field": None,
                "message": f"章节「{section_display}」的内容必须是对象",
            })
            continue

        for field_def in section_fields:
            field_name = field_def["name"]
            field_display = field_def.get("display_name", field_name)
            field_schema = field_def.get("json_schema")

            if field_name not in section_content:
                suggestions.append({
                    "section": section_name,
                    "field": field_name,
                    "message": f"字段「{field_display}」未填写，建议补充",
                })
                continue

            if field_schema is not None:
                try:
                    jsonschema.validate(section_content[field_name], field_schema)
                except jsonschema.ValidationError as e:
                    errors.append({
                        "section": section_name,
                        "field": field_name,
                        "message": f"字段「{field_display}」格式不正确: {e.message}",
                        "path": list(e.absolute_path) if e.absolute_path else [],
                    })

    return errors, suggestions


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

    stmt = select(SpecTemplate).where(SpecTemplate.team_id == team_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()
    if template is None:
        default_sections = SpecTemplateDefaults().DEFAULT_SECTIONS
        return {"sections": default_sections}

    return {"sections": template.sections}


async def get_agent_guide(
    db: AsyncSession, team_id: int, user_id: int, requirement_id: int | None = None
) -> dict:
    result = await get_spec_template(db, team_id, user_id)

    if requirement_id is not None:
        req = await _get_requirement(db, requirement_id)
        if req is None:
            raise BusinessError(ERR_NOT_FOUND, "需求不存在")

        req_team_id = await _get_team_id_by_requirement(db, requirement_id)
        if req_team_id != team_id:
            raise BusinessError(ERR_FORBIDDEN, "无权访问该需求")

        result["requirement"] = {
            "id": req.id,
            "title": req.title,
            "description": req.description,
            "req_type": req.req_type,
            "priority": req.priority,
            "type_detail": req.type_detail,
            "prototype_html": req.prototype_html,
            "status": req.status,
        }

    return result


async def update_spec_template(
    db: AsyncSession, team_id: int, user_id: int, sections: list[dict]
) -> dict:
    await _check_team_member(db, team_id, user_id)

    stmt = select(SpecTemplate).where(SpecTemplate.team_id == team_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()

    if template is None:
        template = SpecTemplate(team_id=team_id, sections=sections, updated_by=user_id)
        db.add(template)
    else:
        template.sections = sections
        template.updated_by = user_id

    await db.commit()
    await db.refresh(template)
    return {"sections": template.sections}


async def get_spec_document(
    db: AsyncSession, req_id: int
) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is None or doc.current_version == 0:
        return {"current_version": 0, "content": None}

    versions = doc.versions or []
    content = versions[-1].get("content") if versions else None
    return {
        "current_version": doc.current_version,
        "content": content,
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
    errors, suggestions = await _validate_spec_content(content, db, team_id)
    if errors:
        raise BusinessError(ERR_VALIDATION, "规范内容格式有误", errors=errors)

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    from datetime import datetime, timezone
    new_version_num = (doc.current_version + 1) if doc else 1
    new_version_entry = {
        "version": new_version_num,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id,
    }

    if doc is None:
        doc = SpecDocument(
            requirement_id=req_id,
            current_version=new_version_num,
            versions=[new_version_entry],
        )
        db.add(doc)
    else:
        versions = list(doc.versions or [])
        versions.append(new_version_entry)
        doc.current_version = new_version_num
        doc.versions = versions

    await db.commit()
    return {
        "version": new_version_num,
        "errors": [],
        "suggestions": suggestions,
    }


async def list_spec_versions(
    db: AsyncSession, req_id: int
) -> list[dict]:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if doc is None:
        return []

    return [
        {
            "version": v["version"],
            "content": v.get("content"),
            "created_by": v.get("created_by"),
            "created_at": v.get("created_at"),
        }
        for v in (doc.versions or [])
    ]


async def get_spec_version_detail(
    db: AsyncSession, req_id: int, version: int
) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if doc is None:
        raise BusinessError(ERR_NOT_FOUND, "版本不存在")

    for v in (doc.versions or []):
        if v["version"] == version:
            return {
                "version": v["version"],
                "content": v["content"],
                "created_by": v.get("created_by"),
                "created_at": v.get("created_at"),
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
