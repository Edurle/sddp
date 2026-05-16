from fastapi import APIRouter

from app.api import (
    auth,
    invitations,
    iterations,
    projects,
    requirements,
    tasks,
    teams,
    test_cases,
    test_executions,
    users,
    admin,
    webhooks,
)

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(admin.router, prefix="/admin", tags=["admin"])
router.include_router(teams.router, prefix="/teams", tags=["teams"])
router.include_router(webhooks.teams_nested_router, prefix="/teams", tags=["webhooks"])
router.include_router(invitations.router, prefix="/invitations", tags=["invitations"])

router.include_router(projects.teams_nested_router, prefix="/teams", tags=["projects"])
router.include_router(projects.router, prefix="/projects", tags=["projects"])

router.include_router(
    iterations.projects_nested_router, prefix="/projects", tags=["iterations"]
)
router.include_router(iterations.router, prefix="/iterations", tags=["iterations"])

router.include_router(
    requirements.iterations_nested_router, prefix="/iterations", tags=["requirements"]
)
router.include_router(requirements.router, prefix="/requirements", tags=["requirements"])

router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
router.include_router(test_cases.router, prefix="/test-cases", tags=["test-cases"])
router.include_router(
    test_executions.router, prefix="/test-executions", tags=["test-executions"]
)
router.include_router(
    test_executions.records_router,
    prefix="/test-execution-records",
    tags=["test-executions"],
)
