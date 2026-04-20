# 规范驱动开发平台 — 项目进度总结

## 1. 项目概述

规范驱动开发平台是一个面向团队的项目管理工具。核心特色是将开发流程模板化：需求经过「编写需求→编写规范→编写测试用例」三步审核后拆分任务，每个任务经过「未开始→编码→测试→完成」。规范是给 AI 编程智能体看的结构化文档。

**技术栈**：后端 FastAPI（MySQL+MongoDB，开发环境用 SQLite），前端 Vue 3，测试 pytest+Playwright。

---

## 2. 开发流程

本项目按规范驱动开发模式推进，共 8 个步骤：

1. ✅ 编写产品需求
2. ✅ 制定实体和表、后端接口、前端页面结构
3. ✅ 编写项目目录结构规范和命名规范
4. ✅ 编写后端接口测试用例
5. ✅ 编写端到端测试用例
6. ✅ 编写测试代码
7. ⬜ 逐步实现需求（分阶段，每阶段测试通过后进入下一阶段）
8. ⬜ 需求冲突时：修改需求→修改测试用例→修改测试代码→修改代码

---

## 3. 已完成的工作

### 步骤 1：产品需求（已完成）

**文件**：`docs/superpowers/specs/2026-04-18-sdd-platform-requirements.md`

**核心决策**：
- 规范 = 模板化开发流程，固定步骤模板
- 规范作用在团队级别
- 规范是给 AI 编程智能体看的结构化文档
- 需求可拆分为任务，每个任务独立走流程
- 需求阶段每步（需求/规范/测试用例）都需要独立审核，审核通过后不可修改
- 权限：自定义角色 + 权限项
- 迭代：完整 Sprint 模式

**9 大功能模块**：

| 模块 | 核心功能 |
|------|----------|
| 用户管理 | 注册/登录/找回密码/修改信息/平台管理员创建用户 |
| 团队管理 | CRUD/邀请/转让/解散 |
| 项目管理 | CRUD/归档/开始日期手动设/结束日期自动取 |
| 迭代管理 | Sprint 模式/看板/统计/完成验证 |
| 需求管理 | 三步审核流程/类型详情(功能/优化/缺陷)/状态流转 |
| 规范管理 | 团队级模板+需求级文档/版本历史 |
| 任务管理 | pending→coding→testing→completed/测试不通过退回 |
| 测试管理 | 用例管理+执行记录/多维统计 |
| 权限管理 | 自定义角色+权限项/内置角色/平台管理员 |

**核心工作流**：
```
需求阶段：编写需求 → 审核 → 编写规范 → 审核 → 编写测试用例 → 审核 → 已通过
任务阶段：未开始 → 编写代码 → 执行测试 → 已完成
```

### 步骤 2：实体/表/接口/页面设计（已完成）

**设计文档**：

| 文件 | 内容 |
|------|------|
| `design/01-entities-and-tables.md` | 16 张 MySQL 表 + 2 个 MongoDB 集合 |
| `design/02-api-auth-user-team-role.md` | 认证/用户/管理员/团队/角色 API |
| `design/03-api-project-iteration-requirement-specification.md` | 项目/迭代/需求/规范 API |
| `design/04-api-task-test-statistics.md` | 任务/测试用例/执行/统计 API |
| `design/05-frontend-pages.md` | 17 个页面的布局和元素编码 |

**关键设计决策**：
- 软删除：所有支持删除的表使用 `is_deleted` + `deleted_at`
- 逻辑外键：SQL DDL 不写 FOREIGN KEY 约束，仅文档标注关系
- 任务状态新增 `pending`（未开始）
- 统一响应格式：`{ code, message, data }`
- 前端元素编码：`{页面编码}-{元素类型}-{名称}`，用于 E2E 测试定位

**实体层级**：
```
团队 → 项目 → 迭代 → 需求 → 任务
                ↕         ↕
           规范模板(团队级) 规范文档(需求级)
```

### 步骤 3：目录结构和命名规范（已完成）

**文件**：`design/06-project-structure-and-naming.md`

**内容**：
- 后端四层架构：models → schemas → services → api
- 前端分层：views / composables / api / stores / types / components(common/business)
- 命名规范：后端蛇形、前端短横线/大驼峰、数据库蛇形复数
- Git 规范：feature/fix/test 分支，feat/fix/test/docs 提交前缀
- 环境配置：开发 SQLite+内存缓存 fallback，生产 MySQL+Redis+MongoDB

### 步骤 4：后端接口测试用例（已完成）

| 文件 | 模块 | 用例数 |
|------|------|--------|
| `design/07-test-cases-backend-auth-user-admin.md` | 认证/用户/管理员 | ~87 |
| `design/08-test-cases-backend-team-role.md` | 团队/成员/邀请/角色 | ~40 |
| `design/09-test-cases-backend-project-iteration.md` | 项目/迭代 | ~47 |
| `design/10-test-cases-backend-requirement-specification.md` | 需求/规范 | ~54 |
| `design/11-test-cases-backend-task-test-statistics.md` | 任务/测试/统计 | ~58 |

**总计 ~286 条后端测试用例**，覆盖正常流程、参数校验、权限不足、状态流转、软删除等场景。

### 步骤 5：端到端测试用例（已完成）

| 文件 | 页面模块 | 用例数 |
|------|----------|--------|
| `design/12-test-cases-e2e-auth.md` | 注册/登录/忘记密码/重置密码 | 16 |
| `design/13-test-cases-e2e-dashboard-admin.md` | 个人中心/管理员用户管理 | 17 |
| `design/14-test-cases-e2e-team-role.md` | 团队详情/成员/角色/设置 | 16 |
| `design/15-test-cases-e2e-project-iteration.md` | 项目/迭代/看板 | 17 |
| `design/16-test-cases-e2e-requirement-specification-task-test.md` | 需求/规范/任务/测试 | 27 |

**总计 93 条 E2E 测试用例**，每条包含前置条件、操作步骤（使用元素编码）、验证方式。

---

## 4. 文件清单

```
docs/superpowers/
├── specs/
│   ├── 2026-04-18-sdd-platform-requirements.md          # 产品需求文档
│   ├── project-progress.md                               # 项目进度总结
│   └── design/
│       ├── 01-entities-and-tables.md                     # 数据库设计（MySQL+MongoDB）
│       ├── 02-api-auth-user-team-role.md                 # API 设计：认证/用户/团队/角色
│       ├── 03-api-project-iteration-requirement-specification.md
│       ├── 04-api-task-test-statistics.md                # API 设计：任务/测试/统计
│       ├── 05-frontend-pages.md                          # 前端页面结构与元素编码
│       ├── 06-project-structure-and-naming.md            # 目录结构与命名规范
│       ├── 07-test-cases-backend-auth-user-admin.md      # 后端测试用例：认证/用户/管理员
│       ├── 08-test-cases-backend-team-role.md             # 后端测试用例：团队/角色
│       ├── 09-test-cases-backend-project-iteration.md     # 后端测试用例：项目/迭代
│       ├── 10-test-cases-backend-requirement-specification.md
│       ├── 11-test-cases-backend-task-test-statistics.md  # 后端测试用例：任务/测试
│       ├── 12-test-cases-e2e-auth.md                      # E2E 测试用例：认证页面
│       ├── 13-test-cases-e2e-dashboard-admin.md           # E2E 测试用例：个人中心/管理员
│       ├── 14-test-cases-e2e-team-role.md                 # E2E 测试用例：团队/角色
│       ├── 15-test-cases-e2e-project-iteration.md         # E2E 测试用例：项目/迭代
│       └── 16-test-cases-e2e-requirement-specification-task-test.md
└── plans/
    └── 2026-04-19-write-all-tests.md                     # 测试编写实施计划

backend/
├── pyproject.toml
├── requirements.txt
├── app/
│   ├── main.py, config.py, database.py, cache.py, deps.py, exceptions.py
│   ├── models/ (13 files, 16 ORM models)
│   ├── mongo_models/ (2 files, 2 document models)
│   ├── schemas/ (14 files, all request/response schemas)
│   ├── api/ (14 files, 71 route endpoints)
│   ├── services/ (14 files, stubs)
│   └── utils/ (5 files, security/pagination/permissions/email)
└── tests/
    ├── conftest.py (fixtures + auth helpers)
    └── test_*.py (14 files, 325 tests)

frontend/
├── package.json, vite.config.ts, tsconfig.json, playwright.config.ts
├── src/
│   ├── main.ts, App.vue, env.d.ts
│   ├── router/index.ts (11 routes)
│   ├── stores/auth.ts, api/client.ts
│   └── views/ (16 page components with data-testid)
└── tests/
    ├── fixtures/auth.ts
    └── *.spec.ts (11 files, 144 tests)
```

---

## 5. 后续工作

### 步骤 6：编写测试代码（已完成）

**后端项目骨架**（FastAPI 四层架构）已搭建完成，包含：
- 配置管理（SQLite fallback）、异步数据库、缓存、JWT 认证、权限检查
- 16 个 SQLAlchemy 模型 + 2 个 MongoDB 文档模型
- 14 个 Pydantic Schema 文件（请求/响应模型）
- 71 个 API 路由端点存根（函数体 raise NotImplementedError）
- 13 个 Service 空文件 + 工具函数

**后端测试**（pytest）：14 个文件，共 **325 条**测试用例

| 文件 | 用例数 | 对应规范 |
|------|--------|----------|
| `backend/tests/conftest.py` | fixtures | 测试数据库 + 用户/团队/项目等 fixtures |
| `backend/tests/test_auth.py` | 40 | TC-AUTH-001~040 |
| `backend/tests/test_users.py` | 25 | TC-USER-001~025 |
| `backend/tests/test_admin.py` | 30 | TC-ADMIN-001~030 |
| `backend/tests/test_teams.py` | 19 | TC-TEAM-001~019 |
| `backend/tests/test_team_members.py` | 15 | TC-MEMBER-001~015 |
| `backend/tests/test_invitations.py` | 7 | TC-INVITE-001~007 |
| `backend/tests/test_roles.py` | 13 | TC-ROLE-001~013 |
| `backend/tests/test_projects.py` | 25 | 项目 API 测试 |
| `backend/tests/test_iterations.py` | 26 | 迭代 API 测试 |
| `backend/tests/test_requirements.py` | 46 | 需求 API 测试 |
| `backend/tests/test_specifications.py` | 18 | 规范 API 测试 |
| `backend/tests/test_tasks.py` | 28 | 任务 API 测试 |
| `backend/tests/test_test_cases.py` | 14 | 测试用例管理 API 测试 |
| `backend/tests/test_test_executions.py` | 10 | 测试执行 API 测试 |
| `backend/tests/test_statistics.py` | 9 | 统计 API 测试 |

**前端项目骨架**（Vue 3 + TypeScript）已搭建完成，包含：
- Vite 配置、TypeScript 配置、Playwright 配置
- 11 个路由页面（带 data-testid 元素编码）
- Pinia auth store + Axios API client
- Playwright 登录 fixture

**前端 E2E 测试**（Playwright）：11 个文件，共 **144 条**测试用例

| 文件 | 用例数 | 对应规范 |
|------|--------|----------|
| `frontend/tests/auth.spec.ts` | 24 | 注册/登录/忘记密码/重置密码 |
| `frontend/tests/dashboard.spec.ts` | 8 | 个人中心 |
| `frontend/tests/admin-users.spec.ts` | 10 | 管理员用户管理 |
| `frontend/tests/team.spec.ts` | 13 | 团队详情/设置 |
| `frontend/tests/team-members.spec.ts` | 12 | 成员管理 |
| `frontend/tests/team-roles.spec.ts` | 9 | 角色管理 |
| `frontend/tests/project.spec.ts` | 9 | 项目管理 |
| `frontend/tests/iteration.spec.ts` | 12 | 迭代/看板 |
| `frontend/tests/requirement.spec.ts` | 17 | 需求/规范 |
| `frontend/tests/task.spec.ts` | 14 | 任务详情/执行 |
| `frontend/tests/test-management.spec.ts` | 16 | 测试用例/执行/统计 |

> 所有测试当前均失败（路由返回 NotImplementedError），等待步骤 7 实现后逐步通过。

### 步骤 7：逐步实现需求

按优先级分阶段实现，每阶段完成后运行测试，全部通过后进入下一阶段：

**阶段 1 — 基础架构与用户系统**
- 项目脚手架（前后端目录、配置、数据库迁移）
- 用户管理（注册/登录/Token/找回密码）
- 权限框架（角色/权限项/权限检查中间件）

**阶段 2 — 团队管理**
- 团队 CRUD
- 成员邀请与移出
- 角色管理

**阶段 3 — 项目与迭代**
- 项目 CRUD 与归档
- 迭代 CRUD 与状态流转
- 迭代看板

**阶段 4 — 核心工作流**
- 需求管理（三步审核流程）
- 规范管理（模板+文档+版本）
- 测试用例管理

**阶段 5 — 任务与测试执行**
- 任务管理（pending→coding→testing→completed）
- 测试执行与记录
- 统计功能

**阶段 6 — 复用组件与体验优化**
- 前端通用组件精化（按钮/弹窗/表格/分页器等）
- 管理员用户管理页面

### 步骤 8：需求冲突处理

当实现过程中发现需求冲突或遗漏时：
1. 修改产品需求文档
2. 修改相关测试用例
3. 修改测试代码
4. 修改实现代码
5. 重新运行测试确认通过
