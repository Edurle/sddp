from datetime import datetime

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BusinessError, ERR_CREDENTIALS, ERR_NOT_FOUND, ERR_VALIDATION, ERR_EMAIL_EXISTS
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.role import Role, MemberRole
from app.models.project import Project
from app.models.iteration import Iteration
from app.models.requirement import Requirement
from app.models.requirement_review import RequirementReview
from app.models.task import Task
from app.utils.security import hash_password, verify_password
from app.utils.pagination import paginate
from app.services import invitation as inv_svc


async def get_user_info(db: AsyncSession, user_id: int) -> dict:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise BusinessError(ERR_NOT_FOUND, "用户不存在")

    teams = await _get_user_teams(db, user_id)

    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "is_admin": user.is_admin,
        "teams": teams,
    }


async def _get_user_teams(db: AsyncSession, user_id: int) -> list[dict]:
    stmt = (
        select(Team.id, Team.name)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user_id, TeamMember.is_deleted == False, Team.is_deleted == False)
    )
    result = await db.execute(stmt)
    teams = result.all()

    team_list = []
    for team_id, team_name in teams:
        role_names = await _get_team_role_names(db, user_id, team_id)
        team_list.append({
            "id": team_id,
            "name": team_name,
            "role_names": role_names,
        })

    return team_list


async def _get_team_role_names(db: AsyncSession, user_id: int, team_id: int) -> list[str]:
    member_stmt = select(TeamMember.id).where(
        TeamMember.user_id == user_id, TeamMember.team_id == team_id, TeamMember.is_deleted == False
    )
    member_result = await db.execute(member_stmt)
    member_row = member_result.first()
    if member_row is None:
        return []

    member_id = member_row[0]
    role_stmt = (
        select(Role.name)
        .join(MemberRole, MemberRole.role_id == Role.id)
        .where(MemberRole.member_id == member_id, Role.is_deleted == False)
    )
    role_result = await db.execute(role_stmt)
    return [row[0] for row in role_result.all()]


async def update_profile(db: AsyncSession, user_id: int, nickname: str | None = None, avatar: str | None = None) -> dict:
    if nickname is None and avatar is None:
        raise BusinessError(ERR_VALIDATION, "至少提供一个字段")
    if nickname is not None and (len(nickname) < 2 or len(nickname) > 32):
        raise BusinessError(ERR_VALIDATION, "昵称长度须为2-32个字符")

    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise BusinessError(ERR_NOT_FOUND, "用户不存在")

    if nickname is not None:
        user.nickname = nickname
    if avatar is not None:
        user.avatar = avatar

    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "avatar": user.avatar,
        "is_admin": user.is_admin,
    }


async def change_password(db: AsyncSession, user_id: int, old_password: str, new_password: str) -> dict:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise BusinessError(ERR_NOT_FOUND, "用户不存在")

    if not verify_password(old_password, user.password_hash):
        raise BusinessError(ERR_CREDENTIALS, "原密码错误")

    user.password_hash = hash_password(new_password)
    await db.commit()

    return {"message": "密码修改成功"}


async def get_pending_items(db: AsyncSession, user_id: int) -> dict:
    teams = await _get_user_teams_detailed(db, user_id)

    team_ids = [t["id"] for t in teams]
    projects = await _get_user_projects(db, team_ids)

    project_ids = [p["id"] for p in projects]
    active_iterations = await _get_active_iterations(db, project_ids)

    assigned_tasks = await _get_assigned_tasks(db, user_id)

    pending_reviews = await _get_pending_reviews(db, user_id)

    return {
        "teams": teams,
        "projects": projects,
        "active_iterations": active_iterations,
        "assigned_tasks": assigned_tasks,
        "pending_reviews": pending_reviews,
        "pending_tasks": assigned_tasks,
        "pending_invitations": await inv_svc.get_pending_invitations(db, user_id),
    }


async def get_pending_reviews(db: AsyncSession, user_id: int) -> list[dict]:
    return await _get_pending_reviews(db, user_id)


async def _get_user_teams_detailed(db: AsyncSession, user_id: int) -> list[dict]:
    stmt = (
        select(Team.id, Team.name, Team.owner_id)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == user_id, TeamMember.is_deleted == False, Team.is_deleted == False)
    )
    result = await db.execute(stmt)
    rows = result.all()
    items = []
    for team_id, team_name, owner_id in rows:
        role_names = await _get_team_role_names(db, user_id, team_id)
        items.append({
            "id": team_id,
            "name": team_name,
            "role": role_names[0] if role_names else "member",
        })
    return items


async def _get_user_projects(db: AsyncSession, team_ids: list[int]) -> list[dict]:
    if not team_ids:
        return []
    stmt = select(Project).where(
        Project.team_id.in_(team_ids),
        Project.is_deleted == False,
    )
    result = await db.execute(stmt)
    projects = result.scalars().all()
    return [
        {"id": p.id, "name": p.name, "team_id": p.team_id, "status": p.status}
        for p in projects
    ]


async def _get_active_iterations(db: AsyncSession, project_ids: list[int]) -> list[dict]:
    if not project_ids:
        return []
    stmt = select(Iteration).where(
        Iteration.project_id.in_(project_ids),
        Iteration.status.in_(["in_progress", "planned"]),
    )
    result = await db.execute(stmt)
    iterations = result.scalars().all()
    return [
        {"id": i.id, "name": i.name, "project_id": i.project_id, "status": i.status}
        for i in iterations
    ]


async def _get_assigned_tasks(db: AsyncSession, user_id: int) -> list[dict]:
    from app.services.task import list_tasks_by_assignee
    result = await list_tasks_by_assignee(db, user_id)
    return result["items"]


async def _get_pending_reviews(db: AsyncSession, user_id: int) -> list[dict]:
    stmt = (
        select(RequirementReview)
        .where(RequirementReview.reviewer_id == user_id, RequirementReview.status == "pending")
        .order_by(RequirementReview.created_at.desc())
    )
    result = await db.execute(stmt)
    reviews = result.scalars().all()
    items = []
    for r in reviews:
        req_stmt = select(Requirement).where(Requirement.id == r.requirement_id)
        req_result = await db.execute(req_stmt)
        req = req_result.scalar_one_or_none()
        items.append({
            "review_id": r.id,
            "requirement_id": r.requirement_id,
            "requirement_title": req.title if req else None,
            "review_type": r.review_type,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return items


async def list_users(db: AsyncSession, page: int, page_size: int, search: str = "") -> dict:
    stmt = select(User).order_by(User.id)
    if search:
        stmt = stmt.where(
            or_(
                User.email.contains(search),
                User.nickname.contains(search),
            )
        )
    result = await paginate(stmt, page, page_size, db)
    items = []
    for user in result["items"]:
        items.append({
            "id": user.id,
            "email": user.email,
            "nickname": user.nickname,
            "is_active": user.is_active,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        })
    return {
        "page": result["page"],
        "page_size": result["page_size"],
        "total": result["total"],
        "items": items,
    }


async def create_user_by_admin(db: AsyncSession, email: str, nickname: str, password: str) -> dict:
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    if result.scalar_one_or_none() is not None:
        raise BusinessError(ERR_EMAIL_EXISTS, "邮箱已注册")

    user = User(
        email=email,
        nickname=nickname,
        password_hash=hash_password(password),
        email_verified=True,
        is_active=True,
        is_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "email": user.email,
        "nickname": user.nickname,
        "is_active": user.is_active,
        "is_admin": user.is_admin,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


async def toggle_user_status(db: AsyncSession, target_user_id: int, is_active: bool, admin_user_id: int) -> dict:
    if target_user_id == admin_user_id and not is_active:
        raise BusinessError(ERR_VALIDATION, "不能禁用自己")

    stmt = select(User).where(User.id == target_user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise BusinessError(ERR_NOT_FOUND, "用户不存在")

    user.is_active = is_active
    await db.commit()
    await db.refresh(user)

    return {
        "id": user.id,
        "is_active": user.is_active,
    }


async def reset_user_password(db: AsyncSession, user_id: int, new_password: str) -> dict:
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise BusinessError(ERR_NOT_FOUND, "用户不存在")

    user.password_hash = hash_password(new_password)
    await db.commit()

    return {"message": "密码重置成功"}


async def get_projects_tree(db: AsyncSession, user_id: int) -> list[dict]:
    team_ids_stmt = (
        select(TeamMember.team_id)
        .where(TeamMember.user_id == user_id, TeamMember.is_deleted == False)
    )
    team_result = await db.execute(team_ids_stmt)
    team_ids = [row[0] for row in team_result.all()]

    if not team_ids:
        return []

    project_stmt = (
        select(Project)
        .where(Project.team_id.in_(team_ids), Project.is_deleted == False)
        .order_by(Project.created_at.desc())
    )
    project_result = await db.execute(project_stmt)
    projects = project_result.scalars().all()

    result = []
    for proj in projects:
        iter_stmt = (
            select(Iteration)
            .where(Iteration.project_id == proj.id)
            .order_by(Iteration.created_at.desc())
        )
        iter_result = await db.execute(iter_stmt)
        iterations = iter_result.scalars().all()

        iter_list = []
        for it in iterations:
            req_stmt = (
                select(Requirement)
                .where(Requirement.iteration_id == it.id, Requirement.is_deleted == False)
                .order_by(Requirement.priority.desc(), Requirement.created_at.asc())
            )
            req_result = await db.execute(req_stmt)
            requirements = req_result.scalars().all()

            req_list = []
            for r in requirements:
                task_stmt = select(Task).where(Task.requirement_id == r.id).order_by(Task.created_at.asc())
                task_result = await db.execute(task_stmt)
                tasks = task_result.scalars().all()
                req_list.append({
                    "id": r.id,
                    "title": r.title,
                    "status": r.status,
                    "req_type": r.req_type,
                    "priority": r.priority,
                    "tasks": [
                        {"id": t.id, "title": t.title, "status": t.status, "assignee_id": t.assignee_id}
                        for t in tasks
                    ],
                })

            iter_list.append({
                "id": it.id,
                "name": it.name,
                "status": it.status,
                "start_date": str(it.start_date) if it.start_date else None,
                "end_date": str(it.end_date) if it.end_date else None,
                "requirements": req_list,
            })

        result.append({
            "id": proj.id,
            "name": proj.name,
            "description": proj.description,
            "status": proj.status,
            "team_id": proj.team_id,
            "iterations": iter_list,
        })

    return result


async def get_user_work(db: AsyncSession, user_id: int) -> dict:
    pending_reviews = await _get_pending_reviews(db, user_id)

    from app.services.task import list_tasks_by_assignee
    assigned_result = await list_tasks_by_assignee(db, user_id)
    assigned_tasks = assigned_result["items"]

    teams = await _get_user_teams_detailed(db, user_id)
    team_ids = [t["id"] for t in teams]
    projects = await _get_user_projects(db, team_ids)
    project_ids = [p["id"] for p in projects]

    draftable_items = await _get_draftable_items(db, user_id, teams, project_ids)

    return {
        "pending_reviews": pending_reviews,
        "assigned_tasks": assigned_tasks,
        "draftable_items": draftable_items,
        "summary": {
            "reviews_waiting": len(pending_reviews),
            "tasks_in_progress": len([t for t in assigned_tasks if t.get("status") not in ("completed",)]),
            "items_to_draft": len(draftable_items),
        },
    }


async def _get_draftable_items(
    db: AsyncSession, user_id: int, teams: list[dict], project_ids: list[int],
) -> list[dict]:
    if not project_ids:
        return []

    role_map = {}
    for t in teams:
        role_map[t["id"]] = t.get("role", "member").lower()

    iter_stmt = select(Iteration).where(Iteration.project_id.in_(project_ids))
    iter_result = await db.execute(iter_stmt)
    iterations = iter_result.scalars().all()
    if not iterations:
        return []

    existing_projects = await _get_user_projects(db, list(set(t["id"] for t in teams)))
    project_team_map = {p["id"]: p["team_id"] for p in existing_projects}

    status_role_map = {
        "drafting_req": ["product_manager", "pm", "所有者"],
        "drafting_spec": ["developer", "开发", "所有者"],
        "drafting_tests": ["tester", "qa", "测试", "所有者"],
    }

    req_stmt = select(Requirement).where(
        Requirement.iteration_id.in_([i.id for i in iterations]),
        Requirement.is_deleted == False,
    )
    req_result = await db.execute(req_stmt)
    requirements = req_result.scalars().all()

    next_action_map = {
        "drafting_req": "write_requirement",
        "drafting_spec": "write_spec",
        "drafting_tests": "write_tests",
    }

    items = []
    for req in requirements:
        iter_obj = next((i for i in iterations if i.id == req.iteration_id), None)
        if iter_obj is None:
            continue
        team_id = project_team_map.get(iter_obj.project_id)
        if team_id is None:
            continue
        user_role = role_map.get(team_id, "")
        matching_roles = status_role_map.get(req.status, [])
        if not matching_roles:
            continue
        if user_role not in [r.lower() for r in matching_roles]:
            continue
        items.append({
            "id": req.id,
            "title": req.title,
            "status": req.status,
            "my_role": user_role,
            "next_action": next_action_map.get(req.status, "unknown"),
        })

    return items
