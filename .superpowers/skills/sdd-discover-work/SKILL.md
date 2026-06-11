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
sdd me
```

Verify your identity and permissions. If this fails with "Not authenticated", set your API key:

```bash
export SDD_API_KEY="sdd_your_key_here"
```

### Step 2: Get Dashboard Overview

**Combined work dashboard (recommended):**

```bash
sdd me my-work
```

This returns a combined view of:
- `pending_reviews` — items awaiting your review
- `assigned_tasks` — tasks currently assigned to you
- `draftable_items` — items you can draft specs/tests for

Filter by type:
```bash
sdd me my-work --type reviews
sdd me my-work --type tasks
sdd me my-work --type drafts
```

Use `--json` for machine-readable output.

**Alternative: separate commands:**

```bash
sdd me pending          # teams, projects, tasks, reviews overview
sdd me pending-reviews  # items awaiting your review
sdd me tasks            # assigned tasks with --status filter
```

### Step 3: Check Statistics

View test statistics at different levels to identify problem areas:

```bash
sdd iterations statistics ITERATION_ID     # iteration overview
sdd iterations test-stats ITERATION_ID     # test pass/fail breakdown
sdd projects test-stats PROJECT_ID         # project-level test stats
sdd requirements test-stats REQUIREMENT_ID # requirement-level test stats
```

### Step 4: Decide What to Do Next

**4A — If you have assigned tasks:**

Pick a task and get its full context:
```bash
sdd requirements full-context REQUIREMENT_ID
```

Then proceed to the `sdd-task-execution` skill to work on it.

**4B — If you have pending reviews:**

Get the requirement details:
```bash
sdd requirements get REQUIREMENT_ID
sdd requirements spec REQUIREMENT_ID
```

Then proceed to the `sdd-review` skill.

**4C — If no tasks and no reviews:**

Check for unassigned work:
```bash
sdd requirements list --status drafting_spec
sdd requirements list --status drafting_tests
```

You can also check iteration kanban:
```bash
sdd iterations kanban ITERATION_ID
```

**4D — If an approved requirement needs changes:**

Use supersede to create a change request from an approved requirement:
```bash
sdd requirements supersede REQUIREMENT_ID --title "Requirement Title (v2)"
```

This marks the original as `deprecated` and creates a new requirement in `drafting_req` status linked via `supersede`. Then proceed to write its spec or draft as needed.

To view existing links for any requirement:
```bash
sdd requirements links REQUIREMENT_ID
```

## Output Format

All commands output JSON by default. Use `--format table` for human-readable output (not recommended for agents).

## Error Handling

- **40100 Not authenticated**: Set `SDD_API_KEY` env var
- **40300 Forbidden**: You lack the required permission — contact admin
- **40400 Not found**: The resource ID doesn't exist — verify with list commands
