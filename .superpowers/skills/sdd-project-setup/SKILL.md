---
name: sdd-project-setup
description: Use when an agent needs to set up a new SDD project structure — create team, project, iteration, and initial requirements. Triggers: "create project", "new team", "setup project", "initialize project", "create iteration".
---

# SDD Project Setup

Use this skill to create a complete project structure in SDD: team → project → iteration → requirements.

## Prerequisites

- SDD backend running and API key configured (see `sdd-discover-work` skill)
- User must have permissions: `project:create`, `iteration:create`

## Workflow

### Step 1: Create a Team

```bash
sdd teams create --name "Team Name" --description "Optional description"
```

Save the returned team `id`.

### Step 2: Create a Project Under the Team

```bash
sdd projects create --team TEAM_ID --name "Project Name" --description "Optional" --start-date "2026-05-01"
```

Save the returned project `id`.

### Step 3: Create an Iteration

```bash
sdd iterations create --project PROJECT_ID --name "Sprint 1" --start-date "2026-05-01" --end-date "2026-06-30"
```

If you don't have a project yet, use the direct creation shortcut:
```bash
sdd iterations create --name "Sprint 1"
```
This auto-creates a team and project if none exist.

Save the returned iteration `id`.

### Step 4: Start the Iteration

```bash
sdd iterations start ITERATION_ID
```

### Step 5: Create Requirements

For each requirement:

```bash
sdd requirements create \
  --title "Feature: User Login" \
  --type feature \
  --priority 3 \
  --description "Users should be able to log in with email and password" \
  --iteration ITERATION_ID
```

Requirement types: `feature`, `bugfix`, `improvement`, `research`

Priority levels: `0` (none), `1` (low), `2` (medium), `3` (high)

### Step 6: Invite Team Members (Optional)

```bash
sdd teams invite TEAM_ID --identifier "user@example.com"
```

### Step 7: Create Roles (Optional)

```bash
sdd teams create-role TEAM_ID --name "developer" --permissions "project:create,task:create,task:update,spec:edit"
```

### Step 8: Assign Roles (Optional)

```bash
sdd teams assign-roles TEAM_ID USER_ID --role-ids "5,6"
```

## Verification

```bash
sdd teams get TEAM_ID
sdd projects get PROJECT_ID
sdd iterations get ITERATION_ID
sdd requirements list --iteration ITERATION_ID
```

## Next Steps

After setup, proceed to:
- `sdd-spec-writing` skill — write specifications for requirements
- `sdd-discover-work` skill — find work to do

## Error Handling

- **40002 Email exists**: Use a different email for new users
- **40007 Role name exists**: Use a different role name
- **40203 Active iterations**: Complete or archive existing iterations first
