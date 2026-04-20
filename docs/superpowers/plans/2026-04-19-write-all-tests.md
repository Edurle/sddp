# 编写全部测试代码 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建项目骨架后，编写全部后端接口测试（~286条）和前端E2E测试（~93条），所有测试在实现前应失败。

**Architecture:** 后端 FastAPI 四层架构（models→schemas→services→api），测试用 TestClient 直接调接口。前端 Vue 3 + Playwright E2E 测试。开发环境用 SQLite 替代 MySQL。

**Tech Stack:** FastAPI, SQLAlchemy, Pydantic, pytest, httpx/TestClient, Vue 3, Playwright, TypeScript

---

## Phase 1: 后端项目骨架

### Task 1: 创建后端目录结构和配置文件

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/requirements.txt`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`
- Create: `backend/app/cache.py`
- Create: `backend/app/exceptions.py`
- Create: `backend/app/deps.py`

- [ ] 创建目录结构
- [ ] 编写 pyproject.toml（pytest 配置、项目元数据）
- [ ] 编写 requirements.txt（fastapi, sqlalchemy, pydantic, python-jose, passlib, httpx, pytest, pytest-asyncio, motor, pymongo）
- [ ] 编写 config.py（环境变量读取，SQLite fallback）
- [ ] 编写 database.py（SQLAlchemy async engine + session，MongoDB client）
- [ ] 编写 cache.py（内存缓存 fallback）
- [ ] 编写 exceptions.py（BusinessError 及错误码常量）
- [ ] 编写 main.py（FastAPI app，路由注册）
- [ ] 编写 deps.py（get_db, get_current_user 等依赖注入）
- [ ] 提交

### Task 2: 创建全部 SQLAlchemy 模型

**Files:**
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/team.py`
- Create: `backend/app/models/role.py`
- Create: `backend/app/models/invitation.py`
- Create: `backend/app/models/project.py`
- Create: `backend/app/models/iteration.py`
- Create: `backend/app/models/requirement.py`
- Create: `backend/app/models/requirement_review.py`
- Create: `backend/app/models/task.py`
- Create: `backend/app/models/test_case.py`
- Create: `backend/app/models/test_execution.py`
- Create: `backend/app/models/password_reset_token.py`

**参考:** `design/01-entities-and-tables.md` 全部 16 张表的字段定义

- [ ] 编写 User 模型（含 Base 类）
- [ ] 编写 Team 模型（软删除）
- [ ] 编写 TeamMember 模型（软删除，唯一约束 team_id+user_id）
- [ ] 编写 Role 模型（软删除，唯一约束 team_id+name）
- [ ] 编写 RolePermission 模型（唯一约束 role_id+permission）
- [ ] 编写 MemberRole 模型（唯一约束 member_id+role_id）
- [ ] 编写 Invitation 模型（status CHECK）
- [ ] 编写 Project 模型（软删除，status CHECK）
- [ ] 编写 Iteration 模型（status CHECK, dates CHECK）
- [ ] 编写 Requirement 模型（软删除，status CHECK, type_detail JSON）
- [ ] 编写 RequirementReview 模型（review_type CHECK, status CHECK）
- [ ] 编写 Task 模型（软删除，status CHECK）
- [ ] 编写 TestCase 模型（软删除，case_type CHECK）
- [ ] 编写 TestExecutionRound 模型
- [ ] 编写 TestExecutionRecord 模型（status CHECK）
- [ ] 编写 PasswordResetToken 模型
- [ ] 编写 __init__.py 导出所有模型
- [ ] 提交

### Task 3: 创建 MongoDB 模型

**Files:**
- Create: `backend/app/mongo_models/__init__.py`
- Create: `backend/app/mongo_models/spec_template.py`
- Create: `backend/app/mongo_models/spec_document.py`

**参考:** `design/01-entities-and-tables.md` 第4节

- [ ] 编写 SpecTemplate 文档模型
- [ ] 编写 SpecDocument 文档模型（含版本历史）
- [ ] 提交

### Task 4: 创建全部 Pydantic Schema

**Files:**
- Create: `backend/app/schemas/__init__.py`
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/schemas/team.py`
- Create: `backend/app/schemas/role.py`
- Create: `backend/app/schemas/invitation.py`
- Create: `backend/app/schemas/project.py`
- Create: `backend/app/schemas/iteration.py`
- Create: `backend/app/schemas/requirement.py`
- Create: `backend/app/schemas/specification.py`
- Create: `backend/app/schemas/task.py`
- Create: `backend/app/schemas/test_case.py`
- Create: `backend/app/schemas/test_execution.py`
- Create: `backend/app/schemas/common.py`（统一响应、分页响应模型）

**参考:** `design/02-*.md`, `03-*.md`, `04-*.md` 的请求/响应定义

- [ ] 编写 common.py（ApiResponse, PageResponse, ErrorResponse）
- [ ] 编写 auth.py（RegisterRequest, LoginRequest, VerifyEmailRequest, ForgotPasswordRequest, ResetPasswordRequest, LoginResponse）
- [ ] 编写 user.py（UserInfo, UserUpdate, PasswordChange, PendingItems）
- [ ] 编写 team.py（TeamCreate, TeamUpdate, TeamDetail, TeamMember）
- [ ] 编写 role.py（RoleCreate, RoleUpdate, RoleDetail）
- [ ] 编写 invitation.py（InviteCreate, InviteAction, InviteDetail）
- [ ] 编写 project.py（ProjectCreate, ProjectUpdate, ProjectDetail, ProjectStatistics）
- [ ] 编写 iteration.py（IterationCreate, IterationUpdate, IterationDetail, KanbanData）
- [ ] 编写 requirement.py（RequirementCreate, RequirementUpdate, RequirementDetail, ReviewSubmit, ReviewAction）
- [ ] 编写 specification.py（SpecTemplateUpdate, SpecContent, SpecVersion）
- [ ] 编写 task.py（TaskCreate, TaskUpdate, TaskDetail）
- [ ] 编写 test_case.py（TestCaseCreate, TestCaseUpdate, TestCaseDetail）
- [ ] 编写 test_execution.py（TestExecutionRecord, TestExecutionRound, TestStatistics）
- [ ] 提交

### Task 5: 创建 API 路由存根

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/router.py`
- Create: `backend/app/api/auth.py`
- Create: `backend/app/api/users.py`
- Create: `backend/app/api/admin.py`
- Create: `backend/app/api/teams.py`
- Create: `backend/app/api/team_members.py`
- Create: `backend/app/api/invitations.py`
- Create: `backend/app/api/roles.py`
- Create: `backend/app/api/projects.py`
- Create: `backend/app/api/iterations.py`
- Create: `backend/app/api/requirements.py`
- Create: `backend/app/api/specifications.py`
- Create: `backend/app/api/tasks.py`
- Create: `backend/app/api/test_cases.py`
- Create: `backend/app/api/test_executions.py`

**参考:** `design/02-*.md`, `03-*.md`, `04-*.md` 的路由定义

- [ ] 每个文件创建对应的路由端点（函数体用 raise NotImplementedError 或返回占位响应）
- [ ] router.py 注册所有子路由
- [ ] main.py include router
- [ ] 提交

### Task 6: 创建 Service 和 Utility 存根

**Files:**
- Create: `backend/app/services/__init__.py`
- Create: `backend/app/services/*.py`（13个服务文件）
- Create: `backend/app/utils/__init__.py`
- Create: `backend/app/utils/security.py`
- Create: `backend/app/utils/email.py`
- Create: `backend/app/utils/pagination.py`
- Create: `backend/app/utils/permissions.py`

- [ ] 创建所有 service 文件（空文件或空类）
- [ ] 编写 security.py（密码哈希和 JWT 生成/验证函数）
- [ ] 编写 pagination.py（分页查询工具函数）
- [ ] 编写 permissions.py（权限检查依赖）
- [ ] 编写 email.py（邮件发送存根）
- [ ] 提交

---

## Phase 2: 后端测试基础设施

### Task 7: 编写 conftest.py

**Files:**
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/conftest.py`

**参考:** 所有 API 设计文档的认证方式和数据关系

- [ ] 配置测试数据库（SQLite 内存数据库）
- [ ] 创建测试用 FastAPI TestClient fixture
- [ ] 创建用户相关 fixtures（普通用户、管理员、未验证用户、禁用用户）
- [ ] 创建团队相关 fixtures（团队、团队成员、角色、权限）
- [ ] 创建项目/迭代/需求 fixtures
- [ ] 创建认证 helper（获取认证 headers 的工具函数）
- [ ] 提交

---

## Phase 3: 后端接口测试（docs 07-11）

### Task 8: test_auth.py

**参考:** `design/07-test-cases-backend-auth-user-admin.md` 第1节（TC-AUTH-001 ~ TC-AUTH-040，共40条）

- [ ] 注册成功 / 参数校验（12条）
- [ ] 验证邮箱（6条）
- [ ] 登录（10条）
- [ ] 忘记密码（4条）
- [ ] 重置密码（8条）
- [ ] 提交

### Task 9: test_users.py

**参考:** `design/07-test-cases-backend-auth-user-admin.md` 第2节（TC-USER-001 ~ TC-USER-025，共25条）

- [ ] 获取当前用户信息（4条）
- [ ] 修改用户信息（9条）
- [ ] 修改密码（8条）
- [ ] 获取待处理事项（4条）
- [ ] 提交

### Task 10: test_admin.py

**参考:** `design/07-test-cases-backend-auth-user-admin.md` 第3节（TC-ADMIN-001 ~ TC-ADMIN-030，共30条）

- [ ] 用户列表（9条）
- [ ] 创建用户（12条）
- [ ] 启用/禁用用户（9条）
- [ ] 提交

### Task 11: test_teams.py

**参考:** `design/08-test-cases-backend-team-role.md` 第1节（TC-TEAM-001 ~ TC-TEAM-019，共19条）

- [ ] 创建团队（4条）
- [ ] 获取团队详情（3条）
- [ ] 编辑团队（4条）
- [ ] 解散团队（4条）
- [ ] 转让团队（4条）
- [ ] 提交

### Task 12: test_team_members.py

**参考:** `design/08-test-cases-backend-team-role.md` 第2节（TC-MEMBER-001 ~ TC-MEMBER-015，共15条）

- [ ] 获取成员列表（3条）
- [ ] 邀请成员（5条）
- [ ] 移出成员（4条）
- [ ] 分配角色（3条）
- [ ] 提交

### Task 13: test_invitations.py

**参考:** `design/08-test-cases-backend-team-role.md` 第3节（TC-INVITE-001 ~ TC-INVITE-007，共7条）

- [ ] 获取我的邀请（2条）
- [ ] 处理邀请（5条）
- [ ] 提交

### Task 14: test_roles.py

**参考:** `design/08-test-cases-backend-team-role.md` 第4节（TC-ROLE-001 ~ TC-ROLE-013，共13条）

- [ ] 获取角色列表（2条）
- [ ] 创建角色（4条）
- [ ] 编辑角色（4条）
- [ ] 删除角色（3条）
- [ ] 提交

### Task 15: test_projects.py

**参考:** `design/09-test-cases-backend-project-iteration.md` 项目部分

- [ ] 创建/查询/编辑/归档/删除项目测试
- [ ] 提交

### Task 16: test_iterations.py

**参考:** `design/09-test-cases-backend-project-iteration.md` 迭代部分

- [ ] 创建/查询/编辑/启动/完成迭代测试
- [ ] 看板和统计测试
- [ ] 提交

### Task 17: test_requirements.py

**参考:** `design/10-test-cases-backend-requirement-specification.md` 需求部分

- [ ] 创建/查询/编辑/删除需求测试
- [ ] 提交审核/审核操作测试
- [ ] 状态流转测试
- [ ] 提交

### Task 18: test_specifications.py

**参考:** `design/10-test-cases-backend-requirement-specification.md` 规范部分

- [ ] 规范模板 CRUD 测试
- [ ] 规范文档保存/版本管理测试
- [ ] 提交

### Task 19: test_tasks.py

**参考:** `design/11-test-cases-backend-task-test-statistics.md` 任务部分

- [ ] 创建/查询/编辑/删除任务测试
- [ ] 开始测试/完成任务测试
- [ ] 状态流转测试
- [ ] 提交

### Task 20: test_test_cases.py

**参考:** `design/11-test-cases-backend-task-test-statistics.md` 测试用例管理部分

- [ ] 创建/查询/编辑/删除测试用例测试
- [ ] 提交

### Task 21: test_test_executions.py

**参考:** `design/11-test-cases-backend-task-test-statistics.md` 测试执行部分

- [ ] 获取执行轮次/记录测试
- [ ] 更新执行记录测试
- [ ] 提交

### Task 22: test_statistics.py

**参考:** `design/11-test-cases-backend-task-test-statistics.md` 统计部分

- [ ] 需求级/迭代级/项目级统计测试
- [ ] 提交

---

## Phase 4: 前端项目骨架 + E2E 测试基础设施

### Task 23: 创建前端项目骨架

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/playwright.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/views/auth/LoginPage.vue`（+ 其他页面空组件）

**参考:** `design/06-project-structure-and-naming.md` 前端目录结构

- [ ] 初始化 Vue 3 + TypeScript 项目
- [ ] 配置 Playwright
- [ ] 创建最小页面组件（空壳）
- [ ] 提交

### Task 24: 编写 E2E 测试 fixtures

**Files:**
- Create: `frontend/tests/fixtures/auth.ts`

- [ ] 登录 fixture（通过 API 直接创建用户并登录）
- [ ] 提交

---

## Phase 5: 前端 E2E 测试（docs 12-16）

### Task 25: auth.spec.ts

**参考:** `design/12-test-cases-e2e-auth.md`（16条）

- [ ] 注册/登录/忘记密码/重置密码页面测试
- [ ] 提交

### Task 26: dashboard.spec.ts + admin-users.spec.ts

**参考:** `design/13-test-cases-e2e-dashboard-admin.md`（17条）

- [ ] 个人中心页面测试
- [ ] 管理员用户管理页面测试
- [ ] 提交

### Task 27: team.spec.ts + team-members.spec.ts + team-roles.spec.ts

**参考:** `design/14-test-cases-e2e-team-role.md`（16条）

- [ ] 团队详情/成员/角色/设置页面测试
- [ ] 提交

### Task 28: project.spec.ts + iteration.spec.ts

**参考:** `design/15-test-cases-e2e-project-iteration.md`（17条）

- [ ] 项目/迭代/看板页面测试
- [ ] 提交

### Task 29: requirement.spec.ts + task.spec.ts + test-management.spec.ts

**参考:** `design/16-test-cases-e2e-requirement-specification-task-test.md`（27条）

- [ ] 需求/规范/任务/测试管理页面测试
- [ ] 提交

---

## 文件清单总览

```
backend/
├── pyproject.toml
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── cache.py
│   ├── deps.py
│   ├── exceptions.py
│   ├── models/ (13 files)
│   ├── mongo_models/ (2 files)
│   ├── schemas/ (13 files)
│   ├── api/ (15 files)
│   ├── services/ (13 files)
│   └── utils/ (4 files)
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_*.py (14 files)

frontend/
├── package.json
├── vite.config.ts
├── tsconfig.json
├── playwright.config.ts
├── index.html
├── src/ (minimal stubs)
└── tests/
    ├── fixtures/auth.ts
    └── *.spec.ts (11 files)
```
