from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    BusinessError,
    ERR_FORBIDDEN,
    ERR_NOT_FOUND,
    ERR_NOT_REVIEWER,
    ERR_REJECT_NO_COMMENT,
    ERR_REQUIREMENT_STATUS,
    ERR_REVIEW_PROCESSED,
    ERR_VALIDATION,
)
from app.models import (
    Iteration,
    Project,
    Requirement,
    RequirementReview,
    Task,
    TeamMember,
    User,
)
from app.services import review_comment as rc_svc
from app.services import webhook as wh_svc


async def list_requirements(
    db: AsyncSession,
    iteration_id: int,
    user_id: int,
    status: str | None = None,
    req_type: str | None = None,
    sort_by: str | None = None,
    sort_order: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict:
    await _check_iteration_member(db, iteration_id, user_id)

    base_where = [
        Requirement.iteration_id == iteration_id,
        Requirement.is_deleted == False,
    ]
    if status:
        base_where.append(Requirement.status == status)
    if req_type:
        base_where.append(Requirement.req_type == req_type)

    count_stmt = select(func.count()).select_from(Requirement).where(*base_where)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one()

    stmt = select(Requirement).where(*base_where)

    if sort_by == "priority":
        if sort_order == "asc":
            stmt = stmt.order_by(Requirement.priority.asc())
        else:
            stmt = stmt.order_by(Requirement.priority.desc())
    elif sort_by == "created_at":
        if sort_order == "desc":
            stmt = stmt.order_by(Requirement.created_at.desc())
        else:
            stmt = stmt.order_by(Requirement.created_at.asc())
    else:
        stmt = stmt.order_by(Requirement.created_at.desc())

    stmt = stmt.offset(offset).limit(limit + 1)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    items = []
    for req in rows:
        task_count = await _count_tasks(db, req.id)
        items.append({
            "id": req.id,
            "title": req.title,
            "req_type": req.req_type,
            "priority": req.priority,
            "status": req.status,
            "task_count": task_count,
            "created_by": req.created_by,
            "created_at": req.created_at.isoformat() if req.created_at else None,
        })
    return {
        "items": items,
        "total": total,
        "offset": offset,
        "limit": limit,
        "has_more": has_more,
    }


async def create_requirement(
    db: AsyncSession,
    iteration_id: int,
    user_id: int,
    title: str,
    req_type: str,
    priority: int,
    description: str | None = None,
    type_detail: dict | None = None,
    prototype_html: str | None = None,
) -> dict:
    await _check_iteration_member(db, iteration_id, user_id)

    if not title or title.strip() == "":
        raise BusinessError(ERR_VALIDATION, "标题不能为空")

    if req_type not in ("feature", "optimization", "bug"):
        raise BusinessError(ERR_VALIDATION, "需求类型无效")

    req = Requirement(
        iteration_id=iteration_id,
        title=title,
        req_type=req_type,
        priority=priority,
        status="drafting_req",
        description=description,
        type_detail=type_detail,
        prototype_html=prototype_html,
        created_by=user_id,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    suggestions = []
    if not description or not description.strip():
        suggestions.append({"field": "description", "message": "需求描述为空，建议补充以帮助后续规范生成"})
    if not type_detail:
        if req_type == "bug":
            suggestions.append({"field": "type_detail", "message": "bug 类型建议填写复现步骤和严重程度"})
        elif req_type == "optimization":
            suggestions.append({"field": "type_detail", "message": "optimization 类型建议填写当前问题和预期改进"})
    if not prototype_html:
        suggestions.append({"field": "prototype_html", "message": "未提供原型图，建议提供以使页面设计更准确"})

    result = _req_to_dict(req)
    result["errors"] = []
    result["suggestions"] = suggestions
    return result


async def get_requirement_detail(
    db: AsyncSession, req_id: int, user_id: int
) -> dict:
    req = await _get_requirement_or_fail(db, req_id)

    iteration = await _get_iteration(db, req.iteration_id)
    iteration_data = None
    if iteration:
        project = await _get_project(db, iteration.project_id)
        iteration_data = {
            "id": iteration.id,
            "name": iteration.name,
            "project_id": iteration.project_id,
            "status": iteration.status,
            "project": {
                "id": project.id,
                "name": project.name,
                "team_id": project.team_id,
            } if project else None,
        }

    reviews = await _get_reviews(db, req.id)
    tasks = await _get_tasks(db, req.id)

    result = _req_to_dict(req)
    result["iteration"] = iteration_data
    result["current_step"] = req.status
    result["reviews"] = reviews
    result["tasks"] = tasks
    return result


async def update_requirement(
    db: AsyncSession,
    req_id: int,
    user_id: int,
    title: str | None = None,
    req_type: str | None = None,
    priority: str | None = None,
    description: str | None = None,
    type_detail: dict | None = None,
    prototype_html: str | None = None,
) -> dict:
    req = await _get_requirement_or_fail(db, req_id)

    if req.status != "drafting_req":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前状态不允许编辑")

    if title is not None:
        req.title = title
    if req_type is not None:
        req.req_type = req_type
    if priority is not None:
        req.priority = priority
    if description is not None:
        req.description = description
    if type_detail is not None:
        req.type_detail = type_detail
    if prototype_html is not None:
        req.prototype_html = prototype_html

    await db.commit()
    await db.refresh(req)
    return _req_to_dict(req)


async def delete_requirement(
    db: AsyncSession, req_id: int, user_id: int
) -> dict:
    req = await _get_requirement_or_fail(db, req_id)

    if req.status != "drafting_req":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前状态不允许删除")

    req.is_deleted = True
    req.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": req.id}


async def submit_review(
    db: AsyncSession, req_id: int, user_id: int, reviewer_id: int, is_admin: bool = False
) -> dict:
    req = await _get_requirement_or_fail(db, req_id)

    transition_map = {
        "drafting_req": ("reviewing_req", "requirement"),
        "drafting_spec": ("reviewing_spec", "specification"),
        "drafting_tests": ("reviewing_tests", "test_case"),
    }

    if req.status not in transition_map:
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前状态不允许提交审核")

    reviewer = await _get_user(db, reviewer_id)
    if reviewer is None:
        raise BusinessError(ERR_NOT_FOUND, "审核人不存在")

    new_status, review_type = transition_map[req.status]
    req.status = new_status

    review = RequirementReview(
        requirement_id=req.id,
        review_type=review_type,
        reviewer_id=reviewer_id,
        status="pending",
    )
    db.add(review)
    await db.commit()
    await _fire_review_event(db, req, "review.submitted", user_id)
    return {"id": review.id}


async def review_requirement(
    db: AsyncSession, req_id: int, user_id: int, action: str, comment: str | None = None,
    user_permissions: list[str] | None = None,
) -> dict:
    req = await _get_requirement_or_fail(db, req_id)

    stmt = select(RequirementReview).where(
        RequirementReview.requirement_id == req.id,
    ).order_by(RequirementReview.created_at.desc())
    result = await db.execute(stmt)
    review = result.scalars().first()

    if review is None or review.reviewer_id != user_id:
        raise BusinessError(ERR_NOT_REVIEWER, "不是指定的审核人")

    if review.status != "pending":
        raise BusinessError(ERR_REVIEW_PROCESSED, "审核已处理")

    permission_map = {
        "requirement": "requirement:review_req",
        "specification": "requirement:review_spec",
        "test_case": "requirement:review_tests",
    }

    required_perm = permission_map.get(review.review_type)
    if required_perm and user_permissions:
        if required_perm not in user_permissions:
            raise BusinessError(ERR_FORBIDDEN, "无权限")

    approve_transitions = {
        "reviewing_req": "drafting_spec",
        "reviewing_spec": "drafting_tests",
        "reviewing_tests": "approved",
    }

    reject_transitions = {
        "reviewing_req": "drafting_req",
        "reviewing_spec": "drafting_spec",
        "reviewing_tests": "drafting_tests",
    }

    if action == "approve":
        if req.status in approve_transitions:
            req.status = approve_transitions[req.status]
        review.status = "approved"
    elif action == "reject":
        if not comment or comment.strip() == "":
            raise BusinessError(ERR_REJECT_NO_COMMENT, "拒绝审核时必须填写评论")
        if req.status in reject_transitions:
            req.status = reject_transitions[req.status]
        review.status = "rejected"

    review.comment = comment
    review.reviewed_at = datetime.now(timezone.utc)
    await rc_svc.create_review_comment(
        db, req.id, user_id, review.review_type, action, comment,
    )
    await db.commit()
    if action == "approve":
        await _fire_review_event(db, req, "review.approved", user_id, comment)
    elif action == "reject":
        await _fire_review_event(db, req, "review.rejected", user_id, comment)
    return {"id": review.id}


async def _check_iteration_member(db: AsyncSession, iteration_id: int, user_id: int):
    iteration = await _get_iteration(db, iteration_id)
    if iteration is None:
        raise BusinessError(ERR_NOT_FOUND, "迭代不存在")
    project = await _get_project(db, iteration.project_id)
    if project is None:
        raise BusinessError(ERR_FORBIDDEN, "无权限")
    member = await _find_team_member(db, project.team_id, user_id)
    if member is None:
        raise BusinessError(ERR_FORBIDDEN, "无权限")


async def _get_requirement_or_fail(db: AsyncSession, req_id: int) -> Requirement:
    stmt = select(Requirement).where(
        Requirement.id == req_id,
        Requirement.is_deleted == False,
    )
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    return req


async def _is_team_member(db: AsyncSession, req: Requirement, user_id: int) -> bool:
    iteration = await _get_iteration(db, req.iteration_id) if req.iteration_id else None
    if iteration is None:
        return False
    project = await _get_project(db, iteration.project_id)
    if project is None:
        return False
    member = await _find_team_member(db, project.team_id, user_id)
    return member is not None


async def _get_iteration(db: AsyncSession, iteration_id: int) -> Iteration | None:
    stmt = select(Iteration).where(Iteration.id == iteration_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_project(db: AsyncSession, project_id: int) -> Project | None:
    stmt = select(Project).where(Project.id == project_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _get_user(db: AsyncSession, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _find_team_member(db: AsyncSession, team_id: int, user_id: int) -> TeamMember | None:
    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
        TeamMember.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _count_tasks(db: AsyncSession, req_id: int) -> int:
    stmt = select(func.count()).select_from(Task).where(
        Task.requirement_id == req_id,
        Task.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def _get_reviews(db: AsyncSession, req_id: int) -> list[dict]:
    stmt = select(RequirementReview).where(
        RequirementReview.requirement_id == req_id,
    ).order_by(RequirementReview.created_at.asc())
    result = await db.execute(stmt)
    reviews = result.scalars().all()
    return [
        {
            "id": r.id,
            "review_type": r.review_type,
            "reviewer_id": r.reviewer_id,
            "status": r.status,
            "comment": r.comment,
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        }
        for r in reviews
    ]


async def _get_tasks(db: AsyncSession, req_id: int) -> list[dict]:
    stmt = select(Task).where(
        Task.requirement_id == req_id,
        Task.is_deleted == False,
    ).order_by(Task.created_at.asc())
    result = await db.execute(stmt)
    tasks = result.scalars().all()
    return [
        {
            "id": t.id,
            "title": t.title,
            "status": t.status,
            "assignee_id": t.assignee_id,
            "created_by": t.created_by,
        }
        for t in tasks
    ]


def _req_to_dict(req: Requirement) -> dict:
    return {
        "id": req.id,
        "iteration_id": req.iteration_id,
        "title": req.title,
        "req_type": req.req_type,
        "priority": req.priority,
        "status": req.status,
        "description": req.description,
        "type_detail": req.type_detail,
        "prototype_html": req.prototype_html,
        "created_by": req.created_by,
        "is_deleted": req.is_deleted,
        "deleted_at": req.deleted_at.isoformat() if req.deleted_at else None,
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "updated_at": req.updated_at.isoformat() if req.updated_at else None,
    }


async def _fire_review_event(db, req, event, user_id, comment=None):
    iteration = await _get_iteration(db, req.iteration_id)
    if iteration is None:
        return
    project = await _get_project(db, iteration.project_id)
    if project is None:
        return
    await wh_svc.fire_event(
        db, project.team_id, event,
        {"requirement_id": req.id, "requirement_title": req.title, "reviewer_id": user_id, "comment": comment},
    )
