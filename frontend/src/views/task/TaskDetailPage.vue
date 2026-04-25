<template>
  <div class="task-detail-page">
    <div v-if="task" class="detail-layout">
      <TaskSidebar
        :task="task"
        :editing="editing"
        :edit-form="editForm"
        @edit="startEdit"
        @save="saveEdit"
        @delete="deleteTask"
        @start-coding="startCoding"
        @start-testing="startTesting"
        @complete="completeTask"
      />

      <div class="detail-main">
        <div class="detail-tabs">
          <button data-testid="task-detail-tab-spec" :class="['tab-btn', { active: activeTab === 'spec' }]" @click="activeTab = 'spec'">规范</button>
          <button v-if="task.status === 'testing' || task.status === 'completed'" data-testid="task-detail-tab-test-exec" :class="['tab-btn', { active: activeTab === 'test-exec' }]" @click="activeTab = 'test-exec'; fetchTestExecutions()">测试执行</button>
        </div>

        <div v-if="activeTab === 'spec'" class="tab-panel">
          <div class="spec-content" data-testid="task-detail-txt-spec-content">{{ specContent }}</div>
        </div>

        <div v-if="activeTab === 'test-exec'" class="tab-panel">
          <div class="test-summary-cards">
            <div class="summary-card">
              <div class="summary-num num-total">{{ testRecords.length }}</div>
              <div class="summary-label">总用例</div>
            </div>
            <div class="summary-card">
              <div class="summary-num num-pass">{{ testRecords.filter(r => r.status === 'pass' || r.status === 'passed').length }}</div>
              <div class="summary-label">通过</div>
            </div>
            <div class="summary-card">
              <div class="summary-num num-fail">{{ testRecords.filter(r => r.status === 'fail' || r.status === 'failed').length }}</div>
              <div class="summary-label">失败</div>
            </div>
            <div class="summary-card">
              <div class="summary-num num-skip">{{ testRecords.filter(r => r.status === 'skip' || r.status === 'skipped').length }}</div>
              <div class="summary-label">跳过</div>
            </div>
          </div>

          <p data-testid="task-detail-txt-test-summary" class="test-summary-text">{{ testSummary }}</p>

          <table data-testid="task-detail-tbl-test-records" class="test-table">
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
                <td><span :data-testid="`task-detail-txt-record-status-${rec.id}`" :class="['rec-status', `rec-${rec.status}`]">{{ recStatusLabel(rec.status) }}</span></td>
                <td><button :data-testid="`task-detail-btn-record-${rec.id}`" class="update-btn" @click="openRecordDialog(rec)">更新</button></td>
              </tr>
            </tbody>
          </table>

          <div v-if="execHistory.length" class="exec-history">
            <h3 class="exec-title">执行历史</h3>
            <div data-testid="task-detail-list-exec-rounds" class="round-bar">
              <div data-testid="task-detail-list-exec-history">
                <button
                  v-for="(round, idx) in execHistory"
                  :key="round.id || idx"
                  :data-testid="`task-detail-btn-exec-round-${round.id || idx + 1}`"
                  class="round-btn"
                  @click="viewRound(round)"
                >
                  第 {{ idx + 1 }} 轮
                </button>
              </div>
            </div>
            <div v-if="roundRecords.length" data-testid="task-detail-tbl-round-records">
              <table class="test-table">
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
import TaskSidebar from './TaskSidebar.vue'

const route = useRoute()
const router = useRouter()
const taskId = computed(() => route.params.id as string)

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
  assignee?: { id?: number; nickname?: string; email?: string } | null
  requirement?: { id: number; title: string } | null
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

const testSummary = computed(() => {
  if (testRecords.value.length === 0) return '无测试记录'
  const passed = testRecords.value.filter((r) => r.status === 'pass' || r.status === 'passed').length
  if (passed === testRecords.value.length) return '全部通过'
  return `${passed}/${testRecords.value.length} 通过`
})

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
  height: 100vh;
  overflow: hidden;
}
.detail-layout {
  display: flex;
  height: 100%;
}
.detail-main {
  flex: 1;
  padding: 1.25rem 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.detail-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid rgba(0, 0, 0, 0.06);
  margin-bottom: 1.25rem;
  flex-shrink: 0;
}
.tab-btn {
  padding: 8px 18px;
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
.spec-content {
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  padding: 1rem 1.25rem;
  font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
  color: #333;
}
.test-summary-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}
.summary-card {
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  padding: 0.75rem;
  text-align: center;
}
.summary-num {
  font-size: 22px;
  font-weight: 700;
}
.summary-label {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}
.num-total { color: #111; }
.num-pass { color: #52c41a; }
.num-fail { color: #ff4d4f; }
.num-skip { color: #faad14; }
.test-summary-text {
  font-size: 13px;
  color: #666;
  margin-bottom: 1rem;
  font-weight: 500;
}
.test-table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(20px);
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.04);
  margin-bottom: 1.25rem;
}
.test-table th, .test-table td {
  padding: 10px 14px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  text-align: left;
  font-size: 13px;
}
.test-table th {
  background: rgba(0, 0, 0, 0.02);
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #666;
}
.test-table tr:last-child td {
  border-bottom: none;
}
.rec-status {
  font-weight: 500;
}
.rec-pass, .rec-passed {
  color: #52c41a;
}
.rec-fail, .rec-failed {
  color: #ff4d4f;
}
.rec-skip, .rec-skipped {
  color: #faad14;
}
.rec-pending {
  color: #bbb;
}
.update-btn {
  padding: 3px 12px;
  border-radius: 4px;
  font-size: 11px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: #fff;
  color: #1677ff;
  cursor: pointer;
  font-family: inherit;
  font-weight: 500;
  margin: 0;
  transition: all 0.15s;
}
.update-btn:hover {
  border-color: #1677ff;
  background: rgba(22, 119, 255, 0.04);
}
.exec-history {
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding-top: 1rem;
}
.exec-title {
  font-size: 13px;
  font-weight: 600;
  color: #666;
  margin-bottom: 0.75rem;
}
.round-bar {
  margin-bottom: 1rem;
}
.round-bar button, .round-btn {
  padding: 5px 16px;
  border-radius: 20px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  background: #fff;
  color: #333;
  cursor: pointer;
  font-size: 12px;
  font-family: inherit;
  font-weight: 500;
  transition: all 0.15s;
  margin: 0 4px 4px 0;
}
.round-bar button:hover, .round-btn:hover {
  border-color: #1677ff;
  color: #1677ff;
}

@media (max-width: 768px) {
  .detail-layout {
    flex-direction: column;
  }
  .detail-main {
    padding: 1rem;
  }
  .test-summary-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
