# SDD — Spec-Driven Development Tool

**[简体中文](./README.md)**

## Overview

SDD is a full-stack project management and spec-driven development tool. It provides a complete workflow from **Teams → Projects → Iterations → Requirements → Spec Documents → Tasks → Test Cases**, with role-based access control and multi-stage review.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), SQLite (aiosqlite), Pydantic, JWT |
| Frontend | Vue 3, TypeScript, Pinia, Vue Router, Axios, Vite |
| CLI | Python, Typer — command-line tool talking to backend API |
| Testing | pytest + pytest-asyncio (backend), Playwright (frontend E2E) |
| Database | SQLite (relational data & spec documents) |

## Features

- **Team Management** — Create teams, invite members, custom roles with fine-grained permissions
- **Projects & Iterations** — Iteration management within projects, kanban view
- **Requirement Lifecycle** — Multi-stage workflow: Draft Req → Review Req → Draft Spec → Review Spec → Draft Tests → Review Tests → Approved
- **Requirement Links** — Dependency and association management between requirements
- **Spec Documents** — Structured editor, JSON Schema content validation, version history, HTML prototype preview (iframe sandbox)
- **Task Management** — Task assignment, status tracking, auto-generated tasks, Git integration
- **Test Management** — Test case management, auto-generated test cases, test execution rounds, batch execution, pass/fail/skip records
- **Review Comments** — Comment and feedback support across multi-stage reviews
- **Permission System** — 27 fine-grained permissions, customizable roles assigned to members
- **API Keys** — Users can create API keys for programmatic access (supports Bearer Token / Cookie / X-API-Key authentication)
- **Webhooks** — Team-level webhook event notifications
- **Statistics** — Requirement, iteration, and project-level statistics
- **Admin Panel** — Admin user management (create, enable/disable)
- **CLI Tool** — `sdd` command-line tool supporting all backend API operations

## Getting Started

### Prerequisites

- Python 3.12 + Conda
- Node.js 18+

### Installation

```bash
# 1. Create conda env and install backend dependencies
conda create -n sdd python=3.12
conda activate sdd
pip install -r backend/requirements.txt

# 2. Install frontend dependencies
cd frontend && npm install && cd ..
```

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
│   │   ├── api/             # Route handlers (one file per domain)
│   │   ├── schemas/         # Pydantic request/response models
│   │   ├── services/        # Business logic
│   │   ├── models/          # SQLAlchemy ORM models
│   │   ├── deps.py          # Auth dependencies (JWT / API Key / permission checks)
│   │   ├── exceptions.py    # Business error codes
│   │   ├── cache.py         # In-memory cache (TTL)
│   │   └── config.py        # Environment config
│   ├── alembic/             # Database migrations
│   ├── tests/               # pytest tests
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/client.ts    # Axios instance + JWT interceptor
│   │   ├── stores/auth.ts   # Pinia auth store
│   │   ├── router/          # Route configuration
│   │   ├── views/           # Page components
│   │   └── components/      # Reusable UI components
│   ├── tests/               # Playwright E2E tests
│   └── package.json
├── cli/                     # CLI tool (sdd command)
│   ├── sdd_cli/             # Typer CLI implementation
│   └── pyproject.toml
├── alembic.ini              # Alembic config
└── scripts/services.sh      # Service management script
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./sdd.db` | SQLite connection string |
| `JWT_SECRET` | `dev-secret-key` | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `24` | Token expiry (hours) |
| `SDD_SEED_DATA` | `false` | Set to `true` to create seed data on startup |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | empty | Email service (password reset) |

No `.env` file needed for development — all configs have defaults.

## Requirement Workflow

```
Draft Req → Review Req → Draft Spec → Review Spec → Draft Tests → Review Tests → Approved
   ↓           ↓            ↓            ↓             ↓             ↓
   └── Rejected ←┘  └── Rejected ←┘  └── Rejected ←┘  └── Rejected ←┘
```

Each stage can be submitted for review independently. Reviewers can approve or reject with comments.
