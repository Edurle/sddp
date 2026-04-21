<template>
  <div class="requirement-detail-page">
    <h1>需求详情</h1>
    <div v-if="req">
      <div class="step-nav">
        <span data-testid="req-detail-step-nav-step-req" class="step" :class="stepClass('req')">需求</span>
        <span data-testid="req-detail-step-nav-step-spec" class="step" :class="stepClass('spec')">规范</span>
        <span data-testid="req-detail-step-nav-step-tests" class="step" :class="stepClass('tests')">测试</span>
        <span data-testid="req-detail-step-nav-step-approved" class="step" :class="stepClass('approved')">已通过</span>
      </div>

      <div class="main-info">
        <template v-if="!editingReq">
          <h2 data-testid="req-detail-txt-title">{{ req.title }}</h2>
          <AppBadge data-testid="req-detail-tag-type" :text="typeLabel(req.type)" />
          <p data-testid="req-detail-txt-priority">{{ req.priority }}</p>
          <p data-testid="req-detail-txt-description">{{ req.description }}</p>
          <span data-testid="req-detail-tag-status">{{ statusLabel(req.status) }}</span>
          <p data-testid="req-detail-txt-review-status">{{ statusLabel(req.status) }}</p>
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

      <div v-if="req.type === 'bug' && req.type_detail" class="type-detail">
        <p data-testid="req-detail-txt-reproduce-steps">{{ req.type_detail.reproduce_steps }}</p>
        <p data-testid="req-detail-txt-environment">{{ req.type_detail.environment }}</p>
        <p data-testid="req-detail-txt-severity">{{ req.type_detail.severity }}</p>
      </div>

      <div v-if="req.type === 'optimization' && req.type_detail" class="type-detail">
        <p data-testid="req-detail-txt-optimization-issue">{{ req.type_detail.current_issue }}</p>
        <p data-testid="req-detail-txt-optimization-expected">{{ req.type_detail.expected_improvement }}</p>
      </div>

      <div v-if="rejectReason" class="reject-info">
        <p data-testid="req-detail-txt-reject-reason">{{ rejectReason }}</p>
      </div>

      <div class="actions">
        <button v-if="canEdit" data-testid="req-detail-btn-edit-req" @click="startEditReq">编辑</button>
        <button v-if="editingReq" data-testid="req-detail-btn-save-req" @click="saveReq">保存</button>
        <button v-if="canEdit" data-testid="req-detail-btn-delete-req" @click="deleteReq">删除</button>
        <button v-if="canEdit" data-testid="req-detail-btn-submit-req-review" @click="showSubmitReviewDialog = true">提交审核</button>
        <button v-if="canReview" data-testid="req-detail-btn-approve" @click="approveReview">通过</button>
        <button v-if="canReview" data-testid="req-detail-btn-reject" @click="showRejectDialog = true">驳回</button>
      </div>

      <div v-if="reviewHistory.length" class="review-history">
        <h3>审核历史</h3>
        <div data-testid="req-detail-list-review-history">
          <div v-for="(review, idx) in reviewHistory" :key="idx">
            <span>{{ review.action === 'approve' ? '通过' : '驳回' }}</span>
            <span v-if="review.comment"> - {{ review.comment }}</span>
          </div>
        </div>
      </div>

      <div v-if="req.status === 'drafting_spec' || req.status === 'reviewing_spec' || req.status === 'approved' || req.status === 'spec_approved'" class="tabs-section">
        <button data-testid="req-detail-tab-spec" :class="{ active: activeTab === 'spec' }" @click="activeTab = 'spec'">规范</button>
        <button data-testid="req-detail-tab-spec-versions" :class="{ active: activeTab === 'spec-versions' }" @click="activeTab = 'spec-versions'; fetchSpecVersions()">规范版本</button>
        <button data-testid="req-detail-tab-tasks" :class="{ active: activeTab === 'tasks' }" @click="activeTab = 'tasks'; fetchTasks()">任务</button>

        <div v-if="activeTab === 'spec'" class="tab-content">
          <textarea v-model="specContent" data-testid="req-detail-txtarea-spec-content"></textarea>
          <button data-testid="req-detail-btn-save-spec" @click="saveSpec">保存规范</button>
          <button v-if="req.status === 'drafting_spec'" data-testid="req-detail-btn-submit-spec-review" @click="showSubmitSpecReviewDialog = true">提交规范审核</button>
        </div>

        <div v-if="activeTab === 'spec-versions'" class="tab-content">
          <div data-testid="req-detail-list-spec-versions">
            <div v-for="(ver, idx) in specVersions" :key="idx">
              <button :data-testid="`req-detail-btn-spec-version-${idx + 1}`" @click="viewSpecVersion(ver)">
                v{{ idx + 1 }}
              </button>
            </div>
          </div>
          <div v-if="selectedVersionContent" data-testid="req-detail-txt-spec-version-content">
            {{ selectedVersionContent }}
          </div>
        </div>

        <div v-if="activeTab === 'tasks'" class="tab-content">
          <button data-testid="req-detail-btn-add-task" @click="showAddTaskDialog = true">添加任务</button>
          <table data-testid="req-detail-tbl-tasks">
            <thead>
              <tr><th>标题</th><th>状态</th></tr>
            </thead>
            <tbody>
              <tr v-for="task in tasks" :key="task.id">
                <td>{{ task.title }}</td>
                <td>{{ task.status }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <div v-if="showSubmitReviewDialog" class="dialog-overlay" @click.self="showSubmitReviewDialog = false">
      <div data-testid="req-detail-dlg-submit-review" class="dialog">
        <h3>提交审核</h3>
        <select v-model="submitReviewForm.reviewer_id" data-testid="req-detail-dlg-submit-review-sel-reviewer">
          <option value="">请选择审核人</option>
          <option v-for="m in reviewers" :key="m.id" :value="m.id">{{ m.nickname || m.email }}</option>
        </select>
        <button data-testid="req-detail-dlg-submit-review-btn-confirm" @click="submitReview">确认</button>
        <button @click="showSubmitReviewDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showRejectDialog" class="dialog-overlay" @click.self="showRejectDialog = false">
      <div data-testid="req-detail-dlg-reject" class="dialog">
        <h3>驳回</h3>
        <textarea v-model="rejectForm.comment" data-testid="req-detail-dlg-reject-txtarea-comment"></textarea>
        <button data-testid="req-detail-dlg-reject-btn-confirm" @click="rejectReview">确认</button>
        <button @click="showRejectDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showSubmitSpecReviewDialog" class="dialog-overlay" @click.self="showSubmitSpecReviewDialog = false">
      <div data-testid="req-detail-dlg-submit-spec-review" class="dialog">
        <h3>提交规范审核</h3>
        <select v-model="submitSpecReviewForm.reviewer_id" data-testid="req-detail-dlg-submit-spec-review-sel-reviewer">
          <option value="">请选择审核人</option>
          <option v-for="m in reviewers" :key="m.id" :value="m.id">{{ m.nickname || m.email }}</option>
        </select>
        <button data-testid="req-detail-dlg-submit-spec-review-btn-confirm" @click="submitSpecReview">确认</button>
        <button @click="showSubmitSpecReviewDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showAddTaskDialog" class="dialog-overlay" @click.self="showAddTaskDialog = false">
      <div data-testid="req-detail-dlg-add-task" class="dialog">
        <h3>添加任务</h3>
        <div class="form-group">
          <label>标题</label>
          <input v-model="addTaskForm.title" data-testid="req-detail-dlg-add-task-inp-title" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="addTaskForm.description" data-testid="req-detail-dlg-add-task-txtarea-desc"></textarea>
        </div>
        <div class="form-group">
          <label>指派人</label>
          <select v-model="addTaskForm.assignee_id" data-testid="req-detail-dlg-add-task-sel-assignee">
            <option value="">请选择</option>
            <option v-for="m in reviewers" :key="m.id" :value="m.id">{{ m.nickname || m.email }}</option>
          </select>
        </div>
        <button data-testid="req-detail-dlg-add-task-btn-submit" @click="createTask">提交</button>
        <button @click="showAddTaskDialog = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '@/api/client'
import AppBadge from '@/components/common/AppBadge.vue'

const route = useRoute()
const router = useRouter()
const reqId = computed(() => route.params.id as string)

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
}

interface RequirementData {
  id: number
  title: string
  type: string
  priority: string
  status: string
  description: string
  type_detail?: TypeDetail | null
  reviews?: Review[]
  tasks?: TaskItem[]
  iteration_id?: number
}

interface TaskItem {
  id: number
  title: string
  status: string
  description?: string
}

interface Member {
  id: number
  email: string
  nickname?: string
}

interface SpecVersion {
  id?: number
  content?: string
  version?: number
}

const req = ref<RequirementData | null>(null)
const editingReq = ref(false)
const editForm = reactive({ title: '', description: '' })
const showSubmitReviewDialog = ref(false)
const showRejectDialog = ref(false)
const showSubmitSpecReviewDialog = ref(false)
const showAddTaskDialog = ref(false)
const submitReviewForm = reactive({ reviewer_id: '' })
const submitSpecReviewForm = reactive({ reviewer_id: '' })
const rejectForm = reactive({ comment: '' })
const addTaskForm = reactive({ title: '', description: '', assignee_id: '' })
const reviewers = ref<Member[]>([])
const activeTab = ref('spec')
const specContent = ref('')
const specVersions = ref<SpecVersion[]>([])
const selectedVersionContent = ref('')
const tasks = ref<TaskItem[]>([])

const reviewHistory = computed(() => {
  return req.value?.reviews || []
})

const rejectReason = computed(() => {
  const lastReject = [...reviewHistory.value].reverse().find((r) => r.action === 'reject')
  return lastReject?.comment || ''
})

const canEdit = computed(() => {
  return req.value?.status === 'drafting_req'
})

const canReview = computed(() => {
  return req.value?.status === 'reviewing_req' || req.value?.status === 'reviewing_spec'
})

function typeLabel(type: string) {
  if (type === 'feature') return '功能需求'
  if (type === 'bug') return 'Bug'
  if (type === 'optimization') return '优化'
  return type
}

function statusLabel(status: string) {
  const map: Record<string, string> = {
    drafting_req: '草稿',
    reviewing_req: '审核中',
    drafting_spec: '编写规范',
    reviewing_spec: '规范审核中',
    approved: '已通过',
    spec_approved: '规范已通过',
  }
  return map[status] || status
}

function stepClass(step: string) {
  const s = req.value?.status || ''
  if (step === 'req') {
    if (s === 'drafting_req' || s === 'reviewing_req') return 'active'
    if (['drafting_spec', 'reviewing_spec', 'approved', 'spec_approved'].includes(s)) return 'completed'
  }
  if (step === 'spec') {
    if (s === 'drafting_spec' || s === 'reviewing_spec') return 'active'
    if (s === 'approved' || s === 'spec_approved') return 'completed'
  }
  if (step === 'tests') {
    if (s === 'approved' || s === 'spec_approved') return 'active'
  }
  if (step === 'approved') {
    if (s === 'approved' || s === 'spec_approved') return 'active completed'
  }
  return ''
}

async function fetchReq() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}`)
    const data = res.data?.data || res.data
    req.value = data
  } catch {
    // ignore
  }
}

async function fetchReviewers() {
  try {
    if (!req.value?.iteration_id) return
    const res = await apiClient.get(`/api/v1/iterations/${req.value.iteration_id}/requirements`)
    const data = res.data?.data
    const list = data?.items || data?.list || data || []
    if (Array.isArray(list) && list.length > 0 && list[0].email) {
      reviewers.value = list
    }
  } catch {
    // ignore
  }
}

async function startEditReq() {
  if (req.value) {
    editForm.title = req.value.title
    editForm.description = req.value.description
  }
  editingReq.value = true
}

async function saveReq() {
  try {
    await apiClient.put(`/api/v1/requirements/${reqId.value}`, editForm)
    editingReq.value = false
    await fetchReq()
  } catch {
    // ignore
  }
}

async function deleteReq() {
  if (!confirm('确定要删除此需求吗？')) return
  try {
    await apiClient.delete(`/api/v1/requirements/${reqId.value}`)
    if (req.value?.iteration_id) {
      router.push(`/iterations/${req.value.iteration_id}/kanban`)
    } else {
      router.push('/dashboard')
    }
  } catch {
    // ignore
  }
}

async function submitReview() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/submit-review`, {
      reviewer_id: Number(submitReviewForm.reviewer_id),
    })
    showSubmitReviewDialog.value = false
    await fetchReq()
  } catch {
    // ignore
  }
}

async function approveReview() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/review`, {
      action: 'approve',
    })
    await fetchReq()
  } catch {
    // ignore
  }
}

async function rejectReview() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/review`, {
      action: 'reject',
      comment: rejectForm.comment,
    })
    showRejectDialog.value = false
    rejectForm.comment = ''
    await fetchReq()
  } catch {
    // ignore
  }
}

async function saveSpec() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/spec`, {
      content: specContent.value,
    })
  } catch {
    // ignore
  }
}

async function submitSpecReview() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/submit-review`, {
      reviewer_id: Number(submitSpecReviewForm.reviewer_id),
    })
    showSubmitSpecReviewDialog.value = false
    await fetchReq()
  } catch {
    // ignore
  }
}

async function fetchSpecVersions() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/spec/versions`)
    const data = res.data?.data
    specVersions.value = data?.items || data?.list || data || []
  } catch {
    // ignore
  }
}

function viewSpecVersion(ver: SpecVersion) {
  selectedVersionContent.value = ver.content || ''
}

async function fetchTasks() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/tasks`)
    const data = res.data?.data
    tasks.value = data?.items || data?.list || data || []
  } catch {
    // ignore
  }
}

async function createTask() {
  try {
    await apiClient.post('/api/v1/tasks', {
      title: addTaskForm.title,
      description: addTaskForm.description,
      assignee_id: Number(addTaskForm.assignee_id),
      requirement_id: req.value?.id,
    })
    showAddTaskDialog.value = false
    addTaskForm.title = ''
    addTaskForm.description = ''
    addTaskForm.assignee_id = ''
    await fetchTasks()
  } catch {
    // ignore
  }
}

onMounted(async () => {
  await fetchReq()
  await fetchReviewers()
})
</script>

<style scoped>
.step-nav {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.step {
  padding: 4px 12px;
  border-radius: 4px;
  background: #f0f0f0;
}
.step.active {
  background: #1890ff;
  color: white;
}
.step.completed {
  background: #52c41a;
  color: white;
}
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.dialog {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  min-width: 400px;
  max-width: 600px;
}
.form-group {
  margin-bottom: 1rem;
}
.form-group label {
  display: block;
  margin-bottom: 0.25rem;
}
.actions {
  margin: 1rem 0;
  display: flex;
  gap: 0.5rem;
}
.tabs-section {
  margin-top: 1rem;
}
.tab-content {
  margin-top: 0.5rem;
}
textarea {
  width: 100%;
  min-height: 100px;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border: 1px solid #e8e8e8;
  padding: 0.5rem;
}
</style>
