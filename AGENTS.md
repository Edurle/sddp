# SDD — Spec-Driven Development Tool

## Architecture

Monorepo with three packages:

- **`backend/`** — Python 3.12, FastAPI, SQLAlchemy async (PostgreSQL via asyncpg), Pydantic, `jsonschema`. Runs on port 8000.
- **`frontend/`** — Vue 3 + TypeScript, Pinia, Vue Router, Axios, Vite. `@` alias → `src/`. Dev server proxies `/api` → `localhost:8000`. Runs on port 5173.
- **`cli/`** — Python CLI (`sdd`, package `sdd-cli`, current version in `cli/pyproject.toml`) using Typer. Talks to backend API. Installed separately (`pip install -e cli`). Usage guide: `docs/cli-guide.md`.
- **`scripts/services.sh`** — manages both services (start/stop/restart/status/e2e/logs). Bash script (needs bash/Git Bash, not cmd). Backend uses `conda run -n sdd`.

### Backend structure

| Layer | Directory | Pattern |
|-------|-----------|---------|
| Routes | `app/api/` | One file per domain, mounted via `app/api/router.py` under `/api/v1/...` |
| Schemas | `app/schemas/` | Pydantic request/response models |
| Services | `app/services/` | Business logic, called from routes. `path_utils.py` is a pure-function path resolver shared across services. |
| SQL models | `app/models/` | Each model in its own file, all re-exported from `__init__.py` |
| Auth | `app/deps.py` | `get_current_user` (JWT Bearer, cookie, or X-API-Key header), `require_permission`, `require_admin`. **`check_team_permission` reads permissions from the DB (team roles), NOT from the JWT `permissions` claim** — the claim only feeds `require_permission`/`require_admin`. So tests using `check_team_permission` must rely on the `owner_role` fixture's DB-backed perms, not `auth_headers(..., permissions=[...])`. |
| Cache | `app/cache.py` | In-memory `Cache` class with TTL. `cache_instance` is module-level singleton, cleared by `conftest.py` and `init_db`. |

Tests use a real PostgreSQL DB (`TEST_DATABASE_URL`, e.g. `obr_test`) — `conftest.py` creates sessions against it, then `TRUNCATE ... RESTART IDENTITY CASCADE`s all tables after each test. `autouse` fixture in `backend/conftest.py` clears the in-memory cache between tests.

**No Alembic.** Schema is managed by `init_db()` → `Base.metadata.create_all` (`backend/app/database.py`). There is no `backend/alembic/` directory. Adding a column to an existing model requires a manual `ALTER TABLE` against existing DBs (new DBs get it via `create_all`).

### Frontend structure

- Entry: `src/main.ts` → `App.vue` → router
- API client: `src/api/client.ts` — axios with JWT interceptor, API responses wrapped in `{ code, message, data }` (code `0` = success)
- Views: `src/views/{admin,auth,dashboard,iteration,profile,project,requirement,task,team}/`
- Auth guard on `/admin/*` routes checks `is_admin` in JWT payload
- E2E tests: Playwright in `frontend/tests/`, 12 spec files

## Commands

```bash
# Backend tests (from repo root)
conda run -n sdd python -m pytest backend/tests/ -v

# Single test file
conda run -n sdd python -m pytest backend/tests/test_requirements.py -v

# Single test function
conda run -n sdd python -m pytest backend/tests/test_requirements.py::test_create_requirement -v

# CLI tests (needs sdd-cli installed: conda run -n sdd pip install -e cli)
conda run -n sdd python -m pytest cli/tests/ -v

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
- `DATABASE_URL` / `TEST_DATABASE_URL` in `.env` point to PostgreSQL (e.g. `postgresql+asyncpg://.../obr_test`). No SQLite.
- Seed data only created when `SDD_SEED_DATA=true` env var is set (not default)
- Schema via `init_db()`/`create_all` — no Alembic (see Backend structure above)

## Conventions

- **API error responses**: All errors use `{ code, message, data }`. Business errors use numeric codes from `app/exceptions.py` (e.g. `40001` = validation, `40100` = unauthorized, `40300` = forbidden, `40400` = not found). Success = `code: 0`. BusinessErrors return HTTP 200 with error code in body.
- **BusinessError**: takes `(code, message, errors=[])`. When `errors` is populated (e.g. schema validation failures), the error handler returns them in `data`.
- **CSS: Button styling**: Global `button` in `main.css` sets `background: #111; color: #fff`. Any scoped override with a light `background` MUST also set `color` to a dark value. Always set both together.
- **Spec content validation**: `save_spec_document` validates content against JSON Schemas defined in `specification.py`'s `DEFAULT_SECTIONS`. Each section defines `json_schema` on its fields. Uses `jsonschema` library.
- **Spec content is a section-name-keyed dict** (`{entity_definition: {...}, table_design: {...}, ...}`), NOT a `{sections: [...]}` array. Paths into spec content start at the section name (e.g. `entity_definition.fields[0].constraints`).
- **Path-based field updates** (`backend/app/services/path_utils.py`): `set_by_path(doc, path, value)` resolves dot/`[idx]`/`[-1]`/`[key=val]` paths and replaces the target in a deep copy. Only updates existing nodes (no auto-creation). Error messages are Agent-actionable: include the missing segment, existing keys/array length, and how to fix. Used by spec drafts and requirement `type_detail` drill-down.
- **Spec drafts**: `SpecDocument` has `draft_content` / `draft_base_version` (nullable JSONB/INTEGER). `set_spec_draft_field` copies a baseline from the current version on first edit, applies path updates, validates the whole draft against the schema (rollback on failure), commits via `commit_spec_draft` (version+1, clears draft). `GET /specification` returns the draft when present (`is_draft` flag).
- **No code comments** in implementation files unless explicitly requested.
- **No Docker**: 除正式部署外，禁止使用 Docker。开发、测试、调试一律在本地环境直接运行。
- **服务启停顺序**: 启动或重载服务时，必须先执行 `./scripts/services.sh stop` 终止旧进程，再执行 `./scripts/services.sh start` 启动新服务，确保后端端口 8000 和前端端口 5173 不变。禁止直接 start 而不先 stop。

## Git

- 从远程分支创建本地功能分支后，必须用 `git push -u origin <branch-name>` 推送并设置上游为独立远程分支，而不是跟踪源分支（如 `origin/dev`）。否则 `git push` 会直接推到源分支。
