---
name: sdd-spec-writing
description: Use when an agent needs to write or update a specification for a requirement — read context, get the spec template guide, write content, and submit for review. Triggers: "write spec", "create specification", "update spec", "spec for requirement", "write specification".
---

# SDD Specification Writing

Use this skill to write specifications for requirements in the SDD system.

## Prerequisites

- SDD backend running and API key configured
- Requirement exists and is in status `drafting_spec` or `reviewing_spec`
- User has `spec_template:edit` or appropriate permissions

## Workflow

### Step 1: Get Full Requirement Context

```bash
sdd requirements full-context REQUIREMENT_ID
```

Study the output carefully:
- `requirement` — title, description, type, priority, status
- `spec` — current spec if any (check `current_version`)
- `tasks` — existing tasks for this requirement
- `test_cases` — existing test cases

### Step 2: Get the Spec Template Agent Guide

Find your team ID from Step 1 output (look at the project → team chain), then:

```bash
sdd teams agent-guide TEAM_ID
```

This returns the spec template with `agent_prompt` for each field. Each section has:
- `name` — machine name of the section
- `display_name` — human-readable name
- `required` — whether the section must be filled
- `fields` — list of fields with:
  - `name` — field name
  - `type` — field type (text, list, table, etc.)
  - `agent_prompt` — instructions for what to write in this field
  - `json_schema` — validation schema the content must match

### Step 3: Get Current Spec (If Updating)

```bash
sdd requirements spec REQUIREMENT_ID
```

If `current_version > 0`, the spec already exists. Get the current version's content:

```bash
sdd requirements spec-version REQUIREMENT_ID VERSION
```

### Step 4: Write the Spec Content

Build the spec content as a JSON object matching the template sections. Each section's content must pass the `json_schema` validation.

Example structure:
```json
{
  "entity_definition": {
    "description": "...",
    "fields": [
      {"name": "id", "type": "BIGINT", "constraints": "PRIMARY KEY AUTOINCREMENT"}
    ]
  },
  "table_design": {
    "tables": [
      {"name": "items", "fields": [{"name": "id", "type": "BIGINT", "constraints": "PK"}]}
    ]
  },
  "page_structure": {
    "pages": [{"name": "Item List", "code": "item-list", "elements": [...]}]
  },
  "api_design": {
    "endpoints": [{"method": "GET", "path": "/api/v1/items", "description": "List items"}]
  }
}
```

### Step 5: Validate and Save

```bash
sdd requirements save-spec REQUIREMENT_ID --content 'YOUR_JSON_HERE'
```

Or use the simpler direct endpoint:
```bash
sdd requirements save-spec-direct REQUIREMENT_ID --content '{"text": "..."}'
```

**If validation fails (code 40001):** The error response will include `data` with a list of validation errors. Fix each error and retry.

### Step 6: Submit for Review

If the requirement status is `drafting_spec` and the spec is ready:

```bash
sdd requirements submit-spec-review REQUIREMENT_ID --reviewer REVIEWER_USER_ID
```

To find a reviewer, list team members:
```bash
sdd teams members TEAM_ID
```

### Step 7: Check Spec History (Optional)

```bash
sdd requirements spec-versions REQUIREMENT_ID
```

## Common Patterns

### Creating a new spec from scratch

1. `full-context` → understand the requirement
2. `agent-guide` → get template with prompts
3. Write content following each `agent_prompt`
4. `save-spec` → validate and save
5. Fix validation errors if any
6. `submit-spec-review` → send for review

### Updating an existing spec

1. `spec` → get current version
2. `spec-version ID VERSION` → get full content
3. Modify the content
4. `save-spec` → creates a new version
5. `submit-spec-review` → send for review again

## Error Handling

- **40001 Validation error**: Check the `data` field for specific field errors. Each error has `field` and `msg`.
- **40204 Invalid status**: Requirement must be in `drafting_spec` status to save specs. Use `sdd requirements patch ID --status drafting_spec` to change status.
- **40300 Forbidden**: You need `spec_template:edit` permission on the team.
