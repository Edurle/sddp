<template>
  <div class="team-settings-tab">
    <div class="form-group">
      <label>团队名称</label>
      <input v-model="form.name" data-testid="team-settings-inp-name" />
    </div>
    <div class="form-group">
      <label>团队描述</label>
      <textarea v-model="form.description" data-testid="team-settings-txtarea-desc"></textarea>
    </div>
    <button data-testid="team-settings-btn-save" :disabled="isPending('saveSettings')" @click="saveSettings">保存</button>
    <div v-if="successMsg" class="success-message" data-testid="team-settings-txt-success">{{ successMsg }}</div>

    <div class="form-group" style="margin-top: 2rem;">
      <h3>转让团队</h3>
      <button data-testid="team-settings-btn-transfer" @click="showTransferDialog = true">转让所有权</button>
    </div>

    <div class="form-group" style="margin-top: 1rem;">
      <h3>解散团队</h3>
      <button v-if="isOwner" class="btn-danger" data-testid="team-settings-btn-dissolve" @click="showDissolveDialog = true">解散团队</button>
      <button v-else data-testid="team-settings-btn-dissolve" style="display:none">解散团队</button>
    </div>

    <div v-if="showTransferDialog" class="dialog-overlay" @click.self="showTransferDialog = false">
      <div data-testid="team-settings-dlg-transfer" class="dialog">
        <h3>转让团队所有权</h3>
        <select data-testid="team-settings-dlg-transfer-sel-owner" v-model="transferTarget">
          <option value="">选择新所有者</option>
          <option v-for="m in members.filter(m => m.user_id !== currentUserId)" :key="m.user_id" :value="m.user_id">{{ m.nickname }}</option>
        </select>
        <button data-testid="team-settings-dlg-transfer-btn-confirm" :disabled="isPending('transferOwnership')" @click="transferOwnership">确认转让</button>
        <button @click="showTransferDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showDissolveDialog" class="dialog-overlay" @click.self="showDissolveDialog = false">
      <div data-testid="team-settings-dlg-dissolve" class="dialog">
        <h3>解散团队</h3>
        <p>确定要解散团队吗？此操作不可撤销。</p>
        <button class="btn-danger" data-testid="team-settings-dlg-dissolve-btn-confirm" :disabled="isPending('dissolveTeam')" @click="dissolveTeam">确认解散</button>
        <button @click="showDissolveDialog = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/api/client'
import { useAuthStore } from '@/stores/auth'
import { useAsyncAction } from '@/composables/useAsyncAction'

const props = defineProps<{ teamId: string; team: unknown }>()
const emit = defineEmits<{ teamUpdated: [] }>()

const router = useRouter()
const authStore = useAuthStore()
const { isPending, run } = useAsyncAction()

interface TeamData {
  id: number
  name: string
  description: string
  owner_id: number
  owner_name?: string
  owner_nickname?: string
}

interface Member {
  user_id: number | string
  nickname: string
}

const teamData = computed(() => props.team as TeamData | null)
function _getUserIdFromToken(): number | null {
  try {
    const token = localStorage.getItem('token') || sessionStorage.getItem('token')
    if (!token) return null
    const parts = token.split('.')
    if (parts.length !== 3) return null
    const payload = JSON.parse(atob(parts[1]))
    return parseInt(payload.sub, 10)
  } catch {
    return null
  }
}

const isOwner = computed(() => {
  if (!teamData.value) return false
  const userId = authStore.user?.id || _getUserIdFromToken()
  return teamData.value.owner_id === userId
})

const currentUserId = computed(() => {
  return authStore.user?.id || _getUserIdFromToken()
})

const form = reactive({ name: '', description: '' })
const successMsg = ref('')
const showTransferDialog = ref(false)
const showDissolveDialog = ref(false)
const transferTarget = ref('')
const members = ref<Member[]>([])

async function fetchMembers() {
  try {
    const res = await apiClient.get(`/api/v1/teams/${props.teamId}/members`)
    const data = res.data?.data
    members.value = data?.items || data?.list || data || []
  } catch {
    members.value = []
  }
}

function initForm() {
  if (teamData.value) {
    form.name = teamData.value.name
    form.description = teamData.value.description || ''
  }
}

async function saveSettings() {
  await run('saveSettings', async () => {
    successMsg.value = ''
    try {
      await apiClient.put(`/api/v1/teams/${props.teamId}`, form)
      successMsg.value = '保存成功'
      emit('teamUpdated')
    } catch {
      // ignore
    }
  })
}

async function transferOwnership() {
  await run('transferOwnership', async () => {
    try {
      await apiClient.post(`/api/v1/teams/${props.teamId}/transfer`, { new_owner_id: transferTarget.value })
      showTransferDialog.value = false
      emit('teamUpdated')
    } catch {
      // ignore
    }
  })
}

async function dissolveTeam() {
  await run('dissolveTeam', async () => {
    try {
      await apiClient.delete(`/api/v1/teams/${props.teamId}`)
      showDissolveDialog.value = false
      router.push('/dashboard')
    } catch {
      // ignore
    }
  })
}

onMounted(() => {
  fetchMembers()
})

watch(() => props.team, () => initForm(), { deep: true })
</script>
