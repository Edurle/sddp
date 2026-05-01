# SDD — Spec-Driven Development Tool

**[简体中文](./README.md)**

## Overview

SDD is a full-stack project management and spec-driven development tool. It provides a complete workflow from **Teams → Projects → Iterations → Requirements → Spec Documents → Tasks → Test Cases**, with role-based access control and multi-stage review.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12, FastAPI, SQLAlchemy (async), SQLite (aiosqlite), Motor/MongoDB, Pydantic, JWT |
| Frontend | Vue 3, TypeScript, Pinia, Vue Router, Axios, Vite |
| Testing | pytest + pytest-asyncio (backend), Playwright (frontend E2E) |
| Database | SQLite (relational data) + MongoDB (spec documents & templates) |

## Features

- **Team Management** — Create teams, invite members, custom roles with fine-grained permissions
- **Projects & Iterations** — Iteration management within projects, kanban view
- **Requirement Lifecycle** — Multi-stage workflow: Draft Req → Review Req → Draft Spec → Review Spec → Draft Tests → Review Tests → Approved
- **Spec Documents** — Structured editor, JSON Schema content validation, version history, HTML prototype preview (iframe sandbox)
- **Task Management** — Task assignment, status tracking, start coding/testing/complete
- **Test Management** — Test case management, test execution rounds, pass/fail/skip records
- **Permission System** — 23 fine-grained permissions, customizable roles assigned to members
- **Admin Panel** — Admin user management (create, enable/disable)

## Getting Started

### Prerequisites

- Python 3.12 + Conda
- Node.js 18+
- MongoDB (spec document storage, default `localhost:27017`)

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

Test accounts are auto-created on startup:

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

# Frontend typecheck + build
cd frontend && npx vue-tsc -b && npx vite build

# Frontend E2E tests (services must be running)
./scripts/services.sh start && ./scripts/services.sh e2e

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
│   │   ├── mongo_models/    # Motor/MongoDB document models
│   │   ├── deps.py          # Auth dependencies (JWT, permission checks)
│   │   ├── exceptions.py    # Business error codes
│   │   └── config.py        # Environment config
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
└── scripts/services.sh      # Service management script
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./test.db` | SQLite connection string |
| `MONGO_URL` | `mongodb://localhost:27017` | MongoDB connection string |
| `JWT_SECRET` | `dev-secret-key` | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_HOURS` | `24` | Token expiry (hours) |
| `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD` | empty | Email service (password reset) |

No `.env` file needed for development — all configs have defaults.

## Requirement Workflow

```
Draft Req → Review Req → Draft Spec → Review Spec → Draft Tests → Review Tests → Approved
   ↓           ↓            ↓            ↓             ↓             ↓
   └── Rejected ←┘  └── Rejected ←┘  └── Rejected ←┘  └── Rejected ←┘
```

Each stage can be submitted for review independently. Reviewers can approve or reject with comments.
