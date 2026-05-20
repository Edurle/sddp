# E2E Testing Strategy Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Update SDD platform's spec template schema and frontend rendering to support semantic E2E testing metadata (role + accessible_name), enabling getByRole-based testing strategy across any component library.

**Architecture:** Add two new fields (`role`, `accessible_name`) to the spec template's page_structure elements schema. Update agent_prompt to guide AI agents in filling these fields. Update frontend spec rendering to display the new fields. Update existing backend test to reflect the new agent_prompt.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, Vue 3, TypeScript, Playwright

---

## File Structure

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `backend/app/mongo_models/spec_template.py:140-160` | Add `role` and `accessible_name` to elements json_schema, update agent_prompt |
| Modify | `backend/tests/test_spec_template_agent.py:17` | Update expected agent_prompt string to match new prompt |
| Modify | `frontend/src/views/requirement/RequirementDetailPage.vue:112-121` | Add two table columns for role and accessible_name |

---

### Task 1: Update spec template schema

**Files:**
- Modify: `backend/app/mongo_models/spec_template.py:139-161`
- Test: `backend/tests/test_spec_template_agent.py:17`

- [ ] **Step 1: Update the elements json_schema in DEFAULT_SECTIONS**

In `backend/app/mongo_models/spec_template.py`, find the `page_structure` section's `json_schema` → `items` → `properties` → `elements` → `items` → `properties` block (around lines 154-161). Add `role` and `accessible_name` properties.

Change the `properties` block from:
```python
"properties": {
    "code": {"type": "string", "minLength": 1},
    "type": {"type": "string", "minLength": 1},
    "label": {"type": "string", "minLength": 1},
    "interaction": {"type": "string"},
},
```

To:
```python
"properties": {
    "code": {"type": "string", "minLength": 1},
    "type": {"type": "string", "minLength": 1},
    "label": {"type": "string", "minLength": 1},
    "role": {"type": "string"},
    "accessible_name": {"type": "string"},
    "interaction": {"type": "string"},
},
```

- [ ] **Step 2: Update the agent_prompt for page_structure pages field**

In the same file, find the `agent_prompt` for the `pages` field under `page_structure` section (around line 140). Change from:

```python
"agent_prompt": "列出所有页面。每个页面需包含 name（页面名称）、code（页面编码，短横线格式）、route（路由路径）、elements（元素数组，每个元素含 code/type/label/interaction）",
```

To:

```python
"agent_prompt": "列出所有页面。每个页面需包含 name（页面名称）、code（页面编码，短横线格式）、route（路由路径）、elements（元素数组，每个元素含 code/type/label/role/accessible_name/interaction）。其中 role 为该元素的 ARIA 角色（如 button/textbox/combobox/dialog/table/tab/link/heading/alert/checkbox），accessible_name 为该元素的可访问名称，用于 E2E 测试定位（如\"提交需求审核\"、\"审核人\"、\"任务列表\"）",
```

- [ ] **Step 3: Update the description for pages field**

Change the `description` for the `pages` field from:

```python
"description": "每个页面的名称、编码、元素列表（含唯一编码）、交互行为",
```

To:

```python
"description": "每个页面的名称、编码、元素列表（含唯一编码、ARIA 角色、可访问名称）、交互行为",
```

- [ ] **Step 4: Update the backend test for agent_prompt**

In `backend/tests/test_spec_template_agent.py`, update the expected prompt for `("page_structure", "pages")` (line 17) from:

```python
("page_structure", "pages"): "列出所有页面。每个页面需包含 name（页面名称）、code（页面编码，短横线格式）、route（路由路径）、elements（元素数组，每个元素含 code/type/label/interaction）",
```

To:

```python
("page_structure", "pages"): "列出所有页面。每个页面需包含 name（页面名称）、code（页面编码，短横线格式）、route（路由路径）、elements（元素数组，每个元素含 code/type/label/role/accessible_name/interaction）。其中 role 为该元素的 ARIA 角色（如 button/textbox/combobox/dialog/table/tab/link/heading/alert/checkbox），accessible_name 为该元素的可访问名称，用于 E2E 测试定位（如\"提交需求审核\"、\"审核人\"、\"任务列表\"）",
```

- [ ] **Step 5: Run backend tests to verify**

Run: `conda run -n sdd python -m pytest backend/tests/test_spec_template_agent.py -v`
Expected: All tests PASS (3 tests in the file)

- [ ] **Step 6: Commit**

```bash
git add backend/app/mongo_models/spec_template.py backend/tests/test_spec_template_agent.py
git commit -m "feat: add role and accessible_name fields to spec template page_structure elements"
```

---

### Task 2: Update frontend spec rendering

**Files:**
- Modify: `frontend/src/views/requirement/RequirementDetailPage.vue:112-122`

- [ ] **Step 1: Add role and accessible_name columns to the page structure table**

In `frontend/src/views/requirement/RequirementDetailPage.vue`, find the page_structure table (around lines 112-122). Change the table header and rows from:

```html
<table class="spec-table nested">
  <thead><tr><th>元素编码</th><th>类型</th><th>标签</th><th>交互</th></tr></thead>
  <tbody>
    <tr v-for="(el, ei) in (pg.elements || [])" :key="ei">
      <td><code>{{ el.code }}</code></td>
      <td>{{ el.type }}</td>
      <td>{{ el.label }}</td>
      <td>{{ el.interaction || '' }}</td>
    </tr>
  </tbody>
</table>
```

To:

```html
<table class="spec-table nested">
  <thead><tr><th>元素编码</th><th>类型</th><th>标签</th><th>角色</th><th>可访问名称</th><th>交互</th></tr></thead>
  <tbody>
    <tr v-for="(el, ei) in (pg.elements || [])" :key="ei">
      <td><code>{{ el.code }}</code></td>
      <td>{{ el.type }}</td>
      <td>{{ el.label }}</td>
      <td><code v-if="el.role">{{ el.role }}</code><span v-else class="spec-empty">-</span></td>
      <td>{{ el.accessible_name || '-' }}</td>
      <td>{{ el.interaction || '' }}</td>
    </tr>
  </tbody>
</table>
```

- [ ] **Step 2: Build and verify**

Run: `cd frontend && npx vue-tsc -b && npx vite build`
Expected: Build succeeds (pre-existing TS errors in router/index.ts and TeamMembersTab.vue are acceptable)

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/requirement/RequirementDetailPage.vue
git commit -m "feat: display role and accessible_name in spec page structure rendering"
```

---

### Task 3: Final verification

- [ ] **Step 1: Run all backend tests**

Run: `conda run -n sdd python -m pytest backend/tests/test_spec_template_agent.py backend/tests/test_specifications.py -v`
Expected: All tests PASS

- [ ] **Step 2: Push**

```bash
git push
```
