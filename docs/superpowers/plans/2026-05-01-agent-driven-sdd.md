# Agent-Driven SDD 改造实施计划（TDD 模式）

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 SDD 改造为全 Agent 驱动的项目开发工具，Agent 通过 API 完成从需求编写到代码提交的全流程。

**Architecture:** 三阶段改造。P0 建立基础设施（认证 + 数据持久化 + Agent 工作发现 API），P1 增强 Agent 可操作性（规格模板 + 任务代码关联 + 批量测试），P2 打磨质量（响应格式统一 + 分页）。

**Tech Stack:** FastAPI, SQLAlchemy async, Motor/MongoDB, python-jose JWT, bcrypt, jsonschema, SQLite

**TDD 规则:** 每个 Task 严格遵循 **写测试 → 跑测试（失败） → 写实现 → 跑测试（通过） → 提交** 的循环。测试用例对应 `design/18-test-cases-backend-agent-driven.md` 中的编号。

**测试命令:** `conda run -n sdd python -m pytest backend/tests/<file> -v`

---

## Phase 0: 基础设施

### Task 0.1: 接通 MongoDB — Spec 数据持久化

**对应测试用例:** TC-AGENT-049 ~ TC-AGENT-052

**Files:**
- Create: `backend/app/mongo_database.py`
- Modify: `backend/app/services/specification.py`
- Modify: `backend/app/main.py`
- Test: `backend/tests/test_spec_mongo.py`

- [ ] **Step 1: 写测试 — MongoDB 持久化**

创建 `backend/tests/test_spec_mongo.py`。使用 `unittest.mock.AsyncMock` mock Motor collection。

```python
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch


@pytest_asyncio.fixture
async def mock_templates_col():
    col = AsyncMock()
    col.create_index = AsyncMock()
    return col


@pytest_asyncio.fixture
async def mock_documents_col():
    col = AsyncMock()
    col.create_index = AsyncMock()
    return col


@pytest_asyncio.fixture
async def mock_mongo(mock_templates_col, mock_documents_col):
    with patch("app.services.specification.get_spec_templates_collection", return_value=mock_templates_col), \
         patch("app.services.specification.get_spec_documents_collection", return_value=mock_documents_col):
        yield {"templates": mock_templates_col, "documents": mock_documents_col}


class TestSpecTemplateMongo:
    @pytest.mark.asyncio
    async def test_save_template_then_read_back(self, client, db, normal_user, owner_role, mock_mongo):
        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        sections = [{"name": "test_section", "display_name": "测试", "required": True, "fields": []}]

        mock_mongo["templates"].find_one.return_value = None
        mock_mongo["templates"].update_one.return_value = AsyncMock()

        resp = await client.put(
            f"/api/v1/teams/{owner_role['team'].id}/spec-template",
            json={"sections": sections},
            headers=headers,
        )
        assert resp.json()["code"] == 0

        saved_doc = {"team_id": owner_role["team"].id, "sections": sections}
        mock_mongo["templates"].find_one.return_value = saved_doc

        resp2 = await client.get(
            f"/api/v1/teams/{owner_role['team'].id}/spec-template",
            headers=headers,
        )
        assert resp2.json()["code"] == 0
        assert resp2.json()["data"]["sections"] == sections


class TestSpecDocumentMongo:
    @pytest.mark.asyncio
    async def test_save_document_then_read_back(self, client, db, normal_user, owner_role, sample_requirement, mock_mongo):
        from app.models import Requirement
        req = await db.get(Requirement, sample_requirement.id)
        req.status = "drafting_spec"
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        content = {
            "entity_definition": {"description": "test", "fields": [{"name": "id", "type": "integer"}]},
            "table_design": {"tables": [{"name": "users", "fields": [{"name": "id", "type": "BIGINT"}]}]},
            "page_structure": {"pages": [{"name": "test", "code": "test", "elements": [{"code": "t", "type": "button", "label": "t"}]}]},
            "api_design": {"endpoints": [{"method": "GET", "path": "/api/test", "description": "test"}]},
        }

        mock_mongo["documents"].find_one.return_value = None
        mock_mongo["templates"].find_one.return_value = None

        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={"content": content},
            headers=headers,
        )
        assert resp.json()["code"] == 0
        assert resp.json()["data"]["version"] == 1

        saved = {"current_version": 1, "versions": [{"version": 1, "content": content, "created_by": normal_user.id, "created_at": "2026-05-01T00:00:00"}]}
        mock_mongo["documents"].find_one.return_value = saved

        resp2 = await client.get(f"/api/v1/requirements/{sample_requirement.id}/specification", headers=headers)
        assert resp2.json()["code"] == 0
        assert resp2.json()["data"]["current_version"] == 1

    @pytest.mark.asyncio
    async def test_version_history_preserved(self, client, db, normal_user, owner_role, sample_requirement, mock_mongo):
        from app.models import Requirement
        req = await db.get(Requirement, sample_requirement.id)
        req.status = "drafting_spec"
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])

        saved = {
            "current_version": 2,
            "versions": [
                {"version": 1, "content": {"entity_definition": {"description": "v1"}}, "created_by": 1, "created_at": "2026-05-01T00:00:00"},
                {"version": 2, "content": {"entity_definition": {"description": "v2"}}, "created_by": 1, "created_at": "2026-05-01T01:00:00"},
            ],
        }
        mock_mongo["documents"].find_one.return_value = saved
        mock_mongo["templates"].find_one.return_value = None

        resp = await client.get(f"/api/v1/requirements/{sample_requirement.id}/specification/versions", headers=headers)
        assert resp.json()["code"] == 0
        assert len(resp.json()["data"]) == 2
```

- [ ] **Step 2: 跑测试 → 失败**

```bash
conda run -n sdd python -m pytest backend/tests/test_spec_mongo.py -v
```

预期：FAIL（`app.mongo_database` 不存在）

- [ ] **Step 3: 创建 MongoDB 连接模块**

创建 `backend/app/mongo_database.py`:

```python
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import MONGO_URL

_client: AsyncIOMotorClient | None = None


def get_mongo_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGO_URL)
    return _client


def get_database():
    return get_mongo_client().sdd


def get_spec_templates_collection():
    return get_database().specification_templates


def get_spec_documents_collection():
    return get_database().specification_documents


async def ensure_indexes():
    templates = get_spec_templates_collection()
    await templates.create_index("team_id", unique=True)
    documents = get_spec_documents_collection()
    await documents.create_index("requirement_id", unique=True)
```

- [ ] **Step 4: 修改 `specification.py` — 替换 cache 为 MongoDB**

将所有 `cache_instance.get/set` 替换为 MongoDB `find_one/update_one`。在每个函数顶部 import `get_spec_templates_collection` / `get_spec_documents_collection`。

关键改动：
- `_get_template_sections` → `_get_template_sections_from_mongo` 查 MongoDB
- `update_spec_template` → `collection.update_one(..., upsert=True)`
- `save_spec_document` → `collection.find_one` + `collection.update_one`
- `get_spec_document` → `collection.find_one`
- `list_spec_versions` → `collection.find_one`
- `get_spec_version_detail` → `collection.find_one`

- [ ] **Step 5: 修改 `main.py` 启动初始化**

在 `on_startup` 中添加 MongoDB 索引初始化（生产用，测试不需要）。

- [ ] **Step 6: 跑测试 → 通过**

```bash
conda run -n sdd python -m pytest backend/tests/test_spec_mongo.py -v
```

预期：全部 PASS

- [ ] **Step 7: 跑全量 spec 测试确认不破坏现有功能**

```bash
conda run -n sdd python -m pytest backend/tests/test_specifications.py -v
```

- [ ] **Step 8: 提交**

```bash
git add backend/app/mongo_database.py backend/app/services/specification.py backend/app/main.py backend/tests/test_spec_mongo.py
git commit -m "feat: persist spec templates and documents to MongoDB"
```

---

### Task 0.2: API Key 认证

**对应测试用例:** TC-AGENT-001 ~ TC-AGENT-017

**Files:**
- Create: `backend/app/models/api_key.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/deps.py`
- Modify: `backend/app/api/admin.py`
- Test: `backend/tests/test_api_keys.py`

- [ ] **Step 1: 写测试 — API Key 全生命周期**

创建 `backend/tests/test_api_keys.py`，覆盖 TC-AGENT-001 ~ TC-AGENT-017：

```python
import hashlib
import pytest
import pytest_asyncio
from httpx import AsyncClient
from app.models import ApiKey


class TestCreateApiKey:
    @pytest.mark.asyncio
    async def test_admin_create_api_key(self, client, db, admin_user, normal_user):
        headers = auth_headers(admin_user.id, is_admin=True)
        resp = await client.post(
            "/api/v1/admin/api-keys",
            json={"user_id": normal_user.id, "name": "测试Key"},
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["key"].startswith("sdd_")
        assert body["data"]["key_prefix"] == body["data"]["key"][:8]
        assert "name" in body["data"]

    @pytest.mark.asyncio
    async def test_admin_create_key_no_expiry(self, client, db, admin_user, normal_user):
        headers = auth_headers(admin_user.id, is_admin=True)
        resp = await client.post(
            "/api/v1/admin/api-keys",
            json={"user_id": normal_user.id, "name": "永久Key"},
            headers=headers,
        )
        assert resp.json()["code"] == 0
        assert resp.json()["data"]["expires_at"] is None

    @pytest.mark.asyncio
    async def test_non_admin_cannot_create(self, client, db, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.post(
            "/api/v1/admin/api-keys",
            json={"user_id": normal_user.id, "name": "Key"},
            headers=headers,
        )
        assert resp.json()["code"] == 40300

    @pytest.mark.asyncio
    async def test_create_key_user_not_found(self, client, db, admin_user):
        headers = auth_headers(admin_user.id, is_admin=True)
        resp = await client.post(
            "/api/v1/admin/api-keys",
            json={"user_id": 99999, "name": "Key"},
            headers=headers,
        )
        assert resp.json()["code"] == 40400

    @pytest.mark.asyncio
    async def test_create_key_empty_name(self, client, db, admin_user, normal_user):
        headers = auth_headers(admin_user.id, is_admin=True)
        resp = await client.post(
            "/api/v1/admin/api-keys",
            json={"user_id": normal_user.id, "name": ""},
            headers=headers,
        )
        assert resp.json()["code"] == 40001


class TestApiKeyAuth:
    @pytest.mark.asyncio
    async def test_valid_key_access(self, client, db, admin_user, normal_user):
        raw_key = "sdd_testvalidkey1234567890abcdefghij"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = ApiKey(
            name="test", key_hash=key_hash, key_prefix=raw_key[:8],
            user_id=normal_user.id, is_active=True,
        )
        db.add(api_key)
        await db.commit()

        resp = await client.get("/api/v1/users/me", headers={"X-API-Key": raw_key})
        assert resp.json()["code"] == 0

    @pytest.mark.asyncio
    async def test_invalid_key(self, client, db):
        resp = await client.get("/api/v1/users/me", headers={"X-API-Key": "invalid"})
        assert resp.json()["code"] == 40100

    @pytest.mark.asyncio
    async def test_revoked_key(self, client, db, normal_user):
        raw_key = "sdd_revokedkey1234567890abcdefghijkl"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = ApiKey(
            name="test", key_hash=key_hash, key_prefix=raw_key[:8],
            user_id=normal_user.id, is_active=False,
        )
        db.add(api_key)
        await db.commit()

        resp = await client.get("/api/v1/users/me", headers={"X-API-Key": raw_key})
        assert resp.json()["code"] == 40100

    @pytest.mark.asyncio
    async def test_expired_key(self, client, db, normal_user):
        from datetime import datetime, timedelta
        raw_key = "sdd_expiredkey1234567890abcdefghijklm"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = ApiKey(
            name="test", key_hash=key_hash, key_prefix=raw_key[:8],
            user_id=normal_user.id, is_active=True,
            expires_at=datetime.utcnow() - timedelta(hours=1),
        )
        db.add(api_key)
        await db.commit()

        resp = await client.get("/api/v1/users/me", headers={"X-API-Key": raw_key})
        assert resp.json()["code"] == 40100

    @pytest.mark.asyncio
    async def test_key_disabled_user(self, client, db):
        from app.models import User
        from app.utils.security import hash_password
        user = User(
            email="disabled@example.com", nickname="禁用",
            password_hash=hash_password("12345678"), is_active=False,
            is_admin=False, email_verified=True,
        )
        db.add(user)
        await db.flush()

        raw_key = "sdd_disableduser1234567890abcdefghijkl"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = ApiKey(
            name="test", key_hash=key_hash, key_prefix=raw_key[:8],
            user_id=user.id, is_active=True,
        )
        db.add(api_key)
        await db.commit()

        resp = await client.get("/api/v1/users/me", headers={"X-API-Key": raw_key})
        assert resp.json()["code"] == 40100

    @pytest.mark.asyncio
    async def test_key_permissions_fresh(self, client, db, normal_user, owner_role):
        raw_key = "sdd_freshperms1234567890abcdefghijklmn"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = ApiKey(
            name="test", key_hash=key_hash, key_prefix=raw_key[:8],
            user_id=normal_user.id, is_active=True,
        )
        db.add(api_key)
        await db.commit()

        resp = await client.get("/api/v1/users/me", headers={"X-API-Key": raw_key})
        perms = resp.json()["data"].get("permissions", [])
        assert "project:create" in perms

    @pytest.mark.asyncio
    async def test_both_jwt_and_key(self, client, db, normal_user):
        raw_key = "sdd_both1234567890abcdefghijklmn"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = ApiKey(
            name="test", key_hash=key_hash, key_prefix=raw_key[:8],
            user_id=normal_user.id, is_active=True,
        )
        db.add(api_key)
        await db.commit()

        jwt_headers = auth_headers(normal_user.id)
        jwt_headers["X-API-Key"] = raw_key
        resp = await client.get("/api/v1/users/me", headers=jwt_headers)
        assert resp.json()["code"] == 0


class TestListApiKeys:
    @pytest.mark.asyncio
    async def test_list_keys(self, client, db, admin_user, normal_user):
        raw_key = "sdd_listkeys1234567890abcdefghijklmno"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = ApiKey(
            name="test", key_hash=key_hash, key_prefix=raw_key[:8],
            user_id=normal_user.id,
        )
        db.add(api_key)
        await db.commit()

        headers = auth_headers(admin_user.id, is_admin=True)
        resp = await client.get(f"/api/v1/admin/users/{normal_user.id}/api-keys", headers=headers)
        body = resp.json()
        assert body["code"] == 0
        assert len(body["data"]) >= 1
        assert "key" not in body["data"][0]
        assert body["data"][0]["key_prefix"] == raw_key[:8]

    @pytest.mark.asyncio
    async def test_non_admin_cannot_list(self, client, db, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.get(f"/api/v1/admin/users/{normal_user.id}/api-keys", headers=headers)
        assert resp.json()["code"] == 40300


class TestRevokeApiKey:
    @pytest.mark.asyncio
    async def test_revoke_key(self, client, db, admin_user, normal_user):
        raw_key = "sdd_revoke1234567890abcdefghijklmno"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = ApiKey(
            name="test", key_hash=key_hash, key_prefix=raw_key[:8],
            user_id=normal_user.id,
        )
        db.add(api_key)
        await db.commit()
        key_id = api_key.id

        headers = auth_headers(admin_user.id, is_admin=True)
        resp = await client.delete(f"/api/v1/admin/api-keys/{key_id}", headers=headers)
        assert resp.json()["code"] == 0

        await db.refresh(api_key)
        assert api_key.is_active is False

    @pytest.mark.asyncio
    async def test_revoke_twice_idempotent(self, client, db, admin_user, normal_user):
        raw_key = "sdd_twice1234567890abcdefghijklmno"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        api_key = ApiKey(
            name="test", key_hash=key_hash, key_prefix=raw_key[:8],
            user_id=normal_user.id, is_active=False,
        )
        db.add(api_key)
        await db.commit()

        headers = auth_headers(admin_user.id, is_admin=True)
        resp = await client.delete(f"/api/v1/admin/api-keys/{api_key.id}", headers=headers)
        assert resp.json()["code"] == 0

    @pytest.mark.asyncio
    async def test_revoke_not_found(self, client, db, admin_user):
        headers = auth_headers(admin_user.id, is_admin=True)
        resp = await client.delete("/api/v1/admin/api-keys/99999", headers=headers)
        assert resp.json()["code"] == 40400
```

- [ ] **Step 2: 跑测试 → 失败**

```bash
conda run -n sdd python -m pytest backend/tests/test_api_keys.py -v
```

预期：FAIL（`ApiKey` 不存在，路由不存在）

- [ ] **Step 3: 创建 ApiKey 模型**

创建 `backend/app/models/api_key.py`，注册到 `__init__.py`。

- [ ] **Step 4: 修改 `deps.py` 支持 `X-API-Key`**

添加 `_authenticate_api_key` 方法。提取 `_collect_user_permissions` 为公共函数。

- [ ] **Step 5: 添加管理员 API Key 路由**

在 `backend/app/api/admin.py` 添加创建/列出/吊销三个端点。

- [ ] **Step 6: 跑测试 → 通过**

```bash
conda run -n sdd python -m pytest backend/tests/test_api_keys.py -v
```

- [ ] **Step 7: 提交**

```bash
git add backend/app/models/api_key.py backend/app/models/__init__.py backend/app/deps.py backend/app/api/admin.py backend/tests/test_api_keys.py
git commit -m "feat: add API Key authentication for agent access"
```

---

### Task 0.3: Agent 工作发现 API

**对应测试用例:** TC-AGENT-018 ~ TC-AGENT-031

**Files:**
- Modify: `backend/app/api/users.py`
- Modify: `backend/app/api/requirements.py`
- Modify: `backend/app/services/task.py`
- Test: `backend/tests/test_agent_discovery.py`

- [ ] **Step 1: 写测试 — 工作发现**

创建 `backend/tests/test_agent_discovery.py`，覆盖 TC-AGENT-018 ~ TC-AGENT-031：

```python
import pytest
from tests.conftest import auth_headers


class TestMyPending:
    @pytest.mark.asyncio
    async def test_full_pending(self, client, db, normal_user, owner_role, sample_project, sample_iteration, sample_requirement):
        from app.models import Task
        task = Task(requirement_id=sample_requirement.id, title="任务1", assignee_id=normal_user.id, status="coding", created_by=normal_user.id)
        db.add(task)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        resp = await client.get("/api/v1/users/me/pending", headers=headers)
        body = resp.json()
        assert body["code"] == 0
        data = body["data"]
        assert len(data["teams"]) >= 1
        assert len(data["projects"]) >= 1
        assert any(t["id"] == task.id for t in data["assigned_tasks"])

    @pytest.mark.asyncio
    async def test_empty_pending(self, client, db, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.get("/api/v1/users/me/pending", headers=headers)
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["teams"] == []

    @pytest.mark.asyncio
    async def test_unauthorized(self, client, db):
        resp = await client.get("/api/v1/users/me/pending")
        assert resp.json()["code"] == 40100


class TestMyTasks:
    @pytest.mark.asyncio
    async def test_list_my_tasks(self, client, db, normal_user, owner_role, sample_requirement):
        from app.models import Task
        task = Task(requirement_id=sample_requirement.id, title="我的任务", assignee_id=normal_user.id, status="coding", created_by=normal_user.id)
        db.add(task)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        resp = await client.get("/api/v1/users/me/tasks", headers=headers)
        body = resp.json()
        assert body["code"] == 0
        assert len(body["data"]) >= 1
        assert body["data"][0]["requirement_title"] == sample_requirement.title

    @pytest.mark.asyncio
    async def test_filter_by_status(self, client, db, normal_user, owner_role, sample_requirement):
        from app.models import Task
        t1 = Task(requirement_id=sample_requirement.id, title="编码中", assignee_id=normal_user.id, status="coding", created_by=normal_user.id)
        t2 = Task(requirement_id=sample_requirement.id, title="待处理", assignee_id=normal_user.id, status="pending", created_by=normal_user.id)
        db.add_all([t1, t2])
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        resp = await client.get("/api/v1/users/me/tasks?status=coding", headers=headers)
        body = resp.json()
        assert body["code"] == 0
        assert all(t["status"] == "coding" for t in body["data"])

    @pytest.mark.asyncio
    async def test_no_tasks(self, client, db, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.get("/api/v1/users/me/tasks", headers=headers)
        assert resp.json()["data"] == []


class TestMyPendingReviews:
    @pytest.mark.asyncio
    async def test_has_pending_reviews(self, client, db, normal_user, another_user, owner_role, sample_requirement):
        from app.models import RequirementReview
        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="requirement",
            reviewer_id=normal_user.id,
            status="pending",
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        resp = await client.get("/api/v1/users/me/pending-reviews", headers=headers)
        body = resp.json()
        assert body["code"] == 0
        assert len(body["data"]) >= 1

    @pytest.mark.asyncio
    async def test_processed_reviews_excluded(self, client, db, normal_user, owner_role, sample_requirement):
        from app.models import RequirementReview
        review = RequirementReview(
            requirement_id=sample_requirement.id,
            review_type="requirement",
            reviewer_id=normal_user.id,
            status="approved",
        )
        db.add(review)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        resp = await client.get("/api/v1/users/me/pending-reviews", headers=headers)
        assert resp.json()["data"] == []


class TestGlobalRequirements:
    @pytest.mark.asyncio
    async def test_filter_by_status(self, client, db, normal_user, owner_role, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        resp = await client.get("/api/v1/requirements?status=drafting_req", headers=headers)
        body = resp.json()
        assert body["code"] == 0
        assert all(r["status"] == "drafting_req" for r in body["data"])

    @pytest.mark.asyncio
    async def test_filter_by_iteration(self, client, db, normal_user, owner_role, sample_iteration, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        resp = await client.get(f"/api/v1/requirements?iteration_id={sample_iteration.id}", headers=headers)
        body = resp.json()
        assert body["code"] == 0
        assert all(r["iteration_id"] == sample_iteration.id for r in body["data"])

    @pytest.mark.asyncio
    async def test_no_filter(self, client, db, normal_user, owner_role, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        resp = await client.get("/api/v1/requirements", headers=headers)
        assert resp.json()["code"] == 0


class TestFullContext:
    @pytest.mark.asyncio
    async def test_full_context_with_data(self, client, db, normal_user, owner_role, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        resp = await client.get(f"/api/v1/requirements/{sample_requirement.id}/full-context", headers=headers)
        body = resp.json()
        assert body["code"] == 0
        assert "requirement" in body["data"]
        assert "spec" in body["data"]
        assert "test_cases" in body["data"]
        assert "tasks" in body["data"]

    @pytest.mark.asyncio
    async def test_full_context_no_spec(self, client, db, normal_user, owner_role, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        resp = await client.get(f"/api/v1/requirements/{sample_requirement.id}/full-context", headers=headers)
        spec = resp.json()["data"]["spec"]
        assert spec["current_version"] is None or spec["current_version"] == 0

    @pytest.mark.asyncio
    async def test_full_context_not_found(self, client, db, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.get("/api/v1/requirements/99999/full-context", headers=headers)
        assert resp.json()["code"] == 40400
```

- [ ] **Step 2: 跑测试 → 失败**

```bash
conda run -n sdd python -m pytest backend/tests/test_agent_discovery.py -v
```

- [ ] **Step 3: 实现 — 扩展 `users.py` 端点**

添加 `GET /me/tasks`、`GET /me/pending-reviews`、扩展 `GET /me/pending`。

- [ ] **Step 4: 实现 — 添加 `requirements.py` 全局查询和 full-context**

添加 `GET /requirements` 和 `GET /requirements/{id}/full-context`。

- [ ] **Step 5: 实现 — `services/task.py` 添加 `list_tasks_by_assignee`**

- [ ] **Step 6: 跑测试 → 通过**

```bash
conda run -n sdd python -m pytest backend/tests/test_agent_discovery.py -v
```

- [ ] **Step 7: 提交**

```bash
git add backend/app/api/users.py backend/app/api/requirements.py backend/app/services/task.py backend/tests/test_agent_discovery.py
git commit -m "feat: add agent work discovery APIs"
```

---

## Phase 1: Agent 可操作性增强

### Task 1.1: 规格模板增强 — agent_prompt + Schema 强化

**对应测试用例:** TC-AGENT-046 ~ TC-AGENT-048

**Files:**
- Modify: `backend/app/mongo_models/spec_template.py`
- Modify: `backend/app/api/teams.py`
- Test: `backend/tests/test_spec_template_agent.py`

- [ ] **Step 1: 写测试**

```python
class TestAgentGuide:
    @pytest.mark.asyncio
    async def test_default_template_agent_guide(self, client, db, normal_user, owner_role):
        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        resp = await client.get(f"/api/v1/teams/{owner_role['team'].id}/spec-template/agent-guide", headers=headers)
        body = resp.json()
        assert body["code"] == 0
        sections = body["data"]["sections"]
        assert len(sections) >= 5
        for section in sections:
            for field in section["fields"]:
                assert "agent_prompt" in field

    @pytest.mark.asyncio
    async def test_custom_template_agent_guide(self, client, db, normal_user, owner_role):
        headers = auth_headers(normal_user.id, permissions=owner_role["all_permissions"])
        custom = [{"name": "custom", "display_name": "自定义", "required": True, "fields": [{"name": "f1", "display_name": "F1", "type": "text", "agent_prompt": "填写F1"}]}]
        await client.put(f"/api/v1/teams/{owner_role['team'].id}/spec-template", json={"sections": custom}, headers=headers)

        resp = await client.get(f"/api/v1/teams/{owner_role['team'].id}/spec-template/agent-guide", headers=headers)
        assert resp.json()["code"] == 0

    @pytest.mark.asyncio
    async def test_non_member_forbidden(self, client, db, normal_user, another_user):
        headers = auth_headers(another_user.id)
        resp = await client.get("/api/v1/teams/9999/spec-template/agent-guide", headers=headers)
        assert resp.json()["code"] == 40300
```

- [ ] **Step 2: 跑测试 → 失败**

- [ ] **Step 3: 实现 — 添加 `agent_prompt` 到 `SpecTemplateField` 和 `DEFAULT_SECTIONS`，强化 JSON Schema，添加 `agent-guide` 端点**

- [ ] **Step 4: 跑测试 → 通过**

- [ ] **Step 5: 提交**

---

### Task 1.2: Task Git 关联 + start-coding

**对应测试用例:** TC-AGENT-032 ~ TC-AGENT-039

**Files:**
- Modify: `backend/app/models/task.py`
- Modify: `backend/app/services/task.py`
- Modify: `backend/app/api/tasks.py`
- Test: `backend/tests/test_task_git.py`

- [ ] **Step 1: 写测试**

覆盖 start-coding (pending→coding)、git-info 更新、任务详情含 git 字段、PATCH 状态校验。

- [ ] **Step 2: 跑测试 → 失败**

- [ ] **Step 3: 实现 — Task 模型加 4 字段、start_coding 服务、git-info 端点、状态校验**

- [ ] **Step 4: 跑测试 → 通过**

- [ ] **Step 5: 提交**

---

### Task 1.3: 批量测试结果提交

**对应测试用例:** TC-AGENT-040 ~ TC-AGENT-045

**Files:**
- Modify: `backend/app/models/test_execution.py`
- Modify: `backend/app/api/test_executions.py`
- Modify: `backend/app/services/test_execution.py`
- Test: `backend/tests/test_batch_execution.py`

- [ ] **Step 1: 写测试**

覆盖批量提交、log_output/duration_ms、空 records、round 不存在。

- [ ] **Step 2: 跑测试 → 失败**

- [ ] **Step 3: 实现 — Record 加 2 字段、batch 端点和服务**

- [ ] **Step 4: 跑测试 → 通过**

- [ ] **Step 5: 提交**

---

## Phase 2: 质量打磨

### Task 2.1: API 响应格式统一

**Files:**
- Modify: `backend/app/api/tasks.py`, `requirements.py`, `iterations.py`

- [ ] **Step 1: 写测试 — 验证响应格式一致性**

- [ ] **Step 2: 跑测试 → 失败**

- [ ] **Step 3: 修复 `**data` 展开、统一 message、修复 BusinessError 使用**

- [ ] **Step 4: 跑测试 → 通过**

- [ ] **Step 5: 提交**

---

### Task 2.2: 分页支持

**Files:**
- Modify: `backend/app/schemas/common.py`
- Test: `backend/tests/test_pagination.py`

- [ ] **Step 1: 写测试**

- [ ] **Step 2: 跑测试 → 失败**

- [ ] **Step 3: 实现分页**

- [ ] **Step 4: 跑测试 → 通过**

- [ ] **Step 5: 提交**

---

## 依赖图

```
Phase 0 (可并行):
  Task 0.1 MongoDB ──┐
  Task 0.2 API Key ──┤
  Task 0.3 工作发现 ──┘

Phase 1 (可并行):
  Task 1.1 模板增强 ──┐
  Task 1.2 Git 关联 ──┤
  Task 1.3 批量测试 ──┘

Phase 2 (可并行):
  Task 2.1 响应格式 ──┐
  Task 2.2 分页 ──────┘
```
