<template>
  <div class="requirement-detail-page">
    <div v-if="isLoading" class="loading-state">加载中...</div>
    <div v-else-if="req" class="detail-layout">
      <RequirementSidebar
        :req="req"
        :editing="editingReq"
        :edit-form="editForm"
        :saving="isPending('saveReq')"
        :deleting="isPending('deleteReq')"
        :approving="isPending('approveReview')"
        @edit="startEditReq"
        @save="saveReq"
        @delete="deleteReq"
        @submit-review="openSubmitReviewDialog"
        @approve="approveReview"
        @reject="showRejectDialog = true"
        @supersede="showSupersedeDialog = true"
      />

      <div class="detail-main">
        <div class="detail-tabs">
          <button data-testid="req-detail-tab-story" :class="['tab-btn', { active: activeTab === 'story' }]" @click="activeTab = 'story'">用户故事</button>
          <button data-testid="req-detail-tab-spec" :class="['tab-btn', { active: activeTab === 'spec' }]" @click="activeTab = 'spec'">规范</button>
          <button data-testid="req-detail-tab-spec-versions" :class="['tab-btn', { active: activeTab === 'spec-versions' }]" @click="activeTab = 'spec-versions'; fetchSpecVersions()">版本历史</button>
          <button data-testid="req-detail-tab-tasks" :class="['tab-btn', { active: activeTab === 'tasks' }]" @click="activeTab = 'tasks'; fetchTasks()">任务</button>
          <button data-testid="req-detail-tab-test-cases" :class="['tab-btn', { active: activeTab === 'test-cases' }]" @click="activeTab = 'test-cases'; fetchTestCases()">测试用例</button>
          <button data-testid="req-detail-tab-review-history" :class="['tab-btn', { active: activeTab === 'review-history' }]" @click="activeTab = 'review-history'">审核历史</button>
          <button data-testid="req-detail-tab-links" :class="['tab-btn', { active: activeTab === 'links' }]" @click="activeTab = 'links'; fetchLinks()">关联</button>
          <button data-testid="req-detail-tab-commits" :class="['tab-btn', { active: activeTab === 'commits' }]" @click="activeTab = 'commits'; fetchCommits()">提交记录</button>
        </div>

        <RequirementStoryTab v-if="activeTab === 'story'" :description="req.description" />

        <RequirementSpecTab v-if="activeTab === 'spec'" :spec-raw-content="specRawContent" :status="req.status" @submit-review="openSubmitSpecReviewDialog" />

        <RequirementSpecVersionsTab v-if="activeTab === 'spec-versions'" :spec-versions="specVersions" />

        <RequirementTasksTab
          v-if="activeTab === 'tasks'"
          :tasks="tasks"
          @add="fetchReviewers(); showAddTaskDialog = true"
        />

        <RequirementTestCasesTab
          v-if="activeTab === 'test-cases'"
          :test-cases="filteredTestCases"
          :test-stats="testStats"
          :execution-map="tcExecutionMap"
          :filter="testCaseTypeFilter"
          :deleting="isPending('deleteTestCase')"
          @add="showTestCaseDialog = true"
          @submit-review="openSubmitTestsReviewDialog"
          @update:filter="testCaseTypeFilter = $event"
          @change="fetchTestCases"
          @select="viewTestCase = $event"
          @view="openTestCaseDetail"
          @edit="openEditTestCase"
          @delete="deleteTestCase"
        />

        <RequirementReviewHistoryTab v-if="activeTab === 'review-history'" :review-comments="reviewComments" />

        <RequirementLinksTab
          v-if="activeTab === 'links'"
          :links="links"
          :deleting="isPending('deleteLink')"
          @add="showAddLinkDialog = true"
          @delete="deleteLink"
        />

        <RequirementCommitsTab v-if="activeTab === 'commits'" :commits="commits" />
      </div>
    </div>

    <AppDialog :open="showSubmitReviewDialog" test-id="req-detail-dlg-submit-review" @close="showSubmitReviewDialog = false">
      <h3>提交审核</h3>
      <div class="custom-select" data-testid="req-detail-dlg-submit-review-sel-reviewer" @click="toggleDropdown('submitReview')">
        <span>{{ getSelectedReviewerName(submitReviewForm.reviewer_id) || '请选择审核人' }}</span>
        <div v-if="dropdownOpen === 'submitReview'" class="dropdown-options">
          <div v-for="m in reviewers" :key="m.id" class="dropdown-option" @click.stop="submitReviewForm.reviewer_id = String(m.id); dropdownOpen = ''">{{ m.nickname || m.email }}</div>
        </div>
      </div>
      <button data-testid="req-detail-dlg-submit-review-btn-confirm" :disabled="isPending('submitReview')" @click="submitReview">确认</button>
      <button @click="showSubmitReviewDialog = false">取消</button>
    </AppDialog>

    <AppDialog :open="showRejectDialog" test-id="req-detail-dlg-reject" @close="showRejectDialog = false">
      <h3>驳回</h3>
      <textarea v-model="rejectForm.comment" data-testid="req-detail-dlg-reject-txtarea-comment"></textarea>
      <button class="btn-danger" data-testid="req-detail-dlg-reject-btn-confirm" :disabled="isPending('rejectReview')" @click="rejectReview">确认</button>
      <button @click="showRejectDialog = false">取消</button>
    </AppDialog>

    <AppDialog :open="showSubmitSpecReviewDialog" test-id="req-detail-dlg-submit-spec-review" @close="showSubmitSpecReviewDialog = false">
      <h3>提交规范审核</h3>
      <div class="custom-select" data-testid="req-detail-dlg-submit-spec-review-sel-reviewer" @click="toggleDropdown('submitSpecReview')">
        <span>{{ getSelectedReviewerName(submitSpecReviewForm.reviewer_id) || '请选择审核人' }}</span>
        <div v-if="dropdownOpen === 'submitSpecReview'" class="dropdown-options">
          <div v-for="m in reviewers" :key="m.id" class="dropdown-option" @click.stop="submitSpecReviewForm.reviewer_id = String(m.id); dropdownOpen = ''">{{ m.nickname || m.email }}</div>
        </div>
      </div>
      <button data-testid="req-detail-dlg-submit-spec-review-btn-confirm" :disabled="isPending('submitSpecReview')" @click="submitSpecReview">确认</button>
      <button @click="showSubmitSpecReviewDialog = false">取消</button>
    </AppDialog>

    <AppDialog :open="showSubmitTestsReviewDialog" test-id="req-detail-dlg-submit-tests-review" @close="showSubmitTestsReviewDialog = false">
      <h3>提交测试审核</h3>
      <div class="custom-select" data-testid="req-detail-dlg-submit-tests-review-sel-reviewer" @click="toggleDropdown('submitTestsReview')">
        <span>{{ getSelectedReviewerName(submitTestsReviewForm.reviewer_id) || '请选择审核人' }}</span>
        <div v-if="dropdownOpen === 'submitTestsReview'" class="dropdown-options">
          <div v-for="m in reviewers" :key="m.id" class="dropdown-option" @click.stop="submitTestsReviewForm.reviewer_id = String(m.id); dropdownOpen = ''">{{ m.nickname || m.email }}</div>
        </div>
      </div>
      <button data-testid="req-detail-dlg-submit-tests-review-btn-confirm" :disabled="isPending('submitTestsReview')" @click="submitTestsReview">确认</button>
      <button @click="showSubmitTestsReviewDialog = false">取消</button>
    </AppDialog>

    <AppDialog :open="showAddTaskDialog" test-id="req-detail-dlg-add-task" @close="showAddTaskDialog = false">
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
      <button data-testid="req-detail-dlg-add-task-btn-submit" :disabled="isPending('createTask')" @click="createTask">提交</button>
      <button @click="showAddTaskDialog = false">取消</button>
    </AppDialog>

    <AppDialog :open="showTestCaseDialog" test-id="req-detail-dlg-test-case" @close="showTestCaseDialog = false">
      <h3>{{ editingTestCase ? '编辑测试用例' : '创建测试用例' }}</h3>
      <div class="form-group">
        <label>标题</label>
        <input v-model="testCaseForm.title" data-testid="req-detail-dlg-test-case-inp-title" />
      </div>
      <div class="form-group">
        <label>类型</label>
        <select v-model="testCaseForm.case_type" data-testid="req-detail-dlg-test-case-sel-type">
          <option value="ui_test">UI测试</option>
          <option value="happy_path">正常用例</option>
          <option value="edge_case">边界用例</option>
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
      <button data-testid="req-detail-dlg-test-case-btn-save" :disabled="isPending('saveTestCase')" @click="saveTestCase">保存</button>
      <button @click="showTestCaseDialog = false">取消</button>
    </AppDialog>

    <AppDialog :open="!!viewTestCase" dialog-class="tc-detail-dialog" @close="viewTestCase = null">
      <template v-if="viewTestCase">
        <div class="tc-detail-header">
          <h3>测试用例详情</h3>
          <button class="tc-detail-close" @click="viewTestCase = null">&times;</button>
        </div>
        <div class="tc-detail-body">
          <div class="tc-detail-section">
            <div class="tc-section-title">基本信息</div>
            <div class="tc-detail-grid">
              <div class="tc-detail-field">
                <label>标题</label>
                <p class="view-field">{{ viewTestCase.title }}</p>
              </div>
              <div class="tc-detail-field">
                <label>类型</label>
                <p class="view-field">{{ caseTypeLabel(viewTestCase.case_type) }}</p>
              </div>
              <div class="tc-detail-field">
                <label>关联 API</label>
                <p class="view-field">{{ viewTestCase.related_api || '无' }}</p>
              </div>
            </div>
          </div>
          <div class="tc-detail-section">
            <div class="tc-section-title">测试内容</div>
            <TestDslFlow
              :case-type="viewTestCase.case_type"
              :precondition="viewTestCase.precondition"
              :steps="viewTestCase.steps"
              :expected-result="viewTestCase.expected_result"
            />
          </div>
          <div class="tc-detail-section">
            <div class="tc-section-title">执行记录</div>
            <template v-if="tcExecutionMap[viewTestCase.id] && tcExecutionMap[viewTestCase.id].all_results && tcExecutionMap[viewTestCase.id].all_results.length">
              <div class="tc-exec-records">
                <details v-for="(rec, ri) in tcExecutionMap[viewTestCase.id].all_results" :key="ri" class="tc-exec-collapsible" :open="ri === 0">
                  <summary class="tc-exec-summary">
                    <span class="spec-tag" :style="resultTagStyle(rec.status)">{{ tcResultText(rec.status) }}</span>
                    <span class="tc-exec-time">{{ rec.executed_at || '' }}</span>
                    <span v-if="rec.duration_ms" class="tc-exec-dur">{{ rec.duration_ms }}ms</span>
                  </summary>
                  <div class="tc-exec-detail">
                    <div v-if="rec.actual_result" class="tc-exec-field"><strong>实际结果：</strong>{{ rec.actual_result }}</div>
                    <div v-if="rec.failure_reason" class="tc-exec-field tc-exec-fail"><strong>失败原因：</strong>{{ rec.failure_reason }}</div>
                    <div v-if="rec.duration_ms" class="tc-exec-field"><strong>耗时：</strong>{{ rec.duration_ms }}ms</div>
                  </div>
                </details>
              </div>
            </template>
            <p v-else class="tc-empty-hint">暂无执行记录</p>
          </div>
        </div>
      </template>
    </AppDialog>

    <AppDialog :open="showSupersedeDialog" test-id="req-detail-dlg-supersede" @close="showSupersedeDialog = false">
      <h3>创建变更需求</h3>
      <p class="dialog-hint">将当前已通过需求标记为废弃，并创建一个新的变更需求</p>
      <div class="form-group">
        <label>新需求标题</label>
        <input v-model="supersedeForm.title" data-testid="req-detail-dlg-supersede-inp-title" :placeholder="`${req?.title || ''}（变更）`" />
      </div>
      <div class="form-group">
        <label>新需求描述</label>
        <textarea v-model="supersedeForm.description" data-testid="req-detail-dlg-supersede-txtarea-desc" :placeholder="req?.description || ''"></textarea>
      </div>
      <button data-testid="req-detail-dlg-supersede-btn-confirm" :disabled="isPending('supersedeReq')" @click="supersedeReq">确认</button>
      <button @click="showSupersedeDialog = false">取消</button>
    </AppDialog>

    <AppDialog :open="showAddLinkDialog" test-id="req-detail-dlg-add-link" @close="showAddLinkDialog = false">
      <h3>添加关联</h3>
      <div class="form-group">
        <label>目标需求 ID</label>
        <input v-model.number="addLinkForm.target_id" type="number" data-testid="req-detail-dlg-add-link-inp-target" />
      </div>
      <div class="form-group">
        <label>关联类型</label>
        <span class="spec-tag" style="background:var(--intent-info-bg);color:var(--color-primary)">relates_to（关联）</span>
      </div>
      <button data-testid="req-detail-dlg-add-link-btn-confirm" :disabled="isPending('createLink')" @click="createLink">确认</button>
      <button @click="showAddLinkDialog = false">取消</button>
    </AppDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '@/api/client'
import { useNotificationStore } from '@/stores/notification'
import { useConfirm } from '@/composables/useConfirm'
import { useAsyncAction } from '@/composables/useAsyncAction'
import RequirementSidebar from './RequirementSidebar.vue'
import RequirementCommitsTab from './RequirementCommitsTab.vue'
import RequirementSpecVersionsTab from './RequirementSpecVersionsTab.vue'
import RequirementReviewHistoryTab from './RequirementReviewHistoryTab.vue'
import RequirementLinksTab from './RequirementLinksTab.vue'
import RequirementTasksTab from './RequirementTasksTab.vue'
import RequirementStoryTab from './RequirementStoryTab.vue'
import RequirementSpecTab from './RequirementSpecTab.vue'
import RequirementTestCasesTab from './RequirementTestCasesTab.vue'
import TestDslFlow from '@/components/TestDslFlow.vue'
import AppDialog from '@/components/common/AppDialog.vue'

const route = useRoute()
const router = useRouter()
const reqId = computed(() => route.params.id as string)
const notification = useNotificationStore()
const confirm = useConfirm()
const { isPending, run } = useAsyncAction()

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

interface ReviewComment {
  id: number
  reviewer_id: number
  review_type?: string
  action: string
  comment: string | null
  created_at: string
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
  content?: any
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
const editForm = reactive({ title: '', description: '', prototype_html: '' })
const showSubmitReviewDialog = ref(false)
const showRejectDialog = ref(false)
const showSubmitSpecReviewDialog = ref(false)
const showSubmitTestsReviewDialog = ref(false)
const showAddTaskDialog = ref(false)
const showTestCaseDialog = ref(false)
const viewTestCase = ref<any>(null)
const submitReviewForm = reactive({ reviewer_id: '' })
const submitSpecReviewForm = reactive({ reviewer_id: '' })
const submitTestsReviewForm = reactive({ reviewer_id: '' })
const rejectForm = reactive({ comment: '' })
const addTaskForm = reactive({ title: '', description: '', assignee_id: '' })
const reviewers = ref<Member[]>([])
const activeTab = ref('')
const specSections = ref<any[]>([
  {
    name: "entity_definition", display_name: "实体定义", required: true,
    fields: [
      { name: "description", display_name: "实体描述", type: "text", required: true, description: "对实体的简要描述" },
      { name: "fields", display_name: "字段列表", type: "list", required: true, description: "实体包含的字段定义" },
    ],
  },
  {
    name: "table_design", display_name: "数据表设计", required: true,
    fields: [
      { name: "tables", display_name: "表列表", type: "list", required: true, description: "每个表的表名、字段、类型、索引" },
    ],
  },
  {
    name: "page_structure", display_name: "页面结构", required: true,
    fields: [
      { name: "pages", display_name: "页面列表", type: "list", required: true, description: "页面名称、编码、元素列表" },
    ],
  },
  {
    name: "api_design", display_name: "API 设计", required: true,
    fields: [
      { name: "endpoints", display_name: "接口列表", type: "list", required: true, description: "每个接口的URL、方法、参数" },
    ],
  },
  {
    name: "constraints", display_name: "其他约束", required: false,
    fields: [
      { name: "directory_structure", display_name: "目录结构", type: "text", required: false, description: "项目目录结构规范" },
      { name: "naming_conventions", display_name: "命名规范", type: "text", required: false, description: "编码命名规范" },
      { name: "other", display_name: "其他约束", type: "text", required: false, description: "其他技术约束" },
    ],
  },
])
const specFormData = ref<Record<string, Record<string, any>>>({})
const specRawContent = ref<Record<string, any>>({})
const specVersions = ref<SpecVersion[]>([])
const tasks = ref<TaskItem[]>([])
const testCases = ref<TestCaseItem[]>([])
const testCaseTypeFilter = ref('')
const editingTestCase = ref<TestCaseItem | null>(null)
const tcExecutionMap = ref<Record<number, { status: string; all_results: Array<{ status: string; actual_result?: string; failure_reason?: string; duration_ms?: number; executed_at?: string }> }>>({})
const testCaseForm = reactive({
  title: '',
  case_type: 'ui_test',
  precondition: '',
  steps: '',
  expected_result: '',
  related_api: '',
})
const testStats = ref<TestStats>({})
const dropdownOpen = ref('')
const isLoading = ref(true)
const reviewComments = ref<ReviewComment[]>([])

interface LinkItem {
  id: number
  source_id: number
  target_id: number
  link_type: string
  direction: 'incoming' | 'outgoing'
  related_req_id: number
  created_by: number
  created_at: string | null
}

const links = ref<LinkItem[]>([])
const showSupersedeDialog = ref(false)

interface CommitItem {
  id: number
  task_id: number
  commit_sha: string
  message: string | null
  author: string | null
  committed_at: string | null
  created_at: string | null
}

const commits = ref<CommitItem[]>([])

const showAddLinkDialog = ref(false)
const supersedeForm = reactive({ title: '', description: '' })
const addLinkForm = reactive({ target_id: 0 })

async function fetchReviewComments() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/review-comments`)
    reviewComments.value = res.data?.data || []
  } catch {
    reviewComments.value = []
  }
}

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
    fetchReviewComments()
    if (!activeTab.value) {
      autoSelectTab(req.value.status)
    }
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '获取需求失败')
  }
}

function autoSelectTab(status: string) {
  if (['drafting_req', 'reviewing_req'].includes(status)) {
    activeTab.value = 'story'
  } else if (['drafting_tests', 'reviewing_tests'].includes(status)) {
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
    editForm.prototype_html = req.value.prototype_html || ''
  }
  editingReq.value = true
}

async function saveReq() {
  await run('saveReq', async () => {
    try {
      await apiClient.put(`/api/v1/requirements/${reqId.value}`, editForm)
      editingReq.value = false
      await fetchReq()
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '操作失败')
    }
  })
}

async function deleteReq() {
  await run('deleteReq', async () => {
    if (!(await confirm({ title: '删除需求', message: '确定要删除此需求吗？此操作不可撤销。', danger: true, confirmText: '删除' }))) return
    try {
      await apiClient.delete(`/api/v1/requirements/${reqId.value}`)
      if (req.value?.iteration_id) {
        router.push(`/iterations/${req.value.iteration_id}/kanban`)
      } else {
        router.push('/dashboard')
      }
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '删除失败')
    }
  })
}

async function openSubmitReviewDialog() {
  await fetchReviewers()
  showSubmitReviewDialog.value = true
}

async function submitReview() {
  await run('submitReview', async () => {
    try {
      await apiClient.post(`/api/v1/requirements/${reqId.value}/submit-review`, {
        reviewer_id: Number(submitReviewForm.reviewer_id),
      })
      showSubmitReviewDialog.value = false
      await fetchReq()
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '提交审核失败')
    }
  })
}

async function approveReview() {
  await run('approveReview', async () => {
    try {
      await apiClient.post(`/api/v1/requirements/${reqId.value}/review`, {
        action: 'approve',
      })
      await fetchReq()
      fetchReviewComments()
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '审核操作失败')
    }
  })
}

async function rejectReview() {
  await run('rejectReview', async () => {
    try {
      await apiClient.post(`/api/v1/requirements/${reqId.value}/review`, {
        action: 'reject',
        comment: rejectForm.comment,
      })
      showRejectDialog.value = false
      rejectForm.comment = ''
      await fetchReq()
      fetchReviewComments()
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '驳回操作失败')
    }
  })
}

function loadSpecContent(content: Record<string, any>) {
  specRawContent.value = content
  for (const section of specSections.value) {
    if (!specFormData.value[section.name]) {
      specFormData.value[section.name] = {}
    }
    const sectionData = content[section.name] || {}
    for (const field of section.fields) {
      let value = sectionData[field.name]
      specFormData.value[section.name][field.name] = value ?? (field.type === 'list' ? [] : '')
    }
  }
}

async function fetchSpecContent() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/specification`)
    const data = res.data?.data
    loadSpecContent(data?.content || {})
  } catch {
    loadSpecContent({})
  }
}

async function openSubmitSpecReviewDialog() {
  await fetchReviewers()
  showSubmitSpecReviewDialog.value = true
}

async function submitSpecReview() {
  await run('submitSpecReview', async () => {
    try {
      await apiClient.post(`/api/v1/requirements/${reqId.value}/submit-review`, {
        reviewer_id: Number(submitSpecReviewForm.reviewer_id),
      })
      showSubmitSpecReviewDialog.value = false
      await fetchReq()
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '提交规范审核失败')
    }
  })
}

async function openSubmitTestsReviewDialog() {
  await fetchReviewers()
  showSubmitTestsReviewDialog.value = true
}

async function submitTestsReview() {
  await run('submitTestsReview', async () => {
    try {
      await apiClient.post(`/api/v1/requirements/${reqId.value}/submit-review`, {
        reviewer_id: Number(submitTestsReviewForm.reviewer_id),
      })
      showSubmitTestsReviewDialog.value = false
      await fetchReq()
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '提交测试审核失败')
    }
  })
}

async function fetchSpecVersions() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/specification/versions`)
    const data = res.data?.data
    specVersions.value = data?.items || data?.list || data || []
  } catch {
    specVersions.value = []
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
  await run('createTask', async () => {
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
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '操作失败')
    }
  })
}

async function fetchTestCases() {
  try {
    const params: Record<string, unknown> = {}
    if (testCaseTypeFilter.value) params.case_type = testCaseTypeFilter.value
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/test-cases`, { params })
    const data = res.data?.data
    testCases.value = data?.items || data?.list || data || []
    fetchTestCaseExecutions()
  } catch {
    testCases.value = []
  }
}

async function fetchTestCaseExecutions() {
  try {
    const res = await apiClient.get(`/api/v1/test-cases/requirement/${reqId.value}/execution-results`)
    const items = res.data?.data || []
    const map: Record<number, any> = {}
    for (const item of items) {
      map[item.test_case_id] = item
    }
    tcExecutionMap.value = map
  } catch {
    tcExecutionMap.value = {}
  }
}

function caseTypeLabel(caseType: string) {
  if (caseType === 'ui_test') return 'UI测试'
  if (caseType === 'happy_path') return '正常用例'
  if (caseType === 'edge_case') return '边界用例'
  if (caseType === 'api') return 'API'
  return caseType
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

function openTestCaseDetail(tc: TestCaseItem) {
  viewTestCase.value = tc
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
  await run('saveTestCase', async () => {
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
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '操作失败')
    }
  })
}

async function deleteTestCase(tcId: number) {
  await run('deleteTestCase', async () => {
    if (!(await confirm({ title: '删除测试用例', message: '确定要删除此测试用例吗？', danger: true, confirmText: '删除' }))) return
    try {
      await apiClient.delete(`/api/v1/test-cases/${tcId}`)
      await fetchTestCases()
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '删除失败')
    }
  })
}

async function fetchTestStats() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/test-statistics`)
    testStats.value = res.data?.data || {}
  } catch {
    testStats.value = {}
  }
}

async function fetchLinks() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/links`)
    links.value = res.data?.data || []
  } catch {
    links.value = []
  }
}

async function fetchCommits() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/commits`)
    commits.value = res.data?.data || []
  } catch {
    commits.value = []
  }
}

async function createLink() {
  await run('createLink', async () => {
    if (!addLinkForm.target_id) {
      notification.showError('请输入目标需求 ID')
      return
    }
    try {
      await apiClient.post(`/api/v1/requirements/${reqId.value}/links`, {
        target_id: addLinkForm.target_id,
        link_type: 'relates_to',
      })
      showAddLinkDialog.value = false
      addLinkForm.target_id = 0
      await fetchLinks()
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '添加关联失败')
    }
  })
}

async function deleteLink(linkId: number) {
  await run('deleteLink', async () => {
    if (!(await confirm({ title: '删除关联', message: '确定要删除此关联吗？', danger: true, confirmText: '删除' }))) return
    try {
      await apiClient.delete(`/api/v1/requirements/${reqId.value}/links/${linkId}`)
      await fetchLinks()
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '删除关联失败')
    }
  })
}

async function supersedeReq() {
  await run('supersedeReq', async () => {
    try {
      const body: Record<string, string> = {}
      if (supersedeForm.title) body.title = supersedeForm.title
      if (supersedeForm.description) body.description = supersedeForm.description
      const res = await apiClient.post(`/api/v1/requirements/${reqId.value}/supersede`, body)
      showSupersedeDialog.value = false
      supersedeForm.title = ''
      supersedeForm.description = ''
      const newReq = res.data?.data?.new_requirement
      if (newReq) {
        router.push(`/requirements/${newReq.id}`)
      } else {
        await fetchReq()
      }
    } catch (e: any) {
      notification.showError(e?.response?.data?.message || e?.message || '创建变更失败')
    }
  })
}

onMounted(async () => {
  isLoading.value = true
  try {
    await fetchReq()
    await fetchSpecContent()
    await fetchTestStats()
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.view-field {
  margin: 0;
  padding: 8px 12px;
  background: var(--color-surface-muted);
  border-radius: var(--radius-sm);
  font-size: var(--text-sm);
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  color: var(--color-text);
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
.tc-detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}
.tc-detail-header h3 {
  margin: 0;
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
}
.tc-detail-close {
  background: none;
  border: none;
  font-size: var(--text-2xl);
  color: var(--color-text-subtle);
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  transition: background 0.15s;
}
.tc-detail-close:hover {
  background: var(--color-surface-muted);
  color: var(--color-text);
}
.tc-detail-body {
  padding: 1rem 1.5rem 1.5rem;
  overflow-y: auto;
  flex: 1;
}
.tc-detail-section {
  margin-bottom: 1.25rem;
}
.tc-detail-section:last-child {
  margin-bottom: 0;
}
.tc-section-title {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--color-border);
}
.tc-detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}
.tc-detail-grid .tc-detail-field:last-child:nth-child(odd) {
  grid-column: 1 / -1;
}
.tc-detail-field label {
  display: block;
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
  margin-bottom: var(--space-1);
  font-weight: 500;
}
.tc-empty-hint {
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
  margin: 0;
  padding: 0.5rem 0;
}
.tc-exec-records {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.tc-exec-collapsible {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}
.tc-exec-collapsible summary {
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  background: var(--color-surface-muted);
  user-select: none;
  list-style: none;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}
.tc-exec-collapsible summary::before {
  content: '▸';
  font-size: var(--text-2xs);
  transition: transform 0.15s;
  display: inline-block;
  color: var(--color-text-subtle);
}
.tc-exec-collapsible[open] summary::before {
  transform: rotate(90deg);
}
.tc-exec-collapsible summary:hover {
  background: var(--color-surface-muted);
}
.tc-exec-summary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.tc-exec-time {
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
}
.tc-exec-dur {
  font-size: var(--text-2xs);
  color: var(--color-text-muted);
  background: var(--color-surface-muted);
  padding: 1px 6px;
  border-radius: var(--radius-xs);
  margin-left: auto;
}
.tc-exec-detail {
  padding: 0.6rem 0.75rem;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface);
}
.tc-exec-field {
  font-size: var(--text-sm);
  color: var(--color-text);
  margin-top: 0.25rem;
  line-height: 1.5;
}
.tc-exec-field:first-child {
  margin-top: 0;
}
.tc-exec-fail {
  color: var(--intent-danger-text);
}
.requirement-detail-page {
  min-height: 100vh;
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
  border-bottom: 2px solid var(--color-border);
  margin-bottom: 1rem;
  flex-shrink: 0;
}
.tab-btn {
  padding: 8px 16px;
  font-size: var(--text-sm);
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  background: transparent;
  color: var(--color-text-subtle);
  cursor: pointer;
  font-weight: 500;
  font-family: inherit;
  transition: all 0.2s;
}
.tab-btn:hover {
  color: var(--color-text);
}
.tab-btn.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
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
  border-radius: var(--radius-md);
  margin-bottom: 0.75rem;
  border: 1px solid var(--color-border);
}
.spec-hint {
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
}
.save-msg {
  color: var(--intent-success-text);
  font-size: var(--text-sm);
  font-weight: 500;
}
.spec-actions {
  display: flex;
  gap: 6px;
}
.spec-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.section-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.75rem 0;
}
.required-mark {
  color: var(--color-danger);
  margin-left: 2px;
}
.field-group {
  margin-bottom: 0.75rem;
}
.field-label {
  display: block;
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--color-text);
  margin-bottom: var(--space-1);
}
.field-desc {
  font-size: var(--text-2xs);
  color: var(--color-text-subtle);
  margin: 0 0 4px 0;
}
.spec-field-textarea {
  width: 100%;
  min-height: 60px;
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: var(--text-sm);
  line-height: 1.6;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  resize: vertical;
}
.spec-field-json {
  width: 100%;
  min-height: 120px;
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: var(--text-xs);
  line-height: 1.6;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  resize: vertical;
}
.validation-errors {
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: var(--intent-danger-bg);
  border: 1px solid var(--intent-danger-text);
  border-radius: var(--radius-md);
}
.validation-error-item {
  font-size: var(--text-xs);
  color: var(--color-danger);
  margin-bottom: var(--space-1);
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
.task-link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}
.task-link:hover {
  text-decoration: underline;
}

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
.spec-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--color-text-subtle);
  font-size: var(--text-base);
}
.dialog-hint {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  margin-bottom: 1rem;
}
.spec-description {
  color: var(--color-text-muted);
  line-height: 1.6;
  margin-bottom: 1rem;
  font-size: var(--text-base);
}
.spec-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}
.spec-table th {
  background: var(--color-surface-muted);
  text-align: left;
  padding: 10px 12px;
  border-bottom: 2px solid var(--color-border);
  font-weight: 600;
  color: var(--color-text-muted);
  white-space: nowrap;
}
.spec-table td {
  padding: 9px 12px;
  border-bottom: 1px solid var(--color-border);
  vertical-align: top;
}
.spec-table tr:hover td {
  background: var(--color-surface-muted);
}
.spec-table.nested th {
  background: var(--color-surface-muted);
  font-size: var(--text-xs);
  padding: 8px 10px;
}
.spec-table.nested td {
  font-size: var(--text-xs);
  padding: 8px 10px;
}
.spec-table code,
.spec-card-header code,
.spec-trigger {
  font-family: 'SF Mono', 'Menlo', monospace;
  font-weight: 600;
  color: var(--color-text);
  font-size: var(--text-xs);
}
.spec-type {
  font-family: 'SF Mono', 'Menlo', monospace;
  color: var(--color-primary);
  font-size: var(--text-xs);
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
.spec-muted {
  color: var(--color-text-subtle);
}
.spec-fk {
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: var(--text-2xs);
  color: var(--intent-warning-text);
  background: var(--intent-warning-bg);
  padding: 1px 6px;
  border-radius: var(--radius-xs);
}
.spec-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-3);
  overflow: hidden;
}
.spec-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 12px 16px;
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}
.spec-card-desc {
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
}
.spec-card-body {
  padding: var(--space-4);
}
.spec-sub {
  margin-bottom: var(--space-3);
}
.spec-sub:last-child {
  margin-bottom: 0;
}
.spec-sub-title {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}
.spec-method {
  font-family: monospace;
  font-weight: 700;
  font-size: var(--text-xs);
  padding: 3px 10px;
  border-radius: var(--radius-xs);
  white-space: nowrap;
}
.spec-badge {
  font-size: var(--text-xs);
  color: var(--color-primary);
  background: var(--intent-info-bg);
  padding: 2px 8px;
  border-radius: var(--radius-xs);
}
.spec-route {
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}
.spec-response-block {
  background: var(--color-surface-muted);
  border-radius: var(--radius-sm);
  padding: 10px 12px;
  font-size: var(--text-sm);
}
.spec-json-tree {
  background: var(--color-surface-muted);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  font-size: var(--text-sm);
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  line-height: 1.6;
}
.spec-json-tree .json-line {
  margin-bottom: 2px;
}
.spec-key {
  color: var(--color-primary);
  font-weight: 500;
}
.spec-val {
  color: var(--color-text);
}
.spec-error-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 5px 0;
  font-size: var(--text-sm);
}
.spec-error-code {
  font-family: monospace;
  font-weight: 700;
  color: var(--color-danger);
  background: var(--intent-danger-bg);
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
}
.spec-indexes {
  padding: 10px 16px;
  background: var(--color-surface-muted);
  border-top: 1px solid var(--color-border);
  font-size: var(--text-xs);
}
.spec-index-label {
  font-weight: 600;
  color: var(--color-text-subtle);
  margin-right: var(--space-1);
}
.spec-index-item {
  margin-right: var(--space-4);
}
.spec-index-item code {
  color: var(--color-primary);
}
.spec-interactions {
  padding: 10px 16px;
  border-top: 1px solid var(--color-border);
}
.spec-interaction-item {
  display: flex;
  gap: var(--space-2);
  padding: 5px 0;
  font-size: var(--text-xs);
  border-bottom: 1px solid var(--color-border);
}
.spec-interaction-item:last-child {
  border-bottom: none;
}
.spec-trigger {
  color: var(--intent-warning-text);
  font-weight: 500;
  white-space: nowrap;
}
.spec-code-block {
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: var(--text-xs);
  line-height: 1.6;
  white-space: pre-wrap;
  color: var(--color-text);
  margin: 0;
}
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--color-text-subtle);
  font-size: var(--text-base);
}
</style>
