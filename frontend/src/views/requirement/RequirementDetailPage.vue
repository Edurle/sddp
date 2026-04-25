<template>
  <div class="requirement-detail-page">
    <div v-if="req" class="detail-layout">
      <RequirementSidebar
        :req="req"
        :editing="editingReq"
        :edit-form="editForm"
        @edit="startEditReq"
        @save="saveReq"
        @delete="deleteReq"
        @submit-review="openSubmitReviewDialog"
        @approve="approveReview"
        @reject="showRejectDialog = true"
      />

      <div class="detail-main">
        <div class="detail-tabs">
          <button data-testid="req-detail-tab-spec" :class="['tab-btn', { active: activeTab === 'spec' }]" @click="activeTab = 'spec'">规范</button>
          <button data-testid="req-detail-tab-spec-versions" :class="['tab-btn', { active: activeTab === 'spec-versions' }]" @click="activeTab = 'spec-versions'; fetchSpecVersions()">版本历史 ({{ specVersions.length || 0 }})</button>
          <button data-testid="req-detail-tab-tasks" :class="['tab-btn', { active: activeTab === 'tasks' }]" @click="activeTab = 'tasks'; fetchTasks()">任务 ({{ tasks.length || 0 }})</button>
          <button data-testid="req-detail-tab-test-cases" :class="['tab-btn', { active: activeTab === 'test-cases' }]" @click="activeTab = 'test-cases'; fetchTestCases()">测试用例 ({{ testCases.length || 0 }})</button>
        </div>

        <div v-if="activeTab === 'spec'" class="tab-panel">
          <div class="spec-toolbar">
            <span v-if="saveSuccessMsg" class="save-msg">{{ saveSuccessMsg }}</span>
            <span v-else class="spec-hint">在下方编辑规范文档</span>
            <div class="spec-actions">
              <button data-testid="req-detail-btn-save-spec" @click="saveSpec">保存规范</button>
              <button v-if="req.status === 'drafting_spec'" data-testid="req-detail-btn-submit-spec-review" @click="openSubmitSpecReviewDialog">提交规范审核</button>
            </div>
          </div>
          <textarea v-model="specContent" data-testid="req-detail-txtarea-spec-content" class="spec-editor"></textarea>
        </div>

        <div v-if="activeTab === 'spec-versions'" class="tab-panel">
          <div data-testid="req-detail-list-spec-versions" class="version-list">
            <div v-for="(ver, idx) in specVersions" :key="idx" class="version-card" :class="{ selected: selectedVersionContent === getVersionText(ver) }" @click="viewSpecVersion(ver)">
              <div class="version-header">
                <span class="version-num">v{{ ver.version || idx + 1 }}</span>
              </div>
              <div class="version-preview">{{ getVersionText(ver).slice(0, 100) }}{{ getVersionText(ver).length > 100 ? '...' : '' }}</div>
              <button :data-testid="`req-detail-btn-spec-version-${ver.version || idx + 1}`" class="version-view-btn">查看</button>
            </div>
          </div>
          <div v-if="selectedVersionContent" data-testid="req-detail-txt-spec-version-content" class="version-content">
            {{ selectedVersionContent }}
          </div>
        </div>

        <div v-if="activeTab === 'tasks'" class="tab-panel">
          <div class="tab-toolbar">
            <button data-testid="req-detail-btn-add-task" @click="fetchReviewers(); showAddTaskDialog = true">添加任务</button>
          </div>
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

        <div v-if="activeTab === 'test-cases'" class="tab-panel">
          <div class="tab-toolbar">
            <button data-testid="req-detail-btn-add-test-case" @click="showTestCaseDialog = true">添加测试用例</button>
            <select data-testid="req-detail-sel-filter-case-type" v-model="testCaseTypeFilter" @change="fetchTestCases">
              <option value="">全部</option>
              <option value="api">API</option>
              <option value="e2e">E2E</option>
            </select>
            <button data-testid="req-detail-btn-submit-tests-review" @click="openSubmitTestsReviewDialog">提交测试审核</button>
          </div>
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
import RequirementSidebar from './RequirementSidebar.vue'

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

const filteredTestCases = computed(() => {
  if (!testCaseTypeFilter.value) return testCases.value
  return testCases.value.filter((tc) => tc.case_type === testCaseTypeFilter.value)
})

function getVersionText(ver: SpecVersion): string {
  if (typeof ver.content === 'string') return ver.content
  if (ver.content && typeof ver.content === 'object') return (ver.content as Record<string, string>).text || JSON.stringify(ver.content)
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
  selectedVersionContent.value = getVersionText(ver)
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
  await fetchTestStats()
})
</script>

<style scoped>
.requirement-detail-page {
  height: 100vh;
  overflow: hidden;
}
.detail-layout {
  display: flex;
  height: 100%;
}
.detail-main {
  flex: 1;
  padding: 1rem 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.detail-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid rgba(0, 0, 0, 0.06);
  margin-bottom: 1rem;
  flex-shrink: 0;
}
.tab-btn {
  padding: 8px 16px;
  font-size: 13px;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  background: transparent;
  color: #999;
  cursor: pointer;
  font-weight: 500;
  font-family: inherit;
  transition: all 0.2s;
}
.tab-btn:hover {
  color: #333;
}
.tab-btn.active {
  color: #111;
  border-bottom-color: #111;
  font-weight: 600;
}
.tab-panel {
  flex: 1;
}
.tab-toolbar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.75rem;
}
.spec-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  margin-bottom: 0.75rem;
  border: 1px solid rgba(0, 0, 0, 0.04);
}
.spec-hint {
  font-size: 12px;
  color: #999;
}
.save-msg {
  color: #52c41a;
  font-size: 13px;
  font-weight: 500;
}
.spec-actions {
  display: flex;
  gap: 6px;
}
.spec-editor {
  width: 100%;
  min-height: 400px;
  font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.8;
  padding: 1rem;
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  resize: vertical;
}
.version-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.version-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.version-card:hover {
  border-color: rgba(0, 0, 0, 0.12);
}
.version-card.selected {
  border-color: #1677ff;
  background: rgba(22, 119, 255, 0.04);
}
.version-num {
  font-weight: 600;
  font-size: 14px;
  color: #111;
  min-width: 40px;
}
.version-preview {
  flex: 1;
  font-size: 12px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.version-view-btn {
  background: transparent;
  color: #1677ff;
  border: 1px solid #1677ff;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  margin: 0;
}
.version-content {
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  padding: 1rem;
  font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
}
.stat-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
  margin-top: 1rem;
  flex-shrink: 0;
}
.stat-card {
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  padding: 0.75rem;
  text-align: center;
}
.stat-num {
  font-size: 20px;
  font-weight: 700;
  color: #111;
}
.stat-label {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}
.stat-pass .stat-num { color: #52c41a; }
.stat-fail .stat-num { color: #ff4d4f; }
.stat-skip .stat-num { color: #faad14; }
.stat-rate .stat-num { color: #1677ff; }

@media (max-width: 768px) {
  .detail-layout {
    flex-direction: column;
  }
  .detail-main {
    padding: 1rem;
  }
  .stat-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
