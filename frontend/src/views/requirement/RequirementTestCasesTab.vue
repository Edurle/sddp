<template>
  <div class="tab-panel">
    <div class="tab-toolbar">
      <button data-testid="req-detail-btn-add-test-case" @click="$emit('add')">添加测试用例</button>
      <select data-testid="req-detail-sel-filter-case-type" :value="filter" @change="onFilterChange(($event.target as HTMLSelectElement).value)">
        <option value="">全部</option>
        <option value="ui_test">UI测试</option>
        <option value="happy_path">正常用例</option>
        <option value="edge_case">边界用例</option>
      </select>
      <button data-testid="req-detail-btn-submit-tests-review" @click="$emit('submit-review')">提交测试审核</button>
      <label class="show-dep-toggle">
        <input
          type="checkbox"
          data-testid="req-detail-chk-show-deprecated"
          :checked="showDeprecated"
          @change="$emit('update:showDeprecated', ($event.target as HTMLInputElement).checked)"
        />
        显示已废弃
      </label>
    </div>
    <table data-testid="req-detail-tbl-test-cases">
      <thead>
        <tr><th>编号</th><th>标题</th><th>类型</th><th>最新结果</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="tc in testCases" :key="tc.id" :class="{ 'tc-deprecated': tc.status === 'deprecated' }">
          <td>{{ tc.case_number }}</td>
          <td>
            <span class="tc-title" @click="$emit('select', tc)">{{ tc.title }}</span>
            <span v-if="tc.status === 'deprecated'" class="tc-dep-badge" data-testid="req-detail-tag-tc-deprecated">已废弃</span>
          </td>
          <td>{{ tc.case_type }}</td>
          <td>
            <span v-if="executionMap[tc.id]" class="spec-tag" :style="resultTagStyle(executionMap[tc.id].status)">{{ tcResultText(executionMap[tc.id].status) }}</span>
            <span v-else class="tc-no-result">未执行</span>
          </td>
          <td>
            <button @click="$emit('view', tc)">查看</button>
            <template v-if="tc.status !== 'deprecated'">
              <button :data-testid="`req-detail-btn-edit-test-case-${tc.id}`" @click="$emit('edit', tc)">编辑</button>
              <button v-if="canDeprecate" :data-testid="`req-detail-btn-deprecate-test-case-${tc.id}`" :disabled="deprecating" @click="$emit('deprecate', tc.id)">废弃</button>
              <button class="btn-danger" :data-testid="`req-detail-btn-delete-test-case-${tc.id}`" :disabled="deleting" @click="$emit('delete', tc.id)">删除</button>
            </template>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="stat-cards" data-testid="req-detail-txt-test-stats">
      <span data-testid="req-detail-tab-test-stats" style="display: none;"></span>
      <div class="stat-card">
        <div class="stat-num">{{ testStats.total_cases ?? 0 }}</div>
        <div class="stat-label">总用例</div>
      </div>
      <div class="stat-card stat-pass">
        <div class="stat-num" data-testid="req-detail-txt-test-pass-count">{{ testStats.latest_results?.passed ?? 0 }}</div>
        <div class="stat-label">通过</div>
      </div>
      <div class="stat-card stat-fail">
        <div class="stat-num" data-testid="req-detail-txt-test-fail-count">{{ testStats.latest_results?.failed ?? 0 }}</div>
        <div class="stat-label">失败</div>
      </div>
      <div class="stat-card stat-skip">
        <div class="stat-num" data-testid="req-detail-txt-test-skip-count">{{ testStats.latest_results?.skipped ?? 0 }}</div>
        <div class="stat-label">跳过</div>
      </div>
      <div class="stat-card stat-rate">
        <div class="stat-num" data-testid="req-detail-txt-test-total-count">{{ testStats.pass_rate != null ? (testStats.pass_rate * 100).toFixed(0) + '%' : 'N/A' }}</div>
        <div class="stat-label">通过率</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface TestCaseItem {
  id: number
  case_number?: string
  title: string
  case_type: string
  precondition?: string
  steps?: string
  expected_result?: string
  related_api?: string
  requirement_id?: number
  status?: string
}

defineProps<{
  testCases: TestCaseItem[]
  testStats: any
  executionMap: Record<number, { status: string; all_results?: any[] }>
  filter: string
  deleting?: boolean
  deprecating?: boolean
  canDeprecate?: boolean
  showDeprecated?: boolean
}>()

const emit = defineEmits<{
  add: []
  'submit-review': []
  'update:filter': [value: string]
  'update:showDeprecated': [value: boolean]
  change: []
  select: [tc: TestCaseItem]
  view: [tc: TestCaseItem]
  edit: [tc: TestCaseItem]
  delete: [id: number]
  deprecate: [id: number]
}>()

function onFilterChange(value: string) {
  emit('update:filter', value)
  emit('change')
}

function tcResultText(status: string) {
  if (status === 'passed') return '通过'
  if (status === 'failed') return '失败'
  if (status === 'skipped') return '跳过'
  return status
}

function resultTagStyle(status: string) {
  if (status === 'passed') return 'background: var(--intent-success-bg); color: var(--intent-success-text)'
  if (status === 'failed') return 'background: var(--intent-danger-bg); color: var(--intent-danger-text)'
  if (status === 'skipped') return 'background: var(--color-surface-muted); color: var(--color-text-muted)'
  return ''
}
</script>

<style scoped>
.tab-panel {
  flex: 1;
}
.tab-toolbar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.75rem;
}
.tc-title {
  cursor: pointer;
  color: var(--color-primary);
}
.tc-title:hover {
  text-decoration: underline;
}
.tc-no-result {
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
}
.show-dep-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  cursor: pointer;
}
.tc-deprecated td {
  opacity: 0.6;
}
.tc-deprecated .tc-title {
  text-decoration: line-through;
  color: var(--color-text-subtle);
}
.tc-dep-badge {
  display: inline-block;
  margin-left: 8px;
  padding: 1px 8px;
  border-radius: var(--radius-pill);
  font-size: var(--text-2xs);
  font-weight: 600;
  background: var(--intent-neutral-bg);
  color: var(--color-text-subtle);
  vertical-align: middle;
}
.spec-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-md);
  font-size: var(--text-2xs);
  font-weight: 500;
  margin-right: var(--space-1);
  white-space: nowrap;
}
.stat-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
  margin-top: 1rem;
  flex-shrink: 0;
}
.stat-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.75rem;
  text-align: center;
}
.stat-num {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--color-text);
}
.stat-label {
  font-size: var(--text-2xs);
  color: var(--color-text-subtle);
  margin-top: 2px;
}
.stat-pass .stat-num { color: var(--intent-success-text); }
.stat-fail .stat-num { color: var(--color-danger); }
.stat-skip .stat-num { color: var(--intent-warning-text); }
.stat-rate .stat-num { color: var(--color-primary); }

@media (max-width: 768px) {
  .stat-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
