# Frontend Usability & Readability Optimization Design

## Overview

Comprehensive UX optimization covering 17 issues across 5 groups: bug fixes, error feedback, navigation, consistency, and experience details.

---

## Group 1: P0 Bug Fixes

### 1.1 removeMember doesn't call API
**File:** `frontend/src/views/team/TeamMembersTab.vue:212`
**Fix:** Add actual API call `await apiClient.delete(...)` before removing from local array.

### 1.2 completeError never displayed
**File:** `frontend/src/views/task/TaskDetailPage.vue:309`
**Fix:** Add error message display in template below action buttons.

### 1.3 working stat hardcoded to 0
**File:** `frontend/src/views/dashboard/DashboardPage.vue:284`
**Fix:** Remove the `working` stat card since "起草中" is already covered by "草稿中" (drafting_req/spec/tests). Replace with a more useful stat like "总需求" count, or correctly compute "审核中" vs "起草中" from the status breakdown.

### 1.4 completeIteration fires API before confirm
**File:** `frontend/src/views/iteration/IterationListTab.vue` (within IterationListTab component)
**Fix:** Move API call inside confirm callback — only fire after user confirms.

---

## Group 2: Error Feedback + Global Fixes

### 2.1 Global error toast
- Add a notification store (`src/stores/notification.ts`) with `showError(msg)` and `showSuccess(msg)` actions
- Add notification display area in `AppLayout.vue` (fixed position, top-right, auto-dismiss after 3s)
- Replace all `catch { // ignore }` blocks with `catch(e) { showError(e.message || '操作失败') }`
- Key files: DashboardPage, RequirementDetailPage, TaskDetailPage, ProjectDetailPage, TeamDetailPage, TeamMembersTab, IterationListTab

### 2.2 Global button style fix
**File:** `frontend/src/main.css`
- Remove the fragile `button[type="button"]:not([class*="active"])` rule (line 115-119)
- Keep the base `button` rule for common styling (font, cursor, border-radius)
- Ensure scoped button overrides work without fighting global specificity

### 2.3 Dialog responsive fix
**File:** `frontend/src/main.css:224`
- Change `.dialog` from `min-width: 440px` to `min-width: 0; max-width: 90vw; width: auto`

### 2.4 height: 100vh overflow fix
**Files:** `RequirementDetailPage.vue:960`, `TaskDetailPage.vue:362`
- Change `height: 100vh; overflow: hidden` to `min-height: 100vh`
- Remove `overflow: hidden` or change to `overflow-x: hidden`

### 2.5 Admin nav link
**File:** `frontend/src/views/layout/AppLayout.vue`
- Add `v-if="user?.is_admin"` link to `/admin` in the nav bar

---

## Group 3: Navigation + CTA

### 3.1 Breadcrumbs
**File:** `frontend/src/views/layout/AppLayout.vue`
- Add breadcrumb bar below nav, above main content
- Parse current route to build hierarchy: 仪表盘 / 项目名 / 迭代名 / 需求名
- Use route params (project ID, iteration ID, requirement ID) to resolve names
- Each level is a clickable router-link

Implementation approach: Create a `BreadcrumbBar.vue` component that watches `$route` and builds breadcrumb items from route meta + params. Routes can define `meta.breadcrumb` with label and parent route info.

### 3.2 Clickable pending items
**File:** `frontend/src/views/dashboard/DashboardPage.vue:130-139`
- Wrap pending review items in `<router-link :to="/requirements/${item.requirement_id}">`
- Wrap pending task items in `<router-link :to="/tasks/${item.id}">`
- Add status badge and date to each item

### 3.3 Empty state CTAs
Replace all dead-end empty states with actionable ones:
- "暂无项目" → "暂无项目" + link to team detail where projects can be created
- "暂无迭代" → "暂无迭代" + link to create iteration
- "暂无需求" → "暂无需求" + link to create requirement
- "暂无待审核项" → text only, no CTA needed (this is informational)
- "暂无待办任务" → text only
- "暂无待处理邀请" → text only

---

## Group 4: Consistency + Shared Utils

### 4.1 Shared status label utility
**New file:** `frontend/src/utils/status.ts`
```typescript
export function reqStatusLabel(status: string): string {
  const map: Record<string, string> = {
    drafting_req: '草稿', reviewing_req: '需求审核', drafting_spec: '编写规范',
    reviewing_spec: '规范审核', drafting_tests: '编写测试', reviewing_tests: '测试审核',
    approved: '已通过',
  }
  return map[status] || status
}

export function taskStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待执行', coding: '编码中', testing: '测试中', completed: '已完成',
  }
  return map[status] || status
}

export function iterStatusLabel(status: string): string {
  const map: Record<string, string> = {
    planning: '规划中', in_progress: '进行中', completed: '已完成',
  }
  return map[status] || status
}
```

Delete duplicate definitions from: DashboardPage, RequirementSidebar, IterationKanbanPage, TaskSidebar, ProjectDetailPage.

### 4.2 Unified tab style
All pages use underline-style tabs (current dashboard pattern):
- DashboardPage: already correct
- RequirementDetailPage: already correct
- TaskDetailPage: already correct
- TeamDetailPage: change from pill style (`.tab-buttons`) to underline style (`.tabs`)
- Ensure consistent CSS class names across pages

### 4.3 Raw English status → Chinese labels
All `{{ req.status }}` and `{{ task.status }}` in templates should use the shared utility:
- `{{ reqStatusLabel(req.status) }}` instead of `{{ req.status }}`
- `{{ taskStatusLabel(task.status) }}` instead of `{{ task.status }}`

Key files: RequirementDetailPage, IterationKanbanPage, TaskDetailPage

### 4.4 Test stat cards moved inside tab
**File:** `RequirementDetailPage.vue:254-276`
- Move the test statistics cards from outside all tab panels to inside the test-cases tab panel

---

## Group 5: Loading + Polish

### 5.1 Loading indicators
Add `isLoading` ref to key pages:
- DashboardPage (projects tree fetch)
- RequirementDetailPage (requirement + spec fetch)
- TaskDetailPage (task + test data fetch)
- ProjectDetailPage (project data fetch)
- TeamDetailPage (team data fetch)

Display a simple "加载中..." text or spinner when `isLoading` is true, hide content.

### 5.2 Priority display unified
**File:** `IterationKanbanPage.vue`
- Replace raw `{{ req.priority }}` number with colored label: 高(红)/中(黄)/低(绿)
- Match dashboard's priority dot style

### 5.3 Review timeline dedup
**Files:** `RequirementSidebar.vue`, `RequirementDetailPage.vue`
- Remove review history display from sidebar (lines showing duplicate data)
- Keep the review timeline in the detail page only

---

## Implementation Order

1. Group 1 (P0 bugs) — 4 targeted fixes
2. Group 2 (error feedback + globals) — affects all pages
3. Group 4 (consistency) — shared utils + style fixes
4. Group 3 (navigation + CTA) — breadcrumbs + links
5. Group 5 (loading + polish) — final touches

## Scope

~30 file changes across the frontend. No backend changes needed.
