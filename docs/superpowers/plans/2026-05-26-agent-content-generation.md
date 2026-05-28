# Agent Content Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the agent-driven content generation pipeline: suggestion-based validation, requirement guide, spec context injection, task auto-generation, and test case auto-generation.

**Architecture:** Backend-only changes. All changes follow the existing pattern: service function + API route + test. No frontend changes needed.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy async, PostgreSQL, Pydantic, jsonschema

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `backend/app/services/specification.py` | Suggestion-based validation + agent-guide with requirement context |
| Modify | `backend/app/api/teams.py` | agent-guide API with requirement_id param |
| Modify | `backend/app/api/requirements.py` | requirement-guide endpoint + suggestions in create response |
| Create | `backend/app/services/requirement_guide.py` | Requirement creation guide data |
| Modify | `backend/app/models/task.py` | Add task_type, source_section, spec_reference fields |
| Create | `backend/app/services/task_generator.py` | Auto-generate tasks from spec |
| Create | `backend/app/services/test_generator.py` | Auto-generate test cases from spec |
| Modify | `backend/app/api/router.py` | Mount new routes if needed |
| Create | `backend/alembic/versions/xxx_add_task_gen_fields.py` | Migration for task fields |

---

### Task 1: Spec validation — suggestion mode

**Files:**
- Modify: `backend/app/services/specification.py`
- Test: `backend/tests/test_specifications.py`

Change `_validate_spec_content` to return `(errors, suggestions)` tuple. Missing sections/fields become suggestions instead of errors. Only schema violations and type errors are errors.

- [ ] **Step 1: Write the failing test**

In `backend/tests/test_specifications.py`, add:

```python
class TestSpecSuggestionValidation:
    @pytest.mark.asyncio
    async def test_missing_section_returns_suggestion_not_error(self, client, normal_user, owner_role):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id, permissions=["spec_template:edit"])

        content = {
            "entity_definition": {
                "description": "test entity",
                "fields": [{"name": "id", "type": "integer"}],
            }
        }

        resp = await client.post(
            f"/api/v1/requirements",
            json={
                "title": "suggestion test",
                "type": "feature",
                "priority": 2,
                "description": "test",
            },
            headers=headers,
        )
        req_id = resp.json()["data"]["id"]

        from app.services import requirement as req_svc
        await req_svc.update_requirement_status(db=None, req_id=req_id, user_id=normal_user.id, new_status="drafting_spec")

        resp2 = await client.put(
            f"/api/v1/iterations/1/requirements/{req_id}/spec",
            json={"content": content},
            headers=auth_headers(normal_user.id, permissions=["spec_template:edit"]),
        )

        body = resp2.json()
        assert body["code"] == 0
        assert "suggestions" in body["data"]
        section_names = [s["section"] for s in body["data"]["suggestions"]]
        assert "table_design" in section_names

    @pytest.mark.asyncio
    async def test_invalid_schema_returns_error(self, client, normal_user, owner_role):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id, permissions=["spec_template:edit"])

        content = {
            "entity_definition": {
                "description": "test entity",
                "fields": "not_an_array",
            }
        }

        resp = await client.post(
            f"/api/v1/requirements",
            json={
                "title": "error test",
                "type": "feature",
                "priority": 2,
                "description": "test",
            },
            headers=headers,
        )
        req_id = resp.json()["data"]["id"]

        resp2 = await client.put(
            f"/api/v1/iterations/1/requirements/{req_id}/spec",
            json={"content": content},
            headers=auth_headers(normal_user.id, permissions=["spec_template:edit"]),
        )

        body = resp2.json()
        assert body["code"] != 0
```

- [ ] **Step 2: Run tests to see them fail**

Run: `conda run -n sdd python -m pytest backend/tests/test_specifications.py -v -k "suggestion"`
Expected: FAIL (test classes don't exist yet)

- [ ] **Step 3: Modify `_validate_spec_content` to return (errors, suggestions)**

In `backend/app/services/specification.py`, replace `_validate_spec_content`:

```python
async def _validate_spec_content(content: dict, db: AsyncSession, team_id: int) -> tuple[list[dict], list[dict]]:
    sections = await _get_template_sections(db, team_id)
    errors = []
    suggestions = []

    for section in sections:
        section_name = section["name"]
        section_display = section.get("display_name", section_name)
        section_fields = section.get("fields", [])

        if section_name not in content:
            suggestions.append({
                "section": section_name,
                "field": None,
                "message": f"章节「{section_display}」未填写，如涉及相关内容建议补充",
            })
            continue

        section_content = content[section_name]
        if not isinstance(section_content, dict):
            errors.append({
                "section": section_name,
                "field": None,
                "message": f"章节「{section_display}」的内容必须是对象",
            })
            continue

        for field_def in section_fields:
            field_name = field_def["name"]
            field_display = field_def.get("display_name", field_name)
            field_schema = field_def.get("json_schema")

            if field_name not in section_content:
                suggestions.append({
                    "section": section_name,
                    "field": field_name,
                    "message": f"字段「{field_display}」未填写，建议补充",
                })
                continue

            if field_schema is not None:
                try:
                    jsonschema.validate(section_content[field_name], field_schema)
                except jsonschema.ValidationError as e:
                    errors.append({
                        "section": section_name,
                        "field": field_name,
                        "message": f"字段「{field_display}」格式不正确: {e.message}",
                        "path": list(e.absolute_path) if e.absolute_path else [],
                    })

    return errors, suggestions
```

- [ ] **Step 4: Update `save_spec_document` to use new return type**

In the same file, change `save_spec_document`:

```python
async def save_spec_document(db, req_id, user_id, content):
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    if req.status != "drafting_spec":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前状态不允许编辑规格说明")

    team_id = await _get_team_id_by_requirement(db, req_id)
    errors, suggestions = await _validate_spec_content(content, db, team_id)

    if errors:
        raise BusinessError(ERR_VALIDATION, "规范内容格式有误", errors=errors)

    stmt = select(SpecDocument).where(SpecDocument.requirement_id == req_id)
    result = await db.execute(stmt)
    doc = result.scalar_one_or_none()

    from datetime import datetime, timezone
    new_version_num = (doc.current_version + 1) if doc else 1
    new_version_entry = {
        "version": new_version_num,
        "content": content,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user_id,
    }

    if doc is None:
        doc = SpecDocument(
            requirement_id=req_id,
            current_version=new_version_num,
            versions=[new_version_entry],
        )
        db.add(doc)
    else:
        versions = list(doc.versions or [])
        versions.append(new_version_entry)
        doc.current_version = new_version_num
        doc.versions = versions

    await db.commit()
    return {
        "version": new_version_num,
        "errors": [],
        "suggestions": suggestions,
    }
```

- [ ] **Step 5: Run all spec tests**

Run: `conda run -n sdd python -m pytest backend/tests/test_specifications.py backend/tests/test_spec_template_agent.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/specification.py backend/tests/test_specifications.py
git commit -m "feat: spec validation returns suggestions instead of errors for missing fields"
```

---

### Task 2: agent-guide API with requirement context

**Files:**
- Modify: `backend/app/services/specification.py`
- Modify: `backend/app/api/teams.py`
- Test: `backend/tests/test_specifications.py`

Add optional `requirement_id` query param to `GET /teams/{teamId}/spec-template/agent-guide`. When provided, include requirement data in the response.

- [ ] **Step 1: Update `get_agent_guide` service function**

In `backend/app/services/specification.py`, change:

```python
async def get_agent_guide(
    db: AsyncSession, team_id: int, user_id: int, requirement_id: int | None = None
) -> dict:
    result = await get_spec_template(db, team_id, user_id)

    if requirement_id is not None:
        req = await _get_requirement(db, requirement_id)
        if req is None:
            raise BusinessError(ERR_NOT_FOUND, "需求不存在")

        req_team_id = await _get_team_id_by_requirement(db, requirement_id)
        if req_team_id != team_id:
            raise BusinessError(ERR_FORBIDDEN, "无权访问该需求")

        result["requirement"] = {
            "id": req.id,
            "title": req.title,
            "description": req.description,
            "req_type": req.req_type,
            "priority": req.priority,
            "type_detail": req.type_detail,
            "prototype_html": req.prototype_html,
            "status": req.status,
        }

    return result
```

- [ ] **Step 2: Update the API route**

In `backend/app/api/teams.py`, change the `get_agent_guide` function:

```python
@router.get("/{teamId}/spec-template/agent-guide")
async def get_agent_guide(
    teamId: str,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
    requirement_id: int | None = Query(default=None),
) -> dict:
    tid = await _resolve_team_id(db, teamId)
    data = await spec_svc.get_agent_guide(db, tid, int(user["sub"]), requirement_id)
    return {"code": 0, "message": "success", "data": data}
```

Ensure `Query` is imported from `fastapi`.

- [ ] **Step 3: Write test**

```python
class TestAgentGuideWithRequirement:
    @pytest.mark.asyncio
    async def test_agent_guide_without_requirement_id(self, client, normal_user, owner_role):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id)
        resp = await client.get(f"/api/v1/teams/{team.id}/spec-template/agent-guide", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert "requirement" not in body["data"]
        assert "sections" in body["data"]

    @pytest.mark.asyncio
    async def test_agent_guide_with_requirement_id(self, client, normal_user, owner_role):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id)
        resp = await client.post(
            "/api/v1/requirements",
            json={"title": "guide test", "type": "feature", "priority": 2, "description": "test desc"},
            headers=headers,
        )
        req_id = resp.json()["data"]["id"]

        resp2 = await client.get(
            f"/api/v1/teams/{team.id}/spec-template/agent-guide?requirement_id={req_id}",
            headers=headers,
        )
        assert resp2.status_code == 200
        body = resp2.json()
        assert "requirement" in body["data"]
        assert body["data"]["requirement"]["id"] == req_id
        assert body["data"]["requirement"]["title"] == "guide test"
```

- [ ] **Step 4: Run tests**

Run: `conda run -n sdd python -m pytest backend/tests/test_specifications.py -v -k "agent_guide"`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/specification.py backend/app/api/teams.py backend/tests/test_specifications.py
git commit -m "feat: agent-guide API accepts requirement_id to inject requirement context"
```

---

### Task 3: requirement-guide API

**Files:**
- Create: `backend/app/services/requirement_guide.py`
- Modify: `backend/app/api/requirements.py`
- Test: `backend/tests/test_requirement_guide.py`

- [ ] **Step 1: Create requirement guide service**

Create `backend/app/services/requirement_guide.py`:

```python
REQ_TYPES = [
    {
        "value": "feature",
        "label": "功能需求",
        "description": "新功能或功能增强",
    },
    {
        "value": "bug",
        "label": "缺陷修复",
        "description": "Bug 修复",
        "type_detail_schema": {
            "reproduce_steps": "复现步骤",
            "environment": "运行环境",
            "severity": "严重程度 (critical/major/minor)",
        },
    },
    {
        "value": "optimization",
        "label": "优化改进",
        "description": "性能优化或体验改进",
        "type_detail_schema": {
            "current_issue": "当前问题",
            "expected_improvement": "预期改进",
            "metrics": "衡量指标",
        },
    },
]

PRIORITY_LEVELS = [
    {"value": 3, "label": "高"},
    {"value": 2, "label": "中"},
    {"value": 1, "label": "低"},
]

SUGGESTIONS = [
    "建议填写 description 以帮助后续规范生成",
    "如果是 bug 类型，建议填写 type_detail 中的 reproduce_steps 和 severity",
    "建议提供 prototype_html 原型图以便规范中的页面设计更准确",
]


def get_requirement_guide() -> dict:
    return {
        "req_types": REQ_TYPES,
        "priority_levels": PRIORITY_LEVELS,
        "required_fields": ["title", "req_type", "priority", "iteration_id"],
        "optional_fields": ["description", "type_detail", "prototype_html"],
        "suggestions": SUGGESTIONS,
    }
```

- [ ] **Step 2: Add API route**

In `backend/app/api/requirements.py`, add at the top of the router:

```python
from app.services import requirement_guide as rg_svc

@router.get("/guide")
async def get_requirement_guide(
    user: Annotated[dict, Depends(get_current_user)],
) -> dict:
    data = rg_svc.get_requirement_guide()
    return {"code": 0, "message": "success", "data": data}
```

**Important:** This route must be registered BEFORE `@router.get("")` and `@router.get("/{id}")` to avoid path conflicts. Place it right after the router definition, before the list endpoint.

- [ ] **Step 3: Write test**

Create `backend/tests/test_requirement_guide.py`:

```python
import pytest
from tests.conftest import auth_headers


class TestRequirementGuide:
    @pytest.mark.asyncio
    async def test_get_requirement_guide(self, client, normal_user):
        headers = auth_headers(normal_user.id)
        resp = await client.get("/api/v1/requirements/guide", headers=headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["code"] == 0

        data = body["data"]
        assert len(data["req_types"]) == 3
        assert data["req_types"][0]["value"] == "feature"
        assert len(data["priority_levels"]) == 3
        assert "required_fields" in data
        assert "suggestions" in data
        assert len(data["suggestions"]) > 0

    @pytest.mark.asyncio
    async def test_requirement_guide_unauthorized(self, client):
        resp = await client.get("/api/v1/requirements/guide")
        assert resp.status_code == 401
```

- [ ] **Step 4: Run test**

Run: `conda run -n sdd python -m pytest backend/tests/test_requirement_guide.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/requirement_guide.py backend/app/api/requirements.py backend/tests/test_requirement_guide.py
git commit -m "feat: add requirement-guide API for agent requirement creation"
```

---

### Task 4: Task model fields + Alembic migration

**Files:**
- Modify: `backend/app/models/task.py`
- Create: Alembic migration

- [ ] **Step 1: Add fields to Task model**

In `backend/app/models/task.py`, add after `commit_sha`:

```python
    task_type: Mapped[str | None] = mapped_column(String(20), default=None)
    source_section: Mapped[str | None] = mapped_column(String(50), default=None)
    spec_reference: Mapped[dict | None] = mapped_column(JSONB, default=None)
```

Add `JSONB` import:
```python
from sqlalchemy.dialects.postgresql import JSONB
```

- [ ] **Step 2: Update create_task service to accept new fields**

In `backend/app/services/task.py`, update `create_task` signature:

```python
async def create_task(
    db: AsyncSession,
    requirement_id: int,
    user_id: int,
    title: str,
    description: str | None = None,
    assignee_id: int | None = None,
    task_type: str | None = None,
    source_section: str | None = None,
    spec_reference: dict | None = None,
) -> dict:
```

And in the Task creation:
```python
    task = Task(
        requirement_id=requirement_id,
        title=title,
        description=description,
        assignee_id=assignee_id,
        status="pending",
        created_by=user_id,
        task_type=task_type,
        source_section=source_section,
        spec_reference=spec_reference,
    )
```

Update `_task_to_dict` to include new fields:
```python
def _task_to_dict(task: Task) -> dict:
    return {
        "id": task.id,
        "requirement_id": task.requirement_id,
        "title": task.title,
        "description": task.description,
        "assignee_id": task.assignee_id,
        "status": task.status,
        "created_by": task.created_by,
        "task_type": task.task_type,
        "source_section": task.source_section,
        "spec_reference": task.spec_reference,
        "git_branch": task.git_branch,
        "commit_sha": task.commit_sha,
        "pr_url": task.pr_url,
        "artifact_url": task.artifact_url,
        "created_at": task.created_at.isoformat() if task.created_at else None,
        "updated_at": task.updated_at.isoformat() if task.updated_at else None,
    }
```

- [ ] **Step 3: Update API request model**

In `backend/app/api/requirements.py`, update `CreateTaskRequest`:

```python
class CreateTaskRequest(BaseModel):
    title: str
    description: str | None = None
    assignee_id: int | None = None
    task_type: str | None = None
    source_section: str | None = None
    spec_reference: dict | None = None
```

And update the create task endpoint to pass new fields to the service.

- [ ] **Step 4: Generate Alembic migration**

Run: `conda run -n sdd python -m alembic -c backend/alembic.ini revision --autogenerate -m "add_task_gen_fields" -n "add task_type source_section spec_reference"`

- [ ] **Step 5: Run migration**

Run: `conda run -n sdd python -m alembic -c backend/alembic.ini upgrade head`

- [ ] **Step 6: Run task tests**

Run: `conda run -n sdd python -m pytest backend/tests/test_tasks.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/task.py backend/app/services/task.py backend/app/api/requirements.py backend/alembic/
git commit -m "feat: add task_type, source_section, spec_reference fields to Task model"
```

---

### Task 5: generate-tasks API

**Files:**
- Create: `backend/app/services/task_generator.py`
- Modify: `backend/app/api/requirements.py`
- Test: `backend/tests/test_task_generator.py`

- [ ] **Step 1: Create task generator service**

Create `backend/app/services/task_generator.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BusinessError, ERR_NOT_FOUND, ERR_REQUIREMENT_STATUS, ERR_VALIDATION
from app.models import Requirement, Task
from app.models.spec import SpecDocument
from app.services import task as task_svc


async def generate_tasks(
    db: AsyncSession,
    requirement_id: int,
    user_id: int,
    strategy: str = "hybrid",
) -> dict:
    req_stmt = select(Requirement).where(Requirement.id == requirement_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    if req.status != "approved":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "需求未通过审核，无法生成任务")

    spec_stmt = select(SpecDocument).where(SpecDocument.requirement_id == requirement_id)
    spec_result = await db.execute(spec_stmt)
    spec_doc = spec_result.scalar_one_or_none()
    if spec_doc is None or spec_doc.current_version == 0:
        raise BusinessError(ERR_VALIDATION, "规范文档为空，请先填写规范")

    versions = spec_doc.versions or []
    content = versions[-1].get("content", {}) if versions else {}

    created = []
    suggestions = []
    errors = []

    if strategy in ("by_page", "hybrid"):
        pages = _get_pages(content)
        for page in pages:
            task = await task_svc.create_task(
                db, requirement_id, user_id,
                title=f"实现{page.get('name', '未知页面')}",
                description=_build_page_description(page),
                task_type="frontend",
                source_section=f"page_structure:{page.get('code', '')}",
                spec_reference=_build_page_reference(page, content),
            )
            created.append(task)
            if not task.get("assignee_id"):
                suggestions.append({
                    "task_id": task["id"],
                    "field": "assignee_id",
                    "message": f"任务「{task['title']}」未分配负责人，建议指定",
                })

    if strategy in ("by_api", "hybrid"):
        api_groups = _group_apis(content)
        for group_name, endpoints in api_groups.items():
            task = await task_svc.create_task(
                db, requirement_id, user_id,
                title=f"实现{group_name} API",
                description=_build_api_description(endpoints),
                task_type="backend",
                source_section=f"api_design:{group_name}",
                spec_reference={"endpoints": endpoints},
            )
            created.append(task)

    tables = _get_tables(content)
    if tables:
        task = await task_svc.create_task(
            db, requirement_id, user_id,
            title="数据库变更",
            description=_build_table_description(tables),
            task_type="database",
            source_section="table_design",
            spec_reference={"tables": tables},
        )
        created.append(task)

    return {
        "created": created,
        "errors": errors,
        "suggestions": suggestions,
    }


def _get_pages(content: dict) -> list[dict]:
    return content.get("page_structure", {}).get("pages", [])


def _get_tables(content: dict) -> list[dict]:
    return content.get("table_design", {}).get("tables", [])


def _group_apis(content: dict) -> dict[str, list[dict]]:
    endpoints = content.get("api_design", {}).get("endpoints", [])
    groups: dict[str, list[dict]] = {}
    for ep in endpoints:
        path = ep.get("path", "")
        parts = path.strip("/").split("/")
        group = parts[0] if parts else "default"
        groups.setdefault(group, []).append(ep)
    return groups


def _build_page_description(page: dict) -> str:
    elements = page.get("elements", [])
    interactions = page.get("interactions", [])
    lines = [f"页面: {page.get('name', '')}"]
    if page.get("route"):
        lines.append(f"路由: {page['route']}")
    if elements:
        lines.append(f"元素数: {len(elements)}")
    if interactions:
        lines.append(f"交互数: {len(interactions)}")
    return "\n".join(lines)


def _build_page_reference(page: dict, content: dict) -> dict:
    ref = {
        "page_code": page.get("code", ""),
        "page_name": page.get("name", ""),
        "route": page.get("route", ""),
        "elements": page.get("elements", []),
        "interactions": page.get("interactions", []),
    }
    page_apis = _find_apis_for_page(page, content)
    if page_apis:
        ref["related_apis"] = page_apis
    return ref


def _find_apis_for_page(page: dict, content: dict) -> list[dict]:
    page_code = page.get("code", "")
    endpoints = content.get("api_design", {}).get("endpoints", [])
    related = []
    for ep in endpoints:
        path = ep.get("path", "")
        if page_code and page_code.replace("-", "") in path.replace("/", "").replace("_", ""):
            related.append({"method": ep.get("method", ""), "path": path})
    return related


def _build_api_description(endpoints: list[dict]) -> str:
    lines = []
    for ep in endpoints:
        lines.append(f"{ep.get('method', '')} {ep.get('path', '')} — {ep.get('description', '')}")
    return "\n".join(lines)


def _build_table_description(tables: list[dict]) -> str:
    lines = []
    for t in tables:
        field_count = len(t.get("fields", []))
        lines.append(f"{t.get('name', '')} ({field_count} 字段) — {t.get('description', '')}")
    return "\n".join(lines)
```

- [ ] **Step 2: Add API route**

In `backend/app/api/requirements.py`, add:

```python
from app.services import task_generator as tg_svc

class GenerateTasksRequest(BaseModel):
    strategy: str = "hybrid"

@router.post("/{id}/generate-tasks")
async def generate_tasks(
    id: int,
    body: GenerateTasksRequest | None = None,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    strategy = body.strategy if body else "hybrid"
    data = await tg_svc.generate_tasks(db, id, int(user["sub"]), strategy)
    return {"code": 0, "message": "success", "data": data}
```

Note: `GenerateTasksRequest` parameter should use `Body(default=None)` or make it optional. Adjust import as needed.

- [ ] **Step 3: Write test**

Create `backend/tests/test_task_generator.py`:

```python
import pytest
from tests.conftest import auth_headers


class TestTaskGenerator:
    @pytest.mark.asyncio
    async def test_generate_tasks_from_spec(self, client, normal_user, owner_role):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id)

        resp = await client.post(
            "/api/v1/requirements",
            json={"title": "gen task test", "type": "feature", "priority": 2, "description": "test"},
            headers=headers,
        )
        req_id = resp.json()["data"]["id"]

        await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "approved"}, headers=headers)

        await client.put(
            f"/api/v1/iterations/1/requirements/{req_id}/spec",
            json={"content": {
                "page_structure": {
                    "pages": [
                        {
                            "name": "登录页面",
                            "code": "login-page",
                            "route": "/login",
                            "elements": [
                                {"code": "btn-login", "type": "button", "label": "登录", "role": "button", "accessible_name": "登录", "interaction": "提交表单"}
                            ],
                            "interactions": [
                                {"trigger": "btn-login click", "behavior": "提交登录表单"}
                            ]
                        }
                    ]
                },
                "api_design": {
                    "endpoints": [
                        {"method": "POST", "path": "/api/v1/auth/login", "description": "登录接口"}
                    ]
                }
            }},
            headers=auth_headers(normal_user.id, permissions=["spec_template:edit"]),
        )

        resp2 = await client.post(f"/api/v1/requirements/{req_id}/generate-tasks", json={"strategy": "hybrid"}, headers=headers)
        assert resp2.status_code == 200
        body = resp2.json()
        assert body["code"] == 0
        assert len(body["data"]["created"]) >= 2
        task_types = [t["task_type"] for t in body["data"]["created"]]
        assert "frontend" in task_types
```

- [ ] **Step 4: Run test**

Run: `conda run -n sdd python -m pytest backend/tests/test_task_generator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/task_generator.py backend/app/api/requirements.py backend/tests/test_task_generator.py
git commit -m "feat: add generate-tasks API to auto-split tasks from spec"
```

---

### Task 6: generate-test-cases API

**Files:**
- Create: `backend/app/services/test_generator.py`
- Modify: `backend/app/api/requirements.py`
- Test: `backend/tests/test_test_generator.py`

- [ ] **Step 1: Create test generator service**

Create `backend/app/services/test_generator.py`:

```python
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import BusinessError, ERR_NOT_FOUND, ERR_REQUIREMENT_STATUS, ERR_VALIDATION
from app.models import Requirement
from app.models.spec import SpecDocument
from app.services import test_case as tc_svc


async def generate_test_cases(
    db: AsyncSession,
    requirement_id: int,
    user_id: int,
    case_types: list[str] | None = None,
) -> dict:
    if case_types is None:
        case_types = ["e2e", "api"]

    req_stmt = select(Requirement).where(Requirement.id == requirement_id, Requirement.is_deleted == False)
    req_result = await db.execute(req_stmt)
    req = req_result.scalar_one_or_none()
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")
    if req.status not in ("drafting_tests", "approved"):
        raise BusinessError(ERR_REQUIREMENT_STATUS, "需求状态不允许生成测试用例")

    spec_stmt = select(SpecDocument).where(SpecDocument.requirement_id == requirement_id)
    spec_result = await db.execute(spec_stmt)
    spec_doc = spec_result.scalar_one_or_none()
    if spec_doc is None or spec_doc.current_version == 0:
        raise BusinessError(ERR_VALIDATION, "规范文档为空，请先填写规范")

    versions = spec_doc.versions or []
    content = versions[-1].get("content", {}) if versions else {}

    created = []
    suggestions = []
    errors = []

    if "e2e" in case_types:
        pages = content.get("page_structure", {}).get("pages", [])
        for page in pages:
            for el in page.get("elements", []):
                if el.get("interaction"):
                    steps = _build_e2e_steps(page, el)
                    expected = _build_e2e_expected(el)
                    related_api = _find_api_for_element(el, content)

                    tc = await tc_svc.create_test_case(
                        db, requirement_id,
                        title=f"验证{page.get('name', '')}中「{el.get('accessible_name') or el.get('label', '')}」的{el.get('interaction', '交互行为')}",
                        case_type="e2e",
                        precondition=f"用户已登录，页面已加载",
                        steps=steps,
                        expected_result=expected,
                        related_element=el.get("code", ""),
                        related_api=related_api,
                    )
                    created.append(tc)

                    if not related_api:
                        suggestions.append({
                            "case_id": tc["id"],
                            "field": "related_api",
                            "message": f"测试用例「{tc['title']}」未关联 API，建议补充",
                        })

    if "api" in case_types:
        endpoints = content.get("api_design", {}).get("endpoints", [])
        for ep in endpoints:
            tc = await tc_svc.create_test_case(
                db, requirement_id,
                title=f"验证 {ep.get('method', '')} {ep.get('path', '')} 接口",
                case_type="api",
                precondition="系统正常运行",
                steps=f"1. 发送 {ep.get('method', '')} 请求到 {ep.get('path', '')}\n2. 检查响应状态码和返回数据",
                expected_result=f"返回成功状态码，响应体包含预期数据结构",
                related_api=f"{ep.get('method', '')} {ep.get('path', '')}",
            )
            created.append(tc)

    total_interactions = sum(
        len([e for e in p.get("elements", []) if e.get("interaction")])
        for p in content.get("page_structure", {}).get("pages", [])
    )
    e2e_count = len([c for c in created if c.get("case_type") == "e2e"])
    if total_interactions > 0 and e2e_count < total_interactions:
        suggestions.append({
            "type": "coverage",
            "message": f"规范中定义了 {total_interactions} 个交互行为，当前生成了 {e2e_count} 个 E2E 测试用例",
        })

    return {
        "created": created,
        "errors": errors,
        "suggestions": suggestions,
    }


def _build_e2e_steps(page: dict, element: dict) -> str:
    route = page.get("route", "页面")
    an = element.get("accessible_name") or element.get("label", "")
    interaction = element.get("interaction", "")
    return f"1. 导航到 {route} 页面\n2. 操作「{an}」({interaction})\n3. 验证预期结果"


def _build_e2e_expected(element: dict) -> str:
    interaction = element.get("interaction", "")
    return f"{interaction}后系统响应正常"


def _find_api_for_element(element: dict, content: dict) -> str:
    code = element.get("code", "")
    endpoints = content.get("api_design", {}).get("endpoints", [])
    for ep in endpoints:
        path = ep.get("path", "")
        for keyword in code.split("-"):
            if len(keyword) > 2 and keyword in path:
                return f"{ep.get('method', '')} {path}"
    return ""
```

- [ ] **Step 2: Add API route**

In `backend/app/api/requirements.py`, add:

```python
from app.services import test_generator as testgen_svc

class GenerateTestCasesRequest(BaseModel):
    case_types: list[str] | None = None

@router.post("/{id}/generate-test-cases")
async def generate_test_cases(
    id: int,
    body: GenerateTestCasesRequest | None = None,
    user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict:
    case_types = body.case_types if body else None
    data = await testgen_svc.generate_test_cases(db, id, int(user["sub"]), case_types)
    return {"code": 0, "message": "success", "data": data}
```

- [ ] **Step 3: Write test**

Create `backend/tests/test_test_generator.py`:

```python
import pytest
from tests.conftest import auth_headers


class TestTestGenerator:
    @pytest.mark.asyncio
    async def test_generate_test_cases_from_spec(self, client, normal_user, owner_role):
        team = owner_role["team"]
        headers = auth_headers(normal_user.id)

        resp = await client.post(
            "/api/v1/requirements",
            json={"title": "gen tc test", "type": "feature", "priority": 2, "description": "test"},
            headers=headers,
        )
        req_id = resp.json()["data"]["id"]

        await client.patch(f"/api/v1/requirements/{req_id}", json={"status": "drafting_tests"}, headers=headers)

        await client.put(
            f"/api/v1/iterations/1/requirements/{req_id}/spec",
            json={"content": {
                "page_structure": {
                    "pages": [
                        {
                            "name": "登录页",
                            "code": "login",
                            "route": "/login",
                            "elements": [
                                {"code": "btn-login", "type": "button", "label": "登录", "accessible_name": "登录", "interaction": "提交登录表单"}
                            ]
                        }
                    ]
                },
                "api_design": {
                    "endpoints": [
                        {"method": "POST", "path": "/api/v1/auth/login", "description": "登录"}
                    ]
                }
            }},
            headers=auth_headers(normal_user.id, permissions=["spec_template:edit"]),
        )

        resp2 = await client.post(f"/api/v1/requirements/{req_id}/generate-test-cases", json={"case_types": ["e2e", "api"]}, headers=headers)
        assert resp2.status_code == 200
        body = resp2.json()
        assert body["code"] == 0
        assert len(body["data"]["created"]) >= 2
        case_types = [c["case_type"] for c in body["data"]["created"]]
        assert "e2e" in case_types
        assert "api" in case_types
```

- [ ] **Step 4: Run test**

Run: `conda run -n sdd python -m pytest backend/tests/test_test_generator.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/test_generator.py backend/app/api/requirements.py backend/tests/test_test_generator.py
git commit -m "feat: add generate-test-cases API to auto-create test cases from spec"
```

---

### Task 7: Requirement create returns suggestions

**Files:**
- Modify: `backend/app/services/requirement.py`
- Modify: `backend/app/api/requirements.py`

- [ ] **Step 1: Add suggestion logic to create_requirement**

In `backend/app/services/requirement.py`, modify `create_requirement` to return suggestions:

After the existing validation and creation, add suggestion generation before return:

```python
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
```

- [ ] **Step 2: Run existing requirement tests**

Run: `conda run -n sdd python -m pytest backend/tests/test_requirements.py -v`
Expected: All PASS (existing tests may need adjustment if they check exact response shape)

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/requirement.py
git commit -m "feat: requirement create returns suggestions for missing optional fields"
```

---

### Task 8: Final verification

- [ ] **Step 1: Run all backend tests**

Run: `conda run -n sdd python -m pytest backend/tests/ -v --timeout=120`
Expected: All tests PASS

- [ ] **Step 2: Push**

```bash
git push
```
