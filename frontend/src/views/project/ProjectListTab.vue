<template>
  <div class="project-list-tab">
    <div class="toolbar">
      <select data-testid="project-list-sel-status" v-model="statusFilter" @change="fetchProjects">
        <option value="">全部状态</option>
        <option value="active">进行中</option>
        <option value="archived">已归档</option>
      </select>
      <button data-testid="project-list-btn-create" @click="showCreateDialog = true">创建项目</button>
    </div>

    <table data-testid="project-list-tbl-projects">
      <thead>
        <tr>
          <th>名称</th>
          <th>描述</th>
          <th>状态</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="p in projects" :key="p.id" @click="goToProject(p.id)" style="cursor: pointer">
          <td>{{ p.name }}</td>
          <td>{{ p.description || '' }}</td>
          <td>{{ statusText(p.status) }}</td>
        </tr>
      </tbody>
    </table>

    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
      <div data-testid="project-list-dlg-create" class="dialog">
        <h3>创建项目</h3>
        <div class="form-group">
          <label>项目名称</label>
          <input v-model="newProject.name" data-testid="project-list-dlg-create-inp-name" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="newProject.description" data-testid="project-list-dlg-create-txtarea-desc"></textarea>
        </div>
        <div class="form-group">
          <label>开始日期</label>
          <input v-model="newProject.start_date" type="date" data-testid="project-list-dlg-create-inp-start-date" />
        </div>
        <button data-testid="project-list-dlg-create-btn-submit" @click="createProject">创建</button>
        <button @click="showCreateDialog = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/api/client'

const props = defineProps<{ teamId: string }>()
const router = useRouter()

interface Project {
  id: number
  name: string
  description: string
  status: string
}

const projects = ref<Project[]>([])
const statusFilter = ref('')
const showCreateDialog = ref(false)
const newProject = reactive({ name: '', description: '', start_date: '' })

function statusText(status: string) {
  if (status === 'active') return '进行中'
  if (status === 'archived') return '已归档'
  return status
}

async function fetchProjects() {
  try {
    const params: Record<string, unknown> = {}
    if (statusFilter.value) params.status = statusFilter.value
    const res = await apiClient.get(`/api/v1/teams/${props.teamId}/projects`, { params })
    const data = res.data?.data
    projects.value = data?.items || data?.list || data || []
  } catch {
    projects.value = []
  }
}

async function createProject() {
  try {
    await apiClient.post(`/api/v1/teams/${props.teamId}/projects`, newProject)
    showCreateDialog.value = false
    newProject.name = ''
    newProject.description = ''
    newProject.start_date = ''
    await fetchProjects()
  } catch {
    // ignore
  }
}

function goToProject(id: number) {
  router.push(`/projects/${id}`)
}

onMounted(() => fetchProjects())
</script>
