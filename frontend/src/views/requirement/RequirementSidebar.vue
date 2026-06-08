<template>
  <aside class="req-sidebar" data-testid="req-detail-sidebar">
    <div class="sidebar-section">
      <div class="sidebar-label">进度</div>
      <div class="step-list" data-testid="req-detail-step-nav">
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
            <span data-testid="req-detail-tag-status" class="status-tag">{{ reqStatusLabel(req.status) }}</span>
          </div>
          <p class="info-desc" data-testid="req-detail-txt-description">{{ req.description }}</p>
          <p data-testid="req-detail-txt-review-status" class="status-text">{{ reqStatusLabel(req.status) }}</p>

          <div v-if="!editing && req.prototype_html" class="prototype-section">
            <div class="prototype-header">
              <span class="sidebar-label" style="margin: 0;">原型图</span>
              <button class="prototype-zoom-btn" @click="showPrototypeModal = true" title="放大查看">⛶</button>
            </div>
            <iframe
              :srcdoc="req.prototype_html"
              sandbox="allow-scripts"
              class="prototype-iframe"
              data-testid="req-detail-prototype-preview"
            ></iframe>
          </div>

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
          <div class="form-group">
            <label>原型图 HTML</label>
            <textarea v-model="editForm.prototype_html" data-testid="req-detail-txtarea-prototype-html" class="prototype-textarea" placeholder="输入 HTML 代码作为页面原型图"></textarea>
            <div v-if="editForm.prototype_html" class="prototype-preview-edit">
              <iframe :srcdoc="editForm.prototype_html" sandbox="allow-scripts" class="prototype-iframe"></iframe>
            </div>
          </div>
        </template>
      </div>
    </div>

    <div v-if="rejectReason" class="sidebar-section">
      <div class="info-card reject-card">
        <p data-testid="req-detail-txt-reject-reason">{{ rejectReason }}</p>
      </div>
    </div>

    <div class="sidebar-section sidebar-actions">
      <div class="sidebar-label">操作</div>
      <div class="action-buttons">
        <button v-if="canEdit && !editing" data-testid="req-detail-btn-edit-req" @click="$emit('edit')">编辑需求</button>
        <button v-if="editing" data-testid="req-detail-btn-save-req" @click="$emit('save')">保存</button>
        <button v-if="canEdit" data-testid="req-detail-btn-delete-req" class="btn-danger" @click="$emit('delete')">删除</button>
        <button v-if="canEdit" data-testid="req-detail-btn-submit-req-review" @click="$emit('submit-review')">提交审核</button>
        <button v-if="canReview" data-testid="req-detail-btn-approve" @click="$emit('approve')">通过</button>
        <button v-if="canReview" data-testid="req-detail-btn-reject" @click="$emit('reject')">驳回</button>
        <button v-if="canSupersede" data-testid="req-detail-btn-supersede" @click="$emit('supersede')">创建变更</button>
      </div>
    </div>

    <div v-if="showPrototypeModal" class="prototype-modal-overlay" @click.self="showPrototypeModal = false">
      <div class="prototype-modal">
        <div class="prototype-modal-header">
          <span class="prototype-modal-title">原型图 - {{ req.title }}</span>
          <button class="prototype-modal-close" @click="showPrototypeModal = false">✕</button>
        </div>
        <iframe
          :srcdoc="req.prototype_html ?? undefined"
          sandbox="allow-scripts"
          class="prototype-modal-iframe"
        ></iframe>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import AppBadge from '@/components/common/AppBadge.vue'
import { reqStatusLabel } from '@/utils/status'

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
  prototype_html?: string | null
  reviews?: Review[]
  iteration_id?: number
  req_type?: string
}

const props = defineProps<{
  req: RequirementData
  editing: boolean
  editForm: { title: string; description: string; prototype_html: string }
}>()

defineEmits(['edit', 'save', 'delete', 'submit-review', 'approve', 'reject', 'supersede'])

const showPrototypeModal = ref(false)

const steps = [
  { key: 'drafting_req', label: '编写需求' },
  { key: 'reviewing_req', label: '需求审核' },
  { key: 'drafting_spec', label: '编写规范' },
  { key: 'reviewing_spec', label: '规范审核' },
  { key: 'drafting_tests', label: '编写测试' },
  { key: 'reviewing_tests', label: '测试审核' },
  { key: 'approved', label: '已通过' },
  { key: 'deprecated', label: '已废弃' },
]

const canEdit = computed(() => props.req.status === 'drafting_req')
const canReview = computed(() =>
  ['reviewing_req', 'reviewing_spec', 'reviewing_tests'].includes(props.req.status),
)
const canSupersede = computed(() => props.req.status === 'approved')

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

function stepClass(step: string) {
  const s = props.req.status || ''
  if (s === 'deprecated' && step === 'deprecated') return 'current deprecated'
  const order = ['drafting_req', 'reviewing_req', 'drafting_spec', 'reviewing_spec', 'drafting_tests', 'reviewing_tests', 'approved']
  const currentIdx = order.indexOf(s)
  const stepIdx = order.indexOf(step)
  if (currentIdx < 0 || stepIdx < 0) return ''
  if (stepIdx < currentIdx) return 'done'
  if (stepIdx === currentIdx) {
    return step.includes('reviewing') ? 'current review' : 'current'
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
.step-item.deprecated {
  background: #ff4d4f;
  color: #fff;
}
.step-item.deprecated .step-circle {
  background: rgba(255, 255, 255, 0.3);
  color: #fff;
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
.prototype-section {
  margin-top: 4px;
}
.prototype-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
  margin-bottom: 0.5rem;
}
.prototype-zoom-btn {
  background: transparent;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  padding: 2px 6px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  line-height: 1;
}
.prototype-zoom-btn:hover {
  background: rgba(0, 0, 0, 0.04);
  color: #111;
}
.prototype-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.prototype-modal {
  background: #fff;
  border-radius: 12px;
  width: 95vw;
  max-width: 900px;
  height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}
.prototype-modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  flex-shrink: 0;
}
.prototype-modal-title {
  font-size: 14px;
  font-weight: 600;
  color: #111;
}
.prototype-modal-close {
  background: transparent;
  border: none;
  font-size: 18px;
  color: #999;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}
.prototype-modal-close:hover {
  background: rgba(0, 0, 0, 0.04);
  color: #333;
}
.prototype-modal-iframe {
  flex: 1;
  border: none;
  border-radius: 0 0 12px 12px;
  width: 100%;
}
.prototype-iframe {
  width: 100%;
  height: 200px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  background: #fff;
}
.prototype-textarea {
  min-height: 80px;
  font-family: monospace;
  font-size: 11px;
}
.prototype-preview-edit {
  margin-top: 6px;
}
.btn-danger {
  background: #fef2f2 !important;
  color: #dc2626 !important;
  border: 1px solid #fecaca;
}

@media (max-width: 768px) {
  .req-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  }
}
</style>
