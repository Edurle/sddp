# Agent Collaboration Enhancement Design

## Background

SDD is a spec-driven development platform where team members (PM, Developer, QA) use their own agents + CLI tools to complete their responsibilities. The core workflow:

1. PM agent writes requirements + prototypes
2. Developer reviews and approves
3. Developer agent writes specs
4. QA agent writes test cases
5. Reviews happen at each stage, humans decide whether to advance

Current pain points:
- Review is pass/fail only, no comments or history
- No notification when reviews are submitted/approved/rejected
- Agents lack a unified "what should I do now" view
- Progress visibility is limited to the tree view

## Design Overview (Plan A)

4 subsystems that form a complete loop: Agent works → Human reviews → Notification → Next agent picks up.

---

## 1. Review Enhancement

### Data Model

New `review_comments` table (no explicit foreign keys):

| Field | Type | Description |
|-------|------|-------------|
| id | int PK autoincrement | |
| requirement_id | int | Logical reference to requirements |
| reviewer_id | int | Logical reference to users |
| review_type | text | `requirement`, `spec`, `test` |
| action | text | `approve`, `reject`, `comment` |
| comment | text | Review comment text |
| created_at | timestamp with tz | Defaults to now() |

### API Changes

- `POST /api/v1/requirements/{id}/review` — add optional `comment: str | None` field
- `GET /api/v1/requirements/{id}/review-comments` — list all review history for a requirement
- Same pattern for spec review and test review endpoints

### Frontend Changes

- Review action dialog: add comment textarea (optional)
- Review history timeline on requirement detail page: reviewer avatar + time + action badge + comment text

---

## 2. Webhook Notifications

### Trigger Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `review.submitted` | Requirement/spec/test submitted for review | requirement_id, type, submitter_id, submitter_name |
| `review.approved` | Review approved | requirement_id, type, reviewer_id, reviewer_name |
| `review.rejected` | Review rejected | requirement_id, type, reviewer_id, reviewer_name, comment |
| `status.changed` | Requirement status changed | requirement_id, old_status, new_status, changed_by |
| `task.assigned` | Task assigned to user | task_id, task_title, assignee_id, requirement_id |
| `task.completed` | Task marked completed | task_id, task_title, assignee_id, requirement_id |

### Data Model

`webhooks` table (no explicit foreign keys):

| Field | Type | Description |
|-------|------|-------------|
| id | int PK autoincrement | |
| team_id | int | Logical reference to teams |
| url | text | Webhook target URL |
| secret | text | HMAC-SHA256 signing key (optional) |
| events | jsonb | Subscribed events list, e.g. `["review.submitted", "review.approved"]` |
| is_active | bool | Default true |
| created_by | int | Logical reference to users |
| created_at | timestamp with tz | |
| updated_at | timestamp with tz | |

`webhook_deliveries` table (no explicit foreign keys):

| Field | Type | Description |
|-------|------|-------------|
| id | int PK autoincrement | |
| webhook_id | int | Logical reference to webhooks |
| event | text | Event name |
| payload | jsonb | Request body |
| status_code | int | HTTP response code |
| delivered_at | timestamp with tz | |
| error | text | Failure reason if applicable |

### API

- `POST /api/v1/teams/{team_id}/webhooks` — create webhook
- `GET /api/v1/teams/{team_id}/webhooks` — list webhooks
- `PUT /api/v1/teams/{team_id}/webhooks/{id}` — update webhook
- `DELETE /api/v1/teams/{team_id}/webhooks/{id}` — delete webhook
- `GET /api/v1/teams/{team_id}/webhooks/{id}/deliveries` — delivery history

### Delivery Logic

On event trigger:
1. Find all active webhooks for the team that owns the affected requirement
2. Filter by subscribed events
3. POST JSON payload asynchronously with `X-SDD-Signature: sha256=<hmac>` header
4. Record delivery in `webhook_deliveries`

### CLI Commands

- `sdd webhooks list --team-id 1`
- `sdd webhooks create --team-id 1 --url https://... --events review.submitted,review.approved`
- `sdd webhooks update --id 1 --events ...`
- `sdd webhooks delete --id 1`
- `sdd webhooks deliveries --id 1`

---

## 3. Agent Work Discovery

### New API Endpoint

`GET /api/v1/users/me/work`

Returns structured work queue for the current user:

```json
{
  "pending_reviews": [
    {
      "id": 1,
      "title": "用户注册登录",
      "type": "requirement",
      "status": "reviewing_req",
      "submitted_by_name": "pm_agent"
    }
  ],
  "assigned_tasks": [
    {
      "id": 5,
      "title": "实现用户注册API",
      "status": "coding",
      "requirement_id": 1,
      "requirement_title": "用户注册登录"
    }
  ],
  "draftable_items": [
    {
      "id": 2,
      "title": "收支记录管理",
      "status": "drafting_spec",
      "my_role": "developer",
      "next_action": "write_spec"
    }
  ],
  "summary": {
    "reviews_waiting": 1,
    "tasks_in_progress": 1,
    "items_to_draft": 1
  }
}
```

`draftable_items` logic: based on user's role in the team, determine which requirements are waiting for their action:
- Role is PM → requirements with status `drafting_req`
- Role is Developer → requirements with status `drafting_spec`
- Role is QA → requirements with status `drafting_tests`

### CLI Commands

- `sdd my-work` — human-readable summary
- `sdd my-work --json` — JSON output for agent parsing
- `sdd my-work --type reviews` — only pending reviews
- `sdd my-work --type tasks` — only assigned tasks
- `sdd my-work --type drafts` — only items to draft

---

## 4. Progress Summary View

### Frontend Only

New "进度" tab in the dashboard page. Uses existing `GET /api/v1/users/me/projects-tree` API. No new backend needed.

### Layout: Statistics Summary + Expandable List

**Top section — 4 stat cards in a row:**

| 草稿中 | 审核中 | 起草中 | 已通过 |
|--------|--------|--------|--------|
| 3 | 1 | 0 | 0 |

Each card: colored background, large number, small label. Count requirements by lifecycle phase.

**Below — requirement list grouped by iteration, expandable:**

Collapsed row:
```
▶ 用户注册登录  [需求审核中]                    ● 高优
```

Expanded row (click to toggle):
```
▼ 用户注册登录  [需求审核中]                    ● 高优
  ✅ 草稿 通过  🔄 需求审核 等待中  ⬜ 编写规范  ⬜ 规范审核  ⬜ 编写测试  ⬜ 测试审核  ⬜ 已通过
  提交人: pm_agent · 3个任务(全部完成) · 6个测试用例
```

Click requirement title → navigate to detail page.

### Design Principles

- **Not crowded** — generous padding (16px+), ample spacing between elements
- **No unexpected line wraps** — use `white-space: nowrap` on status badges, names, inline stage lists; `overflow: hidden` + `text-overflow: ellipsis` on long titles with `max-width`
- **Expandable by default for first requirement** — rest collapsed, user clicks to expand
- Dropdown filter: project, iteration

### Explicitly Not Doing

- No drag-and-drop
- No in-card editing
- No horizontal scroll columns (rejected — too crowded)

---

## Implementation Order

1. Review comments (backend + frontend) — foundation for notifications
2. Webhook system (backend + CLI) — depends on review events
3. Agent work discovery API + CLI — independent
4. Kanban board (frontend only) — independent, can parallel with 2-3

## Scope

Estimated 8-12 feature points across 4 subsystems. No new infrastructure dependencies — uses existing PostgreSQL + FastAPI + Vue 3 stack.
