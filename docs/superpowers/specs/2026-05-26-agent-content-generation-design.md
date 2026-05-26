# Agent 驱动内容生成设计：需求/规范/任务/测试用例

## 目标

Agent 与人类交互，全自动完成：需求创建 → 规范填写 → 任务拆分 → 测试用例生成。人类通过对话描述需求，Agent 完成所有结构化工作，人类只做审核。平台提供上下文注入、校验反馈和结构化存储。

## 核心原则

1. **人类描述意图，Agent 创建结构** — 人类通过自然语言对话描述需求，Agent 将其转化为结构化的需求/规范/任务/测试用例
2. **Suggestion 机制** — 字段缺失不阻止保存，以建议形式反馈给 Agent 自行决定；字段格式错误才阻止保存
3. **逐级传递上下文** — 需求→规范→任务/测试，每级只消费上一级的输出
4. **结构化校验** — 代码层面验证所有内容，给出精确的错误/建议信息

## 一、需求创建

### 1.1 流程

人类通过对话描述需求（"我需要一个用户登录功能"），Agent 分析对话内容后创建结构化的 Requirement。

### 1.2 Agent 创建需求的引导

新增 `GET /api/v1/teams/{teamId}/requirement-guide` API，返回需求创建的结构化指引：

```json
{
  "code": 0,
  "data": {
    "req_types": [
      {
        "value": "feature",
        "label": "功能需求",
        "description": "新功能或功能增强",
        "type_detail_schema": null
      },
      {
        "value": "bug",
        "label": "缺陷修复",
        "description": "Bug 修复",
        "type_detail_schema": {
          "reproduce_steps": "复现步骤",
          "environment": "运行环境",
          "severity": "严重程度 (critical/major/minor)"
        }
      },
      {
        "value": "optimization",
        "label": "优化改进",
        "description": "性能优化或体验改进",
        "type_detail_schema": {
          "current_issue": "当前问题",
          "expected_improvement": "预期改进",
          "metrics": "衡量指标"
        }
      }
    ],
    "priority_levels": [
      { "value": 3, "label": "高" },
      { "value": 2, "label": "中" },
      { "value": 1, "label": "低" }
    ],
    "required_fields": ["title", "req_type", "priority", "iteration_id"],
    "optional_fields": ["description", "type_detail", "prototype_html"],
    "suggestions": [
      "建议填写 description 以帮助后续规范生成",
      "如果是 bug 类型，建议填写 type_detail 中的 reproduce_steps 和 severity",
      "建议提供 prototype_html 原型图以便规范中的页面设计更准确"
    ]
  }
}
```

Agent 拿到这个指引后：
1. 根据人类的对话内容判断 `req_type`
2. 填写对应的 `type_detail`（bug → reproduce_steps 等）
3. 判断 `priority`
4. 写清楚 `description`
5. 如果能生成原型图，填入 `prototype_html`

### 1.3 需求校验

`POST /api/v1/requirements` 创建时：

| 校验项 | 类型 | 条件 |
|--------|------|------|
| `title` 非空 | error | 始终 |
| `req_type` 合法值 | error | 始终 |
| `priority` 在 1-3 范围 | error | 始终 |
| `iteration_id` 存在 | error | 始终 |
| `description` 非空 | suggestion | 为空时建议补充 |
| `type_detail` 按类型填写完整 | suggestion | bug 缺少 reproduce_steps，optimization 缺少 current_issue 等 |
| `prototype_html` 非空 | suggestion | 为空时建议提供原型图 |

### 1.4 需求创建返回值

创建成功后响应中包含 suggestions：

```json
{
  "code": 0,
  "data": {
    "id": 123,
    "title": "用户登录功能",
    "errors": [],
    "suggestions": [
      {
        "field": "description",
        "message": "需求描述为空，建议补充以帮助后续规范生成"
      },
      {
        "field": "prototype_html",
        "message": "未提供原型图，建议提供以使页面设计更准确"
      }
    ]
  }
}
```

## 二、校验机制：Error vs Suggestion

所有保存类操作统一返回两种反馈：

| 类型 | 含义 | 对保存的影响 |
|------|------|-------------|
| `error` | 格式错误、必填项为空、schema 不通过 | **阻止保存** |
| `suggestion` | 字段缺失、引用不存在、覆盖率不足 | **不阻止保存**，供 Agent 参考 |

统一响应格式：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "errors": [],
    "suggestions": [
      {
        "section": "table_design",
        "field": null,
        "message": "章节「数据表设计」未填写，如涉及数据库变更建议补充"
      }
    ]
  }
}
```

Agent 处理逻辑：
1. `errors` 非空 → 修复后重新提交
2. `errors` 为空，`suggestions` 非空 → 根据需求判断是否补充后再次提交
3. 都为空 → 完成

## 三、规范填写

### 3.1 现状

- `save_spec_document` 校验 content 中的 section/field
- `required: true` 的 section/field 缺失 → 报错阻止保存
- `required: false` 的 section/field 缺失 → 跳过

### 3.2 改动

**校验逻辑改为 suggestion 模式：**

- 所有 section/field 缺失 → 不报错，加入 suggestions
- 已填写的 field → json_schema 校验，不通过则加入 errors（阻止保存）
- 最终：errors 为空则保存成功，suggestions 附加在响应中

具体改动在 `_validate_spec_content` 函数：

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

`save_spec_document` 调整：

```python
async def save_spec_document(db, req_id, user_id, content):
    # ... 状态检查 ...
    errors, suggestions = await _validate_spec_content(content, db, team_id)

    if errors:
        raise BusinessError(ERR_VALIDATION, "规范内容格式有误", errors=errors)

    # ... 保存逻辑 ...

    return {
        "version": new_version_num,
        "errors": [],
        "suggestions": suggestions,
    }
```

### 3.3 Agent 上下文注入

改造 `GET /teams/{teamId}/spec-template/agent-guide`，增加 `requirement_id` 可选参数：

```
GET /teams/{teamId}/spec-template/agent-guide?requirement_id=123
```

当传入 `requirement_id` 时，响应中包含需求信息：

```json
{
  "code": 0,
  "data": {
    "requirement": {
      "id": 123,
      "title": "用户登录功能",
      "description": "实现邮箱+密码登录...",
      "req_type": "feature",
      "priority": 3,
      "type_detail": { ... },
      "prototype_html": "<html>..."
    },
    "sections": [ ... ]
  }
}
```

不传 `requirement_id` 时行为不变（只返回模板）。

改动点：
- `get_agent_guide` service 函数增加 `requirement_id` 可选参数
- API 路由增加 `requirement_id` 可选 query 参数
- 当 `requirement_id` 存在时，查询需求信息并合并到响应中
- 校验用户是该需求所属团队的成员

## 四、任务自动拆分

### 4.1 新增 API

```
POST /api/v1/requirements/{id}/generate-tasks
```

请求体（可选，供人工微调）：

```json
{
  "strategy": "by_page",
  "assignee_overrides": {
    "login-page": 5,
    "user-api": 3
  }
}
```

`strategy` 取值：
- `by_page` — 按 page_structure 的每个 page 生成一个任务（默认）
- `by_api` — 按 api_design 的每个 endpoint 分组生成任务
- `hybrid` — 前端按页面拆分，后端按 API 拆分

响应：

```json
{
  "code": 0,
  "data": {
    "created": [
      { "id": 101, "title": "实现用户登录页面", "task_type": "frontend" },
      { "id": 102, "title": "实现用户注册页面", "task_type": "frontend" },
      { "id": 103, "title": "实现用户认证 API", "task_type": "backend" }
    ],
    "errors": [],
    "suggestions": [
      {
        "task_id": 101,
        "field": "assignee_id",
        "message": "任务「实现用户登录页面」未分配负责人，建议指定"
      }
    ]
  }
}
```

### 4.2 Task 模型新增字段

```python
class Task(Base):
    # ... 现有字段 ...

    task_type: Mapped[str | None] = mapped_column(String(20), default=None)
    # frontend / backend / database / testing / devops

    source_section: Mapped[str | None] = mapped_column(String(50), default=None)
    # page_structure:login-page / api_design:post-login / table_design:users

    spec_reference: Mapped[dict | None] = mapped_column(JSONB, default=None)
    # 规范中对应的详细引用，Agent 编码时参考
```

`spec_reference` 结构示例：

```json
{
  "page_code": "login-page",
  "page_name": "用户登录页面",
  "route": "/login",
  "elements": [
    { "code": "inp-email", "type": "input", "role": "textbox", "accessible_name": "邮箱" },
    { "code": "inp-password", "type": "input", "role": "textbox", "accessible_name": "密码" },
    { "code": "btn-login", "type": "button", "role": "button", "accessible_name": "登录" }
  ],
  "interactions": [
    { "trigger": "btn-login click", "behavior": "提交登录表单" }
  ],
  "related_apis": [
    { "method": "POST", "path": "/api/v1/auth/login" }
  ]
}
```

### 4.3 生成逻辑

`generate_tasks` service 函数：

1. 获取需求的最新 SpecDocument content
2. 获取 strategy（默认 hybrid）
3. 按 strategy 拆分：
   - `page_structure.pages[]` → 每个 page 一个 frontend 任务
   - `api_design.endpoints[]` → 按 path 前缀分组，每组一个 backend 任务
   - `table_design.tables[]` → 如果有新表，一个 database 任务
4. 为每个任务生成：
   - `title`：从 page name / API path / table name 派生
   - `description`：结构化摘要（涉及哪些元素、API、表字段）
   - `task_type`：frontend / backend / database
   - `source_section`：来源标识
   - `spec_reference`：对应的规范详细内容
5. 批量创建 Task
6. 校验 + 返回 suggestions

### 4.4 任务校验规则

| 校验项 | 类型 | 条件 |
|--------|------|------|
| `title` 非空 | error | 始终 |
| `requirement_id` 存在且 approved | error | 始终 |
| `task_type` 合法值 | error | 如填写了 task_type |
| `description` 包含内容 | suggestion | 如为空或过短 |
| `assignee_id` 非空 | suggestion | 未分配负责人 |
| `spec_reference` 关联元素在规范中存在 | suggestion | 引用的 page_code 在规范中找不到 |

## 五、测试用例自动生成

### 5.1 新增 API

```
POST /api/v1/requirements/{id}/generate-test-cases
```

请求体（可选）：

```json
{
  "case_types": ["e2e", "api"],
  "page_filter": ["login-page", "register-page"]
}
```

`case_types` 指定生成哪些类型的测试用例，默认 `["e2e", "api"]`。

响应：

```json
{
  "code": 0,
  "data": {
    "created": [
      {
        "id": 201,
        "case_number": "TC-5-001",
        "title": "验证登录页面点击「登录」按钮提交表单",
        "case_type": "e2e"
      }
    ],
    "errors": [],
    "suggestions": [
      {
        "case_id": 201,
        "field": "related_api",
        "message": "测试用例涉及登录操作，建议关联 API: POST /api/v1/auth/login"
      }
    ]
  }
}
```

### 5.2 生成逻辑

`generate_test_cases` service 函数：

1. 获取需求的最新 SpecDocument content
2. 获取该需求已有的 test cases（避免重复生成）
3. 按 `case_types` 生成：

**E2E 用例**（从 page_structure 生成）：

遍历每个 page 的 interactions 和 elements：
- 每个有 `interaction` 的 element → 一个 E2E 测试用例
- `steps` 使用 `accessible_name` 生成语义化步骤
- `expected_result` 从 interaction 的 behavior 推导
- `related_element` = element 的 code

生成模板：
```
title: "验证{page_name}中「{accessible_name}」的{interaction_summary}"
steps: |
  1. 导航到{route}页面
  2. {操作描述，使用accessible_name}
  3. 验证{预期结果}
expected_result: "{从interaction推导}"
related_element: "{element.code}"
related_api: "{关联的API path}"
```

**API 用例**（从 api_design 生成）：

遍历每个 endpoint：
- 每个 endpoint → 一个 API 测试用例
- `steps` = 发送请求的描述
- `expected_result` = 正常响应码 + data 结构
- `related_api` = method + path

4. 批量创建 TestCase
5. 校验 + 返回 suggestions

### 5.3 测试用例校验规则

| 校验项 | 类型 | 条件 |
|--------|------|------|
| `title` 非空 | error | 始终 |
| `steps` 非空 | error | 始终 |
| `expected_result` 非空 | error | 始终 |
| `related_element` 在规范的 page_structure 中存在 | suggestion | 如填写了 related_element |
| `related_api` 在规范的 api_design 中存在 | suggestion | 如填写了 related_api |
| 每个页面的 interaction 都有对应测试用例 | suggestion | 覆盖率检查 |
| 每个 API endpoint 都有对应测试用例 | suggestion | 覆盖率检查 |

### 5.4 覆盖率 suggestion

生成后统计覆盖率：

```json
{
  "suggestions": [
    {
      "type": "coverage",
      "message": "规范中定义了 12 个交互行为，当前生成了 10 个 E2E 测试用例，覆盖 83%。以下交互未覆盖：[btn-delete click, btn-export click]"
    },
    {
      "type": "coverage",
      "message": "规范中定义了 5 个 API 端点，当前生成了 4 个 API 测试用例，覆盖 80%。以下 API 未覆盖：[DELETE /api/v1/users/:id]"
    }
  ]
}
```

## 六、数据模型改动汇总

### Task 模型新增字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `task_type` | String(20), nullable | frontend / backend / database / testing / devops |
| `source_section` | String(50), nullable | 规范来源标识 |
| `spec_reference` | JSONB, nullable | 规范详细引用 |

需要 Alembic 迁移。

### SpecDocument 无结构变化

version 和 content 的 JSON 结构不变。校验逻辑改变，存储不变。

### TestCase 无结构变化

`related_element` 仍为 String，存 element code。
`related_api` 仍为 String，存 method + path。

### Requirement 无变化

需求模型和 API 不变。

## 七、API 改动汇总

| API | 改动 | 说明 |
|-----|------|------|
| `GET /teams/{id}/requirement-guide` | **新增** | 需求创建引导（字段结构 + 类型说明） |
| `POST /requirements` (create_requirement) | 返回值增加 suggestions | 创建成功时附带建议 |
| `GET /teams/{id}/spec-template/agent-guide` | 增加 `?requirement_id=` 参数 | 注入需求上下文 |
| `PUT /requirements/{id}/spec` (save_spec_document) | 返回值增加 suggestions | 保存成功时附带建议 |
| `POST /requirements/{id}/generate-tasks` | **新增** | 从规范自动生成任务 |
| `POST /requirements/{id}/generate-test-cases` | **新增** | 从规范自动生成测试用例 |
| `POST /requirements/{id}/tasks` (create_task) | 接受新字段 | task_type / source_section / spec_reference |
| `POST /requirements/{id}/test-cases` (create_test_case) | 校验增加 suggestions | 返回建议 |

## 八、完整数据流

```
人类 ↔ Agent 对话
    │ 人类描述需求意图，Agent 分析并创建结构化需求
    │
    ▼
Agent 调用 GET .../requirement-guide
    │ 获取: 需求字段结构 + 类型说明 + suggestions
    │
    ▼
Agent 创建需求 POST .../requirements
    │ title / description / req_type / type_detail / prototype_html
    │ 返回: errors + suggestions
    │ Agent 根据 suggestions 决定是否补充
    │
    ▼
Agent 调用 GET .../agent-guide?requirement_id=X
    │ 获取: 需求信息 + spec template (含 agent_prompt)
    │
    ▼
Agent 提交规范 PUT .../spec
    │ content: { entity_definition, page_structure, api_design, ... }
    │ 返回: errors + suggestions
    │ Agent 根据 suggestions 决定是否补充
    │
    ▼
Agent 调用 POST .../generate-tasks
    │ 从规范自动拆分任务 (按页面/API/表)
    │ 每个 Task 带 spec_reference
    │ 返回: created tasks + suggestions
    │
    ▼
Agent 调用 POST .../generate-test-cases
    │ 从规范的页面结构 + API 设计自动生成
    │ steps 使用 accessible_name
    │ 返回: created cases + coverage suggestions
    │
    ▼
人工审核
```
