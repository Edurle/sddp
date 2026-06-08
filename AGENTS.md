# SDD — Spec-Driven Development Tool

## Architecture

Monorepo with three packages:

- **`backend/`** — Python 3.12, FastAPI, SQLAlchemy async (SQLite via aiosqlite), Pydantic, `jsonschema`. Runs on port 8000.
- **`frontend/`** — Vue 3 + TypeScript, Pinia, Vue Router, Axios, Vite. `@` alias → `src/`. Dev server proxies `/api` → `localhost:8000`. Runs on port 5173.
- **`cli/`** — Python CLI (`sdd`) using Typer. Talks to backend API. Installed separately (`cli/pyproject.toml`).
- **`scripts/services.sh`** — manages both services (start/stop/restart/status/e2e/logs). Backend uses `conda run -n sdd`.

### Backend structure

| Layer | Directory | Pattern |
|-------|-----------|---------|
| Routes | `app/api/` | One file per domain, mounted via `app/api/router.py` under `/api/v1/...` |
| Schemas | `app/schemas/` | Pydantic request/response models |
| Services | `app/services/` | Business logic, called from routes |
| SQL models | `app/models/` | Each model in its own file, all re-exported from `__init__.py` |
| Auth | `app/deps.py` | `get_current_user` (JWT Bearer, cookie, or X-API-Key header), `require_permission`, `require_admin` |
| Cache | `app/cache.py` | In-memory `Cache` class with TTL. `cache_instance` is module-level singleton, cleared by `conftest.py` and `init_db`. |

Tests use the real SQLite DB (not in-memory) — `conftest.py` creates sessions against the configured `DATABASE_URL`, then TRUNCATEs all tables after each test. `autouse` fixture in `backend/conftest.py` clears the in-memory cache between tests.

### Frontend structure

- Entry: `src/main.ts` → `App.vue` → router
- API client: `src/api/client.ts` — axios with JWT interceptor, API responses wrapped in `{ code, message, data }` (code `0` = success)
- Views: `src/views/{admin,auth,dashboard,iteration,profile,project,requirement,task,team}/`
- Auth guard on `/admin/*` routes checks `is_admin` in JWT payload
- E2E tests: Playwright in `frontend/tests/`, 13 spec files

## Commands

```bash
# Backend tests (from repo root)
conda run -n sdd python -m pytest backend/tests/ -v

# Single test file
conda run -n sdd python -m pytest backend/tests/test_requirements.py -v

# Single test function
conda run -n sdd python -m pytest backend/tests/test_requirements.py::test_create_requirement -v

# Frontend typecheck + build
cd frontend && npx vue-tsc -b && npx vite build

# Frontend E2E (needs both services running)
./scripts/services.sh start && ./scripts/services.sh e2e

# Run specific E2E spec
./scripts/services.sh e2e -- tests/auth.spec.ts

# Service management
./scripts/services.sh start       # both
./scripts/services.sh start-be    # backend only
./scripts/services.sh status
./scripts/services.sh logs-be     # tail backend logs
./scripts/services.sh logs-fe     # tail frontend logs
```

## Environment

- Python packages managed via conda env `sdd` — always use `conda run -n sdd` for Python commands
- ruff linting uses conda env `ruff`
- Backend dependencies: `backend/requirements.txt` (installed into conda env)
- Frontend: `npm install` in `frontend/`
- No `.env` file required for dev — defaults in `app/config.py` use local SQLite (`sdd.db`)
- Seed data only created when `SDD_SEED_DATA=true` env var is set (not default)
- Alembic migrations in `backend/alembic/versions/`, config at root `alembic.ini`

## Conventions

- **API error responses**: All errors use `{ code, message, data }`. Business errors use numeric codes from `app/exceptions.py` (e.g. `40001` = validation, `40100` = unauthorized, `40300` = forbidden, `40400` = not found). Success = `code: 0`. BusinessErrors return HTTP 200 with error code in body.
- **BusinessError**: takes `(code, message, errors=[])`. When `errors` is populated (e.g. schema validation failures), the error handler returns them in `data`.
- **CSS: Button styling**: Global `button` in `main.css` sets `background: #111; color: #fff`. Any scoped override with a light `background` MUST also set `color` to a dark value. Always set both together.
- **Spec content validation**: `save_spec_document` validates content against JSON Schemas defined in `specification.py`'s `DEFAULT_SECTIONS`. Each section defines `json_schema` on its fields. Uses `jsonschema` library.
- **No code comments** in implementation files unless explicitly requested.
- **No Docker**: 除正式部署外，禁止使用 Docker。开发、测试、调试一律在本地环境直接运行。
- **服务启停顺序**: 启动或重载服务时，必须先执行 `./scripts/services.sh stop` 终止旧进程，再执行 `./scripts/services.sh start` 启动新服务，确保后端端口 8000 和前端端口 5173 不变。禁止直接 start 而不先 stop。

## Git

- 从远程分支创建本地功能分支后，必须用 `git push -u origin <branch-name>` 推送并设置上游为独立远程分支，而不是跟踪源分支（如 `origin/dev`）。否则 `git push` 会直接推到源分支。
