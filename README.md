# SDD — 规格驱动开发工具

**[English](./README.en.md)**

## 项目简介

SDD 是一个全栈项目管理和规格驱动开发工具。它提供从 **团队 → 项目 → 迭代 → 需求 → 规格文档 → 任务 → 测试用例** 的完整工作流，包含基于角色的权限控制和多阶段评审机制。

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12, FastAPI, SQLAlchemy (async), SQLite (aiosqlite), Pydantic, JWT |
| 前端 | Vue 3, TypeScript, Pinia, Vue Router, Axios, Vite |
| 测试 | pytest + pytest-asyncio (后端), Playwright (前端 E2E) |
| 数据库 | SQLite（关系数据与规格文档） |

## 核心功能

- **团队管理** — 创建团队、邀请成员、自定义角色与权限
- **项目与迭代** — 项目下的迭代管理，看板视图
- **需求全生命周期** — 多阶段工作流：起草需求 → 评审需求 → 起草规格 → 评审规格 → 起草测试 → 评审测试 → 通过
- **规格文档** — 结构化编辑器，JSON Schema 内容校验，版本历史，HTML 原型预览（iframe 沙箱）
- **任务管理** — 任务分配、状态跟踪、开始编码/测试/完成
- **测试管理** — 测试用例管理、测试执行轮次、通过/失败/跳过记录
- **权限系统** — 23 种细粒度权限，可自定义角色分配给成员
- **管理后台** — 管理员用户管理（创建、启用/禁用）

## 快速开始

### 环境要求

- Python 3.12 + Conda
- Node.js 18+

### 安装

```bash
# 1. 创建 conda 环境并安装后端依赖
conda create -n sdd python=3.12
conda activate sdd
pip install -r backend/requirements.txt

# 2. 安装前端依赖
cd frontend && npm install && cd ..
```

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

后端启动时自动创建测试账号：

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

# 前端类型检查 + 构建
cd frontend && npx vue-tsc -b && npx vite build

# 前端 E2E 测试（需先启动服务）
./scripts/services.sh start && ./scripts/services.sh e2e

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
│   │   ├── api/             # 路由（每个文件对应一个领域）
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   ├── services/        # 业务逻辑
│   │   ├── models/          # SQLAlchemy ORM 模型
│   │   ├── deps.py          # 认证依赖（JWT、权限校验）
│   │   ├── exceptions.py    # 业务错误码
│   │   └── config.py        # 环境配置
│   ├── tests/               # pytest 测试
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts    # Axios 实例 + JWT 拦截器
│   │   ├── stores/auth.ts   # Pinia 认证状态
│   │   ├── router/          # 路由配置
│   │   ├── views/           # 页面组件
│   │   └── components/      # 通用 UI 组件
│   ├── tests/               # Playwright E2E 测试
│   └── package.json
└── scripts/services.sh      # 服务管理脚本
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./sdd.db` | SQLite 连接字符串 |
| `JWT_SECRET` | `dev-secret-key` | JWT 签名密钥 |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `24` | Token 过期时间（小时） |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | 空 | 邮件服务（密码重置） |

开发环境无需 `.env` 文件，所有配置均有默认值。

## 需求工作流

```
起草需求 → 评审需求 → 起草规格 → 评审规格 → 起草测试 → 评审测试 → 通过
   ↓          ↓          ↓          ↓          ↓          ↓
   └── 驳回 ←─┘  └── 驳回 ←─┘  └── 驳回 ←─┘  └── 驳回 ←─┘
```

每个阶段可独立提交评审，评审人可批准或驳回并附评语。
