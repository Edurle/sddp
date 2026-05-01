# 后端测试用例 — Agent 驱动改造

> 覆盖 API Key 认证、Agent 工作发现、Task Git 关联、批量测试提交、规范模板 Agent 指南

---

## 1. API Key 认证

### 1.1 创建 API Key

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-AGENT-001 | 管理员创建 API Key | 管理员登录 | `{user_id, name, expires_at}` | 0 | 返回明文 key，key_prefix 为 key 前 8 字符 |
| TC-AGENT-002 | 创建无过期时间的 Key | 管理员登录 | `{user_id, name}` (无 expires_at) | 0 | expires_at 为 null |
| TC-AGENT-003 | 非管理员无法创建 | 普通用户登录 | `{user_id, name}` | 40300 | 无权限 |
| TC-AGENT-004 | 用户不存在 | 管理员登录 | `{user_id: 99999, name}` | 40400 | 用户不存在 |
| TC-AGENT-005 | 名称为空 | 管理员登录 | `{user_id, name: ""}` | 40001 | 参数校验失败 |

### 1.2 使用 API Key 认证

| 用例编号 | 描述 | 前置条件 | 请求头 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|--------|---------------|-------------------|
| TC-AGENT-006 | 有效 Key 访问受保护端点 | 已创建 API Key | `X-API-Key: sdd_xxx` | 0 | 正常返回数据 |
| TC-AGENT-007 | 无效 Key | 无 | `X-API-Key: invalid` | 40100 | 无效的 API Key |
| TC-AGENT-008 | 已吊销 Key | Key is_active=false | `X-API-Key: sdd_xxx` | 40100 | 无效的 API Key |
| TC-AGENT-009 | 过期 Key | expires_at 已过期 | `X-API-Key: sdd_xxx` | 40100 | API Key 已过期 |
| TC-AGENT-010 | Key 关联用户被禁用 | user.is_active=false | `X-API-Key: sdd_xxx` | 40100 | 关联用户不存在 |
| TC-AGENT-011 | Key 权限实时获取 | 角色变更后 | `X-API-Key: sdd_xxx` | 0 | 使用最新权限，非 JWT 冻结权限 |
| TC-AGENT-012 | 同时传 JWT 和 Key | JWT 和 Key 都传 | 两个头都有 | 0 | API Key 优先 |

### 1.3 列出用户 API Key

| 用例编号 | 描述 | 前置条件 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|---------------|-------------------|
| TC-AGENT-013 | 列出用户的 Key | 管理员登录，已创建 Key | 0 | 返回列表，包含 key_prefix 但不含明文 key |
| TC-AGENT-014 | 非管理员无法列出 | 普通用户登录 | 40300 | 无权限 |

### 1.4 吊销 API Key

| 用例编号 | 描述 | 前置条件 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|---------------|-------------------|
| TC-AGENT-015 | 吊销 Key | 管理员登录 | 0 | is_active 变为 false |
| TC-AGENT-016 | 重复吊销 | Key 已吊销 | 0 | 幂等操作 |
| TC-AGENT-017 | 吊销不存在的 Key | 管理员登录 | 40400 | Key 不存在 |

---

## 2. Agent 工作发现

### 2.1 获取我的待办概览

| 用例编号 | 描述 | 前置条件 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|---------------|-------------------|
| TC-AGENT-018 | 返回完整待办 | 用户属于团队、有分配任务和待评审 | 0 | 包含 teams/projects/active_iterations/assigned_tasks/pending_reviews |
| TC-AGENT-019 | 无待办 | 新用户无团队 | 0 | 所有数组为空 |
| TC-AGENT-020 | 未登录 | 无 | 40100 | 未登录 |

### 2.2 获取我的任务列表

| 用例编号 | 描述 | 前置条件 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|---------------|-------------------|
| TC-AGENT-021 | 返回分配给我的任务 | 有 assignee_id=我的任务 | 0 | 包含 requirement_title |
| TC-AGENT-022 | 按状态过滤 | 有多个状态的任务 | 0 | 只返回 coding 状态 |
| TC-AGENT-023 | 无任务 | 未分配任务 | 0 | 空数组 |

### 2.3 获取我的待评审列表

| 用例编号 | 描述 | 前置条件 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|---------------|-------------------|
| TC-AGENT-024 | 返回待评审项 | reviewer_id=我的 pending review | 0 | 包含 requirement_id 和 review_type |
| TC-AGENT-025 | 已处理的评审不返回 | review.status=approved | 0 | 空数组 |

### 2.4 全局查询需求

| 用例编号 | 描述 | 前置条件 | 查询参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-AGENT-026 | 按状态过滤 | 有多个需求 | `status=drafting_spec` | 0 | 只返回 drafting_spec |
| TC-AGENT-027 | 按迭代过滤 | 有多个迭代 | `iteration_id=1` | 0 | 只返回该迭代的需求 |
| TC-AGENT-028 | 无过滤 | 有需求 | 无 | 0 | 返回所有未删除需求 |

### 2.5 获取需求完整上下文

| 用例编号 | 描述 | 前置条件 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|---------------|-------------------|
| TC-AGENT-029 | 需求有完整数据 | 需求有规格+测试用例+任务 | 0 | 包含 requirement/spec/test_cases/tasks |
| TC-AGENT-030 | 需求无规格 | 需求无规格文档 | 0 | spec.current_version=0, spec.content=null |
| TC-AGENT-031 | 需求不存在 | 无 | 40400 | 需求不存在 |

---

## 3. Task Git 关联

### 3.1 开始编码

| 用例编号 | 描述 | 前置条件 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|---------------|-------------------|
| TC-AGENT-032 | pending → coding | task.status=pending | 0 | status=coding |
| TC-AGENT-033 | 非 pending 状态 | task.status=coding | 40204 | 只有 pending 才能开始编码 |
| TC-AGENT-034 | 任务不存在 | 无 | 40400 | 任务不存在 |

### 3.2 更新 Git 信息

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-AGENT-035 | 更新所有 git 字段 | 任务存在 | `{git_branch, commit_sha, pr_url, artifact_url}` | 0 | 返回更新后的值 |
| TC-AGENT-036 | 部分更新 | 已有 git_branch | `{commit_sha}` | 0 | git_branch 不变，commit_sha 更新 |
| TC-AGENT-037 | 任务不存在 | 无 | `{git_branch}` | 40400 | 任务不存在 |

### 3.3 任务详情包含 git 字段

| 用例编号 | 描述 | 前置条件 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|---------------|-------------------|
| TC-AGENT-038 | 有 git 信息 | 已更新 git 字段 | 0 | 包含 git_branch/commit_sha/pr_url/artifact_url |
| TC-AGENT-039 | 无 git 信息 | 未更新 | 0 | git 字段均为 null |

---

## 4. 批量测试结果提交

### 4.1 批量更新执行记录

| 用例编号 | 描述 | 前置条件 | 请求参数 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|----------|---------------|-------------------|
| TC-AGENT-040 | 批量提交通过 | 有 round 和 records | `{records: [{test_case_id, status, duration_ms}]}` | 0 | updated=记录数 |
| TC-AGENT-041 | 混合通过和失败 | 有 round 和 records | `{records: [{passed}, {failed, failure_reason, log_output}]}` | 0 | 所有记录更新 |
| TC-AGENT-042 | round 不存在 | 无 | `{records: [...]}` | 40400 | 执行轮次不存在 |
| TC-AGENT-043 | 空 records | 有 round | `{records: []}` | 0 | updated=0 |

### 4.2 执行记录包含新字段

| 用例编号 | 描述 | 前置条件 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|---------------|-------------------|
| TC-AGENT-044 | 记录包含 log_output 和 duration_ms | 已批量提交含这些字段 | 0 | 返回 log_output 和 duration_ms |
| TC-AGENT-045 | 单条更新也支持新字段 | 有 record | `{status, log_output, duration_ms}` | 0 | 单条 PUT 也更新新字段 |

---

## 5. 规范模板 Agent 指南

### 5.1 获取 Agent 指南

| 用例编号 | 描述 | 前置条件 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|---------------|-------------------|
| TC-AGENT-046 | 返回默认模板指南 | 团队未自定义模板 | 0 | 包含所有 section，每个 field 有 agent_prompt |
| TC-AGENT-047 | 返回自定义模板指南 | 团队已自定义模板 | 0 | 返回自定义内容的 agent_prompt |
| TC-AGENT-048 | 非团队成员 | 无 | 40300 | 无权限 |

---

## 6. MongoDB 持久化

### 6.1 规范模板持久化

| 用例编号 | 描述 | 前置条件 | 操作 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|------|---------------|-------------------|
| TC-AGENT-049 | 保存后能读回 | 无 | PUT 更新模板，GET 读回 | 0 | 内容一致 |
| TC-AGENT-050 | 自定义模板包含 agent_prompt | 无 | PUT 含 agent_prompt 的模板，GET 读回 | 0 | agent_prompt 保留 |

### 6.2 规范文档持久化

| 用例编号 | 描述 | 前置条件 | 操作 | 预期响应 code | 预期响应 data/说明 |
|----------|------|----------|------|---------------|-------------------|
| TC-AGENT-051 | 保存后能读回 | status=drafting_spec | PUT 保存，GET 读回 | 0 | 内容一致，版本递增 |
| TC-AGENT-052 | 版本历史保留 | 已保存多版 | GET versions | 0 | 所有版本都在 |

---

**总计 52 条测试用例**，覆盖 API Key 认证(17)、Agent 工作发现(14)、Task Git 关联(8)、批量测试提交(6)、Agent 指南(3)、MongoDB 持久化(4)。
