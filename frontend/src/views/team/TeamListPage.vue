<template>
  <div class="team-list-page">
    <h1>我的团队</h1>
    <div class="toolbar">
      <button data-testid="team-list-btn-create" @click="showCreateDialog = true">创建团队</button>
    </div>

    <div v-if="teams.length === 0" class="empty-state">
      <p>你还没有加入任何团队</p>
      <button data-testid="team-list-btn-create-empty" @click="showCreateDialog = true">创建第一个团队</button>
    </div>

    <div class="team-cards" v-else>
      <div
        v-for="team in teams"
        :key="team.id"
        class="team-card"
        :data-testid="`team-list-card-team-${team.id}`"
        @click="goToTeam(team.id)"
      >
        <h3 data-testid="team-list-card-txt-name">{{ team.name }}</h3>
        <p data-testid="team-list-card-txt-roles">{{ (team.role_names || []).join(', ') || '成员' }}</p>
      </div>
    </div>

    <AppDialog :open="showCreateDialog" test-id="team-list-dlg-create" @close="showCreateDialog = false">
      <h3>创建团队</h3>
      <div class="form-group">
        <label>团队名称</label>
        <input v-model="newTeam.name" data-testid="team-list-dlg-create-inp-name" />
      </div>
      <div v-if="createError" class="error-message">{{ createError }}</div>
      <div class="form-group">
        <label>描述</label>
        <textarea v-model="newTeam.description" data-testid="team-list-dlg-create-txtarea-desc"></textarea>
      </div>
      <button data-testid="team-list-dlg-create-btn-submit" :disabled="isPending('createTeam')" @click="createTeam">创建</button>
      <button @click="showCreateDialog = false">取消</button>
    </AppDialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useAsyncAction } from '@/composables/useAsyncAction'
import AppDialog from '@/components/common/AppDialog.vue'

const router = useRouter()
const authStore = useAuthStore()
const { isPending, run } = useAsyncAction()

interface Team {
  id: number
  name: string
  role_names?: string[]
}

const teams = ref<Team[]>([])
const showCreateDialog = ref(false)
const createError = ref('')
const newTeam = reactive({ name: '', description: '' })

async function fetchTeams() {
  try {
    await authStore.fetchUser()
    teams.value = (authStore.user as any)?.teams || []
  } catch {
    teams.value = []
  }
}

async function createTeam() {
  await run('createTeam', async () => {
    createError.value = ''
    if (!newTeam.name.trim()) {
      createError.value = '团队名称不能为空'
      return
    }
    try {
      await apiClient.post('/api/v1/teams/', {
        name: newTeam.name,
        description: newTeam.description || null,
      })
      showCreateDialog.value = false
      newTeam.name = ''
      newTeam.description = ''
      await fetchTeams()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '创建失败'
      createError.value = msg
    }
  })
}

function goToTeam(id: number) {
  router.push(`/teams/${id}`)
}

onMounted(() => fetchTeams())
</script>

<style scoped>
.team-list-page h1 {
  margin: 0 0 1rem;
}
.team-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1rem;
}
.team-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 1rem;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.team-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}
.team-card h3 {
  margin: 0 0 0.5rem;
}
.team-card p {
  margin: 0;
  color: var(--color-text-muted);
  font-size: 0.9rem;
}
</style>
