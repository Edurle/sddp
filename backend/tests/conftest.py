from datetime import date
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from httpx._models import _normalize_header_value as _orig_normalize
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


def _normalize_header_value_utf8(value, encoding=None):
    try:
        return _orig_normalize(value, encoding)
    except UnicodeEncodeError:
        if isinstance(value, bytes):
            return value
        return value.encode("utf-8")


import httpx._models as _httpx_models
_httpx_models._normalize_header_value = _normalize_header_value_utf8

from app.database import Base
from app.models import (
    User, Team, TeamMember, Role, RolePermission, MemberRole,
    Invitation, Project, Iteration, Requirement, RequirementReview,
    Task, TestCase, TestExecutionRound, TestExecutionRecord,
    PasswordResetToken, ApiKey,
)
from app.utils.security import hash_password, create_access_token


TEST_DATABASE_URL = "sqlite+aiosqlite://"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionFactory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(autouse=True)
async def mock_mongo_collections():
    templates_store: dict = {}
    documents_store: dict = {}

    templates_col = AsyncMock()
    documents_col = AsyncMock()

    async def _templates_find_one(query):
        return templates_store.get(query.get("team_id"))

    async def _templates_update_one(query, update, **kwargs):
        templates_store[query.get("team_id")] = update["$set"]

    async def _documents_find_one(query):
        return documents_store.get(query.get("requirement_id"))

    async def _documents_update_one(query, update, **kwargs):
        documents_store[query.get("requirement_id")] = update["$set"]

    templates_col.find_one.side_effect = _templates_find_one
    templates_col.update_one.side_effect = _templates_update_one
    templates_col.create_index = AsyncMock()

    documents_col.find_one.side_effect = _documents_find_one
    documents_col.update_one.side_effect = _documents_update_one
    documents_col.create_index = AsyncMock()

    with patch(
        "app.services.specification.get_spec_templates_collection",
        return_value=templates_col,
    ), patch(
        "app.services.specification.get_spec_documents_collection",
        return_value=documents_col,
    ):
        yield {"templates": templates_col, "documents": documents_col}


@pytest_asyncio.fixture
async def db():
    async with TestSessionFactory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db):
    from app.deps import get_current_user, get_db_session
    from app.main import app

    async def override_get_db():
        yield db

    app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


def _make_token(user_id: int, is_admin: bool = False, permissions: list | None = None) -> str:
    return create_access_token({
        "sub": str(user_id),
        "is_admin": is_admin,
        "permissions": permissions or [],
    })


def auth_headers(user_id: int, is_admin: bool = False, permissions: list | None = None) -> dict:
    token = _make_token(user_id, is_admin, permissions)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def normal_user(db):
    user = User(
        email="user@example.com",
        nickname="普通用户",
        password_hash=hash_password("12345678"),
        is_active=True,
        is_admin=False,
        email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db):
    user = User(
        email="admin@example.com",
        nickname="管理员",
        password_hash=hash_password("12345678"),
        is_active=True,
        is_admin=True,
        email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def unverified_user(db):
    user = User(
        email="unverified@example.com",
        nickname="未验证用户",
        password_hash=hash_password("12345678"),
        is_active=True,
        is_admin=False,
        email_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def disabled_user(db):
    user = User(
        email="disabled@example.com",
        nickname="禁用用户",
        password_hash=hash_password("12345678"),
        is_active=False,
        is_admin=False,
        email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def another_user(db):
    user = User(
        email="other@example.com",
        nickname="其他用户",
        password_hash=hash_password("12345678"),
        is_active=True,
        is_admin=False,
        email_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def owner_role(db, normal_user):
    team = Team(name="测试团队", description="用于测试", owner_id=normal_user.id)
    db.add(team)
    await db.flush()

    member = TeamMember(team_id=team.id, user_id=normal_user.id)
    db.add(member)
    await db.flush()

    role = Role(
        team_id=team.id,
        name="所有者",
        is_builtin=True,
        description="团队所有者，拥有全部权限",
    )
    db.add(role)
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
    for p in all_perms:
        db.add(RolePermission(role_id=role.id, permission=p))
    await db.flush()

    db.add(MemberRole(member_id=member.id, role_id=role.id))
    await db.commit()

    return {
        "team": team,
        "member": member,
        "role": role,
        "all_permissions": all_perms,
    }


@pytest_asyncio.fixture
async def team_with_members(db, normal_user, another_user):
    team = Team(name="成员团队", description="有多个成员", owner_id=normal_user.id)
    db.add(team)
    await db.flush()

    owner_member = TeamMember(team_id=team.id, user_id=normal_user.id)
    db.add(owner_member)
    await db.flush()

    role = Role(team_id=team.id, name="所有者", is_builtin=True)
    db.add(role)
    await db.flush()

    db.add(MemberRole(member_id=owner_member.id, role_id=role.id))
    await db.flush()

    other_member = TeamMember(team_id=team.id, user_id=another_user.id)
    db.add(other_member)
    await db.commit()

    return {
        "team": team,
        "owner_member": owner_member,
        "other_member": other_member,
        "owner_role": role,
    }


@pytest_asyncio.fixture
async def sample_project(db, owner_role):
    team = owner_role["team"]
    project = Project(
        team_id=team.id,
        name="测试项目",
        description="用于测试的项目",
        status="active",
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


@pytest_asyncio.fixture
async def sample_iteration(db, sample_project):
    iteration = Iteration(
        project_id=sample_project.id,
        name="Sprint 1",
        goal="第一个迭代",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 4, 15),
        status="planned",
    )
    db.add(iteration)
    await db.commit()
    await db.refresh(iteration)
    return iteration


@pytest_asyncio.fixture
async def sample_requirement(db, sample_iteration, normal_user):
    req = Requirement(
        iteration_id=sample_iteration.id,
        title="测试需求",
        req_type="feature",
        priority=1,
        status="drafting_req",
        description="用于测试的需求",
        created_by=normal_user.id,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


@pytest_asyncio.fixture
async def approved_requirement(db, sample_iteration, normal_user):
    req = Requirement(
        iteration_id=sample_iteration.id,
        title="已通过需求",
        req_type="feature",
        priority=1,
        status="approved",
        description="已通过审核的需求",
        created_by=normal_user.id,
    )
    db.add(req)
    await db.commit()
    await db.refresh(req)
    return req


@pytest_asyncio.fixture
async def sample_task(db, approved_requirement, normal_user):
    task = Task(
        requirement_id=approved_requirement.id,
        title="测试任务",
        description="用于测试的任务",
        status="pending",
        created_by=normal_user.id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


@pytest_asyncio.fixture
async def sample_test_case(db, approved_requirement):
    tc = TestCase(
        requirement_id=approved_requirement.id,
        case_number=f"TC-{approved_requirement.id}-01",
        title="测试用例1",
        case_type="api",
        steps="执行步骤",
        expected_result="预期结果",
    )
    db.add(tc)
    await db.commit()
    await db.refresh(tc)
    return tc
