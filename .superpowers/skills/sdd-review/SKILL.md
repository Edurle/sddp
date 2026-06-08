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

### Step 2A: Check Related Requirements

Check if this requirement is linked to others (dependencies, supersede chain):

```bash
sdd requirements links REQUIREMENT_ID
```

Each link has `direction` (`incoming` / `outgoing`), `link_type` (`relates_to` / `supersede`), and `related_req_id`. This helps understand context — e.g., if reviewing a requirement that supersedes an older one, check the original's spec for reference.

### Step 3: Check Previous Review Comments

If the requirement was previously reviewed and rejected, check prior feedback:

```bash
sdd requirements review-comments REQUIREMENT_ID
```

This returns all review comments from previous rounds. Use this to understand whether prior issues have been addressed.

### Step 4: Review by Type

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

### Step 5: Submit Your Decision

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

### Step 6: Verify Status Change

```bash
sdd requirements get REQUIREMENT_ID
```

## Common Patterns

### Review a previously rejected submission

```bash
sdd requirements review-comments REQUIREMENT_ID
# Check if prior feedback was addressed, then proceed with review
sdd requirements full-context REQUIREMENT_ID
sdd requirements review REQUIREMENT_ID --action approve
```

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

### Reject and suggest creating a change (supersede)

If the requirement needs significant rework after approval, suggest creating a supersede:

```bash
sdd requirements review REQUIREMENT_ID --action reject --comment "Major scope change needed."
sdd requirements supersede REQUIREMENT_ID --title "Requirement Title (v2)" --description "Updated description"
```

This marks the original as `deprecated` and creates a new drafting requirement linked via `supersede`.

## Error Handling

- **40301 Not reviewer**: You are not assigned as a reviewer for this requirement
- **40302 Reject no comment**: Must provide a comment when rejecting
- **40303 Review processed**: This review has already been completed
- **40204 Invalid status**: The requirement is not in a reviewable status
