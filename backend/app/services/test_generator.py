from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BusinessError, ERR_NOT_FOUND, ERR_REQUIREMENT_STATUS, ERR_VALIDATION
from app.models import Requirement
from app.models.spec import SpecDocument
from app.services import test_case as tc_svc


async def generate_test_cases(
    db: AsyncSession,
    requirement_id: int,
    user_id: int,
    case_types: list[str] | None = None,
) -> dict:
    if case_types is None:
        case_types = ["ui_test", "happy_path"]

    req_stmt = select(Requirement).where(Requirement.id == requirement_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    if req.status not in ("drafting_tests", "approved"):
        raise BusinessError(ERR_REQUIREMENT_STATUS, "需求状态不允许生成测试用例")

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

    if "ui_test" in case_types:
        pages = content.get("page_structure", {}).get("pages", [])
        for page in pages:
            for el in page.get("elements", []):
                if el.get("interaction"):
                    steps = _build_e2e_steps(page, el)
                    expected = _build_e2e_expected(el)
                    related_api = _find_api_for_element(el, content)

                    tc = await tc_svc.create_test_case(
                        db, requirement_id,
                        title=f"验证{page.get('name', '')}中「{el.get('accessible_name') or el.get('label', '')}」的{el.get('interaction', '交互行为')}",
                        case_type="ui_test",
                        precondition="用户已登录，页面已加载",
                        steps=steps,
                        expected_result=expected,
                        related_element=el.get("code", ""),
                        related_api=related_api,
                    )
                    created.append(tc)

                    if not related_api:
                        suggestions.append({
                            "case_id": tc["id"],
                            "field": "related_api",
                            "message": f"测试用例「{tc['title']}」未关联 API，建议补充",
                        })

    if "happy_path" in case_types:
        endpoints = content.get("api_design", {}).get("endpoints", [])
        for ep in endpoints:
            tc = await tc_svc.create_test_case(
                db, requirement_id,
                title=f"验证 {ep.get('method', '')} {ep.get('path', '')} 接口",
                case_type="happy_path",
                precondition="系统正常运行",
                steps=f"1. 发送 {ep.get('method', '')} 请求到 {ep.get('path', '')}\n2. 检查响应状态码和返回数据",
                expected_result="返回成功状态码，响应体包含预期数据结构",
                related_api=f"{ep.get('method', '')} {ep.get('path', '')}",
            )
            created.append(tc)

    total_interactions = sum(
        len([e for e in p.get("elements", []) if e.get("interaction")])
        for p in content.get("page_structure", {}).get("pages", [])
    )
    ui_test_count = len([c for c in created if c.get("case_type") == "ui_test"])
    if total_interactions > 0 and ui_test_count < total_interactions:
        suggestions.append({
            "type": "coverage",
            "message": f"规范中定义了 {total_interactions} 个交互行为，当前生成了 {ui_test_count} 个 UI 测试用例",
        })

    return {
        "created": created,
        "errors": errors,
        "suggestions": suggestions,
    }


def _build_e2e_steps(page: dict, element: dict) -> str:
    route = page.get("route", "页面")
    an = element.get("accessible_name") or element.get("label", "")
    interaction = element.get("interaction", "")
    return f"1. 导航到 {route} 页面\n2. 操作「{an}」({interaction})\n3. 验证预期结果"


def _build_e2e_expected(element: dict) -> str:
    interaction = element.get("interaction", "")
    return f"{interaction}后系统响应正常"


def _find_api_for_element(element: dict, content: dict) -> str:
    code = element.get("code", "")
    endpoints = content.get("api_design", {}).get("endpoints", [])
    for ep in endpoints:
        path = ep.get("path", "")
        for keyword in code.split("-"):
            if len(keyword) > 2 and keyword in path:
                return f"{ep.get('method', '')} {path}"
    return ""
