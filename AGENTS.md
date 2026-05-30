# SDD — Spec-Driven Development Tool

## Architecture

Monorepo with two independent packages:

- **`backend/`** — Python 3.12, FastAPI, SQLAlchemy async (SQLite via aiosqlite), Pydantic, Motor/MongoDB (spec documents), `jsonschema` for content validation. Runs on port 8000.
- **`frontend/`** — Vue 3 + TypeScript, Pinia, Vue Router, Axios, Vite. Uses `@` alias → `src/`. Dev server proxies `/api` → `localhost:8000`. Runs on port 5173.
- **`scripts/services.sh`** — manages both services (start/stop/restart/status/e2e/logs). Backend uses `conda run -n sdd`.

### Backend structure

| Layer | Directory | Pattern |
|-------|-----------|---------|
| Routes | `app/api/` | One file per domain, mounted via `app/api/router.py` under `/api/v1/...` |
| Schemas | `app/schemas/` | Pydantic request/response models |
| Services | `app/services/` | Business logic, called from routes |
| SQL models | `app/models/` | SQLAlchemy ORM models (all in `__init__.py`) |
| Mongo models | `app/mongo_models/` | Motor-based document models (`spec_template.py`, `spec_document.py`) |
| Auth | `app/deps.py` | `get_current_user` (JWT Bearer or cookie), `require_permission`, `require_admin` |

Tests use in-memory SQLite (`sqlite+aiosqlite://`) with `setup_database` fixture that creates/drops all tables per test. No MongoDB in tests — spec tests mock Mongo or use `TestSessionFactory` for SQL only.

### Frontend structure

- Entry: `src/main.ts` → `App.vue` → router
- API client: `src/api/client.ts` — axios with JWT interceptor, API responses wrapped in `{ code, message, data }` (code `0` = success)
- Views: `src/views/{admin,auth,dashboard,iteration,project,requirement,task,team}/`
- Auth guard on `/admin/*` routes checks `is_admin` in JWT payload

## Commands

```bash
# Backend tests (from repo root)
conda run -n sdd python -m pytest backend/tests/ -v

# Single test file
conda run -n sdd python -m pytest backend/tests/test_requirements.py -v

# Frontend typecheck + build
cd frontend && npx vue-tsc -b && npx vite build

# Frontend E2E (needs both services running)
./scripts/services.sh start && ./scripts/services.sh e2e

# Service management
./scripts/services.sh start       # both
./scripts/services.sh start-be    # backend only
./scripts/services.sh status
./scripts/services.sh logs-be     # tail backend logs
```

## Environment

- Python packages managed via conda env `sdd` — always use `conda run -n sdd` for Python commands
- Backend dependencies: `backend/requirements.txt` (installed into conda env)
- Frontend: `npm install` in `frontend/`
- No `.env` file required for dev — defaults in `app/config.py` use local SQLite (`test.db`)
- MongoDB env var: `MONGO_URL` (defaults to `mongodb://localhost:27017`)

## Conventions

- **API error responses**: All errors use `{ code, message, data }`. Business errors use numeric codes from `app/exceptions.py` (e.g. `40001` = validation, `40100` = unauthorized, `40300` = forbidden, `40400` = not found). Success = `code: 0`.
- **BusinessError**: takes `(code, message, errors=[])`. When `errors` is populated (e.g. schema validation failures), the error handler returns them in `data`.
- **CSS: Button styling**: Global `button` in `main.css` sets `background: #111; color: #fff`. Any scoped override with a light `background` MUST also set `color` to a dark value. Always set both together.
- **Spec content validation**: `save_spec_document` validates content against JSON Schemas defined in `spec_template.py`'s `DEFAULT_SECTIONS`. Each section defines `json_schema` on its fields. Uses `jsonschema` library.
- **No code comments** in implementation files unless explicitly requested.
- **No Docker**: 除正式部署外，禁止使用 Docker。开发、测试、调试一律在本地环境直接运行。
- **服务启停顺序**: 启动或重载服务时，必须先执行 `./scripts/services.sh stop` 终止旧进程，再执行 `./scripts/services.sh start` 启动新服务，确保后端端口 8000 和前端端口 5173 不变。禁止直接 start 而不先 stop。
