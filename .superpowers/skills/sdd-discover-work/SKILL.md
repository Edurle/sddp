---
name: sdd-discover-work
description: Use when an agent needs to find available work — check pending items, assigned tasks, or pending reviews in the SDD system. Triggers: "what should I work on", "find tasks", "my assignments", "check reviews", "discover work", "pending items".
---

# SDD Work Discovery

Use this skill to discover what work is available in the SDD project management system.

## Prerequisites

- SDD backend running at `http://localhost:8000` (or `SDD_API_URL` env var)
- API key configured: `SDD_API_KEY` env var or `~/.sdd/config.json`

## Workflow

### Step 1: Check Who You Are

```bash
sdd auth whoami
```

Verify your identity and permissions. If this fails with "Not authenticated", set your API key:

```bash
export SDD_API_KEY="sdd_your_key_here"
```

### Step 2: Get Dashboard Overview

```bash
sdd me pending
```

This returns:
- `teams` — teams you belong to
- `projects` — active projects in your teams
- `assigned_tasks` — tasks currently assigned to you
- `pending_reviews` — items awaiting your review

### Step 3: Check Your Assigned Tasks

```bash
sdd me tasks
```

Filter by status if needed:
```bash
sdd me tasks --status coding
sdd me tasks --status testing
sdd me tasks --status pending
```

### Step 4: Check Pending Reviews

```bash
sdd me pending-reviews
```

If there are pending reviews, see Step 5B.

### Step 5: Decide What to Do Next

**5A — If you have assigned tasks:**

Pick a task and get its full context:
```bash
sdd requirements full-context REQUIREMENT_ID
```

Then proceed to the `sdd-task-execution` skill to work on it.

**5B — If you have pending reviews:**

Get the requirement details:
```bash
sdd requirements get REQUIREMENT_ID
sdd requirements spec REQUIREMENT_ID
```

Then proceed to the `sdd-review` skill.

**5C — If no tasks and no reviews:**

Check for unassigned work:
```bash
sdd requirements list --status drafting_spec
sdd requirements list --status drafting_tests
```

You can also check iteration kanban:
```bash
sdd iterations kanban ITERATION_ID
```

## Output Format

All commands output JSON by default. Use `--format table` for human-readable output (not recommended for agents).

## Error Handling

- **40100 Not authenticated**: Set `SDD_API_KEY` env var
- **40300 Forbidden**: You lack the required permission — contact admin
- **40400 Not found**: The resource ID doesn't exist — verify with list commands
