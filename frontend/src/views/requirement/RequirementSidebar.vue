<template>
  <aside class="req-sidebar" data-testid="req-detail-sidebar">
    <div class="sidebar-section">
      <div class="sidebar-label">进度</div>
      <div class="step-list">
        <div
          v-for="step in steps"
          :key="step.key"
          :data-testid="`req-detail-step-nav-step-${step.key}`"
          class="step-item"
          :class="stepClass(step.key)"
        >
          <span class="step-circle">{{ stepCircle(step.key) }}</span>
          <span class="step-text">{{ step.label }}</span>
        </div>
      </div>
    </div>

    <div class="sidebar-section">
      <div class="sidebar-label">基本信息</div>
      <div class="info-card">
        <template v-if="!editing">
          <h2 class="info-title" data-testid="req-detail-txt-title">{{ req.title }}</h2>
          <div class="info-badges">
            <AppBadge data-testid="req-detail-tag-type" :text="typeLabel(req.type)" />
            <AppBadge data-testid="req-detail-txt-priority" :text="priorityLabel(req.priority)" />
            <span data-testid="req-detail-tag-status" class="status-tag">{{ statusLabel(req.status) }}</span>
          </div>
          <p class="info-desc" data-testid="req-detail-txt-description">{{ req.description }}</p>
          <p data-testid="req-detail-txt-review-status" class="status-text">{{ statusLabel(req.status) }}</p>

          <div v-if="req.type === 'bug' && req.type_detail" class="type-detail">
            <p data-testid="req-detail-txt-reproduce-steps">{{ req.type_detail.reproduce_steps }}</p>
            <p data-testid="req-detail-txt-environment">{{ req.type_detail.environment }}</p>
            <p data-testid="req-detail-txt-severity">{{ req.type_detail.severity }}</p>
          </div>
          <div v-if="req.type === 'optimization' && req.type_detail" class="type-detail">
            <p data-testid="req-detail-txt-optimization-issue">{{ req.type_detail.current_issue }}</p>
            <p data-testid="req-detail-txt-optimization-expected">{{ req.type_detail.expected_improvement }}</p>
          </div>
        </template>
        <template v-else>
          <div class="form-group">
            <label>标题</label>
            <input v-model="editForm.title" data-testid="req-detail-inp-title" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="editForm.description" data-testid="req-detail-txtarea-description"></textarea>
          </div>
        </template>
      </div>
    </div>

    <div v-if="rejectReason" class="sidebar-section">
      <div class="info-card reject-card">
        <p data-testid="req-detail-txt-reject-reason">{{ rejectReason }}</p>
      </div>
    </div>

    <div v-if="reviewHistory.length" class="sidebar-section">
      <div class="sidebar-label">审核历史</div>
      <div class="info-card" data-testid="req-detail-list-review-history">
        <div v-for="(review, idx) in reviewHistory" :key="idx" class="review-item">
          <span :class="['review-dot', review.action === 'approve' ? 'dot-pass' : 'dot-reject']">●</span>
          <span class="review-text">{{ review.action === 'approve' ? '通过' : '驳回' }}</span>
          <span v-if="review.comment" class="review-comment"> — {{ review.comment }}</span>
        </div>
      </div>
    </div>

    <div class="sidebar-section sidebar-actions">
      <div class="sidebar-label">操作</div>
      <div class="action-buttons">
        <button v-if="canEdit && !editing" data-testid="req-detail-btn-edit-req" @click="$emit('edit')">编辑需求</button>
        <button v-if="editing" data-testid="req-detail-btn-save-req" @click="$emit('save')">保存</button>
        <button v-if="canEdit" data-testid="req-detail-btn-delete-req" @click="$emit('delete')">删除</button>
        <button v-if="canEdit" data-testid="req-detail-btn-submit-req-review" @click="$emit('submit-review')">提交审核</button>
        <button v-if="canReview" data-testid="req-detail-btn-approve" @click="$emit('approve')">通过</button>
        <button v-if="canReview" data-testid="req-detail-btn-reject" @click="$emit('reject')">驳回</button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import AppBadge from '@/components/common/AppBadge.vue'

interface TypeDetail {
  reproduce_steps?: string
  environment?: string
  severity?: string
  current_issue?: string
  expected_improvement?: string
  metrics?: string
}

interface Review {
  id?: number
  action?: string
  comment?: string
  reviewer_id?: number
  review_type?: string
  status?: string
}

interface RequirementData {
  id: number
  title: string
  type: string
  priority: string | number
  status: string
  description: string
  type_detail?: TypeDetail | null
  reviews?: Review[]
  iteration_id?: number
  req_type?: string
}

const props = defineProps<{
  req: RequirementData
  editing: boolean
  editForm: { title: string; description: string }
}>()

defineEmits(['edit', 'save', 'delete', 'submit-review', 'approve', 'reject'])

const steps = [
  { key: 'req', label: '需求' },
  { key: 'spec', label: '规范' },
  { key: 'tests', label: '测试' },
  { key: 'approved', label: '已通过' },
]

const canEdit = computed(() => props.req.status === 'drafting_req')
const canReview = computed(() =>
  ['reviewing_req', 'reviewing_spec', 'reviewing_tests'].includes(props.req.status),
)

const reviewHistory = computed(() =>
  (props.req.reviews || []).map((r) => ({
    ...r,
    action: r.action || (r.status === 'approved' ? 'approve' : r.status === 'rejected' ? 'reject' : r.status),
  })),
)

const rejectReason = computed(() => {
  const last = [...reviewHistory.value].reverse().find((r) => r.action === 'reject')
  return last?.comment || ''
})

function typeLabel(type: string) {
  const map: Record<string, string> = { feature: '功能需求', bug: 'Bug', optimization: '优化' }
  return map[type] || type
}

function priorityLabel(p: string | number) {
  const map: Record<string, string> = { high: '高优先', 3: '高优先', medium: '中优先', 2: '中优先', low: '低优先', 1: '低优先' }
  return map[String(p)] || String(p)
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    drafting_req: '草稿',
    reviewing_req: '审核中',
    drafting_spec: '编写规范',
    reviewing_spec: '规范审核中',
    drafting_tests: '编写测试用例',
    reviewing_tests: '测试审核中',
    approved: '已通过',
    spec_approved: '规范已通过',
  }
  return map[status] || status
}

function stepClass(step: string) {
  const s = props.req.status || ''
  if (step === 'req') {
    if (s === 'drafting_req') return 'current'
    if (s === 'reviewing_req') return 'current review'
    if (['drafting_spec', 'reviewing_spec', 'drafting_tests', 'reviewing_tests', 'approved', 'spec_approved'].includes(s)) return 'done'
  }
  if (step === 'spec') {
    if (s === 'drafting_spec') return 'current'
    if (s === 'reviewing_spec') return 'current review'
    if (['drafting_tests', 'reviewing_tests', 'approved', 'spec_approved'].includes(s)) return 'done'
  }
  if (step === 'tests') {
    if (s === 'drafting_tests') return 'current'
    if (s === 'reviewing_tests') return 'current review'
    if (['approved', 'spec_approved'].includes(s)) return 'done'
  }
  if (step === 'approved') {
    if (s === 'approved' || s === 'spec_approved') return 'done current'
  }
  return ''
}

function stepCircle(step: string) {
  const cls = stepClass(step)
  if (cls.includes('done')) return '✓'
  const idx = steps.findIndex((s) => s.key === step)
  return String(idx + 1)
}
</script>

<style scoped>
.req-sidebar {
  width: 280px;
  flex-shrink: 0;
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  padding: 1rem;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.01);
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.sidebar-label {
  font-size: 11px;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  font-weight: 600;
}
.info-card {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  padding: 0.75rem;
}
.info-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #111;
}
.info-badges {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}
.status-tag {
  background: #f0f0f0;
  color: #666;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 0.8em;
  font-weight: 500;
}
.status-text {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}
.info-desc {
  color: #666;
  font-size: 13px;
  line-height: 1.5;
}
.type-detail {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(0, 0, 0, 0.04);
  font-size: 12px;
  color: #666;
}
.type-detail p {
  margin-bottom: 4px;
}
.reject-card {
  background: #fff2f0;
  border-color: #ffccc7;
  color: #cf1322;
}
.step-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  font-size: 12px;
  background: #f0f0f0;
  color: #999;
  transition: all 0.2s;
}
.step-circle {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  background: #ddd;
  color: #999;
  flex-shrink: 0;
}
.step-item.current {
  background: #1677ff;
  color: #fff;
}
.step-item.current .step-circle {
  background: rgba(255, 255, 255, 0.3);
  color: #fff;
}
.step-item.review {
  background: #722ed1;
}
.step-item.done {
  background: #111;
  color: #fff;
}
.step-item.done .step-circle {
  background: #fff;
  color: #111;
}
.review-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  font-size: 12px;
  margin-bottom: 6px;
  line-height: 1.5;
}
.review-item:last-child {
  margin-bottom: 0;
}
.review-dot {
  flex-shrink: 0;
  line-height: 1.5;
}
.dot-pass {
  color: #52c41a;
}
.dot-reject {
  color: #ff4d4f;
}
.review-text {
  color: #333;
}
.review-comment {
  color: #999;
}
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.action-buttons button {
  width: 100%;
  margin: 0;
  font-size: 12px;
  padding: 6px 12px;
}

@media (max-width: 768px) {
  .req-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  }
}
</style>
