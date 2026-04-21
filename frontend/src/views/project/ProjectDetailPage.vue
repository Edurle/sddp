<template>
  <div class="project-detail-page">
    <h1>项目详情</h1>
    <div v-if="project">
      <h2 data-testid="project-detail-txt-name">{{ project.name }}</h2>
      <p data-testid="project-detail-txt-desc">{{ project.description || '' }}</p>
      <p data-testid="project-detail-txt-start-date">开始日期: {{ project.start_date || '' }}</p>
      <p data-testid="project-detail-txt-status">{{ statusText(project.status) }}</p>

      <div class="stats">
        <span data-testid="project-detail-txt-stat-req">需求数: {{ project.req_count ?? 0 }}</span>
        <span data-testid="project-detail-txt-stat-task">任务数: {{ project.task_count ?? 0 }}</span>
        <span data-testid="project-detail-txt-stat-test">测试数: {{ project.test_count ?? 0 }}</span>
      </div>

      <div class="actions">
        <button data-testid="project-detail-btn-edit" @click="openEditDialog">编辑</button>
        <button data-testid="project-detail-btn-archive" @click="showArchiveConfirm = true">归档</button>
        <button data-testid="project-detail-btn-delete" @click="showDeleteConfirm = true">删除</button>
        <button
          data-testid="project-detail-tab-iterations"
          :class="{ active: activeTab === 'iterations' }"
          @click="activeTab = 'iterations'"
        >迭代列表</button>
      </div>

      <IterationListTab v-if="activeTab === 'iterations' && project" :project-id="String(project.id)" />
    </div>

    <div v-if="showEditDialog" class="dialog-overlay" @click.self="showEditDialog = false">
      <div data-testid="project-detail-dlg-edit" class="dialog">
        <h3>编辑项目</h3>
        <div class="form-group">
          <label>项目名称</label>
          <input v-model="editForm.name" data-testid="project-detail-dlg-edit-inp-name" />
        </div>
        <button data-testid="project-detail-dlg-edit-btn-save" @click="saveEdit">保存</button>
        <button @click="showEditDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showArchiveConfirm" class="dialog-overlay" @click.self="showArchiveConfirm = false">
      <div data-testid="project-detail-dlg-confirm-archive" class="dialog">
        <h3>确认归档</h3>
        <p>确定要归档该项目吗？</p>
        <button data-testid="project-detail-dlg-confirm-archive-btn-confirm" @click="archiveProject">确认</button>
        <button @click="showArchiveConfirm = false">取消</button>
      </div>
    </div>

    <div v-if="showDeleteConfirm" class="dialog-overlay" @click.self="showDeleteConfirm = false">
      <div data-testid="project-detail-dlg-confirm-delete" class="dialog">
        <h3>确认删除</h3>
        <p>确定要删除该项目吗？</p>
        <button data-testid="project-detail-dlg-confirm-delete-btn-confirm" @click="deleteProject">确认</button>
        <button @click="showDeleteConfirm = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '@/api/client'
import IterationListTab from '../iteration/IterationListTab.vue'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => route.params.id as string)

interface ProjectData {
  id: number
  name: string
  description: string
  status: string
  start_date?: string
  req_count?: number
  task_count?: number
  test_count?: number
  team_id?: number
}

const project = ref<ProjectData | null>(null)
const activeTab = ref('')
const showEditDialog = ref(false)
const showArchiveConfirm = ref(false)
const showDeleteConfirm = ref(false)
const editForm = reactive({ name: '' })

function statusText(status: string) {
  if (status === 'active') return '进行中'
  if (status === 'archived') return '已归档'
  return status
}

async function fetchProject() {
  try {
    const res = await apiClient.get(`/api/v1/projects/${projectId.value}`)
    project.value = res.data?.data || res.data
  } catch {
    // ignore
  }
}

function openEditDialog() {
  if (project.value) {
    editForm.name = project.value.name
  }
  showEditDialog.value = true
}

async function saveEdit() {
  try {
    await apiClient.put(`/api/v1/projects/${projectId.value}`, editForm)
    showEditDialog.value = false
    await fetchProject()
  } catch {
    // ignore
  }
}

async function archiveProject() {
  try {
    await apiClient.patch(`/api/v1/projects/${projectId.value}`, { status: 'archived' })
    showArchiveConfirm.value = false
    await fetchProject()
  } catch {
    // ignore
  }
}

async function deleteProject() {
  try {
    const teamId = project.value?.team_id
    await apiClient.delete(`/api/v1/projects/${projectId.value}`)
    showDeleteConfirm.value = false
    if (teamId) {
      router.push(`/teams/${teamId}`)
    } else {
      router.push('/dashboard')
    }
  } catch {
    // ignore
  }
}

onMounted(() => fetchProject())
</script>
