<template>
  <div class="iteration-list-tab">
    <div class="toolbar">
      <select data-testid="iteration-list-sel-status" v-model="statusFilter" @change="fetchIterations">
        <option value="">全部状态</option>
        <option value="planning">计划中</option>
        <option value="in_progress">进行中</option>
        <option value="completed">已完成</option>
      </select>
      <button data-testid="iteration-list-btn-create" @click="showCreateDialog = true">创建迭代</button>
    </div>

    <table data-testid="iteration-list-tbl-iterations">
      <thead>
        <tr>
          <th>名称</th>
          <th>开始日期</th>
          <th>结束日期</th>
          <th>状态</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="it in iterations" :key="it.id" :data-iteration-id="it.id">
          <td>{{ it.name }}</td>
          <td>{{ it.start_date || '' }}</td>
          <td>{{ it.end_date || '' }}</td>
          <td>{{ statusText(it.status) }}</td>
          <td>
            <button :data-testid="`iteration-list-btn-edit-${it.id}`" @click="openEditDialog(it)">编辑</button>
            <button :data-testid="`iteration-list-btn-kanban-${it.id}`" @click="goToKanban(it.id)">看板</button>
            <button v-if="it.status === 'planning'" :data-testid="`iteration-list-btn-start-${it.id}`" @click="startIteration(it)">开始</button>
            <button v-if="it.status === 'in_progress'" :data-testid="`iteration-list-btn-complete-${it.id}`" @click="completeIteration(it)">完成</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="completeError" class="error-message" data-testid="iteration-list-txt-complete-error">{{ completeError }}</div>

    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
      <div data-testid="iteration-list-dlg-create" class="dialog">
        <h3>创建迭代</h3>
        <div class="form-group">
          <label>名称</label>
          <input v-model="newIter.name" data-testid="iteration-list-dlg-create-inp-name" />
        </div>
        <div class="form-group">
          <label>目标</label>
          <textarea v-model="newIter.goal" data-testid="iteration-list-dlg-create-txtarea-goal"></textarea>
        </div>
        <div class="form-group">
          <label>开始日期</label>
          <input v-model="newIter.start_date" type="date" data-testid="iteration-list-dlg-create-inp-start-date" />
        </div>
        <div class="form-group">
          <label>结束日期</label>
          <input v-model="newIter.end_date" type="date" data-testid="iteration-list-dlg-create-inp-end-date" />
        </div>
        <button data-testid="iteration-list-dlg-create-btn-submit" @click="createIteration">创建</button>
        <button @click="showCreateDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showEditDialog" class="dialog-overlay" @click.self="showEditDialog = false">
      <div data-testid="iteration-list-dlg-edit" class="dialog">
        <h3>编辑迭代</h3>
        <div class="form-group">
          <label>开始日期</label>
          <input v-model="editForm.start_date" type="date" data-testid="iteration-list-dlg-edit-inp-start-date" disabled />
        </div>
        <div class="form-group">
          <label>结束日期</label>
          <input v-model="editForm.end_date" type="date" data-testid="iteration-list-dlg-edit-inp-end-date" />
        </div>
        <button data-testid="iteration-list-dlg-edit-btn-submit" @click="saveEdit">保存</button>
        <button @click="showEditDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showStartConfirm" class="dialog-overlay" @click.self="showStartConfirm = false">
      <div data-testid="iteration-list-dlg-confirm-start" class="dialog">
        <h3>确认开始</h3>
        <p>确定要开始该迭代吗？</p>
        <button data-testid="iteration-list-dlg-confirm-start-btn-confirm" @click="confirmStart">确认</button>
        <button @click="showStartConfirm = false">取消</button>
      </div>
    </div>

    <div v-if="showCompleteConfirm" class="dialog-overlay" @click.self="showCompleteConfirm = false">
      <div data-testid="iteration-list-dlg-confirm-complete" class="dialog">
        <h3>确认完成</h3>
        <p>确定要完成该迭代吗？</p>
        <button data-testid="iteration-list-dlg-confirm-complete-btn-confirm" @click="confirmComplete">确认</button>
        <button @click="showCompleteConfirm = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/api/client'

const props = defineProps<{ projectId: string }>()
const router = useRouter()

interface Iteration {
  id: number
  name: string
  start_date: string
  end_date: string
  status: string
  goal?: string
}

const iterations = ref<Iteration[]>([])
const statusFilter = ref('')
const showCreateDialog = ref(false)
const showEditDialog = ref(false)
const showStartConfirm = ref(false)
const showCompleteConfirm = ref(false)
const completeError = ref('')

const newIter = reactive({ name: '', goal: '', start_date: '', end_date: '' })
const editForm = reactive({ start_date: '', end_date: '' })
const editingId = ref<number | null>(null)
const pendingIter = ref<Iteration | null>(null)

function statusText(status: string) {
  if (status === 'planning') return '计划中'
  if (status === 'in_progress') return '进行中'
  if (status === 'completed') return '已完成'
  return status
}

async function fetchIterations() {
  try {
    const params: Record<string, unknown> = {}
    if (statusFilter.value) params.status = statusFilter.value
    const res = await apiClient.get(`/api/v1/projects/${props.projectId}/iterations`, { params })
    const data = res.data?.data
    iterations.value = data?.items || data?.list || data || []
  } catch {
    iterations.value = []
  }
}

async function createIteration() {
  try {
    await apiClient.post(`/api/v1/projects/${props.projectId}/iterations`, newIter)
    showCreateDialog.value = false
    newIter.name = ''
    newIter.goal = ''
    newIter.start_date = ''
    newIter.end_date = ''
    await fetchIterations()
  } catch {
    // ignore
  }
}

function openEditDialog(it: Iteration) {
  editingId.value = it.id
  editForm.start_date = it.start_date
  editForm.end_date = it.end_date
  showEditDialog.value = true
}

async function saveEdit() {
  try {
    await apiClient.put(`/api/v1/iterations/${editingId.value}`, editForm)
    showEditDialog.value = false
    await fetchIterations()
  } catch {
    // ignore
  }
}

function startIteration(it: Iteration) {
  pendingIter.value = it
  completeError.value = ''
  showStartConfirm.value = true
}

async function confirmStart() {
  if (!pendingIter.value) return
  try {
    await apiClient.post(`/api/v1/iterations/${pendingIter.value.id}/start`)
    showStartConfirm.value = false
    await fetchIterations()
  } catch {
    // ignore
  }
}

function completeIteration(it: Iteration) {
  pendingIter.value = it
  completeError.value = ''
  showCompleteConfirm.value = true
}

async function confirmComplete() {
  if (!pendingIter.value) return
  try {
    await apiClient.post(`/api/v1/iterations/${pendingIter.value.id}/complete`)
    showCompleteConfirm.value = false
    await fetchIterations()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '完成失败'
    completeError.value = msg
    showCompleteConfirm.value = false
  }
}

function goToKanban(id: number) {
  router.push(`/iterations/${id}/kanban`)
}

onMounted(() => fetchIterations())
</script>
