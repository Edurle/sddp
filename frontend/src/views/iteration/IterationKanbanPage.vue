<template>
  <div class="iteration-kanban-page">
    <h1>迭代看板</h1>
    <div v-if="iteration">
      <h2 data-testid="iteration-kanban-txt-name">{{ iteration.name }}</h2>
      <p data-testid="iteration-kanban-txt-stat">
        需求: {{ requirements.length }} | 状态统计: {{ statusSummary }}
      </p>
    </div>

    <button data-testid="iteration-kanban-btn-add-req" @click="showCreateReqDialog = true">添加需求</button>

    <div class="kanban-board">
      <div
        v-for="col in columns"
        :key="col.status"
        class="kanban-column"
        :data-testid="`iteration-kanban-col-${col.status}`"
      >
        <h3>{{ col.label }}</h3>
        <div
          v-for="req in getReqsByStatus(col.status)"
          :key="req.id"
          class="kanban-card"
          :data-testid="`iteration-kanban-card-req-${req.id}`"
        >
          <div
            :data-testid="`iteration-kanban-btn-req-${req.id}`"
            @click="goToRequirement(req.id)"
            style="cursor: pointer"
          >
            <div data-testid="iteration-kanban-card-req-title">{{ req.title }}</div>
            <div data-testid="iteration-kanban-card-req-type">{{ req.req_type }}</div>
            <div data-testid="iteration-kanban-card-req-priority">{{ req.priority }}</div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showCreateReqDialog" class="dialog-overlay" @click.self="showCreateReqDialog = false">
      <div data-testid="iteration-kanban-dlg-create-req" class="dialog">
        <h3>创建需求</h3>
        <div class="form-group">
          <label>标题</label>
          <input v-model="newReq.title" data-testid="iteration-kanban-dlg-create-req-inp-title" />
        </div>
        <div class="form-group">
          <label>类型</label>
          <select v-model="newReq.type" data-testid="iteration-kanban-dlg-create-req-sel-type">
            <option value="feature">功能需求</option>
            <option value="bug">Bug</option>
            <option value="optimization">优化</option>
          </select>
        </div>
        <div class="form-group">
          <label>优先级</label>
          <input v-model="newReq.priority" type="number" data-testid="iteration-kanban-dlg-create-req-inp-priority" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="newReq.description" data-testid="iteration-kanban-dlg-create-req-txtarea-desc"></textarea>
        </div>
        <div class="form-group">
          <label>类型详情</label>
          <textarea v-model="newReq.type_detail" data-testid="iteration-kanban-dlg-create-req-txtarea-type-detail"></textarea>
        </div>
        <button data-testid="iteration-kanban-dlg-create-req-btn-submit" @click="createRequirement">创建</button>
        <button @click="showCreateReqDialog = false">取消</button>
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
const iterationId = computed(() => route.params.id as string)

interface IterationData {
  id: number
  name: string
}

interface Requirement {
  id: number
  title: string
  req_type: string
  type?: string
  priority: string | number
  status: string
  mappedStatus: string
  description?: string
}

const iteration = ref<IterationData | null>(null)
const requirements = ref<Requirement[]>([])
const showCreateReqDialog = ref(false)

const newReq = reactive({
  title: '',
  type: 'feature',
  priority: '1',
  description: '',
  type_detail: '',
})

const columns = [
  { status: 'draft', label: '草稿' },
  { status: 'in_review', label: '审核中' },
  { status: 'approved', label: '已通过' },
  { status: 'in_progress', label: '进行中' },
  { status: 'completed', label: '已完成' },
]

const statusMap: Record<string, string> = {
  'drafting_req': 'draft',
  'reviewing_req': 'in_review',
  'drafting_spec': 'draft',
  'reviewing_spec': 'in_review',
  'drafting_tests': 'draft',
  'reviewing_tests': 'in_review',
  'approved': 'approved',
  'in_progress': 'in_progress',
  'completed': 'completed',
}

const statusSummary = computed(() => {
  const counts: Record<string, number> = {}
  requirements.value.forEach(r => {
    counts[r.mappedStatus] = (counts[r.mappedStatus] || 0) + 1
  })
  return Object.entries(counts).map(([k, v]) => `${k}: ${v}`).join(', ') || '无'
})

function getReqsByStatus(status: string) {
  return requirements.value.filter(r => r.mappedStatus === status)
}

async function fetchData() {
  try {
    const [iterRes, reqRes] = await Promise.allSettled([
      apiClient.get(`/api/v1/iterations/${iterationId.value}`),
      apiClient.get(`/api/v1/iterations/${iterationId.value}/requirements`),
    ])
    if (iterRes.status === 'fulfilled') {
      iteration.value = iterRes.value.data?.data || iterRes.value.data
    }
    if (reqRes.status === 'fulfilled') {
      const data = reqRes.value.data?.data
      const rawReqs = data?.items || data?.list || data || []
      requirements.value = rawReqs.map((r: Record<string, unknown>) => ({
        ...r,
        req_type: r.req_type || r.type || '',
        mappedStatus: statusMap[r.status as string] || (r.status as string),
      }))
    }
  } catch {
    // ignore
  }
}

async function createRequirement() {
  try {
    await apiClient.post('/api/v1/requirements', {
      title: newReq.title,
      type: newReq.type,
      priority: newReq.priority,
      description: newReq.description,
      type_detail: newReq.type_detail ? { text: newReq.type_detail } : null,
      iteration_id: iterationId.value,
    })
    showCreateReqDialog.value = false
    newReq.title = ''
    newReq.type = 'feature'
    newReq.priority = '1'
    newReq.description = ''
    newReq.type_detail = ''
    await fetchData()
  } catch {
    // ignore
  }
}

function goToRequirement(id: number) {
  router.push(`/requirements/${id}`)
}

onMounted(() => fetchData())
</script>

<style scoped>
.kanban-board {
  display: flex;
  gap: 1rem;
  overflow-x: auto;
}
.kanban-column {
  min-width: 250px;
  flex: 1;
  background: #f5f5f5;
  padding: 0.5rem;
  border-radius: 4px;
}
.kanban-card {
  background: white;
  padding: 0.75rem;
  margin: 0.5rem 0;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
}
</style>
