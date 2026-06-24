<template>
  <div class="project-list-tab">
    <div class="toolbar">
      <div class="custom-select" style="position: relative; display: inline-block">
        <div
          data-testid="project-list-sel-status"
          class="select-trigger"
          @click="showStatusDropdown = !showStatusDropdown"
          style="padding: 4px 8px; border: 1px solid var(--color-border); cursor: pointer; min-width: 120px; background: var(--color-surface)"
        >
          {{ statusFilterText }}
        </div>
        <div
          v-if="showStatusDropdown"
          style="position: absolute; top: 100%; left: 0; z-index: 1000; background: var(--color-surface); border: 1px solid var(--color-border); min-width: 120px"
        >
          <div @click="selectStatus('')" style="padding: 4px 8px; cursor: pointer">全部状态</div>
          <div @click="selectStatus('active')" style="padding: 4px 8px; cursor: pointer">进行中</div>
          <div @click="selectStatus('archived')" style="padding: 4px 8px; cursor: pointer">已归档</div>
        </div>
      </div>
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
        <tr v-for="p in projects" :key="p.id" style="cursor: pointer">
          <td>
            <a
              :href="`/projects/${p.id}`"
              style="color: inherit; text-decoration: none; display: block; width: 100%"
            >{{ p.name }}</a>
          </td>
          <td>
            <a
              :href="`/projects/${p.id}`"
              style="color: inherit; text-decoration: none; display: block; width: 100%"
            >{{ p.description || '' }}</a>
          </td>
          <td>
            <a
              :href="`/projects/${p.id}`"
              style="color: inherit; text-decoration: none; display: block; width: 100%"
            >{{ statusText(p.status) }}</a>
          </td>
        </tr>
      </tbody>
    </table>

    <AppDialog :open="showCreateDialog" test-id="project-list-dlg-create" @close="showCreateDialog = false">
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
      <button data-testid="project-list-dlg-create-btn-submit" :disabled="isPending('createProject')" @click="createProject">创建</button>
      <button @click="showCreateDialog = false">取消</button>
    </AppDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { apiClient } from '@/api/client'
import { useAsyncAction } from '@/composables/useAsyncAction'
import AppDialog from '@/components/common/AppDialog.vue'

const props = defineProps<{ teamId: string }>()
const { isPending, run } = useAsyncAction()

interface Project {
  id: number
  name: string
  description: string
  status: string
}

const allProjects = ref<Project[]>([])
const statusFilter = ref('')
const showStatusDropdown = ref(false)
const showCreateDialog = ref(false)
const newProject = reactive({ name: '', description: '', start_date: '' })

const projects = computed(() => {
  if (!statusFilter.value) return allProjects.value
  return allProjects.value.filter(p => p.status === statusFilter.value)
})

const statusFilterText = computed(() => {
  if (statusFilter.value === 'active') return '进行中'
  if (statusFilter.value === 'archived') return '已归档'
  return '全部状态'
})

function statusText(status: string) {
  if (status === 'active') return '进行中'
  if (status === 'archived') return '已归档'
  return status
}

function selectStatus(value: string) {
  statusFilter.value = value
  showStatusDropdown.value = false
}

async function fetchProjects() {
  try {
    const res = await apiClient.get(`/api/v1/teams/${props.teamId}/projects`)
    const data = res.data?.data
    allProjects.value = data?.items || data?.list || data || []
  } catch {
    allProjects.value = []
  }
}

async function createProject() {
  await run('createProject', async () => {
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
  })
}

onMounted(() => fetchProjects())
</script>
