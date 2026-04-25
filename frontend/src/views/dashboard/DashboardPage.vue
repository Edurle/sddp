<template>
  <div class="dashboard-page">
    <h1>仪表盘</h1>
    <div class="user-info">
      <span data-testid="dashboard-txt-nickname">{{ user?.nickname || '' }}</span>
      <span data-testid="dashboard-txt-email">{{ user?.email || '' }}</span>
    </div>

    <div class="tabs">
      <button data-testid="dashboard-tab-teams" :class="{ active: activeTab === 'teams' }" @click="activeTab = 'teams'">我的团队</button>
      <button data-testid="dashboard-tab-pending" :class="{ active: activeTab === 'pending' }" @click="activeTab = 'pending'">待办事项</button>
      <button data-testid="dashboard-tab-profile" :class="{ active: activeTab === 'profile' }" @click="activeTab = 'profile'">个人资料</button>
    </div>

    <div v-if="activeTab === 'teams'">
      <div data-testid="dashboard-list-my-teams">
        <h3>我的团队</h3>
        <div v-if="myTeams.length === 0" class="empty-state">
          暂无团队
          <router-link to="/teams">创建团队</router-link>
        </div>
        <div v-for="team in myTeams" :key="team.id">
          <router-link :to="`/teams/${team.id}`" :data-testid="`dashboard-link-team-${team.id}`">{{ team.name }}</router-link>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'pending'">
      <div class="sub-tabs">
        <button data-testid="dashboard-tab-pending-reviews" :class="{ active: pendingSubTab === 'reviews' }" @click="pendingSubTab = 'reviews'">待审核</button>
        <button data-testid="dashboard-tab-pending-tasks" :class="{ active: pendingSubTab === 'tasks' }" @click="pendingSubTab = 'tasks'">待执行任务</button>
        <button data-testid="dashboard-tab-pending-invitations" :class="{ active: pendingSubTab === 'invitations' }" @click="pendingSubTab = 'invitations'">待处理邀请</button>
      </div>

      <div v-show="pendingSubTab === 'reviews'" data-testid="dashboard-list-pending-reviews">
        <h3>待审核列表</h3>
        <div v-if="pendingReviews.length === 0" class="empty-state">暂无待审核项</div>
        <div v-for="item in pendingReviews" :key="item.id">
          {{ item.title }}
        </div>
      </div>

      <div v-show="pendingSubTab === 'tasks'" data-testid="dashboard-list-pending-tasks">
        <h3>待办任务列表</h3>
        <div v-if="pendingTasks.length === 0" class="empty-state">暂无待办任务</div>
        <div v-for="item in pendingTasks" :key="item.id">
          {{ item.title }}
        </div>
      </div>

      <div v-show="pendingSubTab === 'invitations'" data-testid="dashboard-list-pending-invitations">
        <h3>待处理邀请列表</h3>
        <div v-if="pendingInvitations.length === 0" class="empty-state">暂无待处理邀请</div>
        <div v-for="item in pendingInvitations" :key="item.id">
          {{ item.team_name || item.name }}
          <button :data-testid="`dashboard-btn-accept-invitation-${item.id}`" @click="acceptInvitation(item.id)">接受</button>
          <button :data-testid="`dashboard-btn-reject-invitation-${item.id}`" @click="rejectInvitation(item.id)">拒绝</button>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'profile'">
      <div class="form-group">
        <label>昵称</label>
        <input v-model="profileNickname" data-testid="dashboard-inp-nickname" />
      </div>
      <div v-if="profileSuccess" class="success-message">{{ profileSuccess }}</div>
      <button data-testid="dashboard-btn-save-profile" @click="saveProfile">保存</button>
      <button data-testid="dashboard-btn-change-password" @click="showPasswordDialog = true">修改密码</button>

      <div v-if="showPasswordDialog" class="dialog-overlay" @click.self="showPasswordDialog = false">
        <div data-testid="dashboard-dlg-password" class="dialog">
          <h3>修改密码</h3>
          <div class="form-group">
            <label>旧密码</label>
            <input v-model="passwordForm.old" type="password" data-testid="dashboard-dlg-password-inp-old" />
          </div>
          <div class="form-group">
            <label>新密码</label>
            <input v-model="passwordForm.newPassword" type="password" data-testid="dashboard-dlg-password-inp-new" />
          </div>
          <div class="form-group">
            <label>确认新密码</label>
            <input v-model="passwordForm.confirm" type="password" data-testid="dashboard-dlg-password-inp-confirm" />
          </div>
          <div v-if="passwordError" class="error-message">{{ passwordError }}</div>
          <div v-if="passwordSuccess" class="success-message">{{ passwordSuccess }}</div>
          <button data-testid="dashboard-dlg-password-btn-submit" @click="changePassword">提交</button>
          <button @click="showPasswordDialog = false">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/api/client'

const authStore = useAuthStore()
const user = computed(() => authStore.user)
const myTeams = computed(() => (user.value as any)?.teams || [])

const activeTab = ref('teams')
const pendingSubTab = ref('reviews')
const profileNickname = ref('')
const profileSuccess = ref('')
const showPasswordDialog = ref(false)
const passwordError = ref('')
const passwordSuccess = ref('')
const passwordForm = reactive({ old: '', newPassword: '', confirm: '' })

const pendingReviews = ref<Array<{ id: number; title: string }>>([])
const pendingTasks = ref<Array<{ id: number; title: string }>>([])
const pendingInvitations = ref<Array<{ id: number; team_name?: string; name?: string }>>([])

watch(() => user.value, (u) => {
  if (u) profileNickname.value = (u as any).nickname || ''
}, { immediate: true })

async function fetchData() {
  try {
    const res = await apiClient.get('/api/v1/users/me/pending')
    const data = res.data?.data
    if (data) {
      pendingReviews.value = data.pending_reviews || []
      pendingTasks.value = data.pending_tasks || []
      pendingInvitations.value = data.pending_invitations || []
    }
  } catch {
    // ignore fetch errors
  }
}

async function acceptInvitation(id: number) {
  try {
    await apiClient.post(`/api/v1/invitations/${id}/accept`)
    pendingInvitations.value = pendingInvitations.value.filter(i => i.id !== id)
  } catch {
    // ignore
  }
}

async function rejectInvitation(id: number) {
  try {
    await apiClient.post(`/api/v1/invitations/${id}/reject`)
    pendingInvitations.value = pendingInvitations.value.filter(i => i.id !== id)
  } catch {
    // ignore
  }
}

async function saveProfile() {
  profileSuccess.value = ''
  try {
    await apiClient.put('/api/v1/users/me', { nickname: profileNickname.value })
    await authStore.fetchUser()
    profileSuccess.value = '保存成功'
  } catch {
    // ignore
  }
}

async function changePassword() {
  passwordError.value = ''
  passwordSuccess.value = ''
  if (passwordForm.newPassword !== passwordForm.confirm) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }
  try {
    await apiClient.put('/api/v1/users/me/password', {
      old_password: passwordForm.old,
      new_password: passwordForm.newPassword,
    })
    passwordSuccess.value = '密码修改成功'
    passwordForm.old = ''
    passwordForm.newPassword = ''
    passwordForm.confirm = ''
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '修改失败'
    if (msg.includes('旧密码') || msg.includes('原密码') || msg.includes('old password') || msg.includes('incorrect')) {
      passwordError.value = '旧密码错误'
    } else {
      passwordError.value = msg
    }
  }
}

onMounted(async () => {
  if (authStore.isAuthenticated && !authStore.user) {
    await authStore.fetchUser()
  }
  await fetchData()
})
</script>

<style scoped>
.dashboard-page {
  padding: 1.5rem;
}
.user-info {
  margin-bottom: 1rem;
  display: flex;
  gap: 1rem;
  font-size: 13px;
  color: #666;
}
</style>
