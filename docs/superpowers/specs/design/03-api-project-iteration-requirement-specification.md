# API 设计 — 项目、迭代、需求、规范

> Base URL: `/api/v1`
>
> 统一响应格式:
>
> ```json
> { "code": 0, "message": "success", "data": {} }
> ```

---

## 1. 项目模块

### GET /api/v1/teams/{teamId}/projects

- **权限**: 团队成员
- **查询参数**:
  - `status` (可选) — `active` | `archived`
- **响应 data**:
  ```json
  [
    {
      "id": 1,
      "name": "string",
      "description": "string",
      "start_date": "date",
      "end_date": "date",
      "status": "active|archived",
      "active_iteration": { "id": 1, "name": "string", "status": "string" } | null,
      "created_at": "datetime"
    }
  ]
  ```
  > `end_date` 自动取该项目最新迭代的截止日期。

### POST /api/v1/teams/{teamId}/projects

- **权限**: `project:create`
- **请求**:
  ```json
  {
    "name": "string",
    "description": "string",
    "start_date": "date|null"
  }
  ```
- **响应 data**: `{ "id": 1 }`
- **错误码**:
  | code  | 说明           |
  | ----- | -------------- |
  | 40001 | 参数校验失败   |

### GET /api/v1/projects/{id}

- **权限**: 项目所属团队成员
- **响应 data**:
  ```json
  {
    "id": 1,
    "name": "string",
    "description": "string",
    "start_date": "date",
    "end_date": "date",
    "status": "active|archived",
    "team": { "id": 1, "name": "string" },
    "statistics": {
      "total_requirements": 0,
      "completed_requirements": 0,
      "total_tasks": 0,
      "completed_tasks": 0,
      "test_pass_rate": 0.0
    }
  }
  ```

### PUT /api/v1/projects/{id}

- **权限**: `project:edit`
- **请求**:
  ```json
  {
    "name": "string",
    "description": "string",
    "start_date": "date|null"
  }
  ```

### PUT /api/v1/projects/{id}/archive

- **权限**: `project:archive`
- **说明**: 归档后项目只读。

### DELETE /api/v1/projects/{id}

- **权限**: `project:delete`
- **前置条件**: 仅无活跃迭代时可删除。
- **说明**: 软删除，设置 `is_deleted = TRUE`，`deleted_at = NOW()`。
- **错误码**:
  | code  | 说明                 |
  | ----- | -------------------- |
  | 40203 | 项目下存在活跃迭代   |

---

## 2. 迭代模块

### GET /api/v1/projects/{projectId}/iterations

- **查询参数**:
  - `status` (可选) — `planned` | `in_progress` | `completed`
- **响应 data**:
  ```json
  [
    {
      "id": 1,
      "name": "string",
      "goal": "string",
      "start_date": "date",
      "end_date": "date",
      "status": "planned|in_progress|completed",
      "requirement_count": 0,
      "task_count": 0,
      "created_at": "datetime"
    }
  ]
  ```

### POST /api/v1/projects/{projectId}/iterations

- **权限**: `iteration:create`
- **请求**:
  ```json
  {
    "name": "string",
    "goal": "string",
    "start_date": "date",
    "end_date": "date"
  }
  ```
- **响应 data**: `{ "id": 1 }`

### GET /api/v1/iterations/{id}

- **响应 data**:
  ```json
  {
    "id": 1,
    "name": "string",
    "goal": "string",
    "start_date": "date",
    "end_date": "date",
    "status": "planned|in_progress|completed",
    "project": { "id": 1, "name": "string" },
    "statistics": {
      "total_requirements": 0,
      "approved_requirements": 0,
      "total_tasks": 0,
      "completed_tasks": 0,
      "test_pass_rate": 0.0
    },
    "created_at": "datetime"
  }
  ```

### PUT /api/v1/iterations/{id}

- **权限**: `iteration:edit`
- **请求**:
  ```json
  {
    "name": "string",
    "goal": "string",
    "end_date": "date"
  }
  ```
- **注意**: `start_date` 不可修改。
- **错误码**:
  | code  | 说明               |
  | ----- | ------------------ |
  | 40100 | 开始日期不可修改   |

### POST /api/v1/iterations/{id}/start

- **权限**: `iteration:start`
- **说明**: 将状态从 `planned` → `in_progress`。

### POST /api/v1/iterations/{id}/complete

- **权限**: `iteration:complete`
- **验证**:
  1. 所有需求已拆分任务
  2. 所有任务已完成
  3. 最近一次测试全部通过
- **错误码**:
  | code  | 说明               |
  | ----- | ------------------ |
  | 40200 | 存在未完成的需求   |
  | 40201 | 存在未完成的任务   |
  | 40202 | 存在未通过的测试   |

### GET /api/v1/iterations/{id}/kanban

- **响应 data**:
  ```json
  {
    "columns": [
      {
        "status": "drafting_req|reviewing_req|drafting_spec|reviewing_spec|drafting_tests|reviewing_tests|approved",
        "display_name": "string",
        "requirements": [
          {
            "id": 1,
            "title": "string",
            "req_type": "feature|optimization|bug",
            "priority": 0,
            "created_by": { "id": 1, "nickname": "string" }
          }
        ]
      }
    ]
  }
  ```
- **display_name 映射**:

  | status           | display_name |
  | ---------------- | ------------ |
  | drafting_req     | 编写需求     |
  | reviewing_req    | 需求审核中   |
  | drafting_spec    | 编写规范     |
  | reviewing_spec   | 规范审核中   |
  | drafting_tests   | 编写测试用例 |
  | reviewing_tests  | 测试用例审核中 |
  | approved         | 已通过       |

### GET /api/v1/iterations/{id}/statistics

- **响应 data**:
  ```json
  {
    "requirements": {
      "total": 0,
      "by_status": { "status": 0 }
    },
    "tasks": {
      "total": 0,
      "completed": 0
    },
    "tests": {
      "total_cases": 0,
      "latest_pass_rate": 0.0
    }
  }
  ```

---

## 3. 需求模块

### 状态流转

```
drafting_req → reviewing_req → drafting_spec → reviewing_spec → drafting_tests → reviewing_tests → approved
```

驳回时退回对应的 `drafting_*` 状态：
- `reviewing_req` → `drafting_req`
- `reviewing_spec` → `drafting_spec`
- `reviewing_tests` → `drafting_tests`

---

### GET /api/v1/iterations/{iterationId}/requirements

- **查询参数**:
  - `status` (可选)
  - `req_type` (可选) — `feature` | `optimization` | `bug`
  - `sort_by` (可选) — `priority` | `created_at`
  - `sort_order` (可选) — `asc` | `desc`
- **响应 data**:
  ```json
  [
    {
      "id": 1,
      "title": "string",
      "req_type": "feature|optimization|bug",
      "priority": 0,
      "status": "string",
      "task_count": 0,
      "created_by": { "id": 1, "nickname": "string" },
      "created_at": "datetime"
    }
  ]
  ```

### POST /api/v1/iterations/{iterationId}/requirements

- **权限**: `requirement:create`
- **请求**:
  ```json
  {
    "title": "string",
    "req_type": "feature|optimization|bug",
    "priority": 0,
    "description": "string",
    "type_detail": {},
    "prototype_html": "string"
  }
  ```
  `type_detail` 按类型不同：
  - **feature**: `{ "feature_description": "string" }`
  - **optimization**: `{ "change_description": "string" }`
  - **bug**: `{ "bug_steps": "string", "expected_behavior": "string", "actual_behavior": "string", "fix_description": "string" }`
  
  `prototype_html` 为可选字段，存放页面原型图 HTML 代码，前端以 `<iframe sandbox>` 渲染。
- **响应 data**: `{ "id": 1 }`

### GET /api/v1/requirements/{id}

- **响应 data**:
  ```json
  {
    "id": 1,
    "title": "string",
    "req_type": "feature|optimization|bug",
    "priority": 0,
    "status": "string",
    "description": "string",
    "type_detail": {},
    "iteration": { "id": 1, "name": "string" },
    "created_by": { "id": 1, "nickname": "string" },
    "current_step": "drafting_req|reviewing_req|drafting_spec|reviewing_spec|drafting_tests|reviewing_tests|approved",
    "reviews": [
      {
        "id": 1,
        "review_type": "requirement|specification|test_case",
        "reviewer": { "id": 1, "nickname": "string" },
        "status": "pending|approved|rejected",
        "comment": "string|null",
        "created_at": "datetime",
        "reviewed_at": "datetime|null"
      }
    ],
    "tasks": [
      {
        "id": 1,
        "title": "string",
        "assignee": { "id": 1, "nickname": "string" } | null,
        "status": "coding|testing|completed"
      }
    ],
    "created_at": "datetime",
    "updated_at": "datetime"
  }
  ```

### PUT /api/v1/requirements/{id}

- **权限**: `requirement:edit`
- **前置条件**: 仅 `drafting_req` 状态可编辑。
- **请求**: 同创建。
- **错误码**:
  | code  | 说明                   |
  | ----- | ---------------------- |
  | 40204 | 需求状态不允许此操作   |

### DELETE /api/v1/requirements/{id}

- **权限**: `requirement:delete`
- **前置条件**: 仅 `drafting_req` 状态可删除。
- **说明**: 软删除，设置 `is_deleted = TRUE`，`deleted_at = NOW()`。
- **错误码**:
  | code  | 说明                   |
  | ----- | ---------------------- |
  | 40204 | 需求状态不允许此操作   |

### POST /api/v1/requirements/{id}/submit-review

- **权限**: `requirement:edit`（创建者）
- **请求**:
  ```json
  { "reviewer_id": 1 }
  ```
- **业务规则**:
  - `status` 必须为 `drafting_req` / `drafting_spec` / `drafting_tests` 之一。
  - 提交后变为对应的 `reviewing_*` 状态。
  - 同时创建一条 `requirement_review` 记录（`status=pending`）。
- **错误码**:
  | code  | 说明                   |
  | ----- | ---------------------- |
  | 40204 | 需求状态不允许此操作   |

### POST /api/v1/requirements/{id}/review

- **权限**: 根据当前 `review_type` 对应不同权限：
  - `requirement` → `requirement:review_req`
  - `specification` → `requirement:review_spec`
  - `test_case` → `requirement:review_tests`
- **请求**:
  ```json
  { "action": "approve|reject", "comment": "string" }
  ```
- **规则**:
  - `reject` 时 `comment` 必填。
  - **approve 状态流转**:
    - `reviewing_req` → `drafting_spec`
    - `reviewing_spec` → `drafting_tests`
    - `reviewing_tests` → `approved`
  - **reject 状态流转**:
    - `reviewing_req` → `drafting_req`
    - `reviewing_spec` → `drafting_spec`
    - `reviewing_tests` → `drafting_tests`
- **错误码**:
  | code  | 说明                       |
  | ----- | -------------------------- |
  | 40301 | 不是指定的审核人           |
  | 40302 | 驳回时必须填写理由         |
  | 40303 | 审核已处理不可重复操作     |

---

## 4. 规范模块

### GET /api/v1/teams/{teamId}/spec-template

- **说明**: 获取团队级规范模板。
- **响应 data**:
  ```json
  {
    "team_id": 1,
    "sections": [
      {
        "name": "string",
        "display_name": "string",
        "required": true,
        "fields": [
          {
            "name": "string",
            "display_name": "string",
            "type": "string",
            "required": true,
            "description": "string"
          }
        ]
      }
    ],
    "updated_at": "datetime"
  }
  ```

### PUT /api/v1/teams/{teamId}/spec-template

- **权限**: `spec_template:edit`
- **请求**:
  ```json
  { "sections": [] }
  ```

### GET /api/v1/requirements/{reqId}/specification

- **响应 data**:
  ```json
  {
    "requirement_id": 1,
    "current_version": 1,
    "content": {
      "entity_definition": {},
      "table_design": {},
      "page_structure": {},
      "api_design": {},
      "constraints": {}
    },
    "updated_at": "datetime"
  }
  ```

### PUT /api/v1/requirements/{reqId}/specification

- **前置条件**: 仅 `drafting_spec` 状态或被驳回退回后可编辑。
- **校验规则**: 保存时根据团队模板中定义的 JSON Schema 校验内容，校验失败返回 40001 及详细错误列表。
- **请求**:
  ```json
  {
    "content": {
      "entity_definition": {},
      "table_design": {},
      "page_structure": {
        "pages": [...]
      },
      "api_design": {},
      "constraints": {}
    }
  }
```
- **说明**: 每次保存自动递增版本号。
- **响应 data**: `{ "version": 1 }`
- **错误码**:
  | code  | 说明                                                   |
  | ----- | ------------------------------------------------------ |
  | 40001 | 规范内容校验失败，data 中返回详细错误列表              |
  | 40204 | 需求状态不允许此操作                                   |

### GET /api/v1/requirements/{reqId}/specification/versions

- **响应 data**:
  ```json
  [
    {
      "version": 1,
      "created_by": { "id": 1, "nickname": "string" },
      "created_at": "datetime"
    }
  ]
  ```

### GET /api/v1/requirements/{reqId}/specification/versions/{version}

- **响应 data**:
  ```json
  {
    "version": 1,
    "content": {},
    "created_by": { "id": 1, "nickname": "string" },
    "created_at": "datetime"
  }
  ```

---

## 5. Agent 工作发现

> Agent 通过这些端点发现自己的团队、项目、待办任务和待评审项。

### 5.1 获取我的待办概览

`GET /api/v1/users/me/pending`

**响应 data**

```json
{
  "teams": [
    {"id": 1, "name": "产品研发组", "role": "owner"}
  ],
  "projects": [
    {"id": 1, "name": "后台管理系统 v2.0", "team_id": 1, "status": "active"}
  ],
  "active_iterations": [
    {"id": 1, "name": "Sprint 1", "project_id": 1, "status": "in_progress"}
  ],
  "assigned_tasks": [
    {"id": 1, "title": "实现用户 API 接口", "status": "coding", "requirement_id": 1, "requirement_title": "用户CRUD功能"}
  ],
  "pending_reviews": [
    {"requirement_id": 2, "title": "登录功能", "review_type": "requirement", "review_id": 5, "created_at": "2026-05-01T10:00:00Z"}
  ]
}
```

### 5.2 获取我的任务列表

`GET /api/v1/users/me/tasks`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 按状态过滤：pending / coding / testing / completed |

**响应 data**

```json
[
  {
    "id": 1,
    "title": "实现用户 API 接口",
    "status": "coding",
    "requirement_id": 1,
    "requirement_title": "用户CRUD功能",
    "assignee_id": 2,
    "git_branch": "feature/user-api",
    "created_at": "2026-05-01T10:00:00Z",
    "updated_at": "2026-05-01T12:00:00Z"
  }
]
```

### 5.3 获取我的待评审列表

`GET /api/v1/users/me/pending-reviews`

**响应 data**

```json
[
  {
    "review_id": 5,
    "requirement_id": 2,
    "requirement_title": "登录功能",
    "review_type": "requirement",
    "status": "pending",
    "created_at": "2026-05-01T10:00:00Z"
  }
]
```

### 5.4 全局查询需求

`GET /api/v1/requirements`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 按状态过滤 |
| iteration_id | number | 否 | 按迭代过滤 |
| created_by | number | 否 | 按创建人过滤 |

**响应 data**

```json
[
  {
    "id": 1,
    "title": "用户CRUD功能",
    "req_type": "feature",
    "priority": 1,
    "status": "drafting_spec",
    "iteration_id": 1,
    "created_by": 1,
    "created_at": "2026-05-01T10:00:00Z"
  }
]
```

### 5.5 获取需求完整上下文

`GET /api/v1/requirements/{id}/full-context`

一次调用返回需求 + 规格文档 + 测试用例 + 任务列表，Agent 获取完整开发上下文。

**响应 data**

```json
{
  "requirement": {
    "id": 1,
    "title": "用户CRUD功能",
    "req_type": "feature",
    "status": "drafting_spec",
    "description": "...",
    "created_by": 1
  },
  "spec": {
    "current_version": 2,
    "content": {
      "entity_definition": {},
      "table_design": {},
      "page_structure": {},
      "api_design": {},
      "constraints": {}
    }
  },
  "test_cases": [
    {"id": 1, "title": "创建用户 — 正常流程", "case_type": "api"}
  ],
  "tasks": [
    {"id": 1, "title": "实现用户 API", "status": "coding"}
  ]
}
```

### 5.6 获取规范模板 Agent 指南

`GET /api/v1/teams/{teamId}/spec-template/agent-guide`

**行为**：返回规范模板的结构化 Agent 指南，包含每个章节和字段的 `agent_prompt`。Agent 在编写规范前先读取此端点获取指导。

**响应 data**

```json
{
  "team_id": 1,
  "sections": [
    {
      "name": "entity_definition",
      "display_name": "实体定义",
      "required": true,
      "fields": [
        {
          "name": "description",
          "display_name": "实体描述",
          "type": "text",
          "required": true,
          "agent_prompt": "用一段话描述该实体的用途和核心职责"
        },
        {
          "name": "fields",
          "display_name": "字段列表",
          "type": "list",
          "required": true,
          "agent_prompt": "列出实体的所有字段。每个字段需包含 name（字段名，英文小写下划线）、type（数据类型）、constraints（约束数组）"
        }
      ]
    }
  ]
}
```
