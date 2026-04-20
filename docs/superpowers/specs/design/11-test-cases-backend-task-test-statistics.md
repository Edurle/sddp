# 后端接口测试用例 — 任务、测试用例、测试执行、统计

## 1. 任务管理

任务状态: `pending` → `coding` → `testing` → `completed`

### 获取需求下的任务列表

**接口**: `GET /api/v1/requirements/{reqId}/tasks`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TASK-001 | 获取成功 | 需求下有任务 | 无 | 0 | 返回任务列表 |
| TC-TASK-002 | 按状态筛选 | 同上 | `?status=pending` | 0 | 仅返回pending任务 |
| TC-TASK-003 | 按指派人筛选 | 同上 | `?assignee_id=1` | 0 | 仅返回该指派人任务 |
| TC-TASK-004 | 已软删除不显示 | 有已删除任务 | 无 | 0 | 列表不含已删除 |

### 创建任务

**接口**: `POST /api/v1/requirements/{reqId}/tasks`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TASK-005 | 创建成功 | 需求status=approved，有task:create权限 | `{ "title": "实现用户API", "description": "...", "assignee_id": 2 }` | 0 | `{ "id": 1 }`，status=pending |
| TC-TASK-006 | 需求未通过审核 | 需求status!=approved | 同上 | 40204 | 需求状态不允许 |
| TC-TASK-007 | 标题为空 | 需求已通过 | `{ "title": "" }` | 40001 | 参数校验失败 |
| TC-TASK-008 | 无权限 | 无task:create权限 | 同TC-TASK-005 | 40300 | 无权限 |

### 获取任务详情

**接口**: `GET /api/v1/tasks/{id}`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TASK-009 | 获取成功含规范和测试用例 | 任务存在 | 路径 id=1 | 0 | 含requirement.specification和test_cases |
| TC-TASK-010 | 含最近一轮测试执行摘要 | 有执行记录 | 路径 id=1 | 0 | latest_execution含total/passed/failed/skipped |
| TC-TASK-011 | 无执行记录时latest_execution为null | 无执行记录 | 路径 id=1 | 0 | latest_execution=null |
| TC-TASK-012 | 任务不存在 | 已登录 | 路径 id=999 | 40400 | 资源不存在 |

### 编辑任务

**接口**: `PUT /api/v1/tasks/{id}`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TASK-013 | pending状态编辑成功 | status=pending | 修改title | 0 | 更新成功 |
| TC-TASK-014 | coding状态编辑成功 | status=coding | 修改description | 0 | 更新成功 |
| TC-TASK-015 | testing状态不可编辑 | status=testing | 同上 | 40204 | 任务状态不允许 |
| TC-TASK-016 | completed状态不可编辑 | status=completed | 同上 | 40204 | 任务状态不允许 |

### 删除任务

**接口**: `DELETE /api/v1/tasks/{id}`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TASK-017 | pending状态删除成功（软删除） | status=pending | 无 | 0 | 任务已删除 |
| TC-TASK-018 | coding状态删除成功 | status=coding | 无 | 0 | 任务已删除 |
| TC-TASK-019 | testing状态不可删除 | status=testing | 无 | 40204 | 任务状态不允许 |
| TC-TASK-020 | completed状态不可删除 | status=completed | 无 | 40204 | 任务状态不允许 |

### 开始测试

**接口**: `POST /api/v1/tasks/{id}/start-testing`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TASK-021 | coding→testing成功 | status=coding | 无 | 0 | 返回round_id和records列表 |
| TC-TASK-022 | 自动创建执行轮次和待填写记录 | 同上 | 无 | 0 | records数量=需求的测试用例数 |
| TC-TASK-023 | pending状态不可开始测试 | status=pending | 无 | 40204 | 任务状态不允许 |
| TC-TASK-024 | testing状态不可重复 | status=testing | 无 | 40204 | 任务状态不允许 |

### 完成任务

**接口**: `POST /api/v1/tasks/{id}/complete`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TASK-025 | 完成成功 | status=testing，最近一轮全部passed | 无 | 0 | 任务已完成 |
| TC-TASK-026 | 有未通过的用例 | 同上但有failed | 无 | 40401 | 存在未通过的测试用例 |
| TC-TASK-027 | 无执行记录 | status=testing但无记录 | 无 | 40402 | 没有测试执行记录 |
| TC-TASK-028 | coding状态不可完成 | status=coding | 无 | 40204 | 任务状态不允许 |

---

## 2. 测试用例管理

### 获取测试用例列表

**接口**: `GET /api/v1/requirements/{reqId}/test-cases`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TC-001 | 获取成功 | 需求下有用例 | 无 | 0 | 返回用例列表含case_number |
| TC-TC-002 | 按类型筛选 | 同上 | `?case_type=api` | 0 | 仅返回接口测试用例 |
| TC-TC-003 | 已软删除不显示 | 有已删除用例 | 无 | 0 | 列表不含已删除 |

### 创建测试用例

**接口**: `POST /api/v1/requirements/{reqId}/test-cases`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TC-004 | 创建成功 | status=drafting_tests | `{ "title": "登录成功", "case_type": "api", "precondition": "用户已注册", "steps": "发送登录请求", "expected_result": "返回token", "related_api": "/api/v1/auth/login" }` | 0 | `{ "id": 1, "case_number": "TC-1-001" }` |
| TC-TC-005 | case_number自动生成 | 同上 | 同上 | 0 | 格式为TC-{req_id}-{序号3位补零} |
| TC-TC-006 | 创建e2e用例含related_element | 同上 | case_type="e2e", related_element="login-btn-submit" | 0 | 成功 |
| TC-TC-007 | 审核中不可创建 | status=reviewing_tests | 同TC-TC-004 | 40204 | 需求状态不允许 |
| TC-TC-008 | 审核通过后不可创建 | status=approved | 同TC-TC-004 | 40204 | 需求状态不允许 |
| TC-TC-009 | 标题为空 | status=drafting_tests | `{ "title": "" }` | 40001 | 参数校验失败 |
| TC-TC-010 | steps为空 | status=drafting_tests | `{ "steps": "" }` | 40001 | 参数校验失败 |

### 编辑测试用例

**接口**: `PUT /api/v1/test-cases/{id}`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TC-011 | 编辑成功 | 需求status=drafting_tests | 修改title和steps | 0 | 更新成功 |
| TC-TC-012 | 审核中不可编辑 | 需求status=reviewing_tests | 同上 | 40204 | 需求状态不允许 |

### 删除测试用例

**接口**: `DELETE /api/v1/test-cases/{id}`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TC-013 | 删除成功（软删除） | 需求status=drafting_tests | 无 | 0 | 测试用例已删除 |
| TC-TC-014 | 审核通过后不可删除 | 需求status=approved | 无 | 40204 | 需求状态不允许 |

---

## 3. 测试执行

### 获取任务执行轮次列表

**接口**: `GET /api/v1/tasks/{taskId}/test-executions`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TE-001 | 获取成功 | 有多轮执行 | 无 | 0 | 返回轮次列表含统计 |
| TC-TE-002 | 无执行记录 | 无 | 无 | 0 | 返回空列表 |

### 获取执行记录详情

**接口**: `GET /api/v1/test-executions/{roundId}/records`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TE-003 | 获取成功 | 轮次存在 | 无 | 0 | 返回记录列表含测试用例信息 |
| TC-TE-004 | 含pending状态记录 | 刚创建的轮次 | 无 | 0 | 未填写的记录status=pending |

### 更新执行记录

**接口**: `PUT /api/v1/test-execution-records/{id}`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-TE-005 | 标记通过 | 有task:test权限 | `{ "status": "passed", "actual_result": "返回200和token" }` | 0 | 记录已更新 |
| TC-TE-006 | 标记失败含原因 | 同上 | `{ "status": "failed", "actual_result": "返回500", "failure_reason": "数据库连接失败" }` | 0 | 记录已更新 |
| TC-TE-007 | 失败未填原因 | 同上 | `{ "status": "failed", "failure_reason": "" }` | 40403 | 失败原因必填 |
| TC-TE-008 | 标记跳过 | 同上 | `{ "status": "skipped", "actual_result": "依赖接口不可用" }` | 0 | 记录已更新 |
| TC-TE-009 | 无权限 | 无task:test权限 | 同TC-TE-005 | 40300 | 无权限 |

---

## 4. 测试统计

### 需求维度统计

**接口**: `GET /api/v1/requirements/{reqId}/test-statistics`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-STAT-001 | 获取成功 | 有用例和执行记录 | 无 | 0 | total_cases, latest_results含passed/failed/skipped/not_executed, pass_rate |
| TC-STAT-002 | 无执行记录 | 有用例无执行 | 无 | 0 | latest_results全为not_executed, pass_rate=0 |

### 迭代维度统计

**接口**: `GET /api/v1/iterations/{id}/test-statistics`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-STAT-003 | 获取成功含by_requirement | 迭代有需求数据 | 无 | 0 | 含total_cases, latest_pass_rate, by_requirement明细 |
| TC-STAT-004 | 空迭代 | 无需求 | 无 | 0 | total_cases=0 |

### 项目维度统计

**接口**: `GET /api/v1/projects/{id}/test-statistics`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-STAT-005 | 获取成功含迭代趋势 | 项目有多个迭代 | 无 | 0 | iterations数组含每迭代的pass_rate |
| TC-STAT-006 | 无迭代 | 新项目 | 无 | 0 | iterations为空数组 |
