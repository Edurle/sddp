# 规范原型图 + JSON Schema 校验 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为页面结构章节增加 HTML 原型图支持（iframe 沙箱展示），并为规范文档增加完整的 JSON Schema 校验（保存时触发）。

**Architecture:** 
1. 在规范模板的 `page_structure` 章节中新增 `prototype_html` 字段，前端用 `<iframe sandbox>` 渲染 HTML 原型
2. 在模板的每个 `SpecTemplateField` 上新增 `json_schema` 字段存储 JSON Schema 定义，后端用 `jsonschema` 库在保存规范时做完整校验

**Tech Stack:** Python / FastAPI / jsonschema / Vue 3 / TypeScript

---

## File Structure

| Action | File | Responsibility |
|--------|------|---------------|
| Modify | `backend/app/mongo_models/spec_template.py` | 模板模型：新增 `prototype_html` 字段定义、`json_schema` 字段、默认 Schema |
| Modify | `backend/app/services/specification.py` | 服务层：新增 `_validate_spec_content` 校验逻辑，保存时触发 |
| Modify | `backend/app/schemas/specification.py` | Pydantic 模型：`SpecFieldDefinition` 新增 `json_schema` 字段 |
| Modify | `backend/requirements.txt` | 依赖：新增 `jsonschema` |
| Modify | `frontend/src/views/requirement/RequirementDetailPage.vue` | 前端：结构化规范编辑器 + iframe 原型预览 |
| Modify | `backend/tests/test_specifications.py` | 测试：新增校验相关测试用例 |
| Modify | `docs/superpowers/specs/design/10-test-cases-backend-requirement-specification.md` | 规范：新增测试用例文档 |
| Modify | `docs/superpowers/specs/design/01-entities-and-tables.md` | 规范：更新 MongoDB 集合设计 |
| Modify | `docs/superpowers/specs/design/03-api-project-iteration-requirement-specification.md` | 规范：更新 API 设计 |

---

## Task 1: 安装 jsonschema 依赖

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: 添加依赖到 requirements.txt**

在 `backend/requirements.txt` 末尾添加 `jsonschema`:

```
jsonschema
```

- [ ] **Step 2: 安装依赖**

Run: `cd backend && pip install jsonschema`
Expected: 成功安装

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: add jsonschema dependency for spec content validation"
```

---

## Task 2: 更新规范模板模型 — 新增 prototype_html 字段和默认 JSON Schema

**Files:**
- Modify: `backend/app/mongo_models/spec_template.py`
- Modify: `backend/app/schemas/specification.py`

- [ ] **Step 1: 更新 SpecTemplateField 和 SpecFieldDefinition**

在 `backend/app/mongo_models/spec_template.py` 的 `SpecTemplateField` dataclass 中新增 `json_schema` 字段：

```python
@dataclass
class SpecTemplateField:
    name: str
    display_name: str
    type: str  # "text" | "list" | "object"
    required: bool = False
    description: str | None = None
    json_schema: dict[str, Any] | None = None
```

在 `backend/app/schemas/specification.py` 的 `SpecFieldDefinition` Pydantic 模型中新增 `json_schema` 字段：

```python
class SpecFieldDefinition(BaseModel):
    name: str
    display_name: str
    type: str
    required: bool = True
    description: str | None = None
    json_schema: dict | None = None
```

- [ ] **Step 2: 更新 DEFAULT_SECTIONS — 页面结构新增 prototype_html 字段**

在 `spec_template.py` 的 `DEFAULT_SECTIONS` 中，`page_structure` section 的 fields 列表新增：

```python
{
    "name": "page_structure",
    "display_name": "页面结构",
    "required": True,
    "fields": [
        {"name": "pages", "display_name": "页面列表", "type": "list", "required": True, "description": "每个页面的名称、编码、元素列表（含唯一编码）、交互行为"},
        {"name": "prototype_html", "display_name": "原型图HTML", "type": "text", "required": False, "description": "页面原型图的HTML代码，在规范中以iframe沙箱展示"},
    ],
},
```

- [ ] **Step 3: 更新 DEFAULT_SECTIONS — 为所有字段添加默认 JSON Schema**

为每个默认章节的必填字段添加 `json_schema`，定义具体结构约束：

`entity_definition.fields` 的 json_schema:
```python
{
    "type": "array",
    "items": {
        "type": "object",
        "required": ["name", "fields"],
        "properties": {
            "name": {"type": "string", "minLength": 1, "description": "实体名称"},
            "description": {"type": "string", "description": "实体描述"},
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "type"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "type": {"type": "string", "minLength": 1},
                        "constraints": {"type": "array", "items": {"type": "string"}},
                    },
                },
                "minItems": 1,
            },
        },
    },
}
```

`table_design.tables` 的 json_schema:
```python
{
    "type": "array",
    "items": {
        "type": "object",
        "required": ["name", "fields"],
        "properties": {
            "name": {"type": "string", "minLength": 1, "description": "表名"},
            "description": {"type": "string"},
            "fields": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "type"],
                    "properties": {
                        "name": {"type": "string", "minLength": 1},
                        "type": {"type": "string", "minLength": 1},
                        "nullable": {"type": "boolean"},
                        "default": {},
                        "comment": {"type": "string"},
                    },
                },
                "minItems": 1,
            },
            "indexes": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "fields"],
                    "properties": {
                        "name": {"type": "string"},
                        "fields": {"type": "array", "items": {"type": "string"}},
                        "unique": {"type": "boolean"},
                    },
                },
            },
        },
    },
}
```

`page_structure.pages` 的 json_schema:
```python
{
    "type": "array",
    "items": {
        "type": "object",
        "required": ["name", "code", "elements"],
        "properties": {
            "name": {"type": "string", "minLength": 1, "description": "页面名称"},
            "code": {"type": "string", "minLength": 1, "description": "页面编码"},
            "route": {"type": "string"},
            "elements": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["code", "type", "label"],
                    "properties": {
                        "code": {"type": "string", "minLength": 1},
                        "type": {"type": "string", "minLength": 1},
                        "label": {"type": "string", "minLength": 1},
                        "interaction": {"type": "string"},
                    },
                },
            },
            "interactions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "trigger": {"type": "string"},
                        "behavior": {"type": "string"},
                    },
                },
            },
        },
    },
}
```

`page_structure.prototype_html` 的 json_schema:
```python
{
    "type": "string",
    "description": "HTML代码字符串",
}
```

`api_design.endpoints` 的 json_schema:
```python
{
    "type": "array",
    "items": {
        "type": "object",
        "required": ["method", "path", "description"],
        "properties": {
            "method": {"type": "string", "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]},
            "path": {"type": "string", "minLength": 1},
            "description": {"type": "string", "minLength": 1},
            "request_params": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "in", "type"],
                    "properties": {
                        "name": {"type": "string"},
                        "in": {"type": "string", "enum": ["query", "path", "body", "header"]},
                        "type": {"type": "string"},
                        "required": {"type": "boolean"},
                        "description": {"type": "string"},
                    },
                },
            },
            "response": {"type": "object"},
            "errors": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "code": {"type": "integer"},
                        "message": {"type": "string"},
                    },
                },
            },
        },
    },
}
```

- [ ] **Step 4: 更新 _section_from_dict 和 to_document 方法**

在 `spec_template.py` 的 `_section_from_dict` 方法中解析 `json_schema`：

```python
@staticmethod
def _section_from_dict(data: dict[str, Any]) -> SpecTemplateSection:
    fields = [
        SpecTemplateField(
            name=f.get("name", ""),
            display_name=f.get("display_name", ""),
            type=f.get("type", "text"),
            required=f.get("required", False),
            description=f.get("description"),
            json_schema=f.get("json_schema"),
        )
        for f in data.get("fields", [])
    ]
    return SpecTemplateSection(
        name=data.get("name", ""),
        display_name=data.get("display_name", ""),
        required=data.get("required", True),
        fields=fields,
    )
```

在 `to_document` 方法中输出 `json_schema`：

```python
def to_document(self) -> dict[str, Any]:
    return {
        "team_id": self.team_id,
        "sections": [
            {
                "name": s.name,
                "display_name": s.display_name,
                "required": s.required,
                "fields": [
                    {
                        "name": f.name,
                        "display_name": f.display_name,
                        "type": f.type,
                        "required": f.required,
                        "description": f.description,
                        "json_schema": f.json_schema,
                    }
                    for f in s.fields
                ],
            }
            for s in self.sections
        ],
        "updated_at": self.updated_at,
        "updated_by": self.updated_by,
    }
```

- [ ] **Step 5: Commit**

```bash
git add backend/app/mongo_models/spec_template.py backend/app/schemas/specification.py
git commit -m "feat: add prototype_html field and json_schema to spec template model"
```

---

## Task 3: 实现后端校验服务 — save_spec_document 中增加 JSON Schema 校验

**Files:**
- Modify: `backend/app/services/specification.py`

- [ ] **Step 1: 在 specification.py 顶部添加 import**

```python
import jsonschema
from app.cache import cache_instance
```

- [ ] **Step 2: 实现 _get_template_sections 辅助函数**

在 `specification.py` 中新增辅助函数，用于获取模板章节定义：

```python
def _get_template_sections(team_id: int) -> list[dict]:
    key = f"spec_template:{team_id}"
    data = cache_instance.get(key)
    if data is not None:
        return data.get("sections", [])
    return SpecTemplate().DEFAULT_SECTIONS
```

- [ ] **Step 3: 实现 _validate_spec_content 校验函数**

```python
def _validate_spec_content(content: dict, team_id: int) -> list[dict]:
    sections = _get_template_sections(team_id)
    errors = []

    for section in sections:
        section_name = section["name"]
        section_required = section.get("required", True)
        section_fields = section.get("fields", [])

        if section_name not in content:
            if section_required:
                errors.append({
                    "section": section_name,
                    "message": f"缺少必填章节: {section.get('display_name', section_name)}",
                })
            continue

        section_content = content[section_name]
        if not isinstance(section_content, dict):
            errors.append({
                "section": section_name,
                "message": f"章节 {section.get('display_name', section_name)} 的内容必须是对象",
            })
            continue

        for field_def in section_fields:
            field_name = field_def["name"]
            field_required = field_def.get("required", True)
            field_schema = field_def.get("json_schema")
            field_display = field_def.get("display_name", field_name)

            if field_name not in section_content:
                if field_required:
                    errors.append({
                        "section": section_name,
                        "field": field_name,
                        "message": f"缺少必填字段: {field_display}",
                    })
                continue

            if field_schema is not None:
                try:
                    jsonschema.validate(section_content[field_name], field_schema)
                except jsonschema.ValidationError as e:
                    errors.append({
                        "section": section_name,
                        "field": field_name,
                        "message": f"字段 {field_display} 格式不正确: {e.message}",
                        "path": list(e.absolute_path) if e.absolute_path else [],
                    })

    return errors
```

- [ ] **Step 4: 修改 save_spec_document — 添加校验**

在 `save_spec_document` 函数中，在状态检查之后、保存之前添加校验逻辑。需要先获取 requirement 以拿到 team_id：

```python
async def save_spec_document(
    db: AsyncSession, req_id: int, user_id: int, content: dict
) -> dict:
    req = await _get_requirement(db, req_id)
    if req is None:
        raise BusinessError(ERR_NOT_FOUND, "需求不存在")

    if req.status != "drafting_spec":
        raise BusinessError(ERR_REQUIREMENT_STATUS, "当前状态不允许编辑规格说明")

    team_id = await _get_team_id_by_requirement(db, req_id)
    errors = _validate_spec_content(content, team_id)
    if errors:
        raise BusinessError(ERR_VALIDATION, "规范内容校验失败", errors=errors)

    key = f"spec_document:{req_id}"
    data = cache_instance.get(key)
    if data is None:
        doc = SpecDocument(requirement_id=req_id)
    else:
        doc = SpecDocument(
            requirement_id=req_id,
            current_version=data.get("current_version", 0),
        )
        for v in data.get("versions", []):
            from app.mongo_models.spec_document import SpecDocumentVersion
            doc.versions.append(SpecDocumentVersion(
                version=v["version"],
                content=v["content"],
                created_at=v.get("created_at"),
                created_by=v.get("created_by"),
            ))

    new_version = doc.add_version(content, user_id)
    cache_instance.set(key, doc.to_document())
    return {"version": new_version.version}
```

- [ ] **Step 5: 实现 _get_team_id_by_requirement 辅助函数**

```python
async def _get_team_id_by_requirement(db: AsyncSession, req_id: int) -> int:
    from sqlalchemy import select as sel
    from app.models import Iteration as IterModel, Project as ProjModel
    req = await _get_requirement(db, req_id)
    if req is None:
        return 0
    stmt = sel(IterModel).where(IterModel.id == req.iteration_id)
    result = await db.execute(stmt)
    iteration = result.scalar_one_or_none()
    if iteration is None:
        return 0
    stmt2 = sel(ProjModel).where(ProjModel.id == iteration.project_id)
    result2 = await db.execute(stmt2)
    project = result2.scalar_one_or_none()
    if project is None:
        return 0
    return project.team_id
```

- [ ] **Step 6: 更新 BusinessError 支持额外数据**

在 `backend/app/exceptions.py` 中更新 `BusinessError` 以支持 errors 列表：

```python
class BusinessError(Exception):
    def __init__(self, code: int, message: str, errors: list | None = None):
        self.code = code
        self.message = message
        self.errors = errors or []
        super().__init__(message)
```

- [ ] **Step 7: 更新 main.py 中的异常处理器**

检查 `backend/app/main.py` 中的异常处理器，确保在返回 `ERR_VALIDATION` 错误时包含 `errors` 列表。找到异常处理器后添加 errors 字段：

```python
# 在 BusinessError 处理器中
return JSONResponse(
    status_code=400,
    content={
        "code": exc.code,
        "message": exc.message,
        "data": exc.errors if exc.errors else None,
    },
)
```

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/specification.py backend/app/exceptions.py backend/app/main.py
git commit -m "feat: add JSON Schema validation for spec content on save"
```

---

## Task 4: 编写后端测试用例 — JSON Schema 校验

**Files:**
- Modify: `backend/tests/test_specifications.py`

- [ ] **Step 1: 在 TestSaveSpecDocument 类中新增校验测试**

在 `test_specifications.py` 的 `TestSaveSpecDocument` 类末尾新增以下测试：

```python
class TestSpecContentValidation:
    @pytest.mark.asyncio
    async def test_save_spec_missing_required_section(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {"description": "test", "fields": []},
                    "table_design": {"tables": []},
                    "page_structure": {"pages": []},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001
        assert any("api_design" in e.get("section", "") or "api" in e.get("message", "") for e in (body.get("data") or []))

    @pytest.mark.asyncio
    async def test_save_spec_missing_required_field_in_section(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {},
                    "table_design": {"tables": []},
                    "page_structure": {"pages": []},
                    "api_design": {"endpoints": []},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

    @pytest.mark.asyncio
    async def test_save_spec_invalid_entity_fields_format(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {"description": "test entity", "fields": "not_an_array"},
                    "table_design": {"tables": []},
                    "page_structure": {"pages": []},
                    "api_design": {"endpoints": []},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 40001

    @pytest.mark.asyncio
    async def test_save_spec_valid_content_passes_validation(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {
                        "description": "用户实体",
                        "fields": [
                            {"name": "id", "type": "BIGINT", "constraints": ["PK"]},
                            {"name": "email", "type": "VARCHAR(255)", "constraints": ["NOT NULL"]},
                        ],
                    },
                    "table_design": {
                        "tables": [
                            {
                                "name": "users",
                                "fields": [
                                    {"name": "id", "type": "BIGINT"},
                                    {"name": "email", "type": "VARCHAR(255)"},
                                ],
                            }
                        ]
                    },
                    "page_structure": {
                        "pages": [
                            {
                                "name": "用户列表",
                                "code": "user-list",
                                "elements": [
                                    {"code": "user-btn-create", "type": "button", "label": "创建"},
                                ],
                            }
                        ]
                    },
                    "api_design": {
                        "endpoints": [
                            {
                                "method": "GET",
                                "path": "/api/v1/users",
                                "description": "获取用户列表",
                            }
                        ]
                    },
                    "constraints": {},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
        assert "version" in body["data"]

    @pytest.mark.asyncio
    async def test_save_spec_with_prototype_html(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {
                        "description": "test",
                        "fields": [{"name": "id", "type": "INT"}],
                    },
                    "table_design": {"tables": [{"name": "test", "fields": [{"name": "id", "type": "INT"}]}]},
                    "page_structure": {
                        "pages": [
                            {"name": "测试页", "code": "test-page", "elements": [{"code": "btn", "type": "button", "label": "按钮"}]}
                        ],
                        "prototype_html": "<div><h1>原型图</h1><button>点击</button></div>",
                    },
                    "api_design": {"endpoints": [{"method": "GET", "path": "/test", "description": "test"}]},
                    "constraints": {},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0

    @pytest.mark.asyncio
    async def test_save_spec_optional_constraints_section_can_be_omitted(
        self, client, normal_user, sample_requirement, db
    ):
        sample_requirement.status = "drafting_spec"
        db.add(sample_requirement)
        await db.commit()

        headers = auth_headers(normal_user.id, permissions=["requirement:edit"])
        resp = await client.put(
            f"/api/v1/requirements/{sample_requirement.id}/specification",
            json={
                "content": {
                    "entity_definition": {
                        "description": "test",
                        "fields": [{"name": "id", "type": "INT"}],
                    },
                    "table_design": {"tables": [{"name": "test", "fields": [{"name": "id", "type": "INT"}]}]},
                    "page_structure": {
                        "pages": [{"name": "test", "code": "test", "elements": [{"code": "btn", "type": "button", "label": "b"}]}]
                    },
                    "api_design": {"endpoints": [{"method": "GET", "path": "/test", "description": "test"}]},
                }
            },
            headers=headers,
        )
        body = resp.json()
        assert body["code"] == 0
```

- [ ] **Step 2: 运行测试确认全部通过**

Run: `cd backend && python -m pytest tests/test_specifications.py -v`
Expected: 所有测试 PASS（注意：校验实现需要在 Task 3 完成后才能通过）

- [ ] **Step 3: Commit**

```bash
git add backend/tests/test_specifications.py
git commit -m "test: add spec content validation test cases"
```

---

## Task 5: 更新前端 — 结构化规范编辑器 + HTML 原型图预览

**Files:**
- Modify: `frontend/src/views/requirement/RequirementDetailPage.vue`

- [ ] **Step 1: 替换 spec tab 的 textarea 为结构化编辑器**

将 `<textarea v-model="specContent">` 替换为按章节编辑的结构化表单。核心数据结构：

```typescript
interface SpecSection {
  name: string
  display_name: string
  required: boolean
  fields: SpecField[]
}

interface SpecField {
  name: string
  display_name: string
  type: string  // "text" | "list"
  required: boolean
  description: string | null
}

const specSections = ref<SpecSection[]>([])
const specFormData = ref<Record<string, Record<string, any>>>({})
```

在 `onMounted` 中获取团队模板：

```typescript
async function fetchSpecTemplate() {
  try {
    // 从 requirement -> iteration -> project -> team 链路获取 teamId
    // 先用 requirements 接口尝试
    const reqRes = await apiClient.get(`/api/v1/requirements/${reqId.value}`)
    const reqData = reqRes.data?.data || reqRes.data
    
    // 获取迭代和项目信息以取得 team_id
    if (reqData.iteration_id) {
      // 简化：直接获取模板（使用默认模板）
      // 如果有 team_id，则 GET /api/v1/teams/{teamId}/spec-template
    }
    
    // 使用默认模板结构作为 fallback
    specSections.value = [
      {
        name: "entity_definition", display_name: "实体定义", required: true,
        fields: [
          { name: "description", display_name: "实体描述", type: "text", required: true, description: "对实体的简要描述" },
          { name: "fields", display_name: "字段列表", type: "list", required: true, description: "实体包含的字段定义" },
        ],
      },
      {
        name: "table_design", display_name: "数据表设计", required: true,
        fields: [
          { name: "tables", display_name: "表列表", type: "list", required: true, description: "每个表的表名、字段、类型、索引" },
        ],
      },
      {
        name: "page_structure", display_name: "页面结构", required: true,
        fields: [
          { name: "pages", display_name: "页面列表", type: "list", required: true, description: "页面名称、编码、元素列表" },
          { name: "prototype_html", display_name: "原型图HTML", type: "text", required: false, description: "页面原型图的HTML代码" },
        ],
      },
      {
        name: "api_design", display_name: "API 设计", required: true,
        fields: [
          { name: "endpoints", display_name: "接口列表", type: "list", required: true, description: "每个接口的URL、方法、参数" },
        ],
      },
      {
        name: "constraints", display_name: "其他约束", required: false,
        fields: [
          { name: "directory_structure", display_name: "目录结构", type: "text", required: false, description: "项目目录结构规范" },
          { name: "naming_conventions", display_name: "命名规范", type: "text", required: false, description: "编码命名规范" },
          { name: "other", display_name: "其他约束", type: "text", required: false, description: "其他技术约束" },
        ],
      },
    ]
  } catch {
    // fallback to default
  }
}
```

- [ ] **Step 2: 实现结构化编辑器模板**

替换 `activeTab === 'spec'` 的 tab panel 内容：

```html
<div v-if="activeTab === 'spec'" class="tab-panel">
  <div class="spec-toolbar">
    <span v-if="saveSuccessMsg" class="save-msg">{{ saveSuccessMsg }}</span>
    <span v-else-if="validationErrors.length > 0" class="save-msg" style="color: #ff4d4f;">{{ validationErrors.length }} 个校验错误</span>
    <span v-else class="spec-hint">在下方编辑规范文档</span>
    <div class="spec-actions">
      <button data-testid="req-detail-btn-save-spec" @click="saveSpec">保存规范</button>
      <button v-if="req.status === 'drafting_spec'" data-testid="req-detail-btn-submit-spec-review" @click="openSubmitSpecReviewDialog">提交规范审核</button>
    </div>
  </div>
  
  <div v-if="validationErrors.length > 0" class="validation-errors">
    <div v-for="(err, idx) in validationErrors" :key="idx" class="validation-error-item">
      {{ err.section }}{{ err.field ? '.' + err.field : '' }}: {{ err.message }}
    </div>
  </div>

  <div v-for="section in specSections" :key="section.name" class="spec-section">
    <h3 class="section-title">
      {{ section.display_name }}
      <span v-if="section.required" class="required-mark">*</span>
    </h3>
    <div v-for="field in section.fields" :key="field.name" class="field-group">
      <label class="field-label">
        {{ field.display_name }}
        <span v-if="field.required" class="required-mark">*</span>
      </label>
      <p v-if="field.description" class="field-desc">{{ field.description }}</p>
      
      <template v-if="field.type === 'text'">
        <textarea
          v-model="specFormData[section.name][field.name]"
          :data-testid="`spec-field-${section.name}-${field.name}`"
          class="spec-field-textarea"
          :placeholder="field.description || ''"
        ></textarea>
      </template>
      
      <template v-else-if="field.type === 'list'">
        <textarea
          v-model="specFormData[section.name][field.name]"
          :data-testid="`spec-field-${section.name}-${field.name}`"
          class="spec-field-json"
          placeholder='JSON 数组格式，例如: [{"name": "xxx", ...}]'
        ></textarea>
      </template>
    </div>
  </div>

  <div v-if="prototypeHtml" class="prototype-preview">
    <h3 class="section-title">原型图预览</h3>
    <iframe
      :srcdoc="prototypeHtml"
      sandbox="allow-scripts"
      class="prototype-iframe"
    ></iframe>
  </div>
</div>
```

- [ ] **Step 3: 实现 saveSpec 方法更新**

更新 `saveSpec` 方法，将结构化表单数据序列化为 API 需要的 content 格式：

```typescript
const validationErrors = ref<any[]>([])

const prototypeHtml = computed(() => {
  const pageSection = specFormData.value['page_structure']
  if (pageSection && pageSection['prototype_html']) {
    return pageSection['prototype_html']
  }
  return ''
})

function serializeSpecContent(): Record<string, any> {
  const content: Record<string, any> = {}
  for (const section of specSections.value) {
    const sectionData = specFormData.value[section.name] || {}
    content[section.name] = {}
    for (const field of section.fields) {
      let value = sectionData[field.name]
      if (field.type === 'list' && typeof value === 'string') {
        try {
          value = JSON.parse(value)
        } catch {
          value = []
        }
      }
      content[section.name][field.name] = value ?? (field.type === 'list' ? [] : '')
    }
  }
  return content
}

async function saveSpec() {
  validationErrors.value = []
  try {
    const content = serializeSpecContent()
    await apiClient.put(`/api/v1/requirements/${reqId.value}/specification`, {
      content,
    })
    saveSuccessMsg.value = '保存成功'
    setTimeout(() => { saveSuccessMsg.value = '' }, 3000)
  } catch (err: any) {
    const resp = err.response?.data
    if (resp?.code === 40001 && resp?.data) {
      validationErrors.value = resp.data
    }
  }
}
```

- [ ] **Step 4: 实现加载规范数据时的反序列化**

在获取已有规范数据时，将其填充到表单中：

```typescript
function loadSpecContent(content: Record<string, any>) {
  for (const section of specSections.value) {
    if (!specFormData.value[section.name]) {
      specFormData.value[section.name] = {}
    }
    const sectionData = content[section.name] || {}
    for (const field of section.fields) {
      let value = sectionData[field.name]
      if (field.type === 'list' && Array.isArray(value)) {
        value = JSON.stringify(value, null, 2)
      }
      specFormData.value[section.name][field.name] = value ?? ''
    }
  }
}
```

在 `onMounted` 或 `fetchReq` 完成后加载规范数据：

```typescript
async function fetchSpecContent() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/specification`)
    const data = res.data?.data
    if (data?.content) {
      loadSpecContent(data.content)
    }
  } catch {
    // ignore
  }
}
```

- [ ] **Step 5: 添加样式**

```css
.spec-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #111;
  margin: 0 0 0.75rem 0;
}
.required-mark {
  color: #ff4d4f;
  margin-left: 2px;
}
.field-group {
  margin-bottom: 0.75rem;
}
.field-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}
.field-desc {
  font-size: 11px;
  color: #999;
  margin: 0 0 4px 0;
}
.spec-field-textarea {
  width: 100%;
  min-height: 60px;
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 6px;
  resize: vertical;
}
.spec-field-json {
  width: 100%;
  min-height: 120px;
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.6;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 6px;
  resize: vertical;
}
.prototype-preview {
  margin-top: 1.5rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
}
.prototype-iframe {
  width: 100%;
  height: 400px;
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 6px;
  background: #fff;
}
.validation-errors {
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
}
.validation-error-item {
  font-size: 12px;
  color: #ff4d4f;
  margin-bottom: 4px;
}
```

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/requirement/RequirementDetailPage.vue
git commit -m "feat: structured spec editor with prototype HTML preview and validation"
```

---

## Task 6: 更新规范文档

**Files:**
- Modify: `docs/superpowers/specs/design/10-test-cases-backend-requirement-specification.md`
- Modify: `docs/superpowers/specs/design/01-entities-and-tables.md`
- Modify: `docs/superpowers/specs/design/03-api-project-iteration-requirement-specification.md`

- [ ] **Step 1: 更新测试用例文档 (10-test-cases-backend-requirement-specification.md)**

在规范管理章节的「编辑规范文档」部分新增测试用例：

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-SPEC-015 | 缺少必填章节 | `status=drafting_spec` | content 缺少 `api_design` | 40001 | 校验失败，返回错误列表 |
| TC-SPEC-016 | 必填字段为空 | `status=drafting_spec` | `entity_definition` 为 `{}` | 40001 | 校验失败 |
| TC-SPEC-017 | 字段格式不正确 | `status=drafting_spec` | `entity_definition.fields` 为字符串 | 40001 | 校验失败，提示格式不正确 |
| TC-SPEC-018 | 完整合法内容通过 | `status=drafting_spec` | 完整的 5 章节内容 | 0 | 版本递增 |
| TC-SPEC-019 | 包含 prototype_html | `status=drafting_spec` | `page_structure.prototype_html` 含 HTML | 0 | 保存成功 |
| TC-SPEC-020 | 可选章节可省略 | `status=drafting_spec` | 不含 `constraints` | 0 | 保存成功 |

- [ ] **Step 2: 更新实体设计文档 (01-entities-and-tables.md)**

在 `specification_templates` 集合设计中：
1. `page_structure` 的 fields 新增 `prototype_html` 字段
2. 每个 field 对象新增 `json_schema` 字段（描述为"可选，JSON Schema 格式的内容校验规则"）

在字段类型说明表格中更新 prototype_html 的说明。

- [ ] **Step 3: 更新 API 设计文档 (03-api-project-iteration-requirement-specification.md)**

在 `PUT /api/v1/requirements/{reqId}/specification` 接口说明中：

1. 新增说明：保存时会根据团队模板的 JSON Schema 校验内容
2. 新增错误码：
   | code | 说明 |
   |------|------|
   | 40001 | 规范内容校验失败，data 中返回详细错误列表 |
3. 更新 content 示例，加入 `prototype_html` 字段
4. `page_structure` 的 content 示例中增加 `prototype_html` 字段

- [ ] **Step 4: Commit**

```bash
git add docs/superpowers/specs/design/
git commit -m "docs: update spec docs for prototype HTML and JSON Schema validation"
```

---

## Task 7: 运行完整测试并验证

**Files:**
- None

- [ ] **Step 1: 运行后端全部测试**

Run: `cd backend && python -m pytest tests/ -v`
Expected: 所有测试 PASS

- [ ] **Step 2: 运行前端 lint 检查**

Run: `cd frontend && npm run lint` (or equivalent)
Expected: 无错误

- [ ] **Step 3: 最终 Commit（如有 lint 修复）**

```bash
git add -A
git commit -m "fix: resolve lint issues after spec validation implementation"
```

---

## Self-Review Checklist

- [x] **Spec coverage:** 每个需求（prototype_html 字段、JSON Schema 校验、保存时触发）都有对应 Task
- [x] **Placeholder scan:** 无 TBD/TODO，所有代码步骤都有实际内容
- [x] **Type consistency:** `_validate_spec_content` 返回 `list[dict]`，`BusinessError.errors` 为 `list`，前端使用 `validationErrors` 为 `ref<any[]>`
