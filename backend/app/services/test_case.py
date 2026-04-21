"""Test case service."""

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    ERR_NOT_FOUND,
    ERR_REQUIREMENT_STATUS,
    ERR_VALIDATION,
    BusinessError,
)
from app.models import Requirement, TestCase


async def list_test_cases(
    db: AsyncSession,
    requirement_id: int,
    case_type: str | None = None,
) -> list[dict]:
    stmt = select(TestCase).where(
        TestCase.requirement_id == requirement_id,
        TestCase.is_deleted == False,
    )
    if case_type:
        stmt = stmt.where(TestCase.case_type == case_type)
    stmt = stmt.order_by(TestCase.created_at.asc())

    result = await db.execute(stmt)
    cases = result.scalars().all()
    return [_tc_to_dict(tc) for tc in cases]


async def create_test_case(
    db: AsyncSession,
    requirement_id: int,
    title: str,
    case_type: str,
    precondition: str | None = None,
    steps: str | None = None,
    expected_result: str | None = None,
    related_api: str | None = None,
    related_element: str | None = None,
) -> dict:
    if not title or not title.strip():
        raise BusinessError(ERR_VALIDATION, "用例标题不能为空")
    if not steps or not steps.strip():
        raise BusinessError(ERR_VALIDATION, "用例步骤不能为空")

    req_stmt = select(Requirement).where(Requirement.id == requirement_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    if req.status != "drafting_tests":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "需求状态不允许创建测试用例")

    count_stmt = select(func.count()).select_from(TestCase).where(
        TestCase.requirement_id == requirement_id,
    )
    count_result = await db.execute(count_stmt)
    count = count_result.scalar_one()
    case_number = f"TC-{requirement_id}-{count + 1}"

    tc = TestCase(
        requirement_id=requirement_id,
        case_number=case_number,
        title=title,
        case_type=case_type,
        precondition=precondition,
        steps=steps,
        expected_result=expected_result or "",
        related_api=related_api,
        related_element=related_element,
    )
    db.add(tc)
    await db.commit()
    await db.refresh(tc)
    return _tc_to_dict(tc)


async def update_test_case(
    db: AsyncSession,
    test_case_id: int,
    title: str | None = None,
    case_type: str | None = None,
    precondition: str | None = None,
    steps: str | None = None,
    expected_result: str | None = None,
    related_api: str | None = None,
    related_element: str | None = None,
) -> dict:
    tc = await _get_tc_or_fail(db, test_case_id)

    req_stmt = select(Requirement).where(Requirement.id == tc.requirement_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req and req.status != "drafting_tests":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "需求状态不允许编辑测试用例")

    if title is not None:
        tc.title = title
    if case_type is not None:
        tc.case_type = case_type
    if precondition is not None:
        tc.precondition = precondition
    if steps is not None:
        tc.steps = steps
    if expected_result is not None:
        tc.expected_result = expected_result
    if related_api is not None:
        tc.related_api = related_api
    if related_element is not None:
        tc.related_element = related_element

    await db.commit()
    await db.refresh(tc)
    return _tc_to_dict(tc)


async def delete_test_case(db: AsyncSession, test_case_id: int) -> dict:
    tc = await _get_tc_or_fail(db, test_case_id)

    req_stmt = select(Requirement).where(Requirement.id == tc.requirement_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req and req.status != "drafting_tests":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "需求状态不允许删除测试用例")

    tc.is_deleted = True
    tc.deleted_at = datetime.utcnow()
    await db.commit()
    return {"id": tc.id}


async def _get_tc_or_fail(db: AsyncSession, test_case_id: int) -> TestCase:
    stmt = select(TestCase).where(TestCase.id == test_case_id, TestCase.is_deleted == False)
    result = await db.execute(stmt)
    tc = result.scalar_one_or_none()
    if tc is None:
        raise BusinessError(ERR_NOT_FOUND, "测试用例不存在")
    return tc


def _tc_to_dict(tc: TestCase) -> dict:
    return {
        "id": tc.id,
        "requirement_id": tc.requirement_id,
        "case_number": tc.case_number,
        "title": tc.title,
        "case_type": tc.case_type,
        "precondition": tc.precondition,
        "steps": tc.steps,
        "expected_result": tc.expected_result,
        "related_api": tc.related_api,
        "related_element": tc.related_element,
        "created_at": tc.created_at.isoformat() if tc.created_at else None,
    }
