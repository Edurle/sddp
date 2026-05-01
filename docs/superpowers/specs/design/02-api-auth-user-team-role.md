# API 设计文档 - 认证、用户、团队、角色

> Base URL: `/api/v1`

## 通用约定

### 统一响应格式

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {}
}
```

**分页响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 100,
    "page": 1,
    "page_size": 20,
    "items": []
  }
}
```

**错误响应：**

```json
{
  "code": 40001,
  "message": "参数校验失败",
  "data": null
}
```

### 认证方式

除登录、注册、忘记密码、重置密码、验证邮箱外，所有接口需在请求头携带以下任一：

**方式一：JWT Token**
```
Authorization: Bearer <token>
```

**方式二：API Key（适用于 Agent）**
```
X-API-Key: sdd_xxxxxxxxxxxxxxxxxxxxx
```

> API Key 由管理员创建，支持长期有效，权限与关联用户一致。API Key 认证时每次从数据库获取最新权限（不受 JWT 权限冻结影响）。

### 错误码一览

| 错误码 | 说明 |
|--------|------|
| 0 | 成功 |
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限 |
| 40400 | 资源不存在 |
| 40001 | 参数校验失败 |
| 40002 | 邮箱已注册 |
| 40003 | 邮箱或密码错误 |
| 40004 | 邮箱未验证 |
| 40005 | 邀请不存在/已处理 |
| 40006 | 用户已在团队中 |
| 40007 | 角色名称已存在 |
| 40008 | 不能移出团队所有者 |
| 40009 | 内置角色不可修改 |

---

## 1. 认证模块 (Auth)

### 1.1 POST /api/v1/auth/register - 注册

**权限：** 无需认证

**请求 Body：**

```json
{
  "email": "user@example.com",
  "password": "string (8-64位)",
  "nickname": "string (2-32位)"
}
```

**成功响应：**

```json
{
  "code": 0,
  "message": "注册成功，请查收验证邮件",
  "data": null
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40001 | 参数校验失败（邮箱格式、密码长度、昵称长度等） |
| 40002 | 邮箱已注册 |

---

### 1.2 POST /api/v1/auth/verify-email - 验证邮箱

**权限：** 无需认证

**请求 Body：**

```json
{
  "token": "string (邮件中的验证令牌)"
}
```

**成功响应：**

```json
{
  "code": 0,
  "message": "邮箱验证成功",
  "data": null
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40001 | 参数校验失败（token 为空或无效） |
| 40400 | 验证令牌不存在或已过期 |

---

### 1.3 POST /api/v1/auth/login - 登录

**权限：** 无需认证

**请求 Body：**

```json
{
  "email": "user@example.com",
  "password": "string",
  "remember": false
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| email | string | 是 | 邮箱地址 |
| password | string | 是 | 密码 |
| remember | boolean | 否 | 记住登录状态，true 时 token 有效期 30 天，否则 24 小时 |

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "token": "string (JWT)",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "nickname": "张三",
      "avatar": "https://example.com/avatar.jpg",
      "is_admin": false
    }
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40001 | 参数校验失败 |
| 40003 | 邮箱或密码错误 |
| 40004 | 邮箱未验证 |

---

### 1.4 POST /api/v1/auth/forgot-password - 忘记密码

**权限：** 无需认证

**请求 Body：**

```json
{
  "email": "user@example.com"
}
```

**成功响应：**

```json
{
  "code": 0,
  "message": "重置邮件已发送",
  "data": null
}
```

> 注意：无论邮箱是否存在，均返回相同响应，防止邮箱枚举攻击。

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40001 | 参数校验失败（邮箱格式错误） |

---

### 1.5 POST /api/v1/auth/reset-password - 重置密码

**权限：** 无需认证

**请求 Body：**

```json
{
  "token": "string (邮件中的重置令牌)",
  "new_password": "string (8-64位)"
}
```

**成功响应：**

```json
{
  "code": 0,
  "message": "密码重置成功",
  "data": null
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40001 | 参数校验失败（token 为空、密码长度不足） |
| 40400 | 重置令牌不存在或已过期 |

---

## 2. 用户模块 (User)

### 2.1 GET /api/v1/users/me - 获取当前用户信息

**权限：** 需要登录

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "nickname": "张三",
    "avatar": "https://example.com/avatar.jpg",
    "is_admin": false,
    "teams": [
      {
        "id": 1,
        "name": "前端团队",
        "role_names": ["管理员", "开发者"]
      }
    ]
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |

---

### 2.2 PUT /api/v1/users/me - 修改用户信息

**权限：** 需要登录

**请求 Body：**

```json
{
  "nickname": "李四",
  "avatar": "https://example.com/new-avatar.jpg"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| nickname | string | 否 | 昵称 (2-32位) |
| avatar | string | 否 | 头像 URL |

> 至少提供一个字段。

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "nickname": "李四",
    "avatar": "https://example.com/new-avatar.jpg"
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40001 | 参数校验失败 |

---

### 2.3 PUT /api/v1/users/me/password - 修改密码

**权限：** 需要登录

**请求 Body：**

```json
{
  "old_password": "string",
  "new_password": "string (8-64位)"
}
```

**成功响应：**

```json
{
  "code": 0,
  "message": "密码修改成功",
  "data": null
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40001 | 参数校验失败 |
| 40003 | 原密码错误 |

---

### 2.4 GET /api/v1/users/me/pending - 获取待处理事项

**权限：** 需要登录

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "pending_reviews": [
      {
        "id": 1,
        "type": "requirement",
        "title": "用户登录功能需求",
        "review_type": "review_req",
        "project_name": "电商平台",
        "created_at": "2026-04-18T10:00:00Z"
      }
    ],
    "pending_tasks": [
      {
        "id": 1,
        "title": "实现登录接口",
        "project_name": "电商平台",
        "iteration_name": "Sprint 1",
        "status": "in_progress",
        "due_date": "2026-04-25T00:00:00Z"
      }
    ],
    "pending_invitations": [
      {
        "id": 1,
        "team_id": 2,
        "team_name": "后端团队",
        "inviter": {
          "id": 3,
          "nickname": "王五"
        },
        "created_at": "2026-04-18T10:00:00Z"
      }
    ]
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |

---

## 3. 管理员用户管理 (Admin User)

### 3.1 GET /api/v1/admin/users - 用户列表

**权限：** 管理员 (`is_admin = true`)

**查询参数：**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | number | 否 | 1 | 页码 |
| page_size | number | 否 | 20 | 每页数量（最大 100） |
| search | string | 否 | "" | 搜索关键词（匹配邮箱、昵称） |

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "total": 50,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "id": 1,
        "email": "user@example.com",
        "nickname": "张三",
        "is_active": true,
        "is_admin": false,
        "created_at": "2026-01-01T00:00:00Z"
      }
    ]
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（非管理员） |

---

### 3.2 POST /api/v1/admin/users - 创建用户

**权限：** 管理员 (`is_admin = true`)

**请求 Body：**

```json
{
  "email": "newuser@example.com",
  "nickname": "新用户",
  "password": "string (8-64位)"
}
```

> 管理员创建的用户自动完成邮箱验证，无需验证邮件。

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 10,
    "email": "newuser@example.com",
    "nickname": "新用户",
    "is_active": true,
    "is_admin": false,
    "created_at": "2026-04-18T10:00:00Z"
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（非管理员） |
| 40001 | 参数校验失败 |
| 40002 | 邮箱已注册 |

---

### 3.3 PUT /api/v1/admin/users/{id}/status - 启用/禁用用户

**权限：** 管理员 (`is_admin = true`)

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 用户 ID |

**请求 Body：**

```json
{
  "is_active": false
}
```

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 10,
    "is_active": false
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（非管理员） |
| 40400 | 用户不存在 |
| 40001 | 参数校验失败 |

> 注意：管理员不可禁用自己。

---

## 4. 团队模块 (Team)

### 4.1 POST /api/v1/teams - 创建团队

**权限：** 需要登录

**请求 Body：**

```json
{
  "name": "前端团队",
  "description": "负责前端开发工作"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 团队名称 (2-64位) |
| description | string | 否 | 团队描述 (最大 500 字符) |

> 创建者自动成为团队所有者，拥有全部权限。

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "前端团队"
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40001 | 参数校验失败 |

---

### 4.2 GET /api/v1/teams/{id} - 团队详情

**权限：** 需要登录（团队成员可查看）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 团队 ID |

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "前端团队",
    "description": "负责前端开发工作",
    "owner": {
      "id": 1,
      "nickname": "张三"
    },
    "member_count": 8,
    "created_at": "2026-01-15T00:00:00Z"
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（非团队成员） |
| 40400 | 团队不存在 |

---

### 4.3 PUT /api/v1/teams/{id} - 编辑团队

**权限：** 需要登录（团队所有者或拥有 `member:assign_role` 权限的成员）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 团队 ID |

**请求 Body：**

```json
{
  "name": "前端工程团队",
  "description": "负责所有前端工程化工作"
}
```

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 1,
    "name": "前端工程团队",
    "description": "负责所有前端工程化工作"
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（非所有者或管理员） |
| 40400 | 团队不存在 |
| 40001 | 参数校验失败 |

---

### 4.4 DELETE /api/v1/teams/{id} - 解散团队

**权限：** 需要登录（仅团队所有者）

**说明：** 软删除，设置 `is_deleted = TRUE`，`deleted_at = NOW()`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 团队 ID |

**请求头：**

| Header | 必填 | 说明 |
|--------|------|------|
| X-Confirm-Delete | 是 | 值为团队名称，用于二次确认 |

**成功响应：**

```json
{
  "code": 0,
  "message": "团队已解散",
  "data": null
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（非所有者） |
| 40400 | 团队不存在 |
| 40001 | 二次确认团队名称不匹配 |

---

### 4.5 POST /api/v1/teams/{id}/transfer - 转让团队

**权限：** 需要登录（仅团队所有者）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 团队 ID |

**请求 Body：**

```json
{
  "new_owner_id": 5
}
```

**成功响应：**

```json
{
  "code": 0,
  "message": "团队已转让",
  "data": {
    "id": 1,
    "owner": {
      "id": 5,
      "nickname": "李四"
    }
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（非所有者） |
| 40400 | 团队不存在 / 目标用户不存在 |
| 40001 | 参数校验失败 |
| 40006 | 目标用户不在团队中 |

---

### 4.6 GET /api/v1/teams/{id}/members - 成员列表

**权限：** 需要登录（团队成员可查看）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 团队 ID |

**查询参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| role_id | number | 否 | 按角色 ID 筛选成员 |

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "user_id": 1,
      "nickname": "张三",
      "email": "zhangsan@example.com",
      "avatar": "https://example.com/avatar.jpg",
      "roles": [
        { "id": 1, "name": "所有者" }
      ],
      "joined_at": "2026-01-15T00:00:00Z"
    },
    {
      "user_id": 2,
      "nickname": "李四",
      "email": "lisi@example.com",
      "avatar": "https://example.com/avatar2.jpg",
      "roles": [
        { "id": 2, "name": "开发者" }
      ],
      "joined_at": "2026-02-01T00:00:00Z"
    }
  ]
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（非团队成员） |
| 40400 | 团队不存在 |

---

### 4.7 POST /api/v1/teams/{id}/invitations - 邀请成员

**权限：** 需要登录（拥有 `member:invite` 权限的团队成员）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 团队 ID |

**请求 Body：**

```json
{
  "identifier": "user@example.com"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| identifier | string | 是 | 用户邮箱或用户 ID |

**成功响应：**

```json
{
  "code": 0,
  "message": "邀请已发送",
  "data": {
    "invitation_id": 5,
    "user_id": 3,
    "nickname": "王五"
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（无 member:invite 权限） |
| 40400 | 团队不存在 / 用户不存在 |
| 40001 | 参数校验失败 |
| 40006 | 用户已在团队中 |

---

### 4.8 GET /api/v1/invitations/pending - 我收到的邀请

**权限：** 需要登录

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 5,
      "team_id": 2,
      "team_name": "后端团队",
      "inviter": {
        "id": 3,
        "nickname": "王五"
      },
      "created_at": "2026-04-18T10:00:00Z"
    }
  ]
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |

---

### 4.9 PUT /api/v1/invitations/{id} - 接受/拒绝邀请

**权限：** 需要登录（仅被邀请者本人）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| id | number | 邀请 ID |

**请求 Body：**

```json
{
  "action": "accept"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| action | string | 是 | `"accept"` 或 `"reject"` |

**成功响应（接受）：**

```json
{
  "code": 0,
  "message": "已加入团队",
  "data": {
    "team_id": 2,
    "team_name": "后端团队"
  }
}
```

**成功响应（拒绝）：**

```json
{
  "code": 0,
  "message": "已拒绝邀请",
  "data": null
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（非被邀请者） |
| 40005 | 邀请不存在/已处理 |
| 40006 | 用户已在团队中 |

---

### 4.10 DELETE /api/v1/teams/{teamId}/members/{userId} - 移出成员

**权限：** 需要登录（拥有 `member:remove` 权限的团队成员）

**说明：** 软删除，设置 `team_members.is_deleted = TRUE`，`deleted_at = NOW()`

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| teamId | number | 团队 ID |
| userId | number | 用户 ID |

**成功响应：**

```json
{
  "code": 0,
  "message": "成员已移出",
  "data": null
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（无 member:remove 权限） |
| 40400 | 团队不存在 / 用户不在团队中 |
| 40008 | 不能移出团队所有者 |

---

### 4.11 PUT /api/v1/teams/{teamId}/members/{userId}/roles - 分配角色

**权限：** 需要登录（拥有 `member:assign_role` 权限的团队成员）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| teamId | number | 团队 ID |
| userId | number | 用户 ID |

**请求 Body：**

```json
{
  "role_ids": [2, 3]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| role_ids | number[] | 是 | 角色 ID 列表，覆盖式更新 |

> 注意：所有者角色不可通过此接口分配，转让团队请使用 4.5 接口。

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "user_id": 2,
    "roles": [
      { "id": 2, "name": "开发者" },
      { "id": 3, "name": "评审员" }
    ]
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（无 member:assign_role 权限） |
| 40400 | 团队不存在 / 用户不在团队中 / 角色不存在 |
| 40001 | 参数校验失败 |

---

## 5. 角色与权限 (Role & Permission)

### 权限项枚举

以下为系统支持的所有权限项，用于角色创建和编辑：

| 权限项 | 说明 |
|--------|------|
| `project:create` | 创建项目 |
| `project:edit` | 编辑项目 |
| `project:archive` | 归档项目 |
| `project:delete` | 删除项目 |
| `iteration:create` | 创建迭代 |
| `iteration:edit` | 编辑迭代 |
| `iteration:start` | 启动迭代 |
| `iteration:complete` | 完成迭代 |
| `requirement:create` | 创建需求 |
| `requirement:edit` | 编辑需求 |
| `requirement:delete` | 删除需求 |
| `requirement:review_req` | 评审需求 |
| `requirement:review_spec` | 评审设计规格 |
| `requirement:review_tests` | 评审测试用例 |
| `task:create` | 创建任务 |
| `task:edit` | 编辑任务 |
| `task:delete` | 删除任务 |
| `task:test` | 执行测试 |
| `task:complete` | 完成任务 |
| `member:invite` | 邀请成员 |
| `member:remove` | 移出成员 |
| `member:assign_role` | 分配角色 |
| `spec_template:edit` | 编辑规格模板 |

---

### 5.1 GET /api/v1/teams/{teamId}/roles - 角色列表

**权限：** 需要登录（团队成员可查看）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| teamId | number | 团队 ID |

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "id": 1,
      "name": "所有者",
      "is_builtin": true,
      "permissions": [
        "project:create", "project:edit", "project:archive", "project:delete",
        "iteration:create", "iteration:edit", "iteration:start", "iteration:complete",
        "requirement:create", "requirement:edit", "requirement:delete",
        "requirement:review_req", "requirement:review_spec", "requirement:review_tests",
        "task:create", "task:edit", "task:delete", "task:test", "task:complete",
        "member:invite", "member:remove", "member:assign_role",
        "spec_template:edit"
      ],
      "description": "团队所有者，拥有全部权限"
    },
    {
      "id": 2,
      "name": "开发者",
      "is_builtin": true,
      "permissions": [
        "project:create", "project:edit",
        "iteration:create", "iteration:edit",
        "requirement:create", "requirement:edit",
        "task:create", "task:edit", "task:test", "task:complete"
      ],
      "description": "开发人员，可创建和编辑项目内容"
    },
    {
      "id": 5,
      "name": "评审员",
      "is_builtin": false,
      "permissions": [
        "requirement:review_req", "requirement:review_spec", "requirement:review_tests"
      ],
      "description": "负责需求评审"
    }
  ]
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（非团队成员） |
| 40400 | 团队不存在 |

---

### 5.2 POST /api/v1/teams/{teamId}/roles - 创建角色

**权限：** 需要登录（拥有 `member:assign_role` 权限的团队成员）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| teamId | number | 团队 ID |

**请求 Body：**

```json
{
  "name": "产品经理",
  "description": "负责需求管理和项目规划",
  "permissions": [
    "project:create", "project:edit",
    "requirement:create", "requirement:edit", "requirement:delete",
    "iteration:create", "iteration:edit"
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 角色名称 (2-32位) |
| description | string | 否 | 角色描述 |
| permissions | string[] | 是 | 权限项列表（需为合法权限项） |

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 6,
    "name": "产品经理",
    "is_builtin": false,
    "permissions": [
      "project:create", "project:edit",
      "requirement:create", "requirement:edit", "requirement:delete",
      "iteration:create", "iteration:edit"
    ],
    "description": "负责需求管理和项目规划"
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（无 member:assign_role 权限） |
| 40400 | 团队不存在 |
| 40001 | 参数校验失败（权限项不合法） |
| 40007 | 角色名称已存在 |

---

### 5.3 PUT /api/v1/teams/{teamId}/roles/{roleId} - 编辑角色

**权限：** 需要登录（拥有 `member:assign_role` 权限的团队成员）

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| teamId | number | 团队 ID |
| roleId | number | 角色 ID |

**请求 Body：**

```json
{
  "name": "高级开发者",
  "description": "可评审需求的高级开发人员",
  "permissions": [
    "project:create", "project:edit",
    "requirement:create", "requirement:edit",
    "requirement:review_req", "requirement:review_spec",
    "task:create", "task:edit", "task:test", "task:complete"
  ]
}
```

**成功响应：**

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "id": 5,
    "name": "高级开发者",
    "is_builtin": false,
    "permissions": [
      "project:create", "project:edit",
      "requirement:create", "requirement:edit",
      "requirement:review_req", "requirement:review_spec",
      "task:create", "task:edit", "task:test", "task:complete"
    ],
    "description": "可评审需求的高级开发人员"
  }
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（无 member:assign_role 权限） |
| 40400 | 团队不存在 / 角色不存在 |
| 40001 | 参数校验失败 |
| 40007 | 角色名称已存在 |
| 40009 | 内置角色不可修改 |

---

### 5.4 DELETE /api/v1/teams/{teamId}/roles/{roleId} - 删除角色

**权限：** 需要登录（拥有 `member:assign_role` 权限的团队成员）

**说明：** 软删除，设置 `is_deleted = TRUE`，`deleted_at = NOW()`。内置角色不可删除。

**路径参数：**

| 参数 | 类型 | 说明 |
|------|------|------|
| teamId | number | 团队 ID |
| roleId | number | 角色 ID |

**成功响应：**

```json
{
  "code": 0,
  "message": "角色已删除",
  "data": null
}
```

**错误码：**

| 错误码 | 说明 |
|--------|------|
| 40100 | 未登录 |
| 40101 | Token 过期 |
| 40300 | 无权限（无 member:assign_role 权限） |
| 40400 | 团队不存在 / 角色不存在 |
| 40009 | 内置角色不可删除 |

> 删除角色后，拥有该角色的成员将自动失去对应权限。如果角色正在被使用，仍可删除，相关成员的角色关联自动解除。

---

## 6. API Key 管理

> 供管理员为用户创建和管理 API Key，用于 Agent 长期认证。

### 6.1 创建 API Key

`POST /api/v1/admin/api-keys`

**权限**：管理员

**请求体**

```json
{
  "user_id": 1,
  "name": "开发Agent",
  "expires_at": "2027-01-01T00:00:00Z"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_id | number | 是 | 关联用户ID |
| name | string | 是 | 密钥名称 |
| expires_at | string | 否 | 过期时间（ISO 8601），不传则永不过期 |

**响应 data**

```json
{
  "id": 1,
  "name": "开发Agent",
  "key": "sdd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
  "key_prefix": "sdd_abcd",
  "user_id": 1,
  "expires_at": "2027-01-01T00:00:00Z",
  "created_at": "2026-05-01T10:00:00Z"
}
```

> **注意**：`key` 明文仅在创建时返回一次，后续无法查看。

### 6.2 列出用户的 API Key

`GET /api/v1/admin/users/{id}/api-keys`

**权限**：管理员

**响应 data**

```json
[
  {
    "id": 1,
    "name": "开发Agent",
    "key_prefix": "sdd_abcd",
    "is_active": true,
    "expires_at": "2027-01-01T00:00:00Z",
    "created_at": "2026-05-01T10:00:00Z"
  }
]
```

### 6.3 吊销 API Key

`DELETE /api/v1/admin/api-keys/{id}`

**权限**：管理员

**行为**：设置 `is_active = FALSE`，吊销后使用该 Key 的请求将被拒绝。

**响应 data**

```json
{
  "id": 1
}
```

**错误**

| 错误码 | 说明 |
|--------|------|
| 40400 | API Key 不存在 |
