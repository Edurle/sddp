# SDD — 规格驱动开发工具

**[English](./README.en.md)**

## 项目简介

SDD 是一个全栈项目管理和规格驱动开发工具。它提供从 **团队 → 项目 → 迭代 → 需求 → 规格文档 → 任务 → 测试用例** 的完整工作流，包含基于角色的权限控制和多阶段评审机制。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12, FastAPI, SQLAlchemy (async), PostgreSQL (asyncpg), Pydantic, jsonschema, JWT |
| 前端 | Vue 3, TypeScript, Pinia, Vue Router, Axios, Vite |
| CLI | Python, Typer — 命令行工具（`sdd`），对接后端 API |
| 测试 | pytest + pytest-asyncio (后端), Playwright (前端 E2E) |
| 数据库 | PostgreSQL（关系数据与规格文档，规格内容存为 JSONB） |

> 数据库表结构由 `init_db()` → `Base.metadata.create_all` 创建，**不使用 Alembic**。向已有表新增字段需手动执行 `ALTER TABLE`。

## 核心功能

- **团队管理** — 创建团队、邀请成员、自定义角色与权限
- **项目与迭代** — 项目下的迭代管理，看板视图
- **需求全生命周期** — 多阶段工作流：起草需求 → 评审需求 → 起草规格 → 评审规格 → 起草测试 → 评审测试 → 通过
- **需求关联** — 需求之间的依赖、关联关系管理
- **规格文档** — 结构化编辑器，JSON Schema 内容校验，版本历史，HTML 原型预览（iframe 沙箱）
- **任务管理** — 任务分配、状态跟踪、自动生成任务、Git 集成
- **测试管理** — 测试用例管理（`ui_test` / `happy_path` / `edge_case` 三类）、自动生成测试用例、测试执行轮次、批量执行、通过/失败/跳过记录
- **评审评论** — 多阶段评审中支持评论与反馈
- **权限系统** — 30 种细粒度权限，可自定义角色分配给成员
- **API Key** — 用户可创建 API Key 用于程序化访问（支持 Bearer Token / Cookie / X-API-Key 三种认证方式）
- **Webhook** — 团队级 Webhook 事件通知
- **统计** — 需求、迭代、项目级别的统计数据
- **管理后台** — 管理员用户管理（创建、启用/禁用）
- **CLI 工具** — `sdd` 命令行工具，支持所有后端 API 操作（使用指南见 [`docs/cli-guide.md`](./docs/cli-guide.md)）

## 快速开始

### 环境要求

- Python 3.12 + Conda
- Node.js 18+
- PostgreSQL（需预先创建数据库并配置连接串）

### 安装

```bash
# 1. 创建 conda 环境并安装后端依赖
conda create -n sdd python=3.12
conda activate sdd
pip install -r backend/requirements.txt

# 2. 安装前端依赖
cd frontend && npm install && cd ..

# 3.（可选）安装 CLI 工具
pip install -e cli
```

> 后端通过仓库根目录的 `.env` 读取配置，至少需要设置 `DATABASE_URL` 指向可用的 PostgreSQL 数据库（参考 `.env.example`）。

### 运行

```bash
# 使用脚本一键启动（推荐）
./scripts/services.sh start

# 或分别启动
./scripts/services.sh start-be   # 后端 http://localhost:8000
./scripts/services.sh start-fe   # 前端 http://localhost:5173
```

访问 http://localhost:5173 即可使用。

### 种子数据

设置环境变量 `SDD_SEED_DATA=true` 后启动，将自动创建测试账号和示例团队/项目数据：

| 邮箱 | 密码 | 角色 |
|------|------|------|
| `admin@example.com` | `Admin1234!` | 管理员 |
| `exist@example.com` | `Password123` | 普通用户 |

## 常用命令

```bash
# 后端测试
conda run -n sdd python -m pytest backend/tests/ -v

# 单个测试文件
conda run -n sdd python -m pytest backend/tests/test_requirements.py -v

# 单个测试函数
conda run -n sdd python -m pytest backend/tests/test_requirements.py::test_create_requirement -v

# 前端类型检查 + 构建
cd frontend && npx vue-tsc -b && npx vite build

# 前端 E2E 测试（需先启动服务）
./scripts/services.sh start && ./scripts/services.sh e2e

# 运行指定 E2E 测试
./scripts/services.sh e2e -- tests/auth.spec.ts

# 查看日志
./scripts/services.sh logs-be
./scripts/services.sh logs-fe

# 服务管理
./scripts/services.sh status
./scripts/services.sh stop
./scripts/services.sh restart
```

## 项目结构

```
sdd/
├── backend/
│   ├── app/
│   │   ├── api/             # 路由（每个文件对应一个领域，经 router.py 挂载到 /api/v1）
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   ├── services/        # 业务逻辑（含 path_utils.py 路径解析工具）
│   │   ├── models/          # SQLAlchemy ORM 模型（各自独立文件，__init__.py 统一导出）
│   │   ├── utils/           # 工具（permissions.py 定义全部权限常量等）
│   │   ├── deps.py          # 认证依赖（JWT / Cookie / X-API-Key / 权限校验）
│   │   ├── exceptions.py    # 业务错误码
│   │   ├── cache.py         # 内存缓存（TTL）
│   │   ├── database.py      # init_db / create_all（无 Alembic）
│   │   └── config.py        # 环境配置
│   ├── tests/               # pytest 测试
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts    # Axios 实例 + JWT 拦截器
│   │   ├── stores/          # Pinia 状态
│   │   ├── router/          # 路由配置
│   │   ├── views/           # 页面组件
│   │   └── components/      # 通用 UI 组件
│   ├── tests/               # Playwright E2E 测试
│   └── package.json
├── cli/                     # CLI 工具（sdd 命令，package sdd-cli）
│   ├── sdd_cli/             # Typer CLI 实现
│   └── pyproject.toml
├── docs/cli-guide.md        # CLI 使用指南
└── scripts/services.sh      # 服务管理脚本
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+asyncpg://localhost/sdd` | PostgreSQL 连接字符串 |
| `TEST_DATABASE_URL` | 空 | 测试库连接串（运行后端测试时使用） |
| `JWT_SECRET` | `dev-secret-key` | JWT 签名密钥 |
| `JWT_ALGORITHM` | `HS256` | JWT 签名算法 |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `24` | Token 过期时间（小时） |
| `REMEMBER_TOKEN_EXPIRE_DAYS` | `30` | “记住我” Token 过期天数 |
| `SDD_SEED_DATA` | `false` | 设为 `true` 启动时创建种子数据 |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | 空 / `587` | 邮件服务（密码重置） |

配置从仓库根目录的 `.env` 读取（见 `.env.example`）。除 `DATABASE_URL` 需指向可用的 PostgreSQL 外，其余变量均有默认值。

## 需求工作流

```
起草需求 → 评审需求 → 起草规格 → 评审规格 → 起草测试 → 评审测试 → 通过
   ↓          ↓          ↓          ↓          ↓          ↓
   └── 驳回 ←─┘  └── 驳回 ←─┘  └── 驳回 ←─┘  └── 驳回 ←─┘
```

每个阶段可独立提交评审，评审人可批准或驳回并附评语。通过（`approved`）后的需求可进一步标记为废弃（`deprecated`）。

规格阶段支持**草稿机制**：编辑会先写入 `draft_content`，通过 JSON Schema 整体校验后再提交为新版本（version+1），可随时丢弃草稿。
