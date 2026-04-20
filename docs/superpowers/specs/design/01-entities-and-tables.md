# 数据库设计文档

## 1. 概述

本文档定义规范驱动开发平台的数据库结构。平台采用 **MySQL + MongoDB** 混合存储架构：

- **MySQL**：存储关系型数据（用户、团队、项目、需求、任务、审核等）
- **MongoDB**：存储文档型数据（规范模板、规范文档）

### 设计原则

- 不使用 ENUM 类型，统一使用 `VARCHAR` + `CHECK` 约束（兼容 SQLite 开发环境）
- 所有主键使用 `BIGINT AUTO_INCREMENT`
- 时间字段统一使用 `DATETIME`，默认值为 `CURRENT_TIMESTAMP`
- 外键关系明确标注，采用逻辑外键约束
- JSON 字段用于存储灵活结构化数据（`type_detail`）
- **软删除**：所有支持删除操作的表使用 `is_deleted` + `deleted_at` 字段，不物理删除数据
- 所有查询默认过滤 `is_deleted = FALSE`

---

## 2. ER 关系总览

```
users
  ├──< team_members >── teams
  ├──< invitations (inviter_id / invitee_id)
  ├──< requirement_reviews (reviewer_id)
  ├──< tasks (assignee_id / created_by)
  ├──< test_execution_rounds (executed_by)
  ├──< password_reset_tokens
  │
teams ├──< team_members
      ├──< roles ├──< role_permissions
      │          └──< member_roles >── team_members
      ├──< invitations
      └──< projects ├──< iterations ├──< requirements ├──< requirement_reviews
                    │                                ├──< test_cases
                    │                                └──< tasks ──< test_execution_rounds
                    │                                              └──< test_execution_records >── test_cases
```

### 核心关系说明

| 关系 | 类型 | 说明 |
|------|------|------|
| teams → users (owner_id) | 多对一 | 团队有一个创建者/负责人 |
| team_members → teams, users | 多对多关联 | 用户加入团队，通过 team_members 表关联 |
| roles → teams | 多对一 | 每个团队可定义多个角色 |
| role_permissions → roles | 一对多 | 一个角色拥有多个权限项 |
| member_roles → team_members, roles | 多对多关联 | 成员通过关联表分配角色 |
| invitations → teams, users | 多对一 | 团队邀请用户加入 |
| projects → teams | 多对一 | 项目归属团队 |
| iterations → projects | 多对一 | 迭代归属项目 |
| requirements → iterations | 多对一 | 需求归属迭代 |
| requirement_reviews → requirements, users | 多对一 | 需求的审核记录 |
| tasks → requirements, users | 多对一 | 需求分解为任务 |
| test_cases → requirements | 多对一 | 测试用例关联需求 |
| test_execution_rounds → tasks, users | 多对一 | 测试执行轮次关联任务 |
| test_execution_records → rounds, test_cases | 多对一 | 执行记录关联轮次和用例 |

### MongoDB 关系

| 集合 | 关联 | 说明 |
|------|------|------|
| specification_templates | team_id → teams | 团队级规范模板，一个团队一个模板 |
| specification_documents | requirement_id → requirements | 需求级规范文档，一个需求一个文档（含多版本） |

---

## 3. MySQL 表设计

### 3.1 users — 用户表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 用户ID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | uniq_email | 邮箱，登录凭证 |
| nickname | VARCHAR(100) | NOT NULL | — | 昵称 |
| password_hash | VARCHAR(255) | NOT NULL | — | 密码哈希值 |
| avatar | VARCHAR(500) | DEFAULT NULL | — | 头像URL |
| is_active | BOOLEAN | NOT NULL DEFAULT TRUE | — | 账号是否启用 |
| is_admin | BOOLEAN | NOT NULL DEFAULT FALSE | — | 是否系统管理员 |
| email_verified | BOOLEAN | NOT NULL DEFAULT FALSE | — | 邮箱是否已验证 |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 创建时间 |
| updated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | — | 更新时间 |

```sql
CREATE TABLE users (
    id              BIGINT       AUTO_INCREMENT PRIMARY KEY,
    email           VARCHAR(255) NOT NULL,
    nickname        VARCHAR(100) NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    avatar          VARCHAR(500) DEFAULT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    is_admin        BOOLEAN      NOT NULL DEFAULT FALSE,
    email_verified  BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uniq_email UNIQUE (email)
);
```

---

### 3.2 teams — 团队表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 团队ID |
| name | VARCHAR(100) | NOT NULL | — | 团队名称 |
| description | TEXT | DEFAULT NULL | — | 团队描述 |
| owner_id | BIGINT | FK → users(id), NOT NULL | idx_owner | 团队负责人 |
| is_deleted | BOOLEAN | NOT NULL DEFAULT FALSE | — | 是否已删除 |
| deleted_at | DATETIME | DEFAULT NULL | — | 删除时间 |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 创建时间 |
| updated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | — | 更新时间 |

```sql
CREATE TABLE teams (
    id          BIGINT   AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    description TEXT         DEFAULT NULL,
    owner_id    BIGINT   NOT NULL,
    is_deleted  BOOLEAN  NOT NULL DEFAULT FALSE,
    deleted_at  DATETIME     DEFAULT NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_owner (owner_id)
);
```

---

### 3.3 team_members — 团队成员表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 记录ID |
| team_id | BIGINT | FK → teams(id), NOT NULL | idx_team | 团队ID |
| user_id | BIGINT | FK → users(id), NOT NULL | idx_user | 用户ID |
| joined_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 加入时间 |
| is_deleted | BOOLEAN | NOT NULL DEFAULT FALSE | — | 是否已移出 |
| deleted_at | DATETIME | DEFAULT NULL | — | 移出时间 |

**唯一约束**：`UNIQUE (team_id, user_id)` — 同一用户在同一团队中仅有一条记录。

```sql
CREATE TABLE team_members (
    id        BIGINT   AUTO_INCREMENT PRIMARY KEY,
    team_id   BIGINT   NOT NULL,
    user_id   BIGINT   NOT NULL,
    joined_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    deleted_at DATETIME    DEFAULT NULL,
    CONSTRAINT uniq_team_user UNIQUE (team_id, user_id),
    INDEX idx_team (team_id),
    INDEX idx_user (user_id)
);
```

---

### 3.4 roles — 角色表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 角色ID |
| team_id | BIGINT | FK → teams(id), NOT NULL | idx_team | 所属团队 |
| name | VARCHAR(50) | NOT NULL | — | 角色名称 |
| is_builtin | BOOLEAN | NOT NULL DEFAULT FALSE | — | 是否系统内置角色 |
| description | VARCHAR(255) | DEFAULT NULL | — | 角色描述 |
| is_deleted | BOOLEAN | NOT NULL DEFAULT FALSE | — | 是否已删除 |
| deleted_at | DATETIME | DEFAULT NULL | — | 删除时间 |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 创建时间 |

**唯一约束**：`UNIQUE (team_id, name)` — 同一团队内角色名称唯一。

```sql
CREATE TABLE roles (
    id          BIGINT      AUTO_INCREMENT PRIMARY KEY,
    team_id     BIGINT      NOT NULL,
    name        VARCHAR(50) NOT NULL,
    is_builtin  BOOLEAN     NOT NULL DEFAULT FALSE,
    description VARCHAR(255) DEFAULT NULL,
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE,
    deleted_at  DATETIME       DEFAULT NULL,
    created_at  DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uniq_team_role_name UNIQUE (team_id, name),
    INDEX idx_team (team_id)
);
```

---

### 3.5 role_permissions — 角色权限表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 记录ID |
| role_id | BIGINT | FK → roles(id), NOT NULL | idx_role | 角色ID |
| permission | VARCHAR(100) | NOT NULL | — | 权限标识，如 `requirement:create`、`spec:review` |

**唯一约束**：`UNIQUE (role_id, permission)` — 同一角色下权限不重复。

```sql
CREATE TABLE role_permissions (
    id         BIGINT       AUTO_INCREMENT PRIMARY KEY,
    role_id    BIGINT       NOT NULL,
    permission VARCHAR(100) NOT NULL,
    CONSTRAINT uniq_role_permission UNIQUE (role_id, permission),
    INDEX idx_role (role_id)
);
```

**常用权限标识**：

| 权限标识 | 说明 |
|----------|------|
| `requirement:create` | 创建需求 |
| `requirement:review` | 审核需求 |
| `requirement:edit` | 编辑需求（草稿状态） |
| `spec:create` | 编写规范 |
| `spec:review` | 审核规范 |
| `test_case:create` | 编写测试用例 |
| `test_case:review` | 审核测试用例 |
| `task:create` | 创建任务 |
| `task:assign` | 分配任务 |
| `task:execute` | 执行任务/测试 |
| `project:manage` | 管理项目 |
| `iteration:manage` | 管理迭代 |
| `member:invite` | 邀请成员 |
| `role:manage` | 管理角色权限 |

---

### 3.6 member_roles — 成员角色关联表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 记录ID |
| member_id | BIGINT | FK → team_members(id), NOT NULL | idx_member | 团队成员记录ID |
| role_id | BIGINT | FK → roles(id), NOT NULL | idx_role | 角色ID |

**唯一约束**：`UNIQUE (member_id, role_id)` — 同一成员不重复分配同一角色。

```sql
CREATE TABLE member_roles (
    id        BIGINT AUTO_INCREMENT PRIMARY KEY,
    member_id BIGINT NOT NULL,
    role_id   BIGINT NOT NULL,
    CONSTRAINT uniq_member_role UNIQUE (member_id, role_id),
    INDEX idx_member (member_id),
    INDEX idx_role (role_id)
);
```

---

### 3.7 invitations — 邀请表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 邀请ID |
| team_id | BIGINT | FK → teams(id), NOT NULL | idx_team | 目标团队 |
| inviter_id | BIGINT | FK → users(id), NOT NULL | idx_inviter | 邀请人 |
| invitee_id | BIGINT | FK → users(id), NOT NULL | idx_invitee | 被邀请人 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending', CHECK (status IN ('pending','accepted','rejected')) | — | 邀请状态 |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 创建时间 |
| responded_at | DATETIME | DEFAULT NULL | — | 响应时间 |

```sql
CREATE TABLE invitations (
    id           BIGINT      AUTO_INCREMENT PRIMARY KEY,
    team_id      BIGINT      NOT NULL,
    inviter_id   BIGINT      NOT NULL,
    invitee_id   BIGINT      NOT NULL,
    status       VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at   DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at DATETIME         DEFAULT NULL,
    CONSTRAINT chk_inv_status CHECK (status IN ('pending', 'accepted', 'rejected')),
    INDEX idx_team (team_id),
    INDEX idx_inviter (inviter_id),
    INDEX idx_invitee (invitee_id)
);
```

---

### 3.8 projects — 项目表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 项目ID |
| team_id | BIGINT | FK → teams(id), NOT NULL | idx_team | 所属团队 |
| name | VARCHAR(200) | NOT NULL | — | 项目名称 |
| description | TEXT | DEFAULT NULL | — | 项目描述 |
| start_date | DATE | DEFAULT NULL | — | 项目开始日期 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'active', CHECK (status IN ('active','archived')) | — | 项目状态 |
| is_deleted | BOOLEAN | NOT NULL DEFAULT FALSE | — | 是否已删除 |
| deleted_at | DATETIME | DEFAULT NULL | — | 删除时间 |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 创建时间 |
| updated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | — | 更新时间 |

```sql
CREATE TABLE projects (
    id          BIGINT       AUTO_INCREMENT PRIMARY KEY,
    team_id     BIGINT       NOT NULL,
    name        VARCHAR(200) NOT NULL,
    description TEXT              DEFAULT NULL,
    start_date  DATE              DEFAULT NULL,
    status      VARCHAR(20) NOT NULL DEFAULT 'active',
    is_deleted  BOOLEAN     NOT NULL DEFAULT FALSE,
    deleted_at  DATETIME         DEFAULT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_proj_status CHECK (status IN ('active', 'archived')),
    INDEX idx_team (team_id)
);
```

---

### 3.9 iterations — 迭代表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 迭代ID |
| project_id | BIGINT | FK → projects(id), NOT NULL | idx_project | 所属项目 |
| name | VARCHAR(100) | NOT NULL | — | 迭代名称 |
| goal | TEXT | DEFAULT NULL | — | 迭代目标 |
| start_date | DATE | NOT NULL | — | 开始日期 |
| end_date | DATE | NOT NULL | — | 结束日期 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'planned', CHECK (status IN ('planned','in_progress','completed')) | — | 迭代状态 |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 创建时间 |
| updated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | — | 更新时间 |

```sql
CREATE TABLE iterations (
    id         BIGINT       AUTO_INCREMENT PRIMARY KEY,
    project_id BIGINT       NOT NULL,
    name       VARCHAR(100) NOT NULL,
    goal       TEXT             DEFAULT NULL,
    start_date DATE         NOT NULL,
    end_date   DATE         NOT NULL,
    status     VARCHAR(20)  NOT NULL DEFAULT 'planned',
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_iter_status CHECK (status IN ('planned', 'in_progress', 'completed')),
    CONSTRAINT chk_iter_dates CHECK (end_date >= start_date),
    INDEX idx_project (project_id)
);
```

---

### 3.10 requirements — 需求表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 需求ID |
| iteration_id | BIGINT | FK → iterations(id), NOT NULL | idx_iteration | 所属迭代 |
| title | VARCHAR(255) | NOT NULL | — | 需求标题 |
| req_type | VARCHAR(20) | NOT NULL, CHECK (req_type IN ('feature','optimization','bug')) | idx_type | 需求类型 |
| priority | INT | NOT NULL DEFAULT 0 | — | 优先级，数值越大优先级越高 |
| status | VARCHAR(30) | NOT NULL DEFAULT 'drafting_req', CHECK (status IN ('drafting_req','reviewing_req','drafting_spec','reviewing_spec','drafting_tests','reviewing_tests','approved')) | idx_status | 需求状态 |
| description | TEXT | DEFAULT NULL | — | 需求描述 |
| type_detail | JSON | DEFAULT NULL | — | 类型附加信息（如 Bug 的复现步骤） |
| created_by | BIGINT | FK → users(id), NOT NULL | idx_creator | 创建人 |
| is_deleted | BOOLEAN | NOT NULL DEFAULT FALSE | — | 是否已删除 |
| deleted_at | DATETIME | DEFAULT NULL | — | 删除时间 |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 创建时间 |
| updated_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | — | 更新时间 |

**状态流转图**：

```
drafting_req → reviewing_req → drafting_spec → reviewing_spec → drafting_tests → reviewing_tests → approved
                   ↓ rejected       ↓ rejected          ↓ rejected
               drafting_req    drafting_spec      drafting_tests
```

> 审核通过后进入下一阶段，不可回退；审核驳回时退回上一阶段重新编辑。

```sql
CREATE TABLE requirements (
    id            BIGINT       AUTO_INCREMENT PRIMARY KEY,
    iteration_id  BIGINT       NOT NULL,
    title         VARCHAR(255) NOT NULL,
    req_type      VARCHAR(20)  NOT NULL,
    priority      INT          NOT NULL DEFAULT 0,
    status        VARCHAR(30)  NOT NULL DEFAULT 'drafting_req',
    description   TEXT             DEFAULT NULL,
    type_detail   JSON             DEFAULT NULL,
    created_by    BIGINT       NOT NULL,
    is_deleted    BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_at    DATETIME         DEFAULT NULL,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_req_type   CHECK (req_type IN ('feature', 'optimization', 'bug')),
    CONSTRAINT chk_req_status CHECK (status IN (
        'drafting_req', 'reviewing_req',
        'drafting_spec', 'reviewing_spec',
        'drafting_tests', 'reviewing_tests',
        'approved'
    )),
    INDEX idx_iteration (iteration_id),
    INDEX idx_type (req_type),
    INDEX idx_status (status),
    INDEX idx_creator (created_by)
);
```

**type_detail JSON 结构示例**：

```json
// req_type = 'bug' 时
{
    "reproduce_steps": "步骤1→步骤2→步骤3",
    "environment": "Chrome 120 / Windows 11",
    "severity": "high"
}

// req_type = 'optimization' 时
{
    "current_behavior": "当前响应时间 > 3s",
    "expected_behavior": "响应时间 < 500ms",
    "metric": "API响应时间"
}
```

---

### 3.11 requirement_reviews — 需求审核记录表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 审核ID |
| requirement_id | BIGINT | FK → requirements(id), NOT NULL | idx_requirement | 关联需求 |
| review_type | VARCHAR(20) | NOT NULL, CHECK (review_type IN ('requirement','specification','test_case')) | idx_type | 审核类型 |
| reviewer_id | BIGINT | FK → users(id), NOT NULL | idx_reviewer | 审核人 |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending', CHECK (status IN ('pending','approved','rejected')) | — | 审核状态 |
| comment | TEXT | DEFAULT NULL | — | 审核意见（驳回时必填理由） |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 创建时间 |
| reviewed_at | DATETIME | DEFAULT NULL | — | 审核时间 |

```sql
CREATE TABLE requirement_reviews (
    id             BIGINT      AUTO_INCREMENT PRIMARY KEY,
    requirement_id BIGINT      NOT NULL,
    review_type    VARCHAR(20) NOT NULL,
    reviewer_id    BIGINT      NOT NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'pending',
    comment        TEXT            DEFAULT NULL,
    created_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    reviewed_at    DATETIME        DEFAULT NULL,
    CONSTRAINT chk_review_type   CHECK (review_type IN ('requirement', 'specification', 'test_case')),
    CONSTRAINT chk_review_status CHECK (status IN ('pending', 'approved', 'rejected')),
    INDEX idx_requirement (requirement_id),
    INDEX idx_type (review_type),
    INDEX idx_reviewer (reviewer_id)
);
```

**审核类型与需求状态的对应关系**：

| review_type | 触发时机 | 审核通过后状态变更 |
|-------------|----------|-------------------|
| `requirement` | drafting_req → reviewing_req | reviewing_req → drafting_spec |
| `specification` | drafting_spec → reviewing_spec | reviewing_spec → drafting_tests |
| `test_case` | drafting_tests → reviewing_tests | reviewing_tests → approved |

---

### 3.12 tasks — 任务表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 任务ID |
| requirement_id | BIGINT | FK → requirements(id), NOT NULL | idx_requirement | 关联需求 |
| title | VARCHAR(255) | NOT NULL | — | 任务标题 |
| description | TEXT | DEFAULT NULL | — | 任务描述 |
| assignee_id | BIGINT | FK → users(id), DEFAULT NULL | idx_assignee | 执行人（可为空） |
| status | VARCHAR(20) | NOT NULL DEFAULT 'pending', CHECK (status IN ('pending','coding','testing','completed')) | idx_status | 任务状态 |

**任务状态流转**：

```
pending → coding → testing → completed
           ↑         │
           └─────────┘  测试不通过，退回编码
```

```sql
CREATE TABLE tasks (
    id              BIGINT       AUTO_INCREMENT PRIMARY KEY,
    requirement_id  BIGINT       NOT NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT             DEFAULT NULL,
    assignee_id     BIGINT           DEFAULT NULL,
    status          VARCHAR(20)  NOT NULL DEFAULT 'pending',
    created_by      BIGINT       NOT NULL,
    is_deleted      BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_at      DATETIME         DEFAULT NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT chk_task_status  CHECK (status IN ('pending', 'coding', 'testing', 'completed')),
    INDEX idx_requirement (requirement_id),
    INDEX idx_assignee (assignee_id),
    INDEX idx_status (status),
    INDEX idx_creator (created_by)
);
```

---

### 3.13 test_cases — 测试用例表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 用例ID |
| requirement_id | BIGINT | FK → requirements(id), NOT NULL | idx_requirement | 关联需求 |
| case_number | VARCHAR(50) | UNIQUE, NOT NULL | uniq_case_number | 用例编号（如 TC-001） |
| title | VARCHAR(255) | NOT NULL | — | 用例标题 |
| case_type | VARCHAR(10) | NOT NULL, CHECK (case_type IN ('api','e2e')) | idx_type | 用例类型 |
| precondition | TEXT | DEFAULT NULL | — | 前置条件 |
| steps | TEXT | NOT NULL | — | 测试步骤 |
| expected_result | TEXT | NOT NULL | — | 预期结果 |
| related_api | VARCHAR(500) | DEFAULT NULL | — | 关联API路径 |
| related_element | VARCHAR(200) | DEFAULT NULL | — | 关联UI元素 |
| is_deleted | BOOLEAN | NOT NULL DEFAULT FALSE | — | 是否已删除 |
| deleted_at | DATETIME | DEFAULT NULL | — | 删除时间 |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 创建时间 |

```sql
CREATE TABLE test_cases (
    id               BIGINT       AUTO_INCREMENT PRIMARY KEY,
    requirement_id   BIGINT       NOT NULL,
    case_number      VARCHAR(50)  NOT NULL,
    title            VARCHAR(255) NOT NULL,
    case_type        VARCHAR(10)  NOT NULL,
    precondition     TEXT             DEFAULT NULL,
    steps            TEXT         NOT NULL,
    expected_result  TEXT         NOT NULL,
    related_api      VARCHAR(500) DEFAULT NULL,
    related_element  VARCHAR(200) DEFAULT NULL,
    is_deleted       BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_at       DATETIME         DEFAULT NULL,
    created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_tc_type CHECK (case_type IN ('api', 'e2e')),
    CONSTRAINT uniq_case_number UNIQUE (case_number),
    INDEX idx_requirement (requirement_id),
    INDEX idx_type (case_type)
);
```

---

### 3.14 test_execution_rounds — 测试执行轮次表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 轮次ID |
| task_id | BIGINT | FK → tasks(id), NOT NULL | idx_task | 关联任务 |
| executed_by | BIGINT | FK → users(id), NOT NULL | idx_executor | 执行人 |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 创建时间 |

```sql
CREATE TABLE test_execution_rounds (
    id           BIGINT   AUTO_INCREMENT PRIMARY KEY,
    task_id      BIGINT   NOT NULL,
    executed_by  BIGINT   NOT NULL,
    created_at   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_task (task_id),
    INDEX idx_executor (executed_by)
);
```

---

### 3.15 test_execution_records — 测试执行记录表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 记录ID |
| round_id | BIGINT | FK → test_execution_rounds(id), NOT NULL | idx_round | 关联轮次 |
| test_case_id | BIGINT | FK → test_cases(id), NOT NULL | idx_case | 关联用例 |
| status | VARCHAR(10) | NOT NULL, CHECK (status IN ('passed','failed','skipped')) | idx_status | 执行结果 |
| actual_result | TEXT | DEFAULT NULL | — | 实际结果 |
| failure_reason | TEXT | DEFAULT NULL | — | 失败原因 |
| executed_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 执行时间 |

```sql
CREATE TABLE test_execution_records (
    id              BIGINT      AUTO_INCREMENT PRIMARY KEY,
    round_id        BIGINT      NOT NULL,
    test_case_id    BIGINT      NOT NULL,
    status          VARCHAR(10) NOT NULL,
    actual_result   TEXT            DEFAULT NULL,
    failure_reason  TEXT            DEFAULT NULL,
    executed_at     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_terec_status CHECK (status IN ('passed', 'failed', 'skipped')),
    INDEX idx_round (round_id),
    INDEX idx_case (test_case_id),
    INDEX idx_status (status)
);
```

---

### 3.16 password_reset_tokens — 密码重置令牌表

| 字段 | 类型 | 约束 | 索引 | 说明 |
|------|------|------|------|------|
| id | BIGINT | PK, AUTO_INCREMENT | PRIMARY | 令牌ID |
| user_id | BIGINT | FK → users(id), NOT NULL | idx_user | 关联用户 |
| token | VARCHAR(255) | UNIQUE, NOT NULL | uniq_token | 重置令牌 |
| expires_at | DATETIME | NOT NULL | — | 过期时间 |
| used | BOOLEAN | NOT NULL DEFAULT FALSE | — | 是否已使用 |
| created_at | DATETIME | NOT NULL DEFAULT CURRENT_TIMESTAMP | — | 创建时间 |

```sql
CREATE TABLE password_reset_tokens (
    id         BIGINT       AUTO_INCREMENT PRIMARY KEY,
    user_id    BIGINT       NOT NULL,
    token      VARCHAR(255) NOT NULL,
    expires_at DATETIME     NOT NULL,
    used       BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uniq_token UNIQUE (token),
    INDEX idx_user (user_id)
);
```

---

## 4. MongoDB 集合设计

### 4.1 specification_templates — 规范模板集合

团队级别的规范模板，定义编写规范时需要填写的结构。每个团队维护一份模板。

**关联**：`team_id` → MySQL `teams.id`

```json
{
  "_id": ObjectId,
  "team_id": NumberLong,
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
          "description": "对实体的简要描述"
        },
        {
          "name": "fields",
          "display_name": "字段列表",
          "type": "list",
          "required": true,
          "description": "实体包含的字段定义（字段名、类型、约束）"
        }
      ]
    },
    {
      "name": "table_design",
      "display_name": "数据表设计",
      "required": true,
      "fields": [
        {
          "name": "tables",
          "display_name": "表列表",
          "type": "list",
          "required": true,
          "description": "每个表的表名、字段、类型、索引、外键关系"
        }
      ]
    },
    {
      "name": "page_structure",
      "display_name": "页面结构",
      "required": true,
      "fields": [
        {
          "name": "pages",
          "display_name": "页面列表",
          "type": "list",
          "required": true,
          "description": "每个页面的名称、编码、元素列表（含唯一编码）、交互行为"
        }
      ]
    },
    {
      "name": "api_design",
      "display_name": "API 设计",
      "required": true,
      "fields": [
        {
          "name": "endpoints",
          "display_name": "接口列表",
          "type": "list",
          "required": true,
          "description": "每个接口的 URL、HTTP 方法、请求参数、响应参数、错误码"
        }
      ]
    },
    {
      "name": "constraints",
      "display_name": "其他约束",
      "required": false,
      "fields": [
        {
          "name": "directory_structure",
          "display_name": "目录结构",
          "type": "text",
          "required": false,
          "description": "项目目录结构规范"
        },
        {
          "name": "naming_conventions",
          "display_name": "命名规范",
          "type": "text",
          "required": false,
          "description": "编码命名规范"
        },
        {
          "name": "other",
          "display_name": "其他约束",
          "type": "text",
          "required": false,
          "description": "其他技术约束"
        }
      ]
    }
  ],
  "updated_at": ISODate,
  "updated_by": NumberLong
}
```

**字段类型说明**：

| type 值 | 含义 | 前端渲染方式 |
|---------|------|-------------|
| `text` | 纯文本 | 文本输入框 / 文本域 |
| `list` | 列表 | 可增删的列表编辑器 |
| `object` | 对象 | 嵌套结构编辑器 |

**索引**：

```
{ "team_id": 1 }  — 唯一索引，每个团队一份模板
```

---

### 4.2 specification_documents — 规范文档集合

需求级别的规范文档，包含完整的版本历史。每次保存规范内容时创建新版本。

**关联**：`requirement_id` → MySQL `requirements.id`

```json
{
  "_id": ObjectId,
  "requirement_id": NumberLong,
  "current_version": Number,
  "versions": [
    {
      "version": 1,
      "content": {
        "entity_definition": {
          "entities": [
            {
              "name": "user",
              "display_name": "用户",
              "description": "系统用户实体",
              "fields": [
                { "name": "id", "type": "BIGINT", "constraints": ["PK", "AUTO_INCREMENT"] },
                { "name": "email", "type": "VARCHAR(255)", "constraints": ["NOT NULL", "UNIQUE"] }
              ]
            }
          ]
        },
        "table_design": {
          "tables": [
            {
              "name": "users",
              "description": "用户表",
              "fields": [
                { "name": "id", "type": "BIGINT", "nullable": false, "default": null, "comment": "用户ID" },
                { "name": "email", "type": "VARCHAR(255)", "nullable": false, "default": null, "comment": "邮箱" }
              ],
              "indexes": [
                { "name": "uniq_email", "fields": ["email"], "unique": true }
              ]
            }
          ]
        },
        "page_structure": {
          "pages": [
            {
              "name": "用户管理",
              "code": "user-management",
              "route": "/admin/users",
              "elements": [
                {
                  "code": "user-mgmt-btn-create",
                  "type": "button",
                  "label": "创建用户",
                  "interaction": "点击打开创建用户弹窗"
                },
                {
                  "code": "user-mgmt-inp-search",
                  "type": "input",
                  "label": "搜索",
                  "interaction": "输入关键词搜索用户"
                },
                {
                  "code": "user-mgmt-tbl-users",
                  "type": "table",
                  "label": "用户列表",
                  "columns": ["ID", "邮箱", "昵称", "状态", "创建时间", "操作"],
                  "interactions": [
                    { "trigger": "row-action-toggle", "behavior": "启用/禁用用户" }
                  ]
                },
                {
                  "code": "user-mgmt-pag-list",
                  "type": "pagination",
                  "label": "分页器",
                  "interaction": "翻页"
                }
              ]
            }
          ]
        },
        "api_design": {
          "endpoints": [
            {
              "method": "GET",
              "path": "/api/v1/admin/users",
              "description": "获取用户列表",
              "request_params": [
                { "name": "page", "in": "query", "type": "integer", "required": false, "description": "页码" },
                { "name": "page_size", "in": "query", "type": "integer", "required": false, "description": "每页数量" }
              ],
              "response": {
                "code": 0,
                "data": {
                  "total": 100,
                  "items": [{ "id": 1, "email": "string", "nickname": "string" }]
                }
              },
              "errors": [
                { "code": 40100, "message": "未登录" }
              ]
            }
          ]
        },
        "constraints": {
          "directory_structure": "src/\n  controllers/\n  services/\n  models/",
          "naming_conventions": "接口URL使用蛇形命名，前端元素编码使用短横线命名",
          "other": ""
        }
      },
      "created_at": ISODate("2025-01-15T10:30:00Z"),
      "created_by": NumberLong
    },
    {
      "version": 2,
      "content": { ... },
      "created_at": ISODate("2025-01-16T14:20:00Z"),
      "created_by": NumberLong
    }
  ]
}
```

**索引**：

```
{ "requirement_id": 1 }  — 唯一索引，每个需求一份文档
```

**版本管理规则**：

- 每次保存创建新版本，`current_version` 递增
- 审核通过后规范内容锁定，不可修改（需通过需求状态控制）
- `content` 中的键名（如 `entity_definition`）与 `specification_templates.sections[].name` 对应

---

## 5. 完整建表顺序

按照外键依赖关系，建表顺序如下：

```
1. users
2. teams                      → users
3. team_members               → teams, users
4. roles                      → teams
5. role_permissions           → roles
6. member_roles               → team_members, roles
7. invitations                → teams, users
8. projects                   → teams
9. iterations                 → projects
10. requirements              → iterations, users
11. requirement_reviews       → requirements, users
12. tasks                     → requirements, users
13. test_cases                → requirements
14. test_execution_rounds     → tasks, users
15. test_execution_records    → test_execution_rounds, test_cases
16. password_reset_tokens     → users
```

---

## 6. 业务流程与数据流转

### 6.1 需求阶段

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────────┐     ┌──────────┐
│ drafting_req │────▶│ reviewing_req    │────▶│ drafting_spec   │────▶│ reviewing_spec   │────▶│ drafting_tests  │────▶│ reviewing_tests  │────▶│ approved │
└─────────────┘     └──────────────────┘     └─────────────────┘     └──────────────────┘     └─────────────────┘     └──────────────────┘     └──────────┘
                          │ rejected                                         │ rejected                                         │ rejected
                          ▼                                                   ▼                                                  ▼
                    ┌─────────────┐                                   ┌─────────────────┐                                ┌─────────────────┐
                    │ drafting_req │                                   │ drafting_spec   │                                │ drafting_tests  │
                    └─────────────┘                                   └─────────────────┘                                └─────────────────┘
```

**数据操作映射**：

| 阶段转换 | MySQL 操作 | MongoDB 操作 |
|----------|-----------|-------------|
| 创建需求 | INSERT requirements | — |
| 提交需求审核 | UPDATE requirements.status = 'reviewing_req' | — |
| 审核需求通过 | UPDATE requirements.status = 'drafting_spec' | — |
| 审核需求驳回 | UPDATE requirements.status = 'drafting_req' + INSERT requirement_reviews | — |
| 保存规范草稿 | — | UPDATE specification_documents（新增 version） |
| 提交规范审核 | UPDATE requirements.status = 'reviewing_spec' | — |
| 审核规范通过 | UPDATE requirements.status = 'drafting_tests' | — |
| 创建测试用例 | INSERT test_cases | — |
| 提交测试用例审核 | UPDATE requirements.status = 'reviewing_tests' | — |
| 审核测试用例通过 | UPDATE requirements.status = 'approved' | — |

### 6.2 任务阶段

```
┌────────┐     ┌─────────┐     ┌───────────┐
│ coding │────▶│ testing │────▶│ completed │
└────────┘     └─────────┘     └───────────┘
   ▲               │
   └───────────────┘  测试不通过
```

**数据操作映射**：

| 操作 | MySQL 操作 |
|------|-----------|
| 创建任务 | INSERT tasks (status = 'coding') |
| 提交测试 | UPDATE tasks.status = 'testing' |
| 开始测试执行 | INSERT test_execution_rounds |
| 记录用例结果 | INSERT test_execution_records |
| 测试全部通过 | UPDATE tasks.status = 'completed' |
| 测试不通过 | UPDATE tasks.status = 'coding' |
