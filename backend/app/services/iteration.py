from datetime import date

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import (
    ERR_FORBIDDEN,
    ERR_NOT_FOUND,
    ERR_REQUIREMENT_STATUS,
    ERR_UNAUTHORIZED,
    ERR_UNCOMPLETED_REQS,
    ERR_UNCOMPLETED_TASKS,
    ERR_UNPASSED_TESTS,
    ERR_VALIDATION,
)
from app.models import Iteration, Project, Requirement, Task, TeamMember
from app.models.test_case import TestCase
from app.models.test_execution import TestExecutionRecord, TestExecutionRound


KANBAN_COLUMNS = [
    ("drafting_req", "编写需求"),
    ("reviewing_req", "需求审核中"),
    ("drafting_spec", "编写规范"),
    ("reviewing_spec", "规范审核中"),
    ("drafting_tests", "编写测试用例"),
    ("reviewing_tests", "测试用例审核中"),
    ("approved", "已通过"),
]


async def list_iterations(
    db: AsyncSession,
    project_id: int,
    user_id: int,
    status: str | None = None,
) -> list[dict]:
    project = await _get_project_or_fail(db, project_id)
    await _check_member_by_project(db, project, user_id)

    stmt = select(Iteration).where(Iteration.project_id == project_id)
    if status:
        stmt = stmt.where(Iteration.status == status)
    stmt = stmt.order_by(Iteration.created_at.desc())

    result = await db.execute(stmt)
    iterations = result.scalars().all()

    items = []
    for it in iterations:
        d = _iteration_to_dict(it)
        req_count = await _count_iteration_requirements(db, it.id)
        task_count = await _count_iteration_tasks(db, it.id)
        d["requirement_count"] = req_count
        d["task_count"] = task_count
        items.append(d)
    return items


async def create_iteration(
    db: AsyncSession,
    project_id: int,
    user_id: int,
    name: str,
    goal: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    from app.exceptions import BusinessError

    if not name or not name.strip():
        raise BusinessError(ERR_VALIDATION, "迭代名称不能为空")

    project = await _get_project_or_fail(db, project_id)
    await _check_member_by_project(db, project, user_id)

    sd = date.fromisoformat(start_date) if start_date else None
    ed = date.fromisoformat(end_date) if end_date else None

    if sd and ed and ed < sd:
        raise BusinessError(ERR_VALIDATION, "结束日期不能早于开始日期")

    iteration = Iteration(
        project_id=project_id,
        name=name,
        goal=goal,
        start_date=sd,
        end_date=ed,
        status="planned",
    )
    db.add(iteration)
    await db.commit()
    await db.refresh(iteration)
    return _iteration_to_dict(iteration)


async def get_iteration_detail(
    db: AsyncSession, iteration_id: int, user_id: int
) -> dict:
    iteration = await _get_iteration_or_fail(db, iteration_id)
    project = await _get_project_or_fail(db, iteration.project_id)
    await _check_member_by_project(db, project, user_id)

    stats = await _get_iteration_statistics(db, iteration_id)

    result = _iteration_to_dict(iteration)
    result["project"] = _project_to_dict(project)
    result["statistics"] = stats
    return result


async def update_iteration(
    db: AsyncSession,
    iteration_id: int,
    user_id: int,
    name: str | None = None,
    goal: str | None = None,
    end_date: str | None = None,
    start_date: str | None = None,
) -> dict:
    from app.exceptions import BusinessError

    iteration = await _get_iteration_or_fail(db, iteration_id)
    project = await _get_project_or_fail(db, iteration.project_id)
    await _check_member_by_project(db, project, user_id)

    if start_date is not None:
        raise BusinessError(ERR_UNAUTHORIZED, "不能修改开始日期")

    if iteration.status == "completed":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "已完成迭代不能修改")

    if name is not None:
        iteration.name = name
    if goal is not None:
        iteration.goal = goal
    if end_date is not None:
        iteration.end_date = date.fromisoformat(end_date)

    await db.commit()
    await db.refresh(iteration)
    return _iteration_to_dict(iteration)


async def start_iteration(
    db: AsyncSession, iteration_id: int, user_id: int
) -> dict:
    from app.exceptions import BusinessError

    iteration = await _get_iteration_or_fail(db, iteration_id)
    project = await _get_project_or_fail(db, iteration.project_id)
    await _check_member_by_project(db, project, user_id)

    if iteration.status != "planned":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "迭代状态不允许启动")

    iteration.status = "in_progress"
    await db.commit()
    await db.refresh(iteration)
    return _iteration_to_dict(iteration)


async def complete_iteration(
    db: AsyncSession, iteration_id: int, user_id: int
) -> dict:
    from app.exceptions import BusinessError

    iteration = await _get_iteration_or_fail(db, iteration_id)
    project = await _get_project_or_fail(db, iteration.project_id)
    await _check_member_by_project(db, project, user_id)

    if iteration.status != "in_progress":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "迭代状态不允许完成")

    uncompleted_reqs_stmt = select(func.count()).select_from(Requirement).where(
        Requirement.iteration_id == iteration_id,
        Requirement.is_deleted == False,
        Requirement.status != "approved",
    )
    uc_reqs_result = await db.execute(uncompleted_reqs_stmt)
    if uc_reqs_result.scalar_one() > 0:
        raise BusinessError(ERR_UNCOMPLETED_REQS, "存在未完成的需求")

    req_ids_stmt = select(Requirement.id).where(
        Requirement.iteration_id == iteration_id,
        Requirement.is_deleted == False,
    )
    req_ids_result = await db.execute(req_ids_stmt)
    req_ids = [row[0] for row in req_ids_result.all()]

    if req_ids:
        uncompleted_tasks_stmt = select(func.count()).select_from(Task).where(
            Task.requirement_id.in_(req_ids),
            Task.is_deleted == False,
            Task.status != "completed",
        )
        uc_tasks_result = await db.execute(uncompleted_tasks_stmt)
        if uc_tasks_result.scalar_one() > 0:
            raise BusinessError(ERR_UNCOMPLETED_TASKS, "存在未完成的任务")

        completed_tasks_stmt = select(Task.id).where(
            Task.requirement_id.in_(req_ids),
            Task.is_deleted == False,
            Task.status == "completed",
        )
        ct_result = await db.execute(completed_tasks_stmt)
        completed_task_ids = [row[0] for row in ct_result.all()]

        if completed_task_ids:
            round_stmt = select(TestExecutionRound.id).where(
                TestExecutionRound.task_id.in_(completed_task_ids)
            )
            round_result = await db.execute(round_stmt)
            round_ids = [row[0] for row in round_result.all()]

            if round_ids:
                latest_round_id = max(round_ids)
                failed_stmt = select(func.count()).select_from(
                    TestExecutionRecord
                ).where(
                    TestExecutionRecord.round_id == latest_round_id,
                    TestExecutionRecord.status != "passed",
                )
                failed_result = await db.execute(failed_stmt)
                if failed_result.scalar_one() > 0:
                    raise BusinessError(ERR_UNPASSED_TESTS, "存在未通过的测试")
            else:
                raise BusinessError(ERR_UNPASSED_TESTS, "存在未通过的测试")

    iteration.status = "completed"
    await db.commit()
    await db.refresh(iteration)
    return _iteration_to_dict(iteration)


async def get_iteration_kanban(
    db: AsyncSession, iteration_id: int, user_id: int
) -> dict:
    iteration = await _get_iteration_or_fail(db, iteration_id)
    project = await _get_project_or_fail(db, iteration.project_id)
    await _check_member_by_project(db, project, user_id)

    req_stmt = select(Requirement).where(
        Requirement.iteration_id == iteration_id,
        Requirement.is_deleted == False,
    )
    req_result = await db.execute(req_stmt)
    requirements = req_result.scalars().all()

    reqs_by_status: dict[str, list[dict]] = {}
    for r in requirements:
        reqs_by_status.setdefault(r.status, []).append(_requirement_to_dict(r))

    columns = []
    for status, display_name in KANBAN_COLUMNS:
        columns.append({
            "status": status,
            "display_name": display_name,
            "requirements": reqs_by_status.get(status, []),
        })

    return {"columns": columns}


async def get_iteration_statistics_detail(
    db: AsyncSession, iteration_id: int, user_id: int
) -> dict:
    iteration = await _get_iteration_or_fail(db, iteration_id)
    project = await _get_project_or_fail(db, iteration.project_id)
    await _check_member_by_project(db, project, user_id)

    return await _get_full_statistics(db, iteration_id)


async def get_iteration_test_statistics(
    db: AsyncSession, iteration_id: int, user_id: int
) -> dict:
    iteration = await _get_iteration_or_fail(db, iteration_id)
    project = await _get_project_or_fail(db, iteration.project_id)
    await _check_member_by_project(db, project, user_id)

    from app.services.statistics import get_iteration_test_statistics as _get_iter_stats
    return await _get_iter_stats(db, iteration_id)


async def _get_iteration_or_fail(db: AsyncSession, iteration_id: int) -> Iteration:
    from app.exceptions import BusinessError

    stmt = select(Iteration).where(Iteration.id == iteration_id)
    result = await db.execute(stmt)
    iteration = result.scalar_one_or_none()
    if iteration is None:
        raise BusinessError(ERR_NOT_FOUND, "迭代不存在")
    return iteration


async def _get_project_or_fail(db: AsyncSession, project_id: int) -> Project:
    from app.exceptions import BusinessError

    stmt = select(Project).where(Project.id == project_id, Project.is_deleted == False)
    result = await db.execute(stmt)
    project = result.scalar_one_or_none()
    if project is None:
        raise BusinessError(ERR_NOT_FOUND, "项目不存在")
    return project


async def _check_member_by_project(
    db: AsyncSession, project: Project, user_id: int
):
    from app.exceptions import BusinessError

    stmt = select(TeamMember).where(
        TeamMember.team_id == project.team_id,
        TeamMember.user_id == user_id,
        TeamMember.is_deleted == False,
    )
    result = await db.execute(stmt)
    member = result.scalar_one_or_none()
    if member is None:
        raise BusinessError(ERR_FORBIDDEN, "无权限")


async def _count_iteration_requirements(db: AsyncSession, iteration_id: int) -> int:
    stmt = select(func.count()).select_from(Requirement).where(
        Requirement.iteration_id == iteration_id,
        Requirement.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def _count_iteration_tasks(db: AsyncSession, iteration_id: int) -> int:
    req_stmt = select(Requirement.id).where(
        Requirement.iteration_id == iteration_id,
        Requirement.is_deleted == False,
    )
    req_result = await db.execute(req_stmt)
    req_ids = [row[0] for row in req_result.all()]
    if not req_ids:
        return 0

    stmt = select(func.count()).select_from(Task).where(
        Task.requirement_id.in_(req_ids),
        Task.is_deleted == False,
    )
    result = await db.execute(stmt)
    return result.scalar_one()


async def _get_iteration_statistics(db: AsyncSession, iteration_id: int) -> dict:
    req_total_stmt = select(func.count()).select_from(Requirement).where(
        Requirement.iteration_id == iteration_id,
        Requirement.is_deleted == False,
    )
    total_reqs = (await db.execute(req_total_stmt)).scalar_one()

    approved_reqs_stmt = select(func.count()).select_from(Requirement).where(
        Requirement.iteration_id == iteration_id,
        Requirement.is_deleted == False,
        Requirement.status == "approved",
    )
    approved_reqs = (await db.execute(approved_reqs_stmt)).scalar_one()

    req_ids_stmt = select(Requirement.id).where(
        Requirement.iteration_id == iteration_id,
        Requirement.is_deleted == False,
    )
    req_ids_result = await db.execute(req_ids_stmt)
    req_ids = [row[0] for row in req_ids_result.all()]

    total_tasks = 0
    completed_tasks = 0
    if req_ids:
        tt_stmt = select(func.count()).select_from(Task).where(
            Task.requirement_id.in_(req_ids),
            Task.is_deleted == False,
        )
        total_tasks = (await db.execute(tt_stmt)).scalar_one()

        ct_stmt = select(func.count()).select_from(Task).where(
            Task.requirement_id.in_(req_ids),
            Task.is_deleted == False,
            Task.status == "completed",
        )
        completed_tasks = (await db.execute(ct_stmt)).scalar_one()

    return {
        "total_requirements": total_reqs,
        "approved_requirements": approved_reqs,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "test_pass_rate": 0,
    }


async def _get_full_statistics(db: AsyncSession, iteration_id: int) -> dict:
    req_stmt = select(Requirement).where(
        Requirement.iteration_id == iteration_id,
        Requirement.is_deleted == False,
    )
    req_result = await db.execute(req_stmt)
    requirements = req_result.scalars().all()

    by_status: dict[str, int] = {}
    for r in requirements:
        by_status[r.status] = by_status.get(r.status, 0) + 1

    req_ids = [r.id for r in requirements]

    total_tasks = 0
    completed_tasks = 0
    total_cases = 0
    latest_pass_rate = 0.0

    if req_ids:
        tt_stmt = select(func.count()).select_from(Task).where(
            Task.requirement_id.in_(req_ids),
            Task.is_deleted == False,
        )
        total_tasks = (await db.execute(tt_stmt)).scalar_one()

        ct_stmt = select(func.count()).select_from(Task).where(
            Task.requirement_id.in_(req_ids),
            Task.is_deleted == False,
            Task.status == "completed",
        )
        completed_tasks = (await db.execute(ct_stmt)).scalar_one()

        tc_stmt = select(func.count()).select_from(TestCase).where(
            TestCase.requirement_id.in_(req_ids),
            TestCase.is_deleted == False,
        )
        total_cases = (await db.execute(tc_stmt)).scalar_one()

    return {
        "requirements": {
            "total": len(requirements),
            "by_status": by_status,
        },
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
        },
        "tests": {
            "total_cases": total_cases,
            "latest_pass_rate": latest_pass_rate,
        },
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


def _requirement_to_dict(req: Requirement) -> dict:
    return {
        "id": req.id,
        "iteration_id": req.iteration_id,
        "title": req.title,
        "req_type": req.req_type,
        "priority": req.priority,
        "status": req.status,
        "description": req.description,
        "type_detail": req.type_detail,
        "created_by": req.created_by,
        "is_deleted": req.is_deleted,
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "updated_at": req.updated_at.isoformat() if req.updated_at else None,
    }
