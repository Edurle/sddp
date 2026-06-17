from typing import Annotated, Any
import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_current_user, get_db_session, check_team_permission, _team_id_from_iteration, _team_id_from_requirement, _team_id_from_test_case
from app.exceptions import BusinessError, ERR_FORBIDDEN, ERR_NOT_FOUND, ERR_REQUIREMENT_STATUS, ERR_VALIDATION, ERR_FIELD_PATH_NOT_FOUND
from app.models import Requirement
from app.services import requirement as req_svc
from app.services import requirement_guide as rg_svc
from app.services import requirement_link as link_svc
from app.services import review_comment as rc_svc
from app.services import specification as spec_svc
from app.services import task as task_svc
from app.services import task_commit as commit_svc
from app.services import task_generator as tg_svc
from app.services import test_case as tc_svc
from app.services import test_generator as testgen_svc
from app.services.statistics import get_requirement_test_statistics

router = APIRouter()


_SUBMIT_REVIEW_PERM_MAP = {
    "drafting_req": "requirement:submit_review_req",
    "drafting_spec": "requirement:submit_review_spec",
    "drafting_tests": "requirement:submit_review_tests",
}


async def _check_submit_review_permission(
    db: AsyncSession, req_id: int, user: dict, fallback_perm: str,
) -> None:
    req_stmt = select(Requirement).where(Requirement.id == req_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req is not None and req.created_by == int(user["sub"]):
        return
    if user.get("is_admin"):
        return
    team_id = await _team_id_from_requirement(db, req_id)
    perm = _SUBMIT_REVIEW_PERM_MAP.get(req.status if req else None) or fallback_perm
    await check_team_permission(db, user, team_id, perm)


class CreateRequirementRequest(BaseModel):
    title: str
    req_type: str
    priority: int
    description: str | None = None
    type_detail: dict | None = None
    prototype_html: str | None = None


class UpdateRequirementRequest(BaseModel):
    title: str | None = None
    req_type: str | None = None
    priority: str | None = None
    description: str | None = None
    type_detail: dict | None = None
    prototype_html: str | None = None



class SubmitReviewRequest(BaseModel):
    reviewer_id: int


class ReviewRequest(BaseModel):
    action: str
    comment: str | None = None


class CreateTaskRequest(BaseModel):
    title: str
    description: str | None = None
    assignee_id: int | None = None
    task_type: str | None = None
    source_section: str | None = None
    spec_reference: dict | None = None


class GenerateTasksRequest(BaseModel):
    strategy: str = "hybrid"


class GenerateTestCasesRequest(BaseModel):
    case_types: list[str] | None = None


class CreateTestCaseRequest(BaseModel):
    title: str
    case_type: str
    precondition: str | None = None
    steps: str | None = None
    expected_result: str | None = None
    related_api: str | None = None
    related_element: str | None = None


class UpdateSpecificationRequest(BaseModel):
    content: dict


iterations_nested_router = APIRouter()


class DirectCreateRequirementRequest(BaseModel):
    title: str
    type: str
    priority: str | int = 0
    description: str | None = None
    type_detail: dict | None = None
    prototype_html: str | None = None
    iteration_id: int | None = None


class PatchRequirementRequest(BaseModel):
    status: str | None = None
    title: str | None = None
    description: str | None = None
    type_detail: dict | None = None
    prototype_html: str | None = None
    type_detail_path: str | None = None
    value: Any = None


def _clamp_pagination(offset: int, limit: int) -> tuple[int, int]:
    if offset < 0:
        offset = 0
    if limit < 1:
        limit = 1
    if limit > 200:
        limit = 200
    return offset, limit


@router.get("/guide")
async def get_requirement_guide(
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    data = rg_svc.get_requirement_guide()
    return {"code": 0, "message": "success", "data": data}


@router.get("")
async def list_requirements_global(
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(default=None),
    iteration_id: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1),
) -> dict:
    offset, limit = _clamp_pagination(offset, limit)

    base_where = [Requirement.is_deleted == False]
    if status:
        base_where.append(Requirement.status == status)
    if iteration_id is not None:
        base_where.append(Requirement.iteration_id == iteration_id)

    from sqlalchemy import func

    count_stmt = select(func.count()).select_from(Requirement).where(*base_where)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = select(Requirement).where(*base_where)
    stmt = stmt.order_by(Requirement.created_at.desc())
    stmt = stmt.offset(offset).limit(limit + 1)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = []
    for req in rows:
        items.append({
            "id": req.id,
            "iteration_id": req.iteration_id,
            "title": req.title,
            "req_type": req.req_type,
            "priority": req.priority,
            "status": req.status,
            "description": req.description,
            "created_by": req.created_by,
            "created_at": req.created_at.isoformat() if req.created_at else None,
            "updated_at": req.updated_at.isoformat() if req.updated_at else None,
        })
    return {
        "code": 0,
        "message": "success",
        "data": {
            "items": items,
            "total": total,
            "offset": offset,
            "limit": limit,
            "has_more": has_more,
        },
    }


@router.post("")
async def direct_create_requirement(
    body: DirectCreateRequirementRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    from app.models import Team, TeamMember, Project, Iteration as IterModel
    import time

    iteration_id = body.iteration_id
    if iteration_id is None:
        user_id = int(user["sub"])
        stmt = select(TeamMember).where(TeamMember.user_id == user_id, TeamMember.is_deleted == False).limit(1)
        result = await db.execute(stmt)
        membership = result.scalar_one_or_none()
        if membership is None:
            team = Team(name=f"test-team-{user_id}", owner_id=user_id)
            db.add(team)
            await db.flush()
            member = TeamMember(team_id=team.id, user_id=user_id)
            db.add(member)
            await db.flush()
        else:
            stmt2 = select(Team).where(Team.id == membership.team_id, Team.is_deleted == False)
            r2 = await db.execute(stmt2)
            team = r2.scalar_one_or_none()
            if team is None:
                team = Team(name=f"test-team-{user_id}", owner_id=user_id)
                db.add(team)
                await db.flush()
                member = TeamMember(team_id=team.id, user_id=user_id)
                db.add(member)
                await db.flush()

        stmt3 = select(Project).where(Project.team_id == team.id, Project.is_deleted == False).limit(1)
        r3 = await db.execute(stmt3)
        project = r3.scalar_one_or_none()
        if project is None:
            project = Project(team_id=team.id, name=f"test-project-{team.id}", status="active")
            db.add(project)
            await db.flush()

        stmt4 = select(IterModel).where(IterModel.project_id == project.id).limit(1)
        r4 = await db.execute(stmt4)
        iteration = r4.scalar_one_or_none()
        if iteration is None:
            from datetime import date
            iteration = IterModel(
                project_id=project.id,
                name=f"Sprint 1",
                start_date=date(2026, 1, 1),
                end_date=date(2026, 3, 31),
                status="in_progress",
            )
            db.add(iteration)
            await db.flush()
        iteration_id = iteration.id

    priority_val = body.priority
    if isinstance(priority_val, str):
        pmap = {"high": 3, "medium": 2, "low": 1}
        priority_val = pmap.get(priority_val, 0)

    data = await req_svc.create_requirement(
        db, iteration_id, int(user["sub"]),
        body.title, body.type, priority_val,
        body.description, body.type_detail,
        body.prototype_html,
    )
    return {"code": 0, "message": "success", "data": data}


@router.patch("/{id}")
async def patch_requirement(
    id: int,
    body: PatchRequirementRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, id), "requirement:edit")
    from app.models import Requirement
    from app.services.requirement import VALID_STATUS_TRANSITIONS, EDITABLE_STATUSES
    stmt = select(Requirement).where(Requirement.id == id, Requirement.is_deleted == False)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    has_field_edits = any(v is not None for v in [
        body.title, body.description, body.type_detail, body.prototype_html, body.type_detail_path
    ])
    if has_field_edits and req.status not in EDITABLE_STATUSES:
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前状态不允许编辑")

    if body.type_detail is not None and body.type_detail_path is not None:
        raise BusinessError(
            ERR_VALIDATION,
            "type_detail_path 与 type_detail 不可同时提供，二选一。",
        )

    if body.type_detail_path is not None:
        from app.services.path_utils import (
            PathSyntaxError, PathNotFoundError, MultipleMatchError, set_by_path,
        )
        base = req.type_detail if isinstance(req.type_detail, dict) else {}
        if not base:
            raise BusinessError(
                ERR_FIELD_PATH_NOT_FOUND,
                "路径不存在：type_detail 当前为空，无法下钻。请先用 type_detail 整体设置初始结构。",
            )
        full_path = f"type_detail.{body.type_detail_path}"
        try:
            new_td = set_by_path({"type_detail": base}, full_path, body.value)["type_detail"]
        except PathSyntaxError as e:
            raise BusinessError(ERR_VALIDATION, str(e))
        except MultipleMatchError as e:
            raise BusinessError(ERR_VALIDATION, str(e))
        except PathNotFoundError as e:
            raise BusinessError(ERR_FIELD_PATH_NOT_FOUND, str(e))
        req.type_detail = new_td
        await db.commit()
        await db.refresh(req)
        return {"code": 0, "message": "success", "data": {"id": req.id, "status": req.status}}

    if body.status is not None and body.status != req.status:
        allowed = VALID_STATUS_TRANSITIONS.get(req.status, set())
        if body.status not in allowed:
            raise BusinessError(ERR_REQUIREMENT_STATUS, f"不允许从 {req.status} 转换到 {body.status}")
        req.status = body.status

    if body.title is not None:
        req.title = body.title
    if body.description is not None:
        req.description = body.description
    if body.type_detail is not None:
        req.type_detail = body.type_detail
    if body.prototype_html is not None:
        req.prototype_html = body.prototype_html
    await db.commit()
    await db.refresh(req)
    return {"code": 0, "message": "success", "data": {"id": req.id, "status": req.status}}


_REVIEW_PERM_MAP = {
    "reviewing_req": "requirement:review_req",
    "reviewing_spec": "requirement:review_spec",
    "reviewing_tests": "requirement:review_tests",
}


@router.post("/{id}/approve")
async def approve_requirement_direct(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    from app.exceptions import BusinessError, ERR_NOT_FOUND
    from app.models import Requirement as ReqModel, RequirementReview
    stmt = select(ReqModel).where(ReqModel.id == id, ReqModel.is_deleted == False)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    review_perm = _REVIEW_PERM_MAP.get(req.status)
    if review_perm:
        await check_team_permission(db, user, await _team_id_from_requirement(db, id), review_perm)

    approve_map = {
        "reviewing_req": "drafting_spec",
        "reviewing_spec": "drafting_tests",
        "reviewing_tests": "approved",
    }
    new_status = approve_map.get(req.status)
    if new_status:
        req.status = new_status

    rev_stmt = select(RequirementReview).where(
        RequirementReview.requirement_id == id,
        RequirementReview.status == "pending",
    ).order_by(RequirementReview.created_at.desc())
    rev_result = await db.execute(rev_stmt)
    review = rev_result.scalar_one_or_none()
    if review:
        review.status = "approved"
        from datetime import datetime, timezone
        review.reviewed_at = datetime.now(timezone.utc)
        review.reviewer_id = int(user["sub"])

    await db.commit()
    await db.refresh(req)
    return {"code": 0, "message": "success", "data": {"id": req.id, "status": req.status}}


@router.post("/{id}/spec")
async def save_spec_direct(
    id: int,
    body: dict,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, id), "specification:edit")
    content = body.get("content", "")
    if isinstance(content, str):
        content = {"text": content}
    data = await spec_svc.save_spec_document(db, id, int(user["sub"]), content)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/submit-spec-review")
async def submit_spec_review_direct(
    id: int,
    body: SubmitReviewRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await _check_submit_review_permission(db, id, user, "requirement:submit_review_spec")
    data = await req_svc.submit_review(db, id, int(user["sub"]), body.reviewer_id)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/approve-spec")
async def approve_spec_direct(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, id), "requirement:review_spec")
    from app.exceptions import BusinessError, ERR_NOT_FOUND
    from app.models import Requirement as ReqModel, RequirementReview
    stmt = select(ReqModel).where(ReqModel.id == id, ReqModel.is_deleted == False)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    approve_map = {
        "reviewing_spec": "drafting_tests",
    }
    new_status = approve_map.get(req.status)
    if new_status:
        req.status = new_status

    rev_stmt = select(RequirementReview).where(
        RequirementReview.requirement_id == id,
        RequirementReview.status == "pending",
    ).order_by(RequirementReview.created_at.desc())
    rev_result = await db.execute(rev_stmt)
    review = rev_result.scalar_one_or_none()
    if review:
        review.status = "approved"
        from datetime import datetime, timezone
        review.reviewed_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(req)
    return {"code": 0, "message": "success", "data": {"id": req.id, "status": req.status}}


@router.post("/{id}/submit-tests-review")
async def submit_tests_review_direct(
    id: int,
    body: SubmitReviewRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await _check_submit_review_permission(db, id, user, "requirement:submit_review_tests")
    data = await req_svc.submit_review(db, id, int(user["sub"]), body.reviewer_id)
    return {"code": 0, "message": "success", "data": data}


@iterations_nested_router.get("/{iterationId}/requirements")
async def list_iteration_requirements(
    iterationId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(default=None),
    req_type: str | None = Query(default=None),
    sort_by: str | None = Query(default=None),
    sort_order: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1),
) -> dict:
    offset, limit = _clamp_pagination(offset, limit)
    data = await req_svc.list_requirements(
        db, iterationId, int(user["sub"]), status, req_type, sort_by, sort_order,
        offset=offset, limit=limit,
    )
    return {"code": 0, "message": "success", "data": data}


@iterations_nested_router.post("/{iterationId}/requirements")
async def create_iteration_requirement(
    iterationId: int,
    body: CreateRequirementRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_iteration(db, iterationId), "requirement:create")
    data = await req_svc.create_requirement(
        db, iterationId, int(user["sub"]),
        body.title, body.req_type, body.priority,
        body.description, body.type_detail,
        body.prototype_html,
    )
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}/full-context")
async def get_requirement_full_context(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    from app.models import Requirement as ReqModel, TestCase as TCModel
    from app.exceptions import BusinessError, ERR_NOT_FOUND

    stmt = select(ReqModel).where(ReqModel.id == id, ReqModel.is_deleted == False)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    from app.services import specification as spec_svc
    from app.services import task as task_svc
    from app.services import test_case as tc_svc

    requirement_data = req_svc._req_to_dict(req)

    spec = None
    try:
        spec = await spec_svc.get_spec_document(db, id)
    except Exception:
        logging.getLogger(__name__).exception("failed to load spec for requirement %s", id)

    task_list = await task_svc.list_tasks(db, id)
    task_items = task_list["items"]

    tc_list = await tc_svc.list_test_cases(db, id)
    tc_items = tc_list["items"]

    return {
        "code": 0,
        "message": "success",
        "data": {
            "requirement": requirement_data,
            "spec": spec,
            "tasks": task_items,
            "test_cases": tc_items,
        },
    }


@router.get("/{id}")
async def get_requirement(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await req_svc.get_requirement_detail(db, id, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.put("/{id}")
async def update_requirement(
    id: int,
    body: UpdateRequirementRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, id), "requirement:edit")
    data = await req_svc.update_requirement(
        db, id, int(user["sub"]),
        body.title, body.req_type, body.priority,
        body.description, body.type_detail,
        body.prototype_html,
    )
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{id}")
async def delete_requirement(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, id), "requirement:delete")
    data = await req_svc.delete_requirement(db, id, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/submit-review")
async def submit_review(
    id: int,
    body: SubmitReviewRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await _check_submit_review_permission(db, id, user, "requirement:submit_review_req")
    data = await req_svc.submit_review(db, id, int(user["sub"]), body.reviewer_id, user.get("is_admin", False))
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/review")
async def review_requirement(
    id: int,
    body: ReviewRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await req_svc.review_requirement(
        db, id, int(user["sub"]), body.action, body.comment,
        user.get("permissions", []),
    )
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}/review-comments")
async def get_review_comments(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await rc_svc.list_review_comments(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}/test-statistics")
async def get_req_test_stats(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await get_requirement_test_statistics(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{reqId}/test-cases")
async def list_test_cases(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    case_type: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1),
) -> dict:
    offset, limit = _clamp_pagination(offset, limit)
    data = await tc_svc.list_test_cases(db, reqId, case_type=case_type, offset=offset, limit=limit)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{reqId}/test-cases")
async def create_test_case(
    reqId: int,
    body: CreateTestCaseRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, reqId), "test_case:create")
    data = await tc_svc.create_test_case(
        db, reqId,
        title=body.title,
        case_type=body.case_type,
        precondition=body.precondition,
        steps=body.steps,
        expected_result=body.expected_result,
        related_api=body.related_api,
        related_element=body.related_element,
    )
    return {"code": 0, "message": "success", "data": data}


@router.get("/{reqId}/tasks")
async def list_tasks(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    status: str | None = Query(default=None),
    assignee_id: int | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1),
) -> dict:
    offset, limit = _clamp_pagination(offset, limit)
    data = await task_svc.list_tasks(db, reqId, status=status, assignee_id=assignee_id, offset=offset, limit=limit)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{reqId}/tasks")
async def create_task(
    reqId: int,
    body: CreateTaskRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, reqId), "task:create")
    data = await task_svc.create_task(
        db, reqId, int(user["sub"]),
        title=body.title,
        description=body.description,
        assignee_id=body.assignee_id,
        task_type=body.task_type,
        source_section=body.source_section,
        spec_reference=body.spec_reference,
    )
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/generate-tasks")
async def generate_tasks_endpoint(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    body: GenerateTasksRequest | None = None,
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, id), "task:create")
    strategy = body.strategy if body else "hybrid"
    data = await tg_svc.generate_tasks(db, id, int(user["sub"]), strategy)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/generate-test-cases")
async def generate_test_cases_endpoint(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    body: GenerateTestCasesRequest | None = None,
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, id), "test_case:create")
    case_types = body.case_types if body else None
    data = await testgen_svc.generate_test_cases(db, id, int(user["sub"]), case_types)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{reqId}/specification")
async def get_specification(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await spec_svc.get_spec_document(db, reqId)
    return {"code": 0, "message": "success", "data": data}


@router.put("/{reqId}/specification")
async def update_specification(
    reqId: int,
    body: UpdateSpecificationRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, reqId), "specification:edit")
    data = await spec_svc.save_spec_document(db, reqId, int(user["sub"]), body.content)
    return {"code": 0, "message": "success", "data": data}


class SetSpecDraftFieldRequest(BaseModel):
    path: str
    value: Any = None


@router.patch("/{reqId}/specification/draft/field")
async def set_spec_draft_field(
    reqId: int,
    body: SetSpecDraftFieldRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, reqId), "specification:edit")
    data = await spec_svc.set_spec_draft_field(
        db, reqId, int(user["sub"]), body.path, body.value
    )
    return {"code": 0, "message": "success", "data": data}


@router.post("/{reqId}/specification/commit")
async def commit_spec_draft(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, reqId), "specification:edit")
    data = await spec_svc.commit_spec_draft(db, reqId, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{reqId}/specification/draft")
async def discard_spec_draft(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, reqId), "specification:edit")
    data = await spec_svc.discard_spec_draft(db, reqId)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{reqId}/specification/versions")
async def list_specification_versions(
    reqId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await spec_svc.list_spec_versions(db, reqId)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{reqId}/specification/versions/{version}")
async def get_specification_version(
    reqId: int,
    version: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await spec_svc.get_spec_version_detail(db, reqId, version)
    return {"code": 0, "message": "success", "data": data}


class SupersedeRequest(BaseModel):
    title: str | None = None
    description: str | None = None


class CreateLinkRequest(BaseModel):
    target_id: int
    link_type: str


@router.post("/{id}/supersede")
async def supersede_requirement(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    body: SupersedeRequest | None = None,
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, id), "requirement:create")
    title = body.title if body else None
    description = body.description if body else None
    data = await link_svc.supersede_requirement(db, id, int(user["sub"]), title, description)
    return {"code": 0, "message": "success", "data": data}


@router.post("/{id}/links")
async def create_requirement_link(
    id: int,
    body: CreateLinkRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, id), "requirement:edit")
    data = await link_svc.create_link(db, id, body.target_id, body.link_type, int(user["sub"]))
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}/links")
async def list_requirement_links(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await link_svc.list_links(db, id)
    return {"code": 0, "message": "success", "data": data}


@router.delete("/{id}/links/{linkId}")
async def delete_requirement_link(
    id: int,
    linkId: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    await check_team_permission(db, user, await _team_id_from_requirement(db, id), "requirement:edit")
    data = await link_svc.delete_link(db, id, linkId)
    return {"code": 0, "message": "success", "data": data}


@router.get("/{id}/commits")
async def list_requirement_commits(
    id: int,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    data = await commit_svc.list_requirement_commits(db, id)
    return {"code": 0, "message": "success", "data": data}
