---
name: sdd-task-execution
description: Use when an agent needs to execute a development task — start coding, track git info, run tests, submit results, and complete the task. Triggers: "work on task", "start coding", "execute task", "run tests", "submit test results", "complete task".
---

# SDD Task Execution

Use this skill to execute development tasks through their full lifecycle: start → code → test → complete.

## Prerequisites

- SDD backend running and API key configured
- A task assigned to you (find with `sdd-discover-work` skill)
- Task should be in `pending` or `coding` status

## Task Status Flow

```
pending → coding → testing → completed
              ↑         ↓
              └─────────┘ (failed tests → back to coding)
```

Valid transitions:
- `pending` → `coding`
- `coding` → `testing`, `pending`
- `testing` → `completed`, `coding`

## Workflow

### Step 1: Get Task Context

```bash
sdd tasks get TASK_ID
```

Also get the full requirement context:
```bash
sdd requirements full-context REQUIREMENT_ID
```

### Step 2: Start Coding

If the task is `pending`:
```bash
sdd tasks start-coding TASK_ID
```

### Step 3: Read the Specification

```bash
sdd requirements spec REQUIREMENT_ID
```

If a spec exists, get the latest version:
```bash
sdd requirements spec-version REQUIREMENT_ID VERSION
```

### Step 4: Read Test Cases

```bash
sdd requirements test-cases REQUIREMENT_ID
```

### Step 4A: Auto-Generate Tasks or Test Cases (Optional)

If no tasks exist yet, auto-generate them from the spec:

```bash
sdd requirements generate-tasks REQUIREMENT_ID --strategy hybrid
```

Strategies: `hybrid` (default), `by_page`, `by_entity`, `by_api`.

If no test cases exist yet, auto-generate them from the spec:

```bash
sdd requirements generate-test-cases REQUIREMENT_ID
sdd requirements generate-test-cases REQUIREMENT_ID --case-types "api,ui"
```

Case types: `api`, `ui`, `functional`, `edge_case`.

### Step 5: Implement the Code

Write your implementation following the spec. This is done outside SDD.

### Step 6: Update Git Info

```bash
sdd tasks git-info TASK_ID \
  --branch "feat/requirement-TASK_ID" \
  --sha "$(git rev-parse HEAD)"
```

If you have a PR or artifact:
```bash
sdd tasks git-info TASK_ID \
  --branch "feat/123" \
  --sha "abc123def456" \
  --pr "https://github.com/org/repo/pull/456" \
  --artifact "https://ci.example.com/build/789"
```

### Step 7: Start Testing

```bash
sdd tasks start-testing TASK_ID
```

This creates a new test execution round automatically. Alternatively, you can create a round manually:

```bash
sdd tasks create-test-round TASK_ID --test-case-id TEST_CASE_ID
```

### Step 8: Get Test Execution Round

```bash
sdd tasks test-executions TASK_ID
```

Find the latest round `id` from the output.

### Step 9: Submit Test Results

**Batch submission (recommended):**

```bash
sdd test-executions batch --round ROUND_ID --records '[...]'
```

Or from a file:
```bash
sdd test-executions batch --round ROUND_ID --file test-results.json
```

**Create individual test record:**

```bash
sdd tasks create-test-record TASK_ID --test-case-id TEST_CASE_ID --status passed
```

**Update an existing record:**

```bash
sdd test-executions update-record RECORD_ID --status passed --duration-ms 120
```

### Step 10: Check Test Statistics (Optional)

View aggregated test results for the requirement:

```bash
sdd requirements test-stats REQUIREMENT_ID
```

### Step 11: Evaluate Results

If all tests passed:
```bash
sdd tasks complete TASK_ID
```

If some tests failed:
```bash
sdd tasks patch TASK_ID --status coding
```
Then fix the issues and repeat from Step 7.

## Complete Example

```bash
sdd tasks get 42
sdd tasks start-coding 42
sdd requirements full-context 15
sdd requirements generate-tasks 15 --strategy hybrid
sdd requirements generate-test-cases 15
# ... implement code ...
sdd tasks git-info 42 --branch "feat/15-user-login" --sha "$(git rev-parse HEAD)"
sdd tasks start-testing 42
sdd tasks test-executions 42
sdd test-executions batch --round 7 --file results.json
sdd requirements test-stats 15
sdd tasks complete 42
```

## Error Handling

- **40001 Invalid transition**: Check current task status with `sdd tasks get TASK_ID`
- **40401 Test not passed**: All test cases must pass before completing
- **40402 No execution**: Create a test round first with `sdd tasks start-testing TASK_ID`
