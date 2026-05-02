---
name: sdd-review
description: Use when an agent needs to review a requirement, specification, or test case submission — read the content, evaluate quality, and submit an approve or reject decision. Triggers: "review requirement", "review spec", "approve requirement", "reject submission", "pending review", "review submission".
---

# SDD Review

Use this skill to review and approve/reject submissions in the SDD system.

## Prerequisites

- SDD backend running and API key configured
- You must be assigned as a reviewer (check `sdd me pending-reviews`)
- User must have appropriate review permissions

## Review Types

SDD has three review stages in the requirement lifecycle:
1. **Requirement review** — `reviewing_req` → `drafting_spec`
2. **Spec review** — `reviewing_spec` → `drafting_tests`
3. **Test review** — `reviewing_tests` → `approved`

## Workflow

### Step 1: Find Pending Reviews

```bash
sdd me pending-reviews
```

Each item shows: `requirement_id`, `requirement_title`, `review_type`, `status`.

### Step 2: Get Full Context

```bash
sdd requirements full-context REQUIREMENT_ID
```

Review all sections: `requirement`, `spec`, `test_cases`, `tasks`.

### Step 3: Review by Type

**Requirement Review (`review_type: requirement`):**

Evaluate:
- Is the requirement clear and complete?
- Is the priority appropriate?
- Is the description sufficient for spec writing?

**Spec Review (`review_type: spec`):**

```bash
sdd requirements spec REQUIREMENT_ID
sdd requirements spec-version REQUIREMENT_ID VERSION
```

Evaluate:
- Does the spec match the requirement?
- Are all required sections filled?
- Is the entity definition complete?
- Are API endpoints well-defined?

**Test Review (`review_type: test`):**

```bash
sdd requirements test-cases REQUIREMENT_ID
```

Evaluate:
- Do test cases cover all requirements?
- Are test steps reproducible?
- Are expected results verifiable?

### Step 4: Submit Your Decision

**Approve:**
```bash
sdd requirements review REQUIREMENT_ID --action approve
```

Or use direct approve endpoints:
```bash
sdd requirements approve REQUIREMENT_ID        # requirement → drafting_spec
sdd requirements approve-spec REQUIREMENT_ID    # spec → drafting_tests
```

**Reject (must include comment):**
```bash
sdd requirements review REQUIREMENT_ID --action reject --comment "Issues found: ..."
```

Always provide specific, actionable feedback when rejecting.

### Step 5: Verify Status Change

```bash
sdd requirements get REQUIREMENT_ID
```

## Common Patterns

### Quick approve

```bash
sdd requirements approve REQUIREMENT_ID
```

### Reject with detailed feedback

```bash
sdd requirements review REQUIREMENT_ID --action reject --comment "Issues:
1. Missing error handling in API design
2. Table 'users' lacks 'created_at' timestamp
Please address these and resubmit."
```

## Error Handling

- **40301 Not reviewer**: You are not assigned as a reviewer for this requirement
- **40302 Reject no comment**: Must provide a comment when rejecting
- **40303 Review processed**: This review has already been completed
- **40204 Invalid status**: The requirement is not in a reviewable status
