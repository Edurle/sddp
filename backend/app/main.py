import logging
from datetime import datetime, date, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import select

from app.database import init_db, async_session
from app.exceptions import BusinessError, ERR_UNAUTHORIZED, ERR_VALIDATION
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.utils.security import hash_password

logger = logging.getLogger(__name__)

app = FastAPI(title="SDD Backend", version="0.1.0")


async def _seed_data():
    async with async_session() as db:
        result = await db.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            return

        seed_users = [
            User(
                email="exist@example.com",
                nickname="已存在用户",
                password_hash=hash_password("Password123"),
                email_verified=True,
                is_active=True,
                is_admin=False,
            ),
            User(
                email="unverified@example.com",
                nickname="未验证用户",
                password_hash=hash_password("Password123"),
                email_verified=False,
                is_active=True,
                is_admin=False,
            ),
            User(
                email="admin@example.com",
                nickname="管理员",
                password_hash=hash_password("Admin1234!"),
                email_verified=True,
                is_active=True,
                is_admin=True,
            ),
        ]
        for u in seed_users:
            db.add(u)
        await db.flush()

        target_user = User(
            id=123,
            email="target@example.com",
            nickname="目标用户",
            password_hash=hash_password("Password123"),
            email_verified=True,
            is_active=True,
            is_admin=False,
        )
        db.add(target_user)
        await db.flush()

        existing_member_user = User(
            email="existingmember@example.com",
            nickname="已是成员",
            password_hash=hash_password("Password123"),
            email_verified=True,
            is_active=True,
            is_admin=False,
        )
        db.add(existing_member_user)
        await db.flush()

        new_user = User(
            email="newuser@example.com",
            nickname="新用户",
            password_hash=hash_password("Password123"),
            email_verified=True,
            is_active=True,
            is_admin=False,
        )
        db.add(new_user)
        await db.flush()

        reset_token = PasswordResetToken(
            user_id=seed_users[0].id,
            token="valid-test-token",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            used=False,
        )
        db.add(reset_token)
        await db.flush()

        from app.models import Team, TeamMember, Role, RolePermission, MemberRole, Project, Iteration

        team = Team(name="Test Team", description="A test team for E2E testing", owner_id=seed_users[2].id)
        db.add(team)
        await db.flush()

        owner_member = TeamMember(team_id=team.id, user_id=seed_users[2].id)
        db.add(owner_member)
        await db.flush()

        target_member = TeamMember(team_id=team.id, user_id=target_user.id)
        db.add(target_member)
        await db.flush()

        exist_member = TeamMember(team_id=team.id, user_id=seed_users[0].id)
        db.add(exist_member)
        await db.flush()

        existing_member_team = TeamMember(team_id=team.id, user_id=existing_member_user.id)
        db.add(existing_member_team)
        await db.flush()

        admin_role = Role(
            team_id=team.id, name="团队管理员", is_builtin=True,
            description="管理团队日常事务", slug="role-admin",
        )
        db.add(admin_role)
        await db.flush()
        admin_perms = [
            "project:create", "project:edit", "project:archive",
            "iteration:create", "iteration:edit", "iteration:start", "iteration:complete",
            "requirement:create", "requirement:edit",
            "requirement:review_req", "requirement:review_spec", "requirement:review_tests",
            "task:create", "task:edit", "task:test", "task:complete",
            "member:invite", "member:remove", "member:assign_role",
            "spec_template:edit",
        ]
        for p in admin_perms:
            db.add(RolePermission(role_id=admin_role.id, permission=p))
        await db.flush()

        all_perms = [
            "project:create", "project:edit", "project:archive", "project:delete",
            "iteration:create", "iteration:edit", "iteration:start", "iteration:complete",
            "requirement:create", "requirement:edit", "requirement:delete",
            "requirement:review_req", "requirement:review_spec", "requirement:review_tests",
            "task:create", "task:edit", "task:delete", "task:test", "task:complete",
            "member:invite", "member:remove", "member:assign_role",
            "spec_template:edit",
        ]

        owner_role = Role(
            team_id=team.id, name="团队所有者", is_builtin=True,
            description="拥有团队全部权限", slug="role-owner",
        )
        db.add(owner_role)
        await db.flush()
        for p in all_perms:
            db.add(RolePermission(role_id=owner_role.id, permission=p))
        await db.flush()
        db.add(MemberRole(member_id=owner_member.id, role_id=owner_role.id))
        await db.flush()

        db.add(MemberRole(member_id=target_member.id, role_id=admin_role.id))
        await db.flush()

        dev_role = Role(
            team_id=team.id, name="开发者", is_builtin=False,
            description="开发团队成员", slug="role-dev",
        )
        db.add(dev_role)
        await db.flush()
        dev_perms = ["task:create", "task:edit"]
        for p in dev_perms:
            db.add(RolePermission(role_id=dev_role.id, permission=p))
        await db.flush()
        db.add(MemberRole(member_id=exist_member.id, role_id=dev_role.id))
        await db.flush()

        project = Project(
            team_id=team.id, name="Test Project", description="Test project for E2E",
            status="active", start_date=date(2026, 1, 1),
        )
        db.add(project)
        await db.flush()

        from datetime import date as date_type
        iteration = Iteration(
            project_id=project.id, name="Sprint 1",
            start_date=date_type(2026, 1, 1), end_date=date_type(2026, 3, 31),
            status="planning",
        )
        db.add(iteration)
        await db.commit()
        logger.info("Seed data created")


@app.on_event("startup")
async def on_startup():
    await init_db()
    await _seed_data()
    logger.info("Database initialized")


@app.exception_handler(BusinessError)
async def business_error_handler(request: Request, exc: BusinessError):
    return JSONResponse(
        status_code=200,
        content={"code": exc.code, "message": exc.message, "data": exc.errors if exc.errors else None},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"code": -1, "message": f"Internal Server Error: {exc}", "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    for err in exc.errors():
        loc = err.get("loc", ())
        if "authorization" in [str(l).lower() for l in loc]:
            return JSONResponse(
                status_code=200,
                content={"code": ERR_UNAUTHORIZED, "message": "未登录", "data": None},
            )
    return JSONResponse(
        status_code=200,
        content={"code": ERR_VALIDATION, "message": "参数校验失败", "data": None},
    )


from app.api.router import router as api_router  # noqa: E402

app.include_router(api_router, prefix="/api/v1")
