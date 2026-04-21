<template>
  <div class="task-detail-page">
    <h1>任务详情</h1>
    <div v-if="task">
      <div class="main-info">
        <template v-if="!editing">
          <h2 data-testid="task-detail-txt-title">{{ task.title }}</h2>
          <p data-testid="task-detail-txt-description">{{ task.description }}</p>
          <p data-testid="task-detail-txt-status">{{ statusLabel(task.status) }}</p>
          <p data-testid="task-detail-txt-assignee">{{ task.assignee?.nickname || task.assignee?.email || '' }}</p>
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
        <button v-if="task.status === 'testing' && allTestsPassed" data-testid="task-detail-btn-complete" @click="completeTask">完成任务</button>
      </div>

      <div class="tabs-section">
        <button data-testid="task-detail-tab-spec" :class="{ active: activeTab === 'spec' }" @click="activeTab = 'spec'">规范</button>
        <button data-testid="task-detail-tab-test-exec" :class="{ active: activeTab === 'test-exec' }" @click="activeTab = 'test-exec'">测试执行</button>

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
                <td><span :data-testid="`task-detail-txt-record-status-${rec.id}`">{{ rec.status || 'pending' }}</span></td>
                <td><button :data-testid="`task-detail-btn-record-${rec.id}`" @click="openRecordDialog(rec)">更新</button></td>
              </tr>
            </tbody>
          </table>

          <div v-if="execHistory.length" class="exec-history">
            <h3>执行历史</h3>
            <div data-testid="task-detail-list-exec-history">
              <div v-for="(round, idx) in execHistory" :key="round.id || idx">
                <button :data-testid="`task-detail-btn-exec-round-${round.id || idx + 1}`" @click="viewRound(round)">
                  第 {{ idx + 1 }} 轮
                </button>
              </div>
            </div>
            <div v-if="roundRecords.length" data-testid="task-detail-tbl-round-records">
              <table>
                <thead><tr><th>用例</th><th>状态</th><th>结果</th></tr></thead>
                <tbody>
                  <tr v-for="r in roundRecords" :key="r.id">
                    <td>{{ r.test_case?.title || '' }}</td>
                    <td>{{ r.status === 'pass' ? '通过' : r.status === 'fail' ? '失败' : r.status }}</td>
                    <td>{{ r.actual_result || '' }}</td>
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
}

interface TestRound {
  id?: number
  records?: TestRecord[]
}

interface TaskData {
  id: number
  title: string
  description: string
  status: string
  assignee?: Assignee | null
  requirement?: Requirement | null
  requirement_id?: number
  test_records?: TestRecord[]
  latest_execution?: TestRound | null
}

const task = ref<TaskData | null>(null)
const editing = ref(false)
const editForm = reactive({ title: '', description: '' })
const activeTab = ref('spec')
const specContent = ref('')
const testRecords = ref<TestRecord[]>([])
const execHistory = ref<TestRound[]>([])
const roundRecords = ref<TestRecord[]>([])
const showRecordDialog = ref(false)
const recordForm = reactive({ id: 0, status: 'pass', actual_result: '', failure_reason: '' })
const recordError = ref('')

const allTestsPassed = computed(() => {
  if (testRecords.value.length === 0) return false
  return testRecords.value.every((r) => r.status === 'pass')
})

const testSummary = computed(() => {
  if (testRecords.value.length === 0) return '无测试记录'
  const passed = testRecords.value.filter((r) => r.status === 'pass').length
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

async function fetchTask() {
  try {
    const res = await apiClient.get(`/api/v1/tasks/${taskId.value}`)
    const data = res.data?.data || res.data
    task.value = data
    testRecords.value = data.test_records || data.latest_execution?.records || []
    if (data.latest_execution) {
      execHistory.value = [data.latest_execution]
    }
    if (data.requirement_id) {
      fetchSpec(data.requirement_id)
    }
  } catch {
    // ignore
  }
}

async function fetchSpec(reqId: number) {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId}/specification`)
    const data = res.data?.data || res.data
    specContent.value = data?.content || ''
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
  } catch {
    // ignore
  }
}

async function completeTask() {
  if (!allTestsPassed.value) return
  try {
    await apiClient.post(`/api/v1/tasks/${taskId.value}/complete`)
    await fetchTask()
  } catch {
    // ignore
  }
}

function openRecordDialog(rec: TestRecord) {
  recordForm.id = rec.id
  recordForm.status = rec.status || 'pass'
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
      status: recordForm.status,
      actual_result: recordForm.actual_result,
      failure_reason: recordForm.failure_reason,
    })
    showRecordDialog.value = false
    await fetchTask()
  } catch {
    // ignore
  }
}

function viewRound(round: TestRound) {
  roundRecords.value = round.records || []
}

onMounted(() => fetchTask())
</script>

<style scoped>
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
  min-height: 80px;
}
table {
  width: 100%;
  border-collapse: collapse;
}
th, td {
  border: 1px solid #e8e8e8;
  padding: 0.5rem;
}
.error {
  color: red;
}
</style>
