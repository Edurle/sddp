# 后端接口测试用例 — 需求、规范

## 1. 需求管理

需求状态流转: `drafting_req` → `reviewing_req` → `drafting_spec` → `reviewing_spec` → `drafting_tests` → `reviewing_tests` → `approved`

### 获取需求列表

**接口**: `GET /api/v1/iterations/{iterationId}/requirements`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-REQ-001 | 获取成功 | 迭代下有需求 | 无 | 0 | 返回需求列表 |
| TC-REQ-002 | 按状态筛选 | 同上 | `?status=drafting_req` | 0 | 仅返回该状态需求 |
| TC-REQ-003 | 按类型筛选 | 同上 | `?req_type=bug` | 0 | 仅返回缺陷类型 |
| TC-REQ-004 | 按优先级降序 | 同上 | `?sort_by=priority&sort_order=desc` | 0 | 优先级高的在前 |
| TC-REQ-005 | 已软删除不显示 | 有已删除需求 | 无 | 0 | 列表不含已删除 |
| TC-REQ-006 | 非团队成员 | 非成员 | 无 | 40300 | 无权限 |

### 创建需求

**接口**: `POST /api/v1/iterations/{iterationId}/requirements`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-REQ-007 | 创建功能需求成功 | 有 `requirement:create` 权限 | `{ "title": "用户管理", "req_type": "feature", "priority": 10, "description": "实现用户CRUD", "type_detail": { "feature_description": "包含注册登录等功能" } }` | 0 | `{ "id": 1 }` |
| TC-REQ-008 | 创建优化需求 | 同上 | `req_type="optimization"`, `type_detail` 含 `change_description` | 0 | 成功 |
| TC-REQ-009 | 创建缺陷需求 | 同上 | `req_type="bug"`, `type_detail` 含 `bug_steps` + `expected_behavior` + `actual_behavior` + `fix_description` | 0 | 成功 |
| TC-REQ-010 | 标题为空 | 同上 | `{ "title": "" }` | 40001 | 参数校验失败 |
| TC-REQ-011 | 无效需求类型 | 同上 | `req_type="invalid"` | 40001 | 参数校验失败 |
| TC-REQ-012 | 无权限 | 无 `requirement:create` | 同 TC-REQ-007 | 40300 | 无权限 |

### 获取需求详情

**接口**: `GET /api/v1/requirements/{id}`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-REQ-013 | 获取成功含完整信息 | 需求存在 | 路径 `id=1` | 0 | 含 `current_step`, `reviews`, `tasks` |
| TC-REQ-014 | 需求不存在 | 已登录 | 路径 `id=999` | 40400 | 资源不存在 |
| TC-REQ-015 | 已软删除的需求 | 需求已删除 | 路径 `id=1` | 40400 | 资源不存在 |

### 编辑需求

**接口**: `PUT /api/v1/requirements/{id}`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-REQ-016 | `drafting_req` 状态编辑成功 | `status=drafting_req` | 修改 `title` 和 `type_detail` | 0 | 更新成功 |
| TC-REQ-017 | `reviewing_req` 状态不可编辑 | `status=reviewing_req` | 同上 | 40204 | 需求状态不允许 |
| TC-REQ-018 | `approved` 状态不可编辑 | `status=approved` | 同上 | 40204 | 需求状态不允许 |
| TC-REQ-019 | 被驳回退回后可编辑 | 驳回后退回 `drafting_req` | 同上 | 0 | 更新成功 |

### 删除需求

**接口**: `DELETE /api/v1/requirements/{id}`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-REQ-020 | `drafting_req` 状态删除成功（软删除） | `status=drafting_req` | 无 | 0 | 需求已删除 |
| TC-REQ-021 | `reviewing_req` 状态不可删除 | `status=reviewing_req` | 无 | 40204 | 需求状态不允许 |
| TC-REQ-022 | `approved` 状态不可删除 | `status=approved` | 无 | 40204 | 需求状态不允许 |

### 提交审核

**接口**: `POST /api/v1/requirements/{id}/submit-review`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-REQ-023 | 提交需求审核成功 | `status=drafting_req` | `{ "reviewer_id": 2 }` | 0 | `status`→`reviewing_req`，创建 review 记录 |
| TC-REQ-024 | 提交规范审核成功 | `status=drafting_spec` | `{ "reviewer_id": 2 }` | 0 | `status`→`reviewing_spec` |
| TC-REQ-025 | 提交测试用例审核成功 | `status=drafting_tests` | `{ "reviewer_id": 2 }` | 0 | `status`→`reviewing_tests` |
| TC-REQ-026 | reviewing 状态不可重复提交 | `status=reviewing_req` | `{ "reviewer_id": 2 }` | 40204 | 需求状态不允许 |
| TC-REQ-027 | `approved` 状态不可提交 | `status=approved` | `{ "reviewer_id": 2 }` | 40204 | 需求状态不允许 |
| TC-REQ-028 | 审核人不存在 | `drafting_req` | `{ "reviewer_id": 999 }` | 40400 | 审核人不存在 |
| TC-REQ-029 | 非创建者提交 | 非需求创建者 | `{ "reviewer_id": 2 }` | 40300 | 无权限 |

### 审核（通过/驳回）

**接口**: `POST /api/v1/requirements/{id}/review`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-REQ-030 | 通过需求审核 | `status=reviewing_req`，当前用户是指定审核人 | `{ "action": "approve" }` | 0 | `status`→`drafting_spec` |
| TC-REQ-031 | 通过规范审核 | `status=reviewing_spec` | `{ "action": "approve" }` | 0 | `status`→`drafting_tests` |
| TC-REQ-032 | 通过测试用例审核 | `status=reviewing_tests` | `{ "action": "approve" }` | 0 | `status`→`approved` |
| TC-REQ-033 | 驳回需求审核 | `status=reviewing_req` | `{ "action": "reject", "comment": "描述不清晰" }` | 0 | `status`→`drafting_req` |
| TC-REQ-034 | 驳回规范审核 | `status=reviewing_spec` | `{ "action": "reject", "comment": "API设计有误" }` | 0 | `status`→`drafting_spec` |
| TC-REQ-035 | 驳回测试用例审核 | `status=reviewing_tests` | `{ "action": "reject", "comment": "用例不完整" }` | 0 | `status`→`drafting_tests` |
| TC-REQ-036 | 驳回未填理由 | `status=reviewing_req` | `{ "action": "reject", "comment": "" }` | 40302 | 驳回时必须填写理由 |
| TC-REQ-037 | 非指定审核人 | 非 review 记录中的 reviewer | `{ "action": "approve" }` | 40301 | 不是指定的审核人 |
| TC-REQ-038 | 重复审核 | 已审核通过 | `{ "action": "approve" }` | 40303 | 审核已处理 |
| TC-REQ-039 | 审核通过后内容不可修改 | 需求审核已通过 | PUT 修改 `title` | 40204 | 需求状态不允许 |
| TC-REQ-040 | 权限不匹配 | 需求审核中但用户只有 `review_spec` 权限 | `{ "action": "approve" }` | 40300 | 无权限 |

---

## 2. 规范管理

### 获取团队规范模板

**接口**: `GET /api/v1/teams/{teamId}/spec-template`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-SPEC-001 | 获取成功 | 团队成员 | 无 | 0 | 返回含 `sections` 的模板 |
| TC-SPEC-002 | 新团队有默认模板 | 新创建团队 | 无 | 0 | 返回默认模板 |

### 编辑团队规范模板

**接口**: `PUT /api/v1/teams/{teamId}/spec-template`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-SPEC-003 | 编辑成功 | 有 `spec_template:edit` 权限 | `{ "sections": [...] }` | 0 | 模板已更新 |
| TC-SPEC-004 | 无权限 | 无 `spec_template:edit` 权限 | 同上 | 40300 | 无权限 |

### 获取需求规范文档

**接口**: `GET /api/v1/requirements/{reqId}/specification`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-SPEC-005 | 获取成功含当前版本 | 规范已保存 | 无 | 0 | 返回 `current_version` 和 `content` |
| TC-SPEC-006 | 需求未写规范 | 无规范文档 | 无 | 0 | 返回空内容 |

### 编辑规范文档

**接口**: `PUT /api/v1/requirements/{reqId}/specification`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-SPEC-007 | 保存成功版本递增 | `status=drafting_spec` | `{ "content": { "entity_definition": {...}, ... } }` | 0 | `{ "version": 2 }` |
| TC-SPEC-008 | 被驳回后退回可编辑 | 驳回后退回 `drafting_spec` | 同上 | 0 | 版本递增 |
| TC-SPEC-009 | 审核中不可编辑 | `status=reviewing_spec` | 同上 | 40204 | 需求状态不允许 |
| TC-SPEC-010 | 已通过不可编辑 | `status=approved` | 同上 | 40204 | 需求状态不允许 |

### 获取规范版本列表

**接口**: `GET /api/v1/requirements/{reqId}/specification/versions`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-SPEC-011 | 获取成功 | 有多个版本 | 无 | 0 | 返回版本列表含创建者和时间 |
| TC-SPEC-012 | 无版本 | 未保存过规范 | 无 | 0 | 返回空列表 |

### 获取规范历史版本详情

**接口**: `GET /api/v1/requirements/{reqId}/specification/versions/{version}`

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-SPEC-013 | 获取历史版本成功 | 版本存在 | 路径 `version=1` | 0 | 返回该版本 `content` |
| TC-SPEC-014 | 版本不存在 | 版本号超出范围 | 路径 `version=999` | 40400 | 版本不存在 |
