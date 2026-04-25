<template>
  <div class="task-detail-page">
    <h1>任务详情</h1>
    <div v-if="task">
      <div class="main-info">
        <template v-if="!editing">
          <h2 data-testid="task-detail-txt-title">{{ task.title }}</h2>
          <p data-testid="task-detail-txt-description">{{ task.description }}</p>
          <p data-testid="task-detail-txt-status">{{ statusLabel(task.status) }}</p>
          <p data-testid="task-detail-txt-assignee">{{ assigneeName }}</p>
          <p data-testid="task-detail-txt-linked-requirement">{{ task.requirement?.title || '' }}</p>
        </template>
        <template v-else>
          <div class="form-group">
            <label>标题</label>
            <input v-model="editForm.title" data-testid="task-detail-inp-title" />
          </div>
          <div class="form-group">
            <label>描述</label>
            <textarea v-model="editForm.description" data-testid="task-detail-txtarea-description"></textarea>
          </div>
        </template>
      </div>

      <div class="actions">
        <button v-if="task.status === 'pending' && !editing" data-testid="task-detail-btn-start" @click="startCoding">开始编码</button>
        <button v-if="task.status === 'coding'" data-testid="task-detail-btn-start-testing" @click="startTesting">开始测试</button>
        <button v-if="!editing" data-testid="task-detail-btn-edit" @click="startEdit">编辑</button>
        <button v-if="!editing" data-testid="task-detail-btn-delete" @click="deleteTask">删除</button>
        <button v-if="editing" data-testid="task-detail-btn-save" @click="saveEdit">保存</button>
        <button v-if="task.status === 'testing'" data-testid="task-detail-btn-complete" @click="completeTask">完成任务</button>
        <p v-if="completeError" class="error">{{ completeError }}</p>
      </div>

      <div class="tabs-section">
        <button data-testid="task-detail-tab-spec" :class="{ active: activeTab === 'spec' }" @click="activeTab = 'spec'">规范</button>
        <button v-if="task.status === 'testing' || task.status === 'completed'" data-testid="task-detail-tab-test-exec" :class="{ active: activeTab === 'test-exec' }" @click="activeTab = 'test-exec'; fetchTestExecutions()">测试执行</button>

        <div v-if="activeTab === 'spec'" class="tab-content">
          <div data-testid="task-detail-txt-spec-content">{{ specContent }}</div>
        </div>

        <div v-if="activeTab === 'test-exec'" class="tab-content">
          <p data-testid="task-detail-txt-test-summary">{{ testSummary }}</p>
          <table data-testid="task-detail-tbl-test-records">
            <thead>
              <tr>
                <th>用例</th>
                <th>状态</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="rec in testRecords" :key="rec.id">
                <td>{{ rec.test_case?.title || '' }}</td>
                <td><span :data-testid="`task-detail-txt-record-status-${rec.id}`">{{ recStatusLabel(rec.status) }}</span></td>
                <td><button :data-testid="`task-detail-btn-record-${rec.id}`" @click="openRecordDialog(rec)">更新</button></td>
              </tr>
            </tbody>
          </table>

          <div v-if="execHistory.length" class="exec-history">
            <h3>执行历史</h3>
            <div data-testid="task-detail-list-exec-rounds">
              <div data-testid="task-detail-list-exec-history">
                <div v-for="(round, idx) in execHistory" :key="round.id || idx">
                  <button :data-testid="`task-detail-btn-exec-round-${round.id || idx + 1}`" @click="viewRound(round)">
                    第 {{ idx + 1 }} 轮
                  </button>
                </div>
              </div>
            </div>
            <div v-if="roundRecords.length" data-testid="task-detail-tbl-round-records">
              <table>
                <thead><tr><th>用例</th><th>状态</th></tr></thead>
                <tbody>
                  <tr v-for="r in roundRecords" :key="r.id" :data-testid="`task-detail-row-record-${r.id}`">
                    <td>{{ r.test_case?.title || '' }}</td>
                    <td>{{ recStatusLabel(r.status) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showRecordDialog" class="dialog-overlay" @click.self="showRecordDialog = false">
      <div data-testid="task-detail-dlg-record" class="dialog">
        <h3>更新测试记录</h3>
        <select v-model="recordForm.status" data-testid="task-detail-dlg-record-sel-status">
          <option value="pass">通过</option>
          <option value="fail">失败</option>
          <option value="skip">跳过</option>
        </select>
        <div class="form-group">
          <label>实际结果</label>
          <textarea v-model="recordForm.actual_result" data-testid="task-detail-dlg-record-txtarea-result"></textarea>
        </div>
        <div v-if="recordForm.status === 'fail'" class="form-group">
          <label>失败原因</label>
          <textarea v-model="recordForm.failure_reason" data-testid="task-detail-dlg-record-txtarea-reason"></textarea>
        </div>
        <p v-if="recordError" class="error">{{ recordError }}</p>
        <button data-testid="task-detail-dlg-record-btn-save" @click="saveRecord">保存</button>
        <button @click="showRecordDialog = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '@/api/client'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.params.id as string)

interface Assignee {
  id?: number
  nickname?: string
  email?: string
}

interface Requirement {
  id: number
  title: string
}

interface TestCase {
  id?: number
  title?: string
}

interface TestRecord {
  id: number
  status: string
  actual_result?: string
  failure_reason?: string
  test_case?: TestCase
  test_case_id?: number
  round_id?: number
}

interface TestRound {
  id?: number
  round_id?: number
  total?: number
  passed?: number
  failed?: number
  skipped?: number
  records?: TestRecord[]
}

interface TaskData {
  id: number
  title: string
  description: string
  status: string
  assignee_id?: number
  assignee?: Assignee | null
  requirement?: Requirement | null
  requirement_id?: number
  test_records?: TestRecord[]
  test_cases?: TestCase[]
  latest_execution?: TestRound | null
}

const task = ref<TaskData | null>(null)
const editing = ref(false)
const editForm = reactive({ title: '', description: '' })
const activeTab = ref('spec')
const specContent = ref('')
const testRecords = ref<TestRecord[]>([])
const execHistory = ref<TestRound[]>([])
const execRounds = ref<TestRound[]>([])
const roundRecords = ref<TestRecord[]>([])
const showRecordDialog = ref(false)
const recordForm = reactive({ id: 0, status: 'pass', actual_result: '', failure_reason: '' })
const recordError = ref('')
const completeError = ref('')

const assigneeName = computed(() => {
  if (task.value?.assignee?.nickname) return task.value.assignee.nickname
  if (task.value?.assignee?.email) return task.value.assignee.email
  return ''
})

const allTestsPassed = computed(() => {
  if (testRecords.value.length === 0) return false
  return testRecords.value.every((r) => r.status === 'pass' || r.status === 'passed')
})

const testSummary = computed(() => {
  if (testRecords.value.length === 0) return '无测试记录'
  const passed = testRecords.value.filter((r) => r.status === 'pass' || r.status === 'passed').length
  if (passed === testRecords.value.length) return '全部通过'
  return `${passed}/${testRecords.value.length} 通过`
})

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '未开始',
    coding: '编码中',
    testing: '测试中',
    completed: '已完成',
  }
  return map[status] || status
}

function recStatusLabel(status: string) {
  const map: Record<string, string> = {
    pending: 'pending',
    pass: '通过',
    passed: '通过',
    fail: '失败',
    failed: '失败',
    skip: '跳过',
    skipped: '跳过',
  }
  return map[status] || status
}

async function fetchTask() {
  try {
    const res = await apiClient.get(`/api/v1/tasks/${taskId.value}`)
    const data = res.data?.data || res.data
    task.value = data
    if (data.requirement_id) {
      fetchSpec(data.requirement_id)
    }
    if (data.status === 'testing' || data.status === 'completed') {
      activeTab.value = 'test-exec'
      await fetchTestExecutions()
    }
  } catch {
    // ignore
  }
}

async function fetchTestExecutions() {
  try {
    const res = await apiClient.get(`/api/v1/tasks/${taskId.value}/test-executions`)
    const data = res.data?.data
    const rounds = data?.items || data?.list || data || []
    execRounds.value = rounds

    if (rounds.length > 0) {
      const latestRound = rounds[rounds.length - 1]
      const recRes = await apiClient.get(`/api/v1/test-executions/${latestRound.id || latestRound.round_id}/records`)
      const recData = recRes.data?.data
      const records = recData?.items || recData?.list || recData || []
      testRecords.value = records
      execHistory.value = rounds.map((r: TestRound) => ({
        ...r,
        id: r.id || r.round_id,
      }))
    }
  } catch {
    // ignore
  }
}

async function fetchSpec(reqId: number) {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId}/specification`)
    const data = res.data?.data || res.data
    if (data?.content) {
      specContent.value = typeof data.content === 'string' ? data.content : data.content.text || JSON.stringify(data.content, null, 2)
    }
  } catch {
    // ignore
  }
}

function startEdit() {
  if (task.value) {
    editForm.title = task.value.title
    editForm.description = task.value.description
  }
  editing.value = true
}

async function saveEdit() {
  try {
    await apiClient.put(`/api/v1/tasks/${taskId.value}`, editForm)
    editing.value = false
    await fetchTask()
  } catch {
    // ignore
  }
}

async function deleteTask() {
  if (!confirm('确定要删除此任务吗？')) return
  try {
    await apiClient.delete(`/api/v1/tasks/${taskId.value}`)
    router.push('/dashboard')
  } catch {
    // ignore
  }
}

async function startCoding() {
  try {
    await apiClient.patch(`/api/v1/tasks/${taskId.value}`, { status: 'coding' })
    await fetchTask()
  } catch {
    // ignore
  }
}

async function startTesting() {
  try {
    await apiClient.post(`/api/v1/tasks/${taskId.value}/start-testing`)
    await fetchTask()
    activeTab.value = 'test-exec'
    await fetchTestExecutions()
  } catch {
    // ignore
  }
}

async function completeTask() {
  completeError.value = ''
  try {
    await apiClient.post(`/api/v1/tasks/${taskId.value}/complete`)
    await fetchTask()
  } catch (e: any) {
    completeError.value = e?.message || e?.response?.data?.message || '操作失败'
  }
}

function openRecordDialog(rec: TestRecord) {
  recordForm.id = rec.id
  recordForm.status = rec.status === 'passed' ? 'pass' : rec.status === 'failed' ? 'fail' : rec.status
  recordForm.actual_result = rec.actual_result || ''
  recordForm.failure_reason = rec.failure_reason || ''
  recordError.value = ''
  showRecordDialog.value = true
}

async function saveRecord() {
  if (recordForm.status === 'fail' && !recordForm.failure_reason) {
    recordError.value = '失败原因必填'
    return
  }
  try {
    await apiClient.put(`/api/v1/test-execution-records/${recordForm.id}`, {
      status: recordForm.status === 'pass' ? 'passed' : recordForm.status === 'fail' ? 'failed' : recordForm.status === 'skip' ? 'skipped' : recordForm.status,
      actual_result: recordForm.actual_result,
      failure_reason: recordForm.failure_reason,
    })
    showRecordDialog.value = false
    await fetchTestExecutions()
  } catch {
    // ignore
  }
}

async function viewRound(round: TestRound) {
  try {
    const roundId = round.id || round.round_id
    if (!roundId) return
    const recRes = await apiClient.get(`/api/v1/test-executions/${roundId}/records`)
    const recData = recRes.data?.data
    roundRecords.value = recData?.items || recData?.list || recData || []
  } catch {
    roundRecords.value = []
  }
}

async function viewRoundFromList(round: TestRound) {
  try {
    const roundId = round.id || round.round_id
    if (!roundId) return
    const recRes = await apiClient.get(`/api/v1/test-executions/${roundId}/records`)
    const recData = recRes.data?.data
    roundRecords.value = recData?.items || recData?.list || recData || []
  } catch {
    roundRecords.value = []
  }
}

onMounted(async () => {
  await fetchTask()
  if (task.value && (task.value.status === 'testing' || task.value.status === 'completed')) {
    activeTab.value = 'test-exec'
    await fetchTestExecutions()
  }
})
</script>

<style scoped>
.task-detail-page {
  padding: 1.5rem;
}
.exec-history {
  margin-top: 1rem;
  padding-top: 0.5rem;
  border-top: 1px solid #f0f0f0;
}
</style>
