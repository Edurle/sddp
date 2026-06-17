# SDD — Spec-Driven Development Tool

**[简体中文](./README.md)**

## Overview

SDD is a full-stack project management and spec-driven development tool. It provides a complete workflow from **Teams → Projects → Iterations → Requirements → Spec Documents → Tasks → Test Cases**, with role-based access control and multi-stage review.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), PostgreSQL (asyncpg), Pydantic, jsonschema, JWT |
| Frontend | Vue 3, TypeScript, Pinia, Vue Router, Axios, Vite |
| CLI | Python, Typer — command-line tool (`sdd`) talking to backend API |
| Testing | pytest + pytest-asyncio (backend), Playwright (frontend E2E) |
| Database | PostgreSQL (relational data & spec documents; spec content stored as JSONB) |

> The schema is created by `init_db()` → `Base.metadata.create_all`. **Alembic is not used** — adding a column to an existing table requires a manual `ALTER TABLE`.

## Features

- **Team Management** — Create teams, invite members, custom roles with fine-grained permissions
- **Projects & Iterations** — Iteration management within projects, kanban view
- **Requirement Lifecycle** — Multi-stage workflow: Draft Req → Review Req → Draft Spec → Review Spec → Draft Tests → Review Tests → Approved
- **Requirement Links** — Dependency and association management between requirements
- **Spec Documents** — Structured editor, JSON Schema content validation, version history, HTML prototype preview (iframe sandbox)
- **Task Management** — Task assignment, status tracking, auto-generated tasks, Git integration
- **Test Management** — Test case management (`ui_test` / `happy_path` / `edge_case` categories), auto-generated test cases, test execution rounds, batch execution, pass/fail/skip records
- **Review Comments** — Comment and feedback support across multi-stage reviews
- **Permission System** — 30 fine-grained permissions, customizable roles assigned to members
- **API Keys** — Users can create API keys for programmatic access (supports Bearer Token / Cookie / X-API-Key authentication)
- **Webhooks** — Team-level webhook event notifications
- **Statistics** — Requirement, iteration, and project-level statistics
- **Admin Panel** — Admin user management (create, enable/disable)
- **CLI Tool** — `sdd` command-line tool supporting all backend API operations (usage guide: [`docs/cli-guide.md`](./docs/cli-guide.md))

## Getting Started

### Prerequisites

- Python 3.12 + Conda
- Node.js 18+
- PostgreSQL (create a database and configure the connection string first)

### Installation

```bash
# 1. Create conda env and install backend dependencies
conda create -n sdd python=3.12
conda activate sdd
pip install -r backend/requirements.txt

# 2. Install frontend dependencies
cd frontend && npm install && cd ..

# 3. (Optional) Install the CLI tool
pip install -e cli
```

> The backend reads configuration from `.env` at the repo root. At minimum set `DATABASE_URL` to a reachable PostgreSQL database (see `.env.example`).

### Running

```bash
# Start both services (recommended)
./scripts/services.sh start

# Or start individually
./scripts/services.sh start-be   # Backend http://localhost:8000
./scripts/services.sh start-fe   # Frontend http://localhost:5173
```

Visit http://localhost:5173 to use the app.

### Seed Data

Set the environment variable `SDD_SEED_DATA=true` before starting to auto-create test accounts and sample team/project data:

| Email | Password | Role |
|-------|----------|------|
| `admin@example.com` | `Admin1234!` | Admin |
| `exist@example.com` | `Password123` | Normal user |

## Common Commands

```bash
# Backend tests
conda run -n sdd python -m pytest backend/tests/ -v

# Single test file
conda run -n sdd python -m pytest backend/tests/test_requirements.py -v

# Single test function
conda run -n sdd python -m pytest backend/tests/test_requirements.py::test_create_requirement -v

# Frontend typecheck + build
cd frontend && npx vue-tsc -b && npx vite build

# Frontend E2E tests (services must be running)
./scripts/services.sh start && ./scripts/services.sh e2e

# Run specific E2E spec
./scripts/services.sh e2e -- tests/auth.spec.ts

# View logs
./scripts/services.sh logs-be
./scripts/services.sh logs-fe

# Service management
./scripts/services.sh status
./scripts/services.sh stop
./scripts/services.sh restart
```

## Project Structure

```
sdd/
├── backend/
│   ├── app/
│   │   ├── api/             # Route handlers (one file per domain, mounted under /api/v1)
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # Business logic (incl. path_utils.py path resolver)
│   │   ├── models/          # SQLAlchemy ORM models (one per file, re-exported in __init__.py)
│   │   ├── utils/           # Utilities (permissions.py defines all permission constants, etc.)
│   │   ├── deps.py          # Auth dependencies (JWT / Cookie / X-API-Key / permission checks)
│   │   ├── exceptions.py    # Business error codes
│   │   ├── cache.py         # In-memory cache (TTL)
│   │   ├── database.py      # init_db / create_all (no Alembic)
│   │   └── config.py        # Environment config
│   ├── tests/               # pytest tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts    # Axios instance + JWT interceptor
│   │   ├── stores/          # Pinia stores
│   │   ├── router/          # Route configuration
│   │   ├── views/           # Page components
│   │   └── components/      # Reusable UI components
│   ├── tests/               # Playwright E2E tests
│   └── package.json
├── cli/                     # CLI tool (sdd command, package sdd-cli)
│   ├── sdd_cli/             # Typer CLI implementation
│   └── pyproject.toml
├── docs/cli-guide.md        # CLI usage guide
└── scripts/services.sh      # Service management script
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://localhost/sdd` | PostgreSQL connection string |
| `TEST_DATABASE_URL` | empty | Test database connection string (used by backend tests) |
| `JWT_SECRET` | `dev-secret-key` | JWT signing secret |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `24` | Token expiry (hours) |
| `REMEMBER_TOKEN_EXPIRE_DAYS` | `30` | "Remember me" token expiry (days) |
| `SDD_SEED_DATA` | `false` | Set to `true` to create seed data on startup |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | empty / `587` | Email service (password reset) |

Configuration is read from `.env` at the repo root (see `.env.example`). All variables have defaults except `DATABASE_URL`, which must point to a reachable PostgreSQL database.

## Requirement Workflow

```
Draft Req → Review Req → Draft Spec → Review Spec → Draft Tests → Review Tests → Approved
   ↓           ↓            ↓            ↓             ↓             ↓
   └── Rejected ←┘  └── Rejected ←┘  └── Rejected ←┘  └── Rejected ←┘
```

Each stage can be submitted for review independently. Reviewers can approve or reject with comments. An approved requirement can be further marked as `deprecated`.

The spec stage supports a **draft mechanism**: edits are written to `draft_content` first, validated against the JSON Schema as a whole, then committed as a new version (version+1); the draft can be discarded at any time.
