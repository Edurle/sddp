# API 设计 — 任务、测试、统计

> 规范驱动开发平台 API 设计文档第 4 部分
>
> 涵盖任务管理、测试用例管理、测试执行、测试统计模块

Base URL: `/api/v1`

统一响应格式:

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

---

## 1. 任务模块

任务只能从已通过（approved）状态的需求创建。任务状态流转：`pending` → `coding` → `testing` → `completed`。测试失败退回 `coding`。

### 1.1 获取需求下的任务列表

`GET /api/v1/requirements/{reqId}/tasks`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 否 | 按状态过滤：pending / coding / testing / completed |
| assignee_id | number | 否 | 按负责人过滤 |

**响应 data**

```json
[
  {
    "id": 1,
    "title": "string",
    "assignee": { "id": 1, "nickname": "string" } | null,
    "status": "pending|coding|testing|completed",
    "created_at": "datetime"
  }
]
```

---

### 1.2 创建任务

`POST /api/v1/requirements/{reqId}/tasks`

**权限**：`task:create`

**前置条件**：需求 status 必须为 `approved`

**请求体**

```json
{
  "title": "string",
  "description": "string",
  "assignee_id": "number|null"
}
```

**响应 data**

```json
{
  "id": 1
}
```

**错误**

| 错误码 | 说明 |
|--------|------|
| 40204 | 需求状态不允许此操作（需求未通过审核） |

---

### 1.3 获取任务详情

`GET /api/v1/tasks/{id}`

**响应 data**

```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "status": "pending|coding|testing|completed",
  "assignee": { "id": 1, "nickname": "string" } | null,
  "requirement": {
    "id": 1,
    "title": "string",
    "specification": {
      "entity_definition": {},
      "table_design": {},
      "page_structure": {},
      "api_design": {},
      "constraints": {}
    }
  },
  "test_cases": [
    {
      "id": 1,
      "case_number": "TC-1-01",
      "title": "string",
      "case_type": "api|e2e"
    }
  ],
  "latest_execution": {
    "round_id": 1,
    "total": 5,
    "passed": 3,
    "failed": 1,
    "skipped": 1
  } | null,
  "created_by": { "id": 1, "nickname": "string" },
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

---

### 1.4 更新任务

`PUT /api/v1/tasks/{id}`

**权限**：`task:edit`

**前置条件**：仅 `pending` 或 `coding` 状态可编辑

**请求体**

```json
{
  "title": "string",
  "description": "string",
  "assignee_id": "number|null"
}
```

**错误**

| 错误码 | 说明 |
|--------|------|
| 40204 | 任务状态不允许此操作 |

---

### 1.5 删除任务

`DELETE /api/v1/tasks/{id}`

**权限**：`task:delete`

**前置条件**：仅 `pending` 或 `coding` 状态可删除

**说明**：软删除，设置 `is_deleted = TRUE`，`deleted_at = NOW()`

**错误**

| 错误码 | 说明 |
|--------|------|
| 40204 | 任务状态不允许此操作 |

---

### 1.6 开始测试

`POST /api/v1/tasks/{id}/start-testing`

**权限**：`task:test`

**行为**：将任务状态从 `coding` 转为 `testing`，同时自动创建一轮测试执行轮次，为该需求的所有测试用例生成待填写的执行记录。

**响应 data**

```json
{
  "round_id": 1,
  "records": [
    {
      "id": 1,
      "test_case_id": 1,
      "case_number": "TC-1-01",
      "title": "string",
      "status": "pending"
    }
  ]
}
```

---

### 1.7 完成任务

`POST /api/v1/tasks/{id}/complete`

**权限**：`task:complete`

**前置条件**：任务处于 `testing` 状态，且最近一轮测试全部通过

**响应**：任务标记为 `completed`

**错误**

| 错误码 | 说明 |
|--------|------|
| 40401 | 存在未通过的测试用例 |
| 40402 | 没有测试执行记录 |

---

## 2. 测试用例管理

测试用例在需求阶段「编写测试用例」步骤中创建，审核通过后锁定不可修改。

### 2.1 获取需求下的测试用例列表

`GET /api/v1/requirements/{reqId}/test-cases`

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| case_type | string | 否 | 按类型过滤：api / e2e |

**响应 data**

```json
[
  {
    "id": 1,
    "case_number": "TC-1-01",
    "title": "string",
    "case_type": "api|e2e",
    "precondition": "string",
    "steps": "string",
    "expected_result": "string",
    "related_api": "string|null",
    "related_element": "string|null",
    "created_at": "datetime"
  }
]
```

---

### 2.2 创建测试用例

`POST /api/v1/requirements/{reqId}/test-cases`

**权限**：`requirement:edit`

**前置条件**：仅 `drafting_tests` 状态可创建

**请求体**

```json
{
  "title": "string",
  "case_type": "api|e2e",
  "precondition": "string",
  "steps": "string",
  "expected_result": "string",
  "related_api": "string|null",
  "related_element": "string|null"
}
```

> `case_number` 自动生成，格式：`TC-{requirement_id}-{序号(3位补零)}`

**响应 data**

```json
{
  "id": 1,
  "case_number": "TC-1-01"
}
```

**错误**

| 错误码 | 说明 |
|--------|------|
| 40204 | 需求状态不允许此操作 |

---

### 2.3 更新测试用例

`PUT /api/v1/test-cases/{id}`

**权限**：`requirement:edit`

**前置条件**：仅 `drafting_tests` 状态可编辑

**请求体**：同创建

---

### 2.4 删除测试用例

`DELETE /api/v1/test-cases/{id}`

**权限**：`requirement:delete`

**前置条件**：仅 `drafting_tests` 状态可删除

**说明**：软删除，设置 `is_deleted = TRUE`，`deleted_at = NOW()`

---

## 3. 测试执行

### 3.1 获取任务的所有测试执行轮次

`GET /api/v1/tasks/{taskId}/test-executions`

**响应 data**

```json
[
  {
    "round_id": 1,
    "executed_by": { "id": 1, "nickname": "string" },
    "total": 5,
    "passed": 3,
    "failed": 1,
    "skipped": 1,
    "created_at": "datetime"
  }
]
```

---

### 3.2 获取某一轮次的所有执行记录

`GET /api/v1/test-executions/{roundId}/records`

**响应 data**

```json
[
  {
    "id": 1,
    "test_case": {
      "id": 1,
      "case_number": "TC-1-01",
      "title": "string",
      "case_type": "api|e2e",
      "expected_result": "string"
    },
    "status": "passed|failed|skipped|pending",
    "actual_result": "string",
    "failure_reason": "string",
    "executed_at": "datetime"
  }
]
```

---

### 3.3 更新单条执行记录

`PUT /api/v1/test-execution-records/{id}`

**权限**：`task:test`

**请求体**

```json
{
  "status": "passed|failed|skipped",
  "actual_result": "string",
  "failure_reason": "string"
}
```

> `status` 为 `failed` 时，`failure_reason` 必填。

**错误**

| 错误码 | 说明 |
|--------|------|
| 40403 | 失败原因必填 |

---

## 4. 测试统计

### 4.1 需求级测试统计

`GET /api/v1/requirements/{reqId}/test-statistics`

**响应 data**

```json
{
  "total_cases": 10,
  "latest_results": {
    "passed": 8,
    "failed": 1,
    "skipped": 1,
    "not_executed": 0
  },
  "pass_rate": 80.0
}
```

---

### 4.2 迭代级测试统计

`GET /api/v1/iterations/{id}/test-statistics`

**响应 data**

```json
{
  "total_cases": 50,
  "latest_pass_rate": 90.0,
  "by_requirement": [
    {
      "requirement_id": 1,
      "requirement_title": "string",
      "total_cases": 10,
      "latest_passed": 9,
      "latest_failed": 1
    }
  ]
}
```

---

### 4.3 项目级测试统计

`GET /api/v1/projects/{id}/test-statistics`

**响应 data**

```json
{
  "iterations": [
    {
      "iteration_id": 1,
      "iteration_name": "string",
      "total_cases": 50,
      "pass_rate": 90.0
    }
  ]
}
```

---

## 错误码汇总（本文档新增）

| 错误码 | 说明 |
|--------|------|
| 40204 | 需求/任务状态不允许此操作 |
| 40401 | 存在未通过的测试用例 |
| 40402 | 没有测试执行记录 |
| 40403 | 失败原因必填 |
