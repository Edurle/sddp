import jsonschema
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    BusinessError,
    ERR_FORBIDDEN,
    ERR_NOT_FOUND,
    ERR_REQUIREMENT_STATUS,
    ERR_VALIDATION,
    ERR_FIELD_PATH_NOT_FOUND,
    ERR_NO_DRAFT,
)
from app.models import Requirement, TeamMember
from app.models.spec import SpecTemplate, SpecDocument
from app.services.path_utils import (
    PathSyntaxError,
    PathNotFoundError,
    MultipleMatchError,
    set_by_path,
)

DEFAULT_SECTIONS = [
    {
        "name": "entity_definition",
        "display_name": "实体定义",
        "required": True,
        "fields": [
            {"name": "description", "display_name": "实体描述", "type": "text", "required": True, "description": "对实体的简要描述", "agent_prompt": "用一段话描述该实体的用途和核心职责"},
            {
                "name": "fields",
                "display_name": "字段列表",
                "type": "list",
                "required": True,
                "description": "实体包含的字段定义（字段名、类型、约束）",
                "agent_prompt": "列出实体的所有字段。每个字段需包含 name（字段名，英文小写下划线）、type（数据类型，如 string/integer/boolean/datetime/json）、description（字段含义的中文描述）、constraints（约束数组，如 ['required', 'unique', 'max:255'])",
                "json_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "type"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "type": {"type": "string", "minLength": 1},
                            "description": {"type": "string"},
                            "constraints": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                },
            },
        ],
    },
    {
        "name": "table_design",
        "display_name": "数据表设计",
        "required": True,
        "fields": [
            {
                "name": "tables",
                "display_name": "表列表",
                "type": "list",
                "required": True,
                "description": "每个表的表名、字段、类型、索引、外键关系",
                "agent_prompt": "列出所有数据库表。每张表需包含 name（表名，复数形式）、description（表用途）、fields（字段数组，包含 name/type/nullable/default/comment/primary_key/unique/foreign_key/auto_increment）、indexes（索引数组）",
                "json_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "fields"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "description": {"type": "string"},
                            "fields": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "type"],
                                    "properties": {
                                        "name": {"type": "string", "minLength": 1},
                                        "type": {"type": "string", "minLength": 1},
                                        "nullable": {"type": "boolean"},
                                        "default": {},
                                        "comment": {"type": "string"},
                                        "primary_key": {"type": "boolean"},
                                        "unique": {"type": "boolean"},
                                        "foreign_key": {"type": "string"},
                                        "auto_increment": {"type": "boolean"},
                                    },
                                },
                                "minItems": 1,
                            },
                            "indexes": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "fields"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "fields": {"type": "array", "items": {"type": "string"}},
                                        "unique": {"type": "boolean"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        ],
    },
    {
        "name": "page_structure",
        "display_name": "页面结构",
        "required": True,
        "fields": [
            {
                "name": "pages",
                "display_name": "页面列表",
                "type": "list",
                "required": True,
                "description": "每个页面的名称、编码、元素列表（含唯一编码、ARIA 角色、可访问名称）、交互行为",
                "agent_prompt": "列出所有页面。每个页面需包含 name（页面名称）、code（页面编码，短横线格式）、route（路由路径）、elements（元素数组，每个元素含 code/type/label/role/accessible_name/interaction）。其中 role 为该元素的 ARIA 角色（如 button/textbox/combobox/dialog/table/tab/link/heading/alert/checkbox），accessible_name 为该元素的可访问名称，用于 E2E 测试定位（如\"提交需求审核\"、\"审核人\"、\"任务列表\"）",
                "json_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["name", "code", "elements"],
                        "properties": {
                            "name": {"type": "string", "minLength": 1},
                            "code": {"type": "string", "minLength": 1},
                            "route": {"type": "string"},
                            "elements": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["code", "type", "label"],
                                    "properties": {
                                        "code": {"type": "string", "minLength": 1},
                                        "type": {"type": "string", "minLength": 1},
                                        "label": {"type": "string", "minLength": 1},
                                        "role": {"type": "string"},
                                        "accessible_name": {"type": "string"},
                                        "interaction": {"type": "string"},
                                    },
                                },
                            },
                            "interactions": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "trigger": {"type": "string"},
                                        "behavior": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        ],
    },
    {
        "name": "api_design",
        "display_name": "API 设计",
        "required": True,
        "fields": [
            {
                "name": "endpoints",
                "display_name": "接口列表",
                "type": "list",
                "required": True,
                "description": "每个接口的 URL、HTTP 方法、请求参数、响应参数、错误码",
                "agent_prompt": "列出所有 API 接口。每个接口需包含 method（GET/POST/PUT/DELETE/PATCH）、path（URL路径）、description（接口说明）、request_params（请求参数数组，含 name/in/type/required/description）、response（响应体结构，含 code/message/data）、errors（错误码数组）",
                "json_schema": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["method", "path", "description"],
                        "properties": {
                            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
                            "path": {"type": "string", "minLength": 1},
                            "description": {"type": "string", "minLength": 1},
                            "request_params": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "in", "type"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "in": {"type": "string", "enum": ["query", "path", "body", "header"]},
                                        "type": {"type": "string"},
                                        "required": {"type": "boolean"},
                                        "description": {"type": "string"},
                                    },
                                },
                            },
                            "response": {
                                "type": "object",
                                "properties": {
                                    "code": {"type": "integer"},
                                    "message": {"type": "string"},
                                    "data": {},
                                },
                                "required": ["code", "message"],
                            },
                            "errors": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "code": {"type": "integer"},
                                        "message": {"type": "string"},
                                    },
                                },
                            },
                        },
                    },
                },
            },
        ],
    },
    {
        "name": "constraints",
        "display_name": "其他约束",
        "required": False,
        "fields": [
            {"name": "directory_structure", "display_name": "目录结构", "type": "text", "required": False, "description": "项目目录结构规范", "agent_prompt": "描述项目的目录结构规范"},
            {"name": "naming_conventions", "display_name": "命名规范", "type": "text", "required": False, "description": "编码命名规范", "agent_prompt": "描述编码命名规范（变量、函数、文件等）"},
            {"name": "other", "display_name": "其他约束", "type": "text", "required": False, "description": "其他技术约束", "agent_prompt": "描述其他技术约束（性能要求、安全要求等）"},
        ],
    },
]


async def _get_template_sections(db: AsyncSession, team_id: int) -> list[dict]:
    stmt = select(SpecTemplate).where(SpecTemplate.team_id == team_id)
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()
    if template is not None:
        return template.sections
    return DEFAULT_SECTIONS


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
        default_sections = DEFAULT_SECTIONS
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

    if doc is None:
        return {"current_version": 0, "content": None, "is_draft": False}

    # 工作内容（draft_content）即使尚无审批版本（current_version == 0）也应返回。
    if doc.draft_content is not None:
        return {
            "current_version": doc.current_version,
            "content": doc.draft_content,
            "is_draft": True,
            "base_version": doc.draft_base_version,
        }

    versions = doc.versions or []
    content = versions[-1].get("content") if versions else None
    return {
        "current_version": doc.current_version,
        "content": content,
        "is_draft": False,
    }


async def save_spec_document(
    db: AsyncSession, req_id: int, user_id: int, content: dict
) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    if req.status != "drafting_spec":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前状态不允许编辑规格说明")

    if req.status == "deprecated":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "需求已废弃，不可编辑规格说明")

    team_id = await _get_team_id_by_requirement(db, req_id)
    errors, suggestions = await _validate_spec_content(content, db, team_id)
    if errors:
        raise BusinessError(ERR_VALIDATION, "规范内容格式有误", errors=errors)

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    # 编辑不再生成版本：全量内容写入工作草稿，版本只在审批时切（见 snapshot_spec_on_review）。
    if doc is None:
        doc = SpecDocument(
            requirement_id=req_id,
            current_version=0,
            versions=[],
            draft_content=content,
            draft_base_version=0,
        )
        db.add(doc)
    else:
        doc.draft_content = content
        doc.draft_base_version = doc.current_version

    await db.commit()
    return {
        "is_draft": True,
        "errors": [],
        "suggestions": suggestions,
    }


async def set_spec_draft_field(
    db: AsyncSession, req_id: int, user_id: int, path: str, value
) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    if req.status != "drafting_spec":
        raise BusinessError(
            ERR_REQUIREMENT_STATUS,
            f"当前需求状态为 {req.status}，不允许编辑草稿。需处于 drafting_spec 状态。",
        )

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    if doc is None or (doc.draft_content is None and not (doc.versions or [])):
        raise BusinessError(
            ERR_NOT_FOUND,
            "尚无 spec 内容，无法局部更新草稿。请先用 save-spec 提交初始内容。",
        )

    if doc.draft_content is None:
        versions = doc.versions or []
        doc.draft_content = versions[-1].get("content")
        doc.draft_base_version = doc.current_version

    try:
        new_draft = set_by_path(doc.draft_content, path, value)
    except PathSyntaxError as e:
        raise BusinessError(ERR_VALIDATION, str(e))
    except MultipleMatchError as e:
        raise BusinessError(ERR_VALIDATION, str(e))
    except PathNotFoundError as e:
        raise BusinessError(ERR_FIELD_PATH_NOT_FOUND, str(e))

    team_id = await _get_team_id_by_requirement(db, req_id)
    errors, suggestions = await _validate_spec_content(new_draft, db, team_id)
    if errors:
        raise BusinessError(ERR_VALIDATION, "草稿校验失败", errors=errors)

    doc.draft_content = new_draft
    await db.commit()
    return {
        "is_draft": True,
        "base_version": doc.draft_base_version,
        "errors": [],
        "suggestions": suggestions,
    }


async def commit_spec_draft(db: AsyncSession, req_id: int, user_id: int) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    if req.status != "drafting_spec":
        raise BusinessError(
            ERR_REQUIREMENT_STATUS,
            f"当前需求状态为 {req.status}，不允许定版草稿。需处于 drafting_spec 状态。",
        )

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if doc is None or doc.draft_content is None:
        raise BusinessError(
            ERR_NO_DRAFT,
            "无草稿可定版：当前 spec 无未提交草稿。用 set-spec-field 开始编辑草稿。",
        )

    # 版本只在审批（通过/驳回）时生成。草稿即工作内容，定版为幂等 no-op，不再切版本。
    return {"version": doc.current_version, "committed": False}


async def discard_spec_draft(db: AsyncSession, req_id: int) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if doc is None or doc.draft_content is None:
        raise BusinessError(ERR_NO_DRAFT, "无草稿可丢弃：当前 spec 无未提交草稿。")
    doc.draft_content = None
    doc.draft_base_version = None
    await db.commit()
    return {"discarded": True, "current_version": doc.current_version}


async def snapshot_spec_on_review(db: AsyncSession, req_id: int, reviewer_id: int) -> None:
    """规范审批（无论通过/驳回）时，对当前工作内容切一个版本快照。

    版本只在此处产生；编辑路径（save/commit/set-field）均不再生成版本。
    不提交事务，由调用方（审批流程）统一 commit。
    """
    from datetime import datetime, timezone

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()
    if doc is None:
        return

    if doc.draft_content is not None:
        content = doc.draft_content
    else:
        existing = doc.versions or []
        content = existing[-1].get("content") if existing else None
    if content is None:
        return

    new_version_num = doc.current_version + 1
    versions = list(doc.versions or [])
    versions.append({
        "version": new_version_num,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": reviewer_id,
    })
    doc.versions = versions
    doc.current_version = new_version_num
    doc.draft_content = None
    doc.draft_base_version = None


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
