<template>
  <div class="requirement-detail-page">
    <h1>需求详情</h1>
    <div v-if="req">
      <div class="step-nav" data-testid="req-detail-step-nav">
        <span data-testid="req-detail-step-nav-step-req" class="step" :class="stepClass('req')">需求</span>
        <span data-testid="req-detail-step-nav-step-spec" class="step" :class="stepClass('spec')">规范</span>
        <span data-testid="req-detail-step-nav-step-tests" class="step" :class="stepClass('tests')">测试</span>
        <span data-testid="req-detail-step-nav-step-approved" class="step" :class="stepClass('approved')">已通过</span>
        <span class="step-status">{{ statusLabel(req.status) }}</span>
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
        <button v-if="canEdit" data-testid="req-detail-btn-submit-req-review" @click="openSubmitReviewDialog">提交审核</button>
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

      <div class="tabs-section" style="margin-top: 1rem;">
        <button data-testid="req-detail-tab-spec" :class="{ active: activeTab === 'spec' }" @click="activeTab = 'spec'">规范</button>
        <button data-testid="req-detail-tab-spec-versions" :class="{ active: activeTab === 'spec-versions' }" @click="activeTab = 'spec-versions'; fetchSpecVersions()">规范版本</button>
        <button data-testid="req-detail-tab-tasks" :class="{ active: activeTab === 'tasks' }" @click="activeTab = 'tasks'; fetchTasks()">任务</button>
        <button data-testid="req-detail-tab-test-cases" :class="{ active: activeTab === 'test-cases' }" @click="activeTab = 'test-cases'; fetchTestCases()">测试用例</button>
        <button data-testid="req-detail-tab-test-stats" :class="{ active: activeTab === 'test-stats' }" @click="activeTab = 'test-stats'; fetchTestStats()">测试统计</button>

        <div v-if="activeTab === 'spec'" class="tab-content">
          <p v-if="saveSuccessMsg" style="color: green;">{{ saveSuccessMsg }}</p>
          <textarea v-model="specContent" data-testid="req-detail-txtarea-spec-content"></textarea>
          <button data-testid="req-detail-btn-save-spec" @click="saveSpec">保存规范</button>
          <button v-if="req.status === 'drafting_spec'" data-testid="req-detail-btn-submit-spec-review" @click="openSubmitSpecReviewDialog">提交规范审核</button>
        </div>

        <div v-if="activeTab === 'spec-versions'" class="tab-content">
          <div data-testid="req-detail-list-spec-versions">
            <div v-for="(ver, idx) in specVersions" :key="idx">
              <button :data-testid="`req-detail-btn-spec-version-${ver.version || idx + 1}`" @click="viewSpecVersion(ver)">
                v{{ ver.version || idx + 1 }}
              </button>
            </div>
          </div>
          <div v-if="selectedVersionContent" data-testid="req-detail-txt-spec-version-content">
            {{ selectedVersionContent }}
          </div>
        </div>

        <div v-if="activeTab === 'tasks'" class="tab-content">
          <button data-testid="req-detail-btn-add-task" @click="fetchReviewers(); showAddTaskDialog = true">添加任务</button>
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

        <div v-if="activeTab === 'test-cases'" class="tab-content">
          <div style="margin-bottom: 0.5rem; display: flex; gap: 0.5rem; align-items: center;">
            <button data-testid="req-detail-btn-add-test-case" @click="showTestCaseDialog = true">添加测试用例</button>
            <select data-testid="req-detail-sel-filter-case-type" v-model="testCaseTypeFilter" @change="fetchTestCases">
              <option value="">全部</option>
              <option value="api">API</option>
              <option value="e2e">E2E</option>
            </select>
          </div>
          <button data-testid="req-detail-btn-submit-tests-review" @click="openSubmitTestsReviewDialog">提交测试审核</button>
          <table data-testid="req-detail-tbl-test-cases">
            <thead>
              <tr><th>编号</th><th>标题</th><th>类型</th><th>操作</th></tr>
            </thead>
            <tbody>
              <tr v-for="tc in filteredTestCases" :key="tc.id">
                <td>{{ tc.case_number }}</td>
                <td>{{ tc.title }}</td>
                <td>{{ tc.case_type }}</td>
                <td>
                  <button :data-testid="`req-detail-btn-edit-test-case-${tc.id}`" @click="openEditTestCase(tc)">编辑</button>
                  <button :data-testid="`req-detail-btn-delete-test-case-${tc.id}`" @click="deleteTestCase(tc.id)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="activeTab === 'test-stats'" class="tab-content">
          <div data-testid="req-detail-txt-test-stats">
            <p>总用例数: <span data-testid="req-detail-txt-test-total-count">{{ testStats.total_cases ?? 0 }}</span></p>
            <p>通过数: <span data-testid="req-detail-txt-test-pass-count">{{ testStats.latest_results?.passed ?? 0 }}</span></p>
            <p>失败数: <span data-testid="req-detail-txt-test-fail-count">{{ testStats.latest_results?.failed ?? 0 }}</span></p>
            <p>跳过数: <span data-testid="req-detail-txt-test-skip-count">{{ testStats.latest_results?.skipped ?? 0 }}</span></p>
            <p>通过率: {{ testStats.pass_rate != null ? (testStats.pass_rate * 100).toFixed(0) + '%' : 'N/A' }}</p>
          </div>
        </div>
      </div>
    </div>

     <div v-if="showSubmitReviewDialog" class="dialog-overlay" @click.self="showSubmitReviewDialog = false">
       <div data-testid="req-detail-dlg-submit-review" class="dialog">
         <h3>提交审核</h3>
         <div class="custom-select" data-testid="req-detail-dlg-submit-review-sel-reviewer" @click="toggleDropdown('submitReview')">
           <span>{{ getSelectedReviewerName(submitReviewForm.reviewer_id) || '请选择审核人' }}</span>
           <div v-if="dropdownOpen === 'submitReview'" class="dropdown-options">
              <div v-for="m in reviewers" :key="m.id" class="dropdown-option" @click.stop="submitReviewForm.reviewer_id = String(m.id); dropdownOpen = ''">{{ m.nickname || m.email }}</div>
            </div>
          </div>
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
         <div class="custom-select" data-testid="req-detail-dlg-submit-spec-review-sel-reviewer" @click="toggleDropdown('submitSpecReview')">
           <span>{{ getSelectedReviewerName(submitSpecReviewForm.reviewer_id) || '请选择审核人' }}</span>
           <div v-if="dropdownOpen === 'submitSpecReview'" class="dropdown-options">
              <div v-for="m in reviewers" :key="m.id" class="dropdown-option" @click.stop="submitSpecReviewForm.reviewer_id = String(m.id); dropdownOpen = ''">{{ m.nickname || m.email }}</div>
           </div>
         </div>
         <button data-testid="req-detail-dlg-submit-spec-review-btn-confirm" @click="submitSpecReview">确认</button>
         <button @click="showSubmitSpecReviewDialog = false">取消</button>
      </div>
    </div>

     <div v-if="showSubmitTestsReviewDialog" class="dialog-overlay" @click.self="showSubmitTestsReviewDialog = false">
       <div data-testid="req-detail-dlg-submit-tests-review" class="dialog">
         <h3>提交测试审核</h3>
         <div class="custom-select" data-testid="req-detail-dlg-submit-tests-review-sel-reviewer" @click="toggleDropdown('submitTestsReview')">
           <span>{{ getSelectedReviewerName(submitTestsReviewForm.reviewer_id) || '请选择审核人' }}</span>
           <div v-if="dropdownOpen === 'submitTestsReview'" class="dropdown-options">
              <div v-for="m in reviewers" :key="m.id" class="dropdown-option" @click.stop="submitTestsReviewForm.reviewer_id = String(m.id); dropdownOpen = ''">{{ m.nickname || m.email }}</div>
           </div>
         </div>
         <button data-testid="req-detail-dlg-submit-tests-review-btn-confirm" @click="submitTestsReview">确认</button>
         <button @click="showSubmitTestsReviewDialog = false">取消</button>
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
           <div class="custom-select" data-testid="req-detail-dlg-add-task-sel-assignee" @click="toggleDropdown('addTask')">
             <span>{{ getSelectedReviewerName(addTaskForm.assignee_id) || '请选择' }}</span>
             <div v-if="dropdownOpen === 'addTask'" class="dropdown-options">
               <div v-for="m in reviewers" :key="m.id" class="dropdown-option" @click.stop="addTaskForm.assignee_id = String(m.id); dropdownOpen = ''">{{ m.nickname || m.email }}</div>
             </div>
           </div>
         </div>
        <button data-testid="req-detail-dlg-add-task-btn-submit" @click="createTask">提交</button>
        <button @click="showAddTaskDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showTestCaseDialog" class="dialog-overlay" @click.self="showTestCaseDialog = false">
      <div data-testid="req-detail-dlg-test-case" class="dialog">
        <h3>{{ editingTestCase ? '编辑测试用例' : '创建测试用例' }}</h3>
        <div class="form-group">
          <label>标题</label>
          <input v-model="testCaseForm.title" data-testid="req-detail-dlg-test-case-inp-title" />
        </div>
        <div class="form-group">
          <label>类型</label>
          <select v-model="testCaseForm.case_type" data-testid="req-detail-dlg-test-case-sel-type">
            <option value="api">API</option>
            <option value="e2e">E2E</option>
          </select>
        </div>
        <div class="form-group">
          <label>前置条件</label>
          <textarea v-model="testCaseForm.precondition" data-testid="req-detail-dlg-test-case-txtarea-precondition"></textarea>
        </div>
        <div class="form-group">
          <label>步骤</label>
          <textarea v-model="testCaseForm.steps" data-testid="req-detail-dlg-test-case-txtarea-steps"></textarea>
        </div>
        <div class="form-group">
          <label>预期结果</label>
          <textarea v-model="testCaseForm.expected_result" data-testid="req-detail-dlg-test-case-txtarea-expected"></textarea>
        </div>
        <div class="form-group">
          <label>关联 API</label>
          <input v-model="testCaseForm.related_api" data-testid="req-detail-dlg-test-case-inp-related-api" />
        </div>
        <button data-testid="req-detail-dlg-test-case-btn-save" @click="saveTestCase">保存</button>
        <button @click="showTestCaseDialog = false">取消</button>
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
  tasks?: TaskItem[]
  iteration_id?: number
  req_type?: string
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
}

interface TestStats {
  total_cases?: number
  latest_results?: { passed: number; failed: number; skipped: number; not_executed: number }
  pass_rate?: number
}

const req = ref<RequirementData | null>(null)
const editingReq = ref(false)
const editForm = reactive({ title: '', description: '' })
const showSubmitReviewDialog = ref(false)
const showRejectDialog = ref(false)
const showSubmitSpecReviewDialog = ref(false)
const showSubmitTestsReviewDialog = ref(false)
const showAddTaskDialog = ref(false)
const showTestCaseDialog = ref(false)
const submitReviewForm = reactive({ reviewer_id: '' })
const submitSpecReviewForm = reactive({ reviewer_id: '' })
const submitTestsReviewForm = reactive({ reviewer_id: '' })
const rejectForm = reactive({ comment: '' })
const addTaskForm = reactive({ title: '', description: '', assignee_id: '' })
const reviewers = ref<Member[]>([])
const activeTab = ref('')
const specContent = ref('')
const specVersions = ref<SpecVersion[]>([])
const selectedVersionContent = ref('')
const tasks = ref<TaskItem[]>([])
const testCases = ref<TestCaseItem[]>([])
const testCaseTypeFilter = ref('')
const editingTestCase = ref<TestCaseItem | null>(null)
const testCaseForm = reactive({
  title: '',
  case_type: 'api',
  precondition: '',
  steps: '',
  expected_result: '',
  related_api: '',
})
const testStats = ref<TestStats>({})
const dropdownOpen = ref('')
const saveSuccessMsg = ref('')

function toggleDropdown(name: string) {
  const willOpen = dropdownOpen.value !== name
  dropdownOpen.value = willOpen ? name : ''
  if (willOpen) {
    fetchReviewers()
  }
}

function getSelectedReviewerName(id: string | number) {
  if (!id) return ''
  const r = reviewers.value.find((m) => String(m.id) === String(id))
  return r?.nickname || r?.email || ''
}

const reviewHistory = computed(() => {
  return (req.value?.reviews || []).map((r) => ({
    ...r,
    action: r.action || (r.status === 'approved' ? 'approve' : r.status === 'rejected' ? 'reject' : r.status),
  }))
})

const rejectReason = computed(() => {
  const lastReject = [...reviewHistory.value].reverse().find((r) => r.action === 'reject')
  return lastReject?.comment || ''
})

const canEdit = computed(() => {
  return req.value?.status === 'drafting_req'
})

const canReview = computed(() => {
  return req.value?.status === 'reviewing_req' || req.value?.status === 'reviewing_spec' || req.value?.status === 'reviewing_tests'
})

const filteredTestCases = computed(() => {
  if (!testCaseTypeFilter.value) return testCases.value
  return testCases.value.filter((tc) => tc.case_type === testCaseTypeFilter.value)
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
    drafting_tests: '编写测试用例',
    reviewing_tests: '测试审核中',
    approved: '已通过',
    spec_approved: '规范已通过',
  }
  return map[status] || status
}

function stepClass(step: string) {
  const s = req.value?.status || ''
  if (step === 'req') {
    if (s === 'drafting_req') return 'active'
    if (s === 'reviewing_req') return 'active review'
    if (['drafting_spec', 'reviewing_spec', 'drafting_tests', 'reviewing_tests', 'approved', 'spec_approved'].includes(s)) return 'completed'
  }
  if (step === 'spec') {
    if (s === 'drafting_spec') return 'active'
    if (s === 'reviewing_spec') return 'active review'
    if (s === 'drafting_tests' || s === 'reviewing_tests' || s === 'approved' || s === 'spec_approved') return 'completed'
  }
  if (step === 'tests') {
    if (s === 'drafting_tests') return 'active'
    if (s === 'reviewing_tests') return 'active review'
    if (s === 'approved' || s === 'spec_approved') return 'completed'
  }
  if (step === 'approved') {
    if (s === 'approved' || s === 'spec_approved') return 'active completed done'
  }
  return ''
}

function mapReqData(data: any): RequirementData {
  const prioMap: Record<number, string> = { 3: 'high', 2: 'medium', 1: 'low' }
  const prio = data.priority
  const mappedPrio = typeof prio === 'number' ? (prioMap[prio] || prio) : prio
  return {
    ...data,
    type: data.type || data.req_type,
    priority: mappedPrio,
  }
}

async function fetchReq() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}`)
    const data = res.data?.data || res.data
    req.value = mapReqData(data)
    if (!activeTab.value) {
      autoSelectTab(req.value.status)
    }
  } catch {
    // ignore
  }
}

function autoSelectTab(status: string) {
  if (['drafting_tests', 'reviewing_tests'].includes(status)) {
    activeTab.value = 'test-cases'
    fetchTestCases()
  } else if (status === 'approved') {
    activeTab.value = 'tasks'
    fetchTasks()
  } else {
    activeTab.value = 'spec'
  }
}

async function fetchReviewers() {
  try {
    const res = await apiClient.get('/api/v1/users', { params: { page_size: 100 } })
    const data = res.data?.data
    reviewers.value = data?.items || data?.list || data || []
  } catch {
    try {
      const res = await apiClient.get('/api/v1/admin/users')
      const data = res.data?.data
      reviewers.value = data?.items || data?.list || data || []
    } catch {
      reviewers.value = []
    }
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

async function openSubmitReviewDialog() {
  await fetchReviewers()
  showSubmitReviewDialog.value = true
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
    await apiClient.put(`/api/v1/requirements/${reqId.value}/specification`, {
      content: { text: specContent.value },
    })
    saveSuccessMsg.value = '保存成功'
    setTimeout(() => { saveSuccessMsg.value = '' }, 3000)
  } catch {
    // ignore
  }
}

async function openSubmitSpecReviewDialog() {
  await fetchReviewers()
  showSubmitSpecReviewDialog.value = true
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

async function openSubmitTestsReviewDialog() {
  await fetchReviewers()
  showSubmitTestsReviewDialog.value = true
}

async function submitTestsReview() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/submit-review`, {
      reviewer_id: Number(submitTestsReviewForm.reviewer_id),
    })
    showSubmitTestsReviewDialog.value = false
    await fetchReq()
  } catch {
    // ignore
  }
}

async function fetchSpecVersions() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/specification/versions`)
    const data = res.data?.data
    specVersions.value = data?.items || data?.list || data || []
    if (specVersions.value.length > 0 && !selectedVersionContent.value) {
      viewSpecVersion(specVersions.value[specVersions.value.length - 1])
    }
  } catch {
    specVersions.value = []
  }
}

function viewSpecVersion(ver: SpecVersion) {
  if (typeof ver.content === 'string') {
    selectedVersionContent.value = ver.content
  } else if (ver.content && typeof ver.content === 'object') {
    selectedVersionContent.value = (ver.content as Record<string, string>).text || JSON.stringify(ver.content)
  } else {
    selectedVersionContent.value = ''
  }
}

async function fetchTasks() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/tasks`)
    const data = res.data?.data
    tasks.value = data?.items || data?.list || data || []
  } catch {
    tasks.value = []
  }
}

async function createTask() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/tasks`, {
      title: addTaskForm.title,
      description: addTaskForm.description,
      assignee_id: Number(addTaskForm.assignee_id) || undefined,
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

async function fetchTestCases() {
  try {
    const params: Record<string, unknown> = {}
    if (testCaseTypeFilter.value) params.case_type = testCaseTypeFilter.value
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/test-cases`, { params })
    const data = res.data?.data
    testCases.value = data?.items || data?.list || data || []
  } catch {
    testCases.value = []
  }
}

function openEditTestCase(tc: TestCaseItem) {
  editingTestCase.value = tc
  testCaseForm.title = tc.title
  testCaseForm.case_type = tc.case_type
  testCaseForm.precondition = tc.precondition || ''
  testCaseForm.steps = tc.steps || ''
  testCaseForm.expected_result = tc.expected_result || ''
  testCaseForm.related_api = tc.related_api || ''
  showTestCaseDialog.value = true
}

async function saveTestCase() {
  try {
    if (editingTestCase.value) {
      await apiClient.put(`/api/v1/test-cases/${editingTestCase.value.id}`, {
        title: testCaseForm.title,
        case_type: testCaseForm.case_type,
        precondition: testCaseForm.precondition,
        steps: testCaseForm.steps,
        expected_result: testCaseForm.expected_result,
        related_api: testCaseForm.related_api,
      })
    } else {
      await apiClient.post(`/api/v1/requirements/${reqId.value}/test-cases`, {
        title: testCaseForm.title,
        case_type: testCaseForm.case_type,
        precondition: testCaseForm.precondition,
        steps: testCaseForm.steps,
        expected_result: testCaseForm.expected_result,
        related_api: testCaseForm.related_api,
      })
    }
    showTestCaseDialog.value = false
    editingTestCase.value = null
    await fetchTestCases()
  } catch {
    // ignore
  }
}

async function deleteTestCase(tcId: number) {
  if (!confirm('确定要删除此测试用例吗？')) return
  try {
    await apiClient.delete(`/api/v1/test-cases/${tcId}`)
    await fetchTestCases()
  } catch {
    // ignore
  }
}

async function fetchTestStats() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/test-statistics`)
    testStats.value = res.data?.data || {}
  } catch {
    testStats.value = {}
  }
}

onMounted(async () => {
  await fetchReq()
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
select {
  margin-bottom: 0.5rem;
}
.custom-select {
  position: relative;
  padding: 6px 10px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  min-height: 32px;
  background: white;
}
.custom-select .dropdown-options {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  max-height: 200px;
  overflow-y: auto;
  z-index: 1001;
}
.custom-select .dropdown-option {
  padding: 6px 10px;
  cursor: pointer;
}
.custom-select .dropdown-option:hover {
  background: #f0f0f0;
}
</style>
