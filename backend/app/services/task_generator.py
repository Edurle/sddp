from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BusinessError, ERR_NOT_FOUND, ERR_REQUIREMENT_STATUS, ERR_VALIDATION
from app.models import Requirement
from app.models.spec import SpecDocument
from app.services import task as task_svc


async def generate_tasks(
    db: AsyncSession,
    requirement_id: int,
    user_id: int,
    strategy: str = "hybrid",
) -> dict:
    req_stmt = select(Requirement).where(Requirement.id == requirement_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    if req.status != "approved":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "需求未通过审核，无法生成任务")

    spec_stmt = select(SpecDocument).where(SpecDocument.requirement_id == requirement_id)
    spec_result = await db.execute(spec_stmt)
    spec_doc = spec_result.scalar_one_or_none()
    if spec_doc is None or spec_doc.current_version == 0:
        raise BusinessError(ERR_VALIDATION, "规范文档为空，请先填写规范")

    versions = spec_doc.versions or []
    content = versions[-1].get("content", {}) if versions else {}

    created = []
    suggestions = []
    errors = []

    if strategy in ("by_page", "hybrid"):
        pages = _get_pages(content)
        for page in pages:
            task = await task_svc.create_task(
                db, requirement_id, user_id,
                title=f"实现{page.get('name', '未知页面')}",
                description=_build_page_description(page),
                task_type="frontend",
                source_section=f"page_structure:{page.get('code', '')}",
                spec_reference=_build_page_reference(page, content),
            )
            created.append(task)
            if not task.get("assignee_id"):
                suggestions.append({
                    "task_id": task["id"],
                    "field": "assignee_id",
                    "message": f"任务「{task['title']}」未分配负责人，建议指定",
                })

    if strategy in ("by_api", "hybrid"):
        api_groups = _group_apis(content)
        for group_name, endpoints in api_groups.items():
            task = await task_svc.create_task(
                db, requirement_id, user_id,
                title=f"实现{group_name} API",
                description=_build_api_description(endpoints),
                task_type="backend",
                source_section=f"api_design:{group_name}",
                spec_reference={"endpoints": endpoints},
            )
            created.append(task)

    tables = _get_tables(content)
    if tables:
        task = await task_svc.create_task(
            db, requirement_id, user_id,
            title="数据库变更",
            description=_build_table_description(tables),
            task_type="database",
            source_section="table_design",
            spec_reference={"tables": tables},
        )
        created.append(task)

    return {
        "created": created,
        "errors": errors,
        "suggestions": suggestions,
    }


def _get_pages(content: dict) -> list[dict]:
    return content.get("page_structure", {}).get("pages", [])


def _get_tables(content: dict) -> list[dict]:
    return content.get("table_design", {}).get("tables", [])


def _group_apis(content: dict) -> dict[str, list[dict]]:
    endpoints = content.get("api_design", {}).get("endpoints", [])
    groups: dict[str, list[dict]] = {}
    for ep in endpoints:
        path = ep.get("path", "")
        parts = path.strip("/").split("/")
        group = parts[0] if parts else "default"
        groups.setdefault(group, []).append(ep)
    return groups


def _build_page_description(page: dict) -> str:
    elements = page.get("elements", [])
    interactions = page.get("interactions", [])
    lines = [f"页面: {page.get('name', '')}"]
    if page.get("route"):
        lines.append(f"路由: {page['route']}")
    if elements:
        lines.append(f"元素数: {len(elements)}")
    if interactions:
        lines.append(f"交互数: {len(interactions)}")
    return "\n".join(lines)


def _build_page_reference(page: dict, content: dict) -> dict:
    ref = {
        "page_code": page.get("code", ""),
        "page_name": page.get("name", ""),
        "route": page.get("route", ""),
        "elements": page.get("elements", []),
        "interactions": page.get("interactions", []),
    }
    page_apis = _find_apis_for_page(page, content)
    if page_apis:
        ref["related_apis"] = page_apis
    return ref


def _find_apis_for_page(page: dict, content: dict) -> list[dict]:
    page_code = page.get("code", "")
    endpoints = content.get("api_design", {}).get("endpoints", [])
    related = []
    for ep in endpoints:
        path = ep.get("path", "")
        if page_code and page_code.replace("-", "") in path.replace("/", "").replace("_", ""):
            related.append({"method": ep.get("method", ""), "path": path})
    return related


def _build_api_description(endpoints: list[dict]) -> str:
    lines = []
    for ep in endpoints:
        lines.append(f"{ep.get('method', '')} {ep.get('path', '')} — {ep.get('description', '')}")
    return "\n".join(lines)


def _build_table_description(tables: list[dict]) -> str:
    lines = []
    for t in tables:
        field_count = len(t.get("fields", []))
        lines.append(f"{t.get('name', '')} ({field_count} 字段) — {t.get('description', '')}")
    return "\n".join(lines)
