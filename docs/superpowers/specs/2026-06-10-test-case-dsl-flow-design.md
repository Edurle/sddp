# Test Case DSL Flow Rendering

## Problem

Test case detail dialog displays `precondition`, `steps`, `expected_result` as raw `<pre>` text blocks. These fields contain structured YAML DSL content (API DSL and UI DSL) that should be parsed and rendered as a unified flow visualization.

## DSL Types

- **API DSL** (`case_type=api`): `precondition` contains `role` + `data.exists[]` (setup API calls), `steps` contains `call` array, `expected_result` contains `response` assertions.
- **UI DSL** (`case_type=e2e`): `precondition` contains `role` + `setup[]` (UI actions), `steps` contains `action` array, `expected_result` contains `assert` array.
- **Fallback**: non-YAML or parse errors fall back to plain `<pre>` text.

## Approach

Frontend-only solution using `js-yaml` to parse the three YAML fields, merge them into a `FlowLine` model, and render a unified flow visualization (Setup → Steps → Assert) with typed cards.

No backend changes required. DSL type is determined by `case_type` + YAML content structure.

## Files

| File | Action |
|------|--------|
| `frontend/src/utils/parseTestDsl.ts` | New — YAML parser + merger |
| `frontend/src/components/TestDslFlow.vue` | New — Flow line renderer |
| `frontend/src/views/requirement/RequirementDetailPage.vue` | Modify — Dialog template |
| `frontend/package.json` | Modify — Add `js-yaml` |

## Rendering

- **API cards**: HTTP method badge (GET=green, POST=blue, PUT=orange, DELETE=red), monospace path, key-value body/save/cleanup rows.
- **UI cards**: Action pill badge, target/value key-value rows.
- **Assert cards**: Each assertion prefixed with checkmark.
- **Role**: Shown as a header pill if present.
- **Flow sections**: SETUP / STEPS / ASSERT labels, connected visually with left border or separator lines.
- **Fallback**: Original `<pre>` text when YAML parsing fails.

## Error Handling

- YAML parse failure → fallback to raw `<pre>` text.
- Empty fields → show "无".
- Non-standard structure → graceful degradation to raw text display.
