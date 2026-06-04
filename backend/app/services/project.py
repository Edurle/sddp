from datetime import date, datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    ERR_ACTIVE_ITERATIONS,
    ERR_FORBIDDEN,
    ERR_NOT_FOUND,
    ERR_REQUIREMENT_STATUS,
    ERR_VALIDATION,
)
from app.models import Iteration, Project, Team, TeamMember
from app.models.requirement import Requirement
from app.models.task import Task
from app.services import statistics as stat_svc


async def list_team_projects(
    db: AsyncSession, team_id: int, user_id: int, status: str | None = None
) -> list[dict]:
    await _check_member(db, team_id, user_id)

    stmt = select(Project).where(
        Project.team_id == team_id,
        Project.is_deleted == False,
    )
    if status:
        stmt = stmt.where(Project.status == status)
    stmt = stmt.order_by(Project.created_at.desc())

    result = await db.execute(stmt)
    projects = result.scalars().all()

    items = []
    for p in projects:
        d = _project_to_dict(p)
        active_iter = await _get_active_iteration(db, p.id)
        d["active_iteration"] = active_iter
        items.append(d)
    return items


async def create_project(
    db: AsyncSession,
    team_id: int,
    user_id: int,
    name: str,
    description: str | None = None,
    start_date: str | None = None,
) -> dict:
    if not name or not name.strip():
        from app.exceptions import BusinessError

        raise BusinessError(ERR_VALIDATION, "项目名称不能为空")

    await _check_member(db, team_id, user_id)

    sd = None
    if start_date:
        sd = date.fromisoformat(start_date)

    project = Project(
        team_id=team_id,
        name=name,
        description=description,
        start_date=sd,
        status="active",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return _project_to_dict(project)


async def get_project_detail(
    db: AsyncSession, project_id: int, user_id: int
) -> dict:
    project = await _get_project_or_fail(db, project_id)
    await _check_member(db, project.team_id, user_id)

    team = await _get_team(db, project.team_id)
    stats = await _get_project_statistics(db, project_id)

    result = _project_to_dict(project)
    result["team"] = _team_to_dict(team) if team else None
    result["statistics"] = stats
    return result


async def update_project(
    db: AsyncSession,
    project_id: int,
    user_id: int,
    name: str | None = None,
    description: str | None = None,
    start_date: str | None = None,
) -> dict:
    project = await _get_project_or_fail(db, project_id)
    await _check_member(db, project.team_id, user_id)

    if name is not None:
        project.name = name
    if description is not None:
        project.description = description
    if start_date is not None:
        project.start_date = date.fromisoformat(start_date)

    await db.commit()
    await db.refresh(project)
    return _project_to_dict(project)


async def archive_project(
    db: AsyncSession, project_id: int, user_id: int
) -> dict:
    from app.exceptions import BusinessError

    project = await _get_project_or_fail(db, project_id)
    await _check_member(db, project.team_id, user_id)

    if project.status == "archived":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "项目已归档")

    project.status = "archived"
    await db.commit()
    await db.refresh(project)
    return _project_to_dict(project)


async def delete_project(
    db: AsyncSession, project_id: int, user_id: int
) -> dict:
    from app.exceptions import BusinessError

    project = await _get_project_or_fail(db, project_id)
    await _check_member(db, project.team_id, user_id)

    active_count = await _count_active_iterations(db, project_id)
    if active_count > 0:
        raise BusinessError(ERR_ACTIVE_ITERATIONS, "存在进行中的迭代")

    project.is_deleted = True
    project.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": project.id}


async def get_project_test_statistics(
    db: AsyncSession, project_id: int, user_id: int
) -> dict:
    project = await _get_project_or_fail(db, project_id)
    await _check_member(db, project.team_id, user_id)
    from app.services.statistics import get_project_test_statistics as _get_proj_stats
    return await _get_proj_stats(db, project_id)


async def _get_project_or_fail(db: AsyncSession, project_id: int) -> Project:
    from app.exceptions import BusinessError

    stmt = select(Project).where(Project.id == project_id, Project.is_deleted == False)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise BusinessError(ERR_NOT_FOUND, "项目不存在")
    return project


async def _check_member(db: AsyncSession, team_id: int, user_id: int):
    from app.exceptions import BusinessError

    stmt = select(TeamMember).where(
        TeamMember.team_id == team_id,
        TeamMember.user_id == user_id,
        TeamMember.is_deleted == False,
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()
    if member is None:
        raise BusinessError(ERR_FORBIDDEN, "无权限")


async def _get_active_iteration(db: AsyncSession, project_id: int) -> dict | None:
    stmt = select(Iteration).where(
        Iteration.project_id == project_id,
        Iteration.status == "in_progress",
    )
    result = await db.execute(stmt)
    iteration = result.scalar_one_or_none()
    if iteration is None:
        return None
    return _iteration_to_dict(iteration)


async def _count_active_iterations(db: AsyncSession, project_id: int) -> int:
    stmt = select(func.count()).select_from(Iteration).where(
        Iteration.project_id == project_id,
        Iteration.status == "in_progress",
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def _get_project_statistics(db: AsyncSession, project_id: int) -> dict:
    iter_stmt = select(Iteration.id).where(Iteration.project_id == project_id)
    iter_result = await db.execute(iter_stmt)
    iter_ids = [row[0] for row in iter_result.all()]

    if not iter_ids:
        return {
            "total_requirements": 0,
            "completed_requirements": 0,
            "total_tasks": 0,
            "completed_tasks": 0,
            "test_pass_rate": 0,
        }

    req_total_stmt = select(func.count()).select_from(Requirement).where(
        Requirement.iteration_id.in_(iter_ids),
        Requirement.is_deleted == False,
    )
    req_total_result = await db.execute(req_total_stmt)
    total_reqs = req_total_result.scalar_one()

    req_completed_stmt = select(func.count()).select_from(Requirement).where(
        Requirement.iteration_id.in_(iter_ids),
        Requirement.is_deleted == False,
        Requirement.status == "approved",
    )
    req_completed_result = await db.execute(req_completed_stmt)
    completed_reqs = req_completed_result.scalar_one()

    task_stmt = select(Requirement.id).where(
        Requirement.iteration_id.in_(iter_ids),
        Requirement.is_deleted == False,
    )
    task_result = await db.execute(task_stmt)
    req_ids = [row[0] for row in task_result.all()]

    total_tasks = 0
    completed_tasks = 0
    if req_ids:
        tt_stmt = select(func.count()).select_from(Task).where(
            Task.requirement_id.in_(req_ids),
            Task.is_deleted == False,
        )
        tt_result = await db.execute(tt_stmt)
        total_tasks = tt_result.scalar_one()

        ct_stmt = select(func.count()).select_from(Task).where(
            Task.requirement_id.in_(req_ids),
            Task.is_deleted == False,
            Task.status == "completed",
        )
        ct_result = await db.execute(ct_stmt)
        completed_tasks = ct_result.scalar_one()

    test_pass_rate = 0.0
    if req_ids:
        total_cases = 0
        total_passed = 0
        for iid in iter_ids:
            iter_stat = await stat_svc.get_iteration_test_statistics(db, iid)
            total_cases += iter_stat["total_cases"]
            total_passed += iter_stat.get("latest_pass_rate", 0) * iter_stat["total_cases"]
        if total_cases > 0:
            test_pass_rate = total_passed / total_cases

    return {
        "total_requirements": total_reqs,
        "completed_requirements": completed_reqs,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "test_pass_rate": test_pass_rate,
    }


async def _get_team(db: AsyncSession, team_id: int) -> Team | None:
    stmt = select(Team).where(Team.id == team_id, Team.is_deleted == False)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def _project_to_dict(project: Project) -> dict:
    return {
        "id": project.id,
        "team_id": project.team_id,
        "name": project.name,
        "description": project.description,
        "start_date": project.start_date.isoformat() if project.start_date else None,
        "status": project.status,
        "is_deleted": project.is_deleted,
        "deleted_at": project.deleted_at.isoformat() if project.deleted_at else None,
        "created_at": project.created_at.isoformat() if project.created_at else None,
        "updated_at": project.updated_at.isoformat() if project.updated_at else None,
    }


def _iteration_to_dict(iteration: Iteration) -> dict:
    return {
        "id": iteration.id,
        "project_id": iteration.project_id,
        "name": iteration.name,
        "goal": iteration.goal,
        "start_date": iteration.start_date.isoformat() if iteration.start_date else None,
        "end_date": iteration.end_date.isoformat() if iteration.end_date else None,
        "status": iteration.status,
        "created_at": iteration.created_at.isoformat() if iteration.created_at else None,
        "updated_at": iteration.updated_at.isoformat() if iteration.updated_at else None,
    }


def _team_to_dict(team: Team) -> dict:
    return {
        "id": team.id,
        "name": team.name,
        "description": team.description,
        "owner_id": team.owner_id,
        "is_deleted": team.is_deleted,
        "created_at": team.created_at.isoformat() if team.created_at else None,
        "updated_at": team.updated_at.isoformat() if team.updated_at else None,
    }
