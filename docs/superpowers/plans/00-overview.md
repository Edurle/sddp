# Agent Collaboration Enhancement — Plan Overview

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add review comments, webhook notifications, agent work discovery, and progress summary view to enable human+agent collaborative development.

**Architecture:** 4 independent subsystems built on existing FastAPI + PostgreSQL + Vue 3 stack. Each subsystem is self-contained and can be implemented independently.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy async (PostgreSQL), Alembic, Pydantic, Vue 3 + TypeScript, Typer CLI

**Spec:** `docs/superpowers/specs/2026-05-16-agent-collaboration-design.md`

---

## Sub-Plans

Execute in this order (each plan is independent but review comments should come first since webhook events depend on review actions):

1. **`01-review-comments.md`** — Review comment model + API + frontend timeline
2. **`02-webhook-notifications.md`** — Webhook CRUD + event delivery + CLI commands
3. **`03-agent-work-discovery.md`** — GET /me/work API + `sdd my-work` CLI command
4. **`04-progress-summary.md`** — Dashboard "进度" tab with stat cards + expandable list

---

## File Structure

### New Files

| File | Purpose |
|------|---------|
| `backend/app/models/review_comment.py` | ReviewComment ORM model |
| `backend/app/services/review_comment.py` | Review comment business logic |
| `backend/app/services/webhook.py` | Webhook CRUD + delivery logic |
| `backend/app/api/webhooks.py` | Webhook API routes |
| `backend/alembic/versions/xxxx_add_review_comments.py` | Migration for review_comments |
| `backend/alembic/versions/xxxx_add_webhooks.py` | Migration for webhooks + webhook_deliveries |
| `backend/tests/test_review_comments.py` | Tests for review comments |
| `backend/tests/test_webhooks.py` | Tests for webhooks |
| `backend/tests/test_agent_work.py` | Tests for GET /me/work |
| `cli/sdd_cli/webhooks.py` | Webhook CLI commands |

### Modified Files

| File | Changes |
|------|---------|
| `backend/app/models/__init__.py` | Add ReviewComment, Webhook, WebhookDelivery imports |
| `backend/app/api/router.py` | Add webhooks router |
| `backend/app/api/users.py` | Add GET /me/work endpoint |
| `backend/app/services/user.py` | Add get_user_work() function |
| `backend/app/services/requirement.py` | Call webhook events on review actions |
| `backend/tests/conftest.py` | Add ReviewComment, Webhook, WebhookDelivery to TRUNCATE |
| `cli/sdd_cli/main.py` | Add webhooks subcommand |
| `cli/sdd_cli/me.py` | Add my-work command |
| `frontend/src/views/dashboard/DashboardPage.vue` | Add "进度" tab |
| `frontend/src/views/requirement/RequirementDetailPage.vue` | Add review comment UI + timeline |

---

## Implementation Order

```
01-review-comments (backend) ──┐
                                ├──→ 02-webhook-notifications (uses review events)
03-agent-work-discovery ────────┤
04-progress-summary (frontend) ─┘
```

Plans 01, 03, 04 are fully independent and can be parallelized. Plan 02 depends on 01 being complete (needs review events to fire webhooks).
