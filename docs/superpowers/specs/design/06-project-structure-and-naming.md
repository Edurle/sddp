# 项目目录结构规范与命名规范

## 1. 项目根目录

```
sdd/
├── backend/                # 后端（FastAPI）
├── frontend/               # 前端（Vue 3）
├── docs/                   # 文档
│   └── superpowers/
│       └── specs/          # 产品需求与设计规范
├── .gitignore
├── README.md
└── docker-compose.yml      # 开发环境编排（MySQL/MongoDB/Redis）
```

---

## 2. 后端目录结构

```
backend/
├── alembic/                # 数据库迁移
│   ├── versions/           # 迁移脚本
│   ├── env.py
│   └── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py             # FastAPI 应用入口
│   ├── config.py           # 配置管理（环境变量读取）
│   ├── database.py         # 数据库连接（MySQL/SQLite + MongoDB）
│   ├── cache.py            # 缓存管理（Redis/内存缓存）
│   ├── deps.py             # 依赖注入（获取当前用户、数据库会话等）
│   ├── models/             # SQLAlchemy ORM 模型（MySQL）
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── team.py
│   │   ├── role.py
│   │   ├── invitation.py
│   │   ├── project.py
│   │   ├── iteration.py
│   │   ├── requirement.py
│   │   ├── requirement_review.py
│   │   ├── task.py
│   │   ├── test_case.py
│   │   ├── test_execution.py
│   │   └── password_reset_token.py
│   ├── mongo_models/       # MongoDB 文档模型
│   │   ├── __init__.py
│   │   ├── spec_template.py
│   │   └── spec_document.py
│   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── team.py
│   │   ├── role.py
│   │   ├── invitation.py
│   │   ├── project.py
│   │   ├── iteration.py
│   │   ├── requirement.py
│   │   ├── specification.py
│   │   ├── task.py
│   │   ├── test_case.py
│   │   └── test_execution.py
│   ├── api/                # API 路由
│   │   ├── __init__.py
│   │   ├── router.py       # 总路由注册
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── admin.py
│   │   ├── teams.py
│   │   ├── team_members.py
│   │   ├── invitations.py
│   │   ├── roles.py
│   │   ├── projects.py
│   │   ├── iterations.py
│   │   ├── requirements.py
│   │   ├── specifications.py
│   │   ├── tasks.py
│   │   ├── test_cases.py
│   │   └── test_executions.py
│   ├── services/           # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── team.py
│   │   ├── role.py
│   │   ├── invitation.py
│   │   ├── project.py
│   │   ├── iteration.py
│   │   ├── requirement.py
│   │   ├── specification.py
│   │   ├── task.py
│   │   ├── test_case.py
│   │   ├── test_execution.py
│   │   └── statistics.py
│   ├── utils/              # 工具函数
│   │   ├── __init__.py
│   │   ├── security.py     # 密码哈希、JWT
│   │   ├── email.py        # 邮件发送
│   │   ├── pagination.py   # 分页工具
│   │   └── permissions.py  # 权限检查装饰器/依赖
│   └── exceptions.py       # 自定义异常与错误码
├── tests/                  # 测试
│   ├── conftest.py         # pytest 配置与 fixtures
│   ├── test_auth.py
│   ├── test_users.py
│   ├── test_admin.py
│   ├── test_teams.py
│   ├── test_team_members.py
│   ├── test_invitations.py
│   ├── test_roles.py
│   ├── test_projects.py
│   ├── test_iterations.py
│   ├── test_requirements.py
│   ├── test_specifications.py
│   ├── test_tasks.py
│   ├── test_test_cases.py
│   ├── test_test_executions.py
│   └── test_statistics.py
├── requirements.txt
├── pyproject.toml
└── Dockerfile
```

---

## 3. 前端目录结构

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── main.ts             # 应用入口
│   ├── App.vue             # 根组件
│   ├── router/
│   │   └── index.ts        # 路由定义
│   ├── stores/             # Pinia 状态管理
│   │   ├── auth.ts         # 登录状态与用户信息
│   │   └── team.ts         # 当前团队上下文
│   ├── api/                # API 调用封装
│   │   ├── client.ts       # axios 实例与拦截器
│   │   ├── auth.ts
│   │   ├── user.ts
│   │   ├── admin.ts
│   │   ├── team.ts
│   │   ├── invitation.ts
│   │   ├── role.ts
│   │   ├── project.ts
│   │   ├── iteration.ts
│   │   ├── requirement.ts
│   │   ├── specification.ts
│   │   ├── task.ts
│   │   ├── test-case.ts
│   │   ├── test-execution.ts
│   │   └── statistics.ts
│   ├── composables/        # 组合式函数
│   │   ├── use-permission.ts  # 权限检查
│   │   ├── use-pagination.ts  # 分页逻辑
│   │   └── use-form.ts        # 表单通用逻辑
│   ├── components/         # 可复用组件
│   │   ├── common/
│   │   │   ├── AppButton.vue
│   │   │   ├── AppInput.vue
│   │   │   ├── AppSelect.vue
│   │   │   ├── AppTable.vue
│   │   │   ├── AppPagination.vue
│   │   │   ├── AppDialog.vue
│   │   │   ├── AppForm.vue
│   │   │   ├── AppUpload.vue
│   │   │   ├── AppTabs.vue
│   │   │   ├── AppTag.vue
│   │   │   ├── AppBadge.vue
│   │   │   ├── AppBreadcrumb.vue
│   │   │   └── AppSteps.vue
│   │   ├── layout/
│   │   │   ├── AppHeader.vue
│   │   │   ├── AppSidebar.vue
│   │   │   └── AppLayout.vue
│   │   └── business/
│   │       ├── RequirementStatusTag.vue
│   │       ├── TaskStatusTag.vue
│   │       ├── RequirementCard.vue
│   │       ├── ReviewHistory.vue
│   │       └── SpecEditor.vue
│   ├── views/              # 页面组件
│   │   ├── auth/
│   │   │   ├── LoginPage.vue
│   │   │   ├── RegisterPage.vue
│   │   │   ├── ForgotPasswordPage.vue
│   │   │   └── ResetPasswordPage.vue
│   │   ├── dashboard/
│   │   │   └── DashboardPage.vue
│   │   ├── team/
│   │   │   ├── TeamDetailPage.vue
│   │   │   ├── TeamMembersTab.vue
│   │   │   ├── TeamRolesTab.vue
│   │   │   └── TeamSettingsTab.vue
│   │   ├── project/
│   │   │   ├── ProjectListTab.vue
│   │   │   └── ProjectDetailPage.vue
│   │   ├── iteration/
│   │   │   ├── IterationListTab.vue
│   │   │   └── IterationKanbanPage.vue
│   │   ├── requirement/
│   │   │   └── RequirementDetailPage.vue
│   │   ├── task/
│   │   │   └── TaskDetailPage.vue
│   │   └── admin/
│   │       └── AdminUsersPage.vue
│   ├── types/              # TypeScript 类型定义
│   │   ├── api.ts          # API 响应通用类型
│   │   ├── user.ts
│   │   ├── team.ts
│   │   ├── role.ts
│   │   ├── project.ts
│   │   ├── iteration.ts
│   │   ├── requirement.ts
│   │   ├── specification.ts
│   │   ├── task.ts
│   │   └── test.ts
│   └── utils/
│       ├── format.ts       # 格式化工具
│       ├── validate.ts     # 校验工具
│       └── constants.ts    # 常量定义
├── tests/                  # Playwright 端到端测试
│   ├── fixtures/
│   │   └── auth.ts         # 登录 fixture
│   ├── auth.spec.ts
│   ├── user.spec.ts
│   ├── admin-users.spec.ts
│   ├── team.spec.ts
│   ├── team-members.spec.ts
│   ├── team-roles.spec.ts
│   ├── project.spec.ts
│   ├── iteration.spec.ts
│   ├── requirement.spec.ts
│   ├── task.spec.ts
│   └── test-management.spec.ts
├── index.html
├── vite.config.ts
├── tsconfig.json
├── package.json
└── playwright.config.ts
```

---

## 4. 后端命名规范

### 4.1 文件命名

| 类型 | 规则 | 示例 |
|------|------|------|
| Python 模块 | 蛇形命名，小写 | `test_execution.py`, `requirement_review.py` |
| 测试文件 | `test_` 前缀 + 模块名 | `test_auth.py`, `test_requirements.py` |
| 迁移脚本 | Alembic 自动生成 | `20260418_001_create_users.py` |

### 4.2 类命名

| 类型 | 规则 | 示例 |
|------|------|------|
| ORM Model | 大驼峰，与表名对应（单数） | `User`, `TeamMember`, `RequirementReview` |
| Pydantic Schema | 大驼峰 + 用途后缀 | `UserCreate`, `UserResponse`, `RequirementUpdate` |
| Service 类 | 大驼峰 + Service 后缀 | `AuthService`, `RequirementService` |
| Exception | 大驼峰 + Error/Exception 后缀 | `BusinessError`, `PermissionDeniedError` |

### 4.3 函数与变量命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 函数/方法 | 蛇形命名 | `get_user_by_id()`, `create_requirement()` |
| 变量 | 蛇形命名 | `team_id`, `requirement_status` |
| 常量 | 全大写 + 下划线 | `MAX_PAGE_SIZE`, `DEFAULT_STATUS` |
| 私有方法 | 前缀单下划线 | `_validate_permission()` |

### 4.4 API 路由命名

| 类型 | 规则 | 示例 |
|------|------|------|
| URL 路径 | 短横线命名（kebab-case），复数名词 | `/api/v1/test-cases`, `/api/v1/test-executions` |
| 查询参数 | 蛇形命名 | `?page_size=20`, `?sort_by=priority` |
| 路径参数 | 蛇形命名 | `{team_id}`, `{req_id}` |

### 4.5 Pydantic Schema 命名约定

| 用途 | 后缀 | 示例 |
|------|------|------|
| 创建请求 | Create | `RequirementCreate` |
| 更新请求 | Update | `RequirementUpdate` |
| 响应 | Response | `RequirementResponse` |
| 列表响应 | ListResponse | `RequirementListResponse` |
| 分页响应 | PageResponse | `RequirementPageResponse` |

---

## 5. 前端命名规范

### 5.1 文件命名

| 类型 | 规则 | 示例 |
|------|------|------|
| Vue 页面组件 | 大驼峰 + Page 后缀 | `LoginPage.vue`, `ProjectDetailPage.vue` |
| Vue 通用组件 | 大驼峰 + App 前缀 | `AppButton.vue`, `AppTable.vue` |
| Vue 业务组件 | 大驼峰，语义化 | `RequirementCard.vue`, `SpecEditor.vue` |
| Vue Tab 组件 | 大驼峰 + Tab 后缀 | `TeamMembersTab.vue` |
| TypeScript 模块 | 短横线命名 | `test-case.ts`, `test-execution.ts` |
| 测试文件 | 短横线命名 + .spec.ts | `auth.spec.ts`, `team-members.spec.ts` |

### 5.2 组件内命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 组件名 | 大驼峰 | `<AppButton>`, `<RequirementCard>` |
| Props | 蛇形命名（模板中可用短横线） | `:page-size="20"` |
| Emits | 蛇形命名 | `@update-status` |
| 变量/函数 | 小驼峰 | `teamList`, `handleCreateProject()` |
| 常量 | 全大写 + 下划线 | `MAX_PAGE_SIZE` |
| 组合式函数 | use- 前缀 | `usePermission()`, `usePagination()` |
| Pinia Store | use- 前缀 + -Store 后缀 | `useAuthStore()` |

### 5.3 CSS 命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 类名 | BEM：block__element--modifier | `.kanban__card--active` |
| 作用域 | `<style scoped>` | 每个组件使用 scoped style |

### 5.4 路由命名

| 类型 | 规则 | 示例 |
|------|------|------|
| 路由路径 | 短横线命名 | `/forgot-password`, `/admin/users` |
| 路由名称 | 大驼峰 | `TeamDetail`, `IterationKanban` |

---

## 6. 数据库命名规范

| 类型 | 规则 | 示例 |
|------|------|------|
| MySQL 表名 | 蛇形命名，复数 | `team_members`, `test_execution_rounds` |
| MySQL 字段 | 蛇形命名 | `created_at`, `is_deleted`, `req_type` |
| MySQL 索引 | `idx_` 前缀 + 表名简写 + 字段 | `idx_team`, `idx_requirement` |
| MySQL 唯一索引 | `uniq_` 前缀 + 字段 | `uniq_email`, `uniq_case_number` |
| MongoDB 集合 | 蛇形命名 | `specification_templates`, `specification_documents` |
| MongoDB 字段 | 蛇形命名 | `team_id`, `current_version` |

---

## 7. Git 命名规范

### 7.1 分支命名

| 类型 | 格式 | 示例 |
|------|------|------|
| 功能 | `feature/{模块}-{描述}` | `feature/user-management` |
| 修复 | `fix/{模块}-{描述}` | `fix/auth-token-expire` |
| 测试 | `test/{模块}-{描述}` | `test/requirement-api` |

### 7.2 提交信息

格式：`{type}({scope}): {description}`

| type | 说明 |
|------|------|
| feat | 新功能 |
| fix | 修复 |
| test | 测试 |
| docs | 文档 |
| refactor | 重构 |
| chore | 构建/工具 |

示例：`feat(auth): 实现登录注册接口`

---

## 8. 环境配置

### 8.1 开发环境

| 服务 | 说明 |
|------|------|
| SQLite | 替代 MySQL，无需额外安装 |
| 内存缓存 | 替代 Redis，进程内字典实现 |
| MongoDB | 使用 Docker 或本地安装 |

### 8.2 生产环境

| 服务 | 说明 |
|------|------|
| MySQL | 主数据库 |
| Redis | 缓存 |
| MongoDB | 文档存储 |

### 8.3 配置管理

通过环境变量管理，`app/config.py` 统一读取：

```python
# 环境变量示例
DATABASE_URL=mysql+aiomysql://...
MONGO_URL=mongodb://...
REDIS_URL=redis://...
JWT_SECRET=...
SMTP_HOST=...
```

开发环境默认使用 `.env` 文件，`config.py` 中提供 SQLite 和内存缓存的 fallback。
