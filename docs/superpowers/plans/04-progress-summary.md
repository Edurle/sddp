# Plan 4: Progress Summary View

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans.

**Goal:** Add a "进度" tab to the dashboard with stat cards at top + expandable requirement list below, showing lifecycle progress per requirement.

**Spec section:** "4. Progress Summary View" in `docs/superpowers/specs/2026-05-16-agent-collaboration-design.md`

**Depends on:** Nothing (frontend only, reuses existing `GET /me/projects-tree` API).

---

### Task 4.1: Add "进度" Tab to Dashboard

**Files:**
- Modify: `frontend/src/views/dashboard/DashboardPage.vue`

This is the only file that needs modification. The changes are:
1. Add a new "进度" tab button
2. Add the progress tab content with stat cards + expandable list
3. Add supporting TypeScript logic
4. Add scoped CSS styles

- [ ] **Step 1: Add tab button**

In the `.tabs` div, add after the "项目总览" button:

```html
<button data-testid="dashboard-tab-progress" :class="{ active: activeTab === 'progress' }" @click="activeTab = 'progress'">进度</button>
```

- [ ] **Step 2: Add progress tab content**

After the `v-if="activeTab === 'projects'"` div, add the progress tab:

```html
<div v-if="activeTab === 'progress'">
  <div class="stat-cards">
    <div class="stat-card stat-draft">
      <div class="stat-number">{{ progressStats.drafting }}</div>
      <div class="stat-label">草稿中</div>
    </div>
    <div class="stat-card stat-review">
      <div class="stat-number">{{ progressStats.reviewing }}</div>
      <div class="stat-label">审核中</div>
    </div>
    <div class="stat-card stat-work">
      <div class="stat-number">{{ progressStats.working }}</div>
      <div class="stat-label">起草中</div>
    </div>
    <div class="stat-card stat-approved">
      <div class="stat-number">{{ progressStats.approved }}</div>
      <div class="stat-label">已通过</div>
    </div>
  </div>

  <div v-if="flatRequirements.length === 0" class="empty-state">暂无需求</div>
  <div v-for="group in iterationGroups" :key="group.iterationName" class="progress-iteration-group">
    <div class="progress-iteration-label">{{ group.iterationName }}</div>
    <div class="progress-req-list">
      <div v-for="req in group.items" :key="req.id" class="progress-req-card">
        <div class="progress-req-header" @click="toggleExpand('pr', req.id)">
          <span class="expand-icon">{{ isExpanded('pr', req.id) ? '▼' : '▶' }}</span>
          <router-link :to="`/requirements/${req.id}`" class="progress-req-title">{{ req.title }}</router-link>
          <span class="progress-req-status" :class="'prs-' + req.status">{{ statusLabel(req.status) }}</span>
          <span class="priority-indicator" :class="'pi-' + req.priority"></span>
        </div>
        <div v-if="isExpanded('pr', req.id)" class="progress-req-detail">
          <div class="progress-stages">
            <template v-for="(s, i) in lifecycleStages" :key="i">
              <span class="stage-item" :class="stageClass(req.status, s.status)">{{ s.label }}</span>
              <span v-if="i < lifecycleStages.length - 1" class="stage-arrow">→</span>
            </template>
          </div>
          <div v-if="req.tasks && req.tasks.length > 0" class="progress-task-summary">
            {{ req.tasks.length }}个任务 · {{ completedTasks(req) }}已完成
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

- [ ] **Step 3: Add computed properties and data**

In the `<script setup>` section, add:

```typescript
const lifecycleStages = [
  { status: 'drafting_req', label: '草稿' },
  { status: 'reviewing_req', label: '需求审核' },
  { status: 'drafting_spec', label: '编写规范' },
  { status: 'reviewing_spec', label: '规范审核' },
  { status: 'drafting_tests', label: '编写测试' },
  { status: 'reviewing_tests', label: '测试审核' },
  { status: 'approved', label: '已通过' },
]

const STATUS_LABELS_MAP: Record<string, string> = {
  drafting_req: '草稿', reviewing_req: '需求审核', drafting_spec: '编写规范',
  reviewing_spec: '规范审核', drafting_tests: '编写测试', reviewing_tests: '测试审核',
  approved: '已通过',
}

const flatRequirements = computed(() => {
  const items: any[] = []
  for (const proj of projectsTree.value) {
    for (const iter of proj.iterations) {
      for (const req of iter.requirements) {
        items.push({ ...req, _iterationName: iter.name })
      }
    }
  }
  return items
})

const iterationGroups = computed(() => {
  const map = new Map<string, any[]>()
  for (const req of flatRequirements.value) {
    const key = req._iterationName
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(req)
  }
  return Array.from(map.entries()).map(([iterationName, items]) => ({ iterationName, items }))
})

const progressStats = computed(() => {
  const all = flatRequirements.value
  return {
    drafting: all.filter(r => ['drafting_req', 'drafting_spec', 'drafting_tests'].includes(r.status)).length,
    reviewing: all.filter(r => ['reviewing_req', 'reviewing_spec', 'reviewing_tests'].includes(r.status)).length,
    working: 0,
    approved: all.filter(r => r.status === 'approved').length,
  }
})

function statusLabel(s: string): string {
  return STATUS_LABELS_MAP[s] || s
}

function stageClass(currentStatus: string, stageStatus: string): string {
  const order = lifecycleStages.map(s => s.status)
  const currentIdx = order.indexOf(currentStatus)
  const stageIdx = order.indexOf(stageStatus)
  if (stageIdx < currentIdx) return 'stage-done'
  if (stageIdx === currentIdx) return 'stage-current'
  return 'stage-pending'
}

function completedTasks(req: any): number {
  if (!req.tasks) return 0
  return req.tasks.filter((t: any) => t.status === 'completed').length
}
```

- [ ] **Step 4: Add scoped CSS**

```css
.stat-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  flex: 1;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}
.stat-number {
  font-size: 28px;
  font-weight: 700;
}
.stat-label {
  font-size: 13px;
  margin-top: 4px;
}
.stat-draft { background: #f3f4f6; color: #4b5563; }
.stat-review { background: #fef3c7; color: #92400e; }
.stat-work { background: #eff6ff; color: #1e40af; }
.stat-approved { background: #f0fdf4; color: #166534; }

.progress-iteration-group {
  margin-bottom: 24px;
}
.progress-iteration-label {
  font-size: 14px;
  font-weight: 600;
  color: #666;
  margin-bottom: 12px;
  padding-left: 4px;
}
.progress-req-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.progress-req-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
}
.progress-req-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
}
.progress-req-title {
  font-weight: 600;
  color: #111;
  text-decoration: none;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}
.progress-req-title:hover { color: #4f46e5; }
.progress-req-status {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 500;
  flex-shrink: 0;
}
.prs-drafting_req, .prs-drafting_spec, .prs-drafting_tests { background: #f3f4f6; color: #666; }
.prs-reviewing_req, .prs-reviewing_spec, .prs-reviewing_tests { background: #fef3c7; color: #92400e; }
.prs-approved { background: #dcfce7; color: #166534; }
.priority-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-left: auto;
  flex-shrink: 0;
}
.pi-3 { background: #ef4444; }
.pi-2 { background: #f59e0b; }
.pi-1 { background: #22c55e; }

.progress-req-detail {
  padding: 0 16px 16px 40px;
  border-top: 1px solid #f3f4f6;
}
.progress-stages {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
  overflow-x: auto;
  padding-top: 12px;
  margin-bottom: 8px;
}
.stage-item {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 6px;
  white-space: nowrap;
  flex-shrink: 0;
}
.stage-done { background: #dcfce7; color: #166534; }
.stage-current { background: #3b82f6; color: white; font-weight: 600; }
.stage-pending { background: #f3f4f6; color: #aaa; }
.stage-arrow {
  font-size: 11px;
  color: #d1d5db;
  flex-shrink: 0;
}
.progress-task-summary {
  font-size: 12px;
  color: #888;
}
```

- [ ] **Step 5: Build frontend**

Run: `cd frontend && npx vue-tsc -b && npx vite build`
Expected: Build succeeds (only pre-existing TS errors acceptable)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/dashboard/DashboardPage.vue
git commit -m "feat: add progress summary tab with stat cards and expandable list"
```
