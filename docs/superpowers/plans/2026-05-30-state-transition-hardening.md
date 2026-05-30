# 状态流转安全加固 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复路由层绕过 service 层状态校验的漏洞，确保需求编辑、状态变更、任务创建均遵循状态机规则。

**Architecture:** 在路由层增加状态校验，复用 service 层已有的状态转换映射。对 `PATCH /requirements/{id}` 拆分逻辑：字段编辑走 service `update_requirement`，status 变更走合法转换映射。对 `POST /tasks` 直接创建路由增加需求状态检查。

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy async, Pydantic, pytest-asyncio

---

## 问题清单

| # | 漏洞 | 文件 | 影响 |
|---|------|------|------|
| 1 | `PATCH /requirements/{id}` 可在任意状态编辑 title/description 等 | `api/requirements.py:252-279` | 已提交审核的需求仍可被修改 |
| 2 | `PATCH /requirements/{id}` 可设置任意 status，无转换校验 | `api/requirements.py:267-268` | 可跳过审核直接 approved，或回退到任意状态 |
| 3 | `POST /tasks`（直接路由）不检查需求是否 approved | `api/tasks.py:28-55` | 未通过审核的需求可以创建任务 |
| 4 | 测试用例通过 PATCH 设置 `status` 来绕过状态机 | `tests/test_test_generator.py:16`, `tests/test_task_generator.py:16,45` | 测试依赖了有漏洞的接口 |

---

### Task 1: 修复 `PATCH /requirements/{id}` — 添加状态校验

**Files:**
- Modify: `backend/app/api/requirements.py:252-279`

- [ ] **Step 1: 在 service 层增加合法状态转换映射**

在 `backend/app/services/requirement.py` 顶部（import 之后）添加合法转换常量和辅助函数：

```python
VALID_STATUS_TRANSITIONS: dict[str, set[str]] = {
    "drafting_req": {"reviewing_req"},
    "reviewing_req": {"drafting_req", "drafting_spec"},
    "drafting_spec": {"reviewing_spec", "drafting_req"},
    "reviewing_spec": {"drafting_spec", "drafting_tests"},
    "drafting_tests": {"reviewing_tests", "drafting_spec"},
    "reviewing_tests": {"drafting_tests", "approved"},
    "approved": set(),
}

EDITABLE_STATUSES = {"drafting_req"}
```

- [ ] **Step 2: 重写 `patch_requirement` 路由**

将 `backend/app/api/requirements.py:252-279` 替换为：

```python
@router.patch("/{id}")
async def patch_requirement(
    id: int,
    body: PatchRequirementRequest,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    from app.models import Requirement
    from app.services.requirement import VALID_STATUS_TRANSITIONS, EDITABLE_STATUSES
    stmt = select(Requirement).where(Requirement.id == id, Requirement.is_deleted == False)
    result = await db.execute(stmt)
    req = result.scalar_one_or_none()
    if req is None:
        from app.exceptions import BusinessError, ERR_NOT_FOUND
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    has_field_edits = any(v is not None for v in [
        body.title, body.description, body.type_detail, body.prototype_html
    ])
    if has_field_edits and req.status not in EDITABLE_STATUSES:
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前状态不允许编辑")

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
        req.prototype_html = body.html
    await db.commit()
    await db.refresh(req)
    return {"code": 0, "message": "success", "data": {"id": req.id, "status": req.status}}
```

- [ ] **Step 3: 运行现有测试确认基础功能正常**

Run: `conda run -n sdd python -m pytest backend/tests/test_requirements.py -v -k "test_patch_requirement" --no-header -q`
Expected: test_patch_requirement_prototype_html 应该 FAIL（因为 sample_requirement 默认 drafting_req，应该 PASS）

Actually 需要检查 — sample_requirement 默认 status 是 `drafting_req`，所以在 EDITABLE_STATUSES 中，这个测试应该继续 PASS。

Run: `conda run -n sdd python -m pytest backend/tests/test_requirements.py::TestPatchRequirement -v --no-header -q` (如果 class 存在)
或: `conda run -n sdd python -m pytest backend/tests/test_requirements.py -v -k "patch" --no-header -q`

---

### Task 2: 修复 `POST /tasks` 直接创建路由 — 添加需求状态检查

**Files:**
- Modify: `backend/app/api/tasks.py:28-55`

- [ ] **Step 1: 在 direct_create_task 中添加 approved 检查**

将 `backend/app/api/tasks.py:41-42` 的空 `if` 替换为实际检查：

```python
    if req.status != "approved":
        from app.exceptions import BusinessError, ERR_REQUIREMENT_STATUS
        raise BusinessError(ERR_REQUIREMENT_STATUS, "需求未通过审核，无法创建任务")
```

替换原来的：
```python
    if req.status not in ("approved", "drafting_spec", "drafting_tests", "reviewing_tests"):
        pass
```

- [ ] **Step 2: 添加 require_permission 装饰**

在 `direct_create_task` 函数的 `user` 参数增加权限检查：

```python
@router.post("")
async def direct_create_task(
    body: DirectCreateTaskRequest,
    user: Annotated[dict, Depends(require_permission("task:create"))],
    db=Depends(get_db_session),
) -> dict:
```

---

### Task 3: 修复依赖 PATCH 状态跳转的测试

**Files:**
- Modify: `backend/tests/test_test_generator.py`
- Modify: `backend/tests/test_task_generator.py`

- [ ] **Step 1: 修复 test_test_generator.py**

测试文件通过 `PATCH status` 来设置 `drafting_spec` 和 `drafting_tests`。修复方法：创建辅助函数，走合法的状态转换流程。

将 `backend/tests/test_test_generator.py` 中：

```python
await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "drafting_spec"}, headers=headers)
```

替换为走合法转换路径（drafting_req → reviewing_req → drafting_spec）：

```python
await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "reviewing_req"}, headers=headers)
await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "drafting_spec"}, headers=headers)
```

同理，`drafting_tests` 的转换也需要走合法路径（drafting_spec → reviewing_spec → drafting_tests）：

```python
await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "reviewing_spec"}, headers=headers)
await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "drafting_tests"}, headers=headers)
```

- [ ] **Step 2: 修复 test_task_generator.py**

同理，将：
```python
await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "drafting_spec"}, headers=headers)
```

替换为合法两步转换。将：
```python
await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "approved"}, headers=headers)
```

替换为完整合法路径（drafting_tests → reviewing_tests → approved），需要先确保已经到达 drafting_tests 状态。

- [ ] **Step 3: 运行修复后的测试**

Run: `conda run -n sdd python -m pytest backend/tests/test_test_generator.py backend/tests/test_task_generator.py -v --no-header -q`
Expected: ALL PASS

---

### Task 4: 添加状态流转安全测试

**Files:**
- Modify: `backend/tests/test_requirements.py`

- [ ] **Step 1: 在 test_requirements.py 末尾添加状态安全测试类**

```python
class TestRequirementStatusTransitionSecurity:
    @pytest.mark.asyncio
    async def test_patch_cannot_edit_in_reviewing_status(self, client, normal_user, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"status": "reviewing_req"},
            headers=headers,
        )
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"title": "hacked"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] != 0

    @pytest.mark.asyncio
    async def test_patch_cannot_jump_status(self, client, normal_user, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"status": "approved"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] != 0

    @pytest.mark.asyncio
    async def test_patch_can_edit_in_drafting_req(self, client, normal_user, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"title": "new title"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_patch_valid_transition(self, client, normal_user, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.patch(
            f"/api/v1/requirements/{sample_requirement.id}",
            json={"status": "reviewing_req"},
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0
        assert body["data"]["status"] == "reviewing_req"
```

- [ ] **Step 2: 添加任务直接创建状态检查测试**

在 `backend/tests/test_tasks.py`（或 test_requirements.py 末尾）添加：

```python
class TestTaskDirectCreateStatusCheck:
    @pytest.mark.asyncio
    async def test_cannot_create_task_for_unapproved_requirement(self, client, normal_user, sample_requirement):
        headers = auth_headers(normal_user.id, permissions=["task:create"])
        resp = await client.post(
            "/api/v1/tasks",
            json={
                "title": "should fail",
                "requirement_id": sample_requirement.id,
            },
            headers=headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] != 0
```

- [ ] **Step 3: 运行所有新测试**

Run: `conda run -n sdd python -m pytest backend/tests/test_requirements.py -v -k "StatusTransitionSecurity" --no-header -q`
Expected: ALL 4 PASS

---

### Task 5: 全量回归测试

- [ ] **Step 1: 运行全部后端测试**

Run: `conda run -n sdd python -m pytest backend/tests/ -v --no-header -q`
Expected: ALL PASS (0 failures)

- [ ] **Step 2: 前端构建检查**

Run: `cd frontend && npx vue-tsc -b && npx vite build`
Expected: 0 new type errors, build success

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/requirements.py backend/app/api/tasks.py backend/app/services/requirement.py backend/tests/test_requirements.py backend/tests/test_test_generator.py backend/tests/test_task_generator.py
git commit -m "fix: enforce state machine validation in PATCH requirements and POST tasks routes"
```
