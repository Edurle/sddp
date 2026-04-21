<template>
  <div class="dashboard-page">
    <h1>仪表盘</h1>
    <div>
      <span data-testid="dashboard-txt-nickname">{{ user?.nickname || '' }}</span>
      <span data-testid="dashboard-txt-email">{{ user?.email || '' }}</span>
    </div>
    <div>
      <router-link to="/change-password" data-testid="dashboard-link-change-password">修改密码</router-link>
      <router-link to="/edit-profile" data-testid="dashboard-link-edit-profile">编辑资料</router-link>
    </div>
    <div>
      <div data-testid="dashboard-list-pending-reviews">
        <h3>待审核列表</h3>
        <div v-if="pendingReviews.length === 0" class="empty-state">暂无待审核项</div>
        <div v-for="item in pendingReviews" :key="item.id">
          {{ item.title }}
        </div>
      </div>
      <div data-testid="dashboard-list-pending-tasks">
        <h3>待办任务列表</h3>
        <div v-if="pendingTasks.length === 0" class="empty-state">暂无待办任务</div>
        <div v-for="item in pendingTasks" :key="item.id">
          {{ item.title }}
        </div>
      </div>
      <div data-testid="dashboard-list-pending-invitations">
        <h3>待处理邀请列表</h3>
        <div v-if="pendingInvitations.length === 0" class="empty-state">暂无待处理邀请</div>
        <div v-for="item in pendingInvitations" :key="item.id">
          {{ item.team_name || item.name }}
          <button :data-testid="`dashboard-btn-accept-invitation-${item.id}`" @click="acceptInvitation(item.id)">接受</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { apiClient } from '@/api/client'

const authStore = useAuthStore()
const user = computed(() => authStore.user)

const pendingReviews = ref<Array<{ id: number; title: string }>>([])
const pendingTasks = ref<Array<{ id: number; title: string }>>([])
const pendingInvitations = ref<Array<{ id: number; team_name?: string; name?: string }>>([])

async function fetchData() {
  try {
    const [reviewsRes, tasksRes, invitationsRes] = await Promise.allSettled([
      apiClient.get('/api/v1/dashboard/pending-reviews'),
      apiClient.get('/api/v1/dashboard/pending-tasks'),
      apiClient.get('/api/v1/dashboard/pending-invitations'),
    ])
    if (reviewsRes.status === 'fulfilled') {
      pendingReviews.value = reviewsRes.value.data?.data?.items || reviewsRes.value.data?.data || []
    }
    if (tasksRes.status === 'fulfilled') {
      pendingTasks.value = tasksRes.value.data?.data?.items || tasksRes.value.data?.data || []
    }
    if (invitationsRes.status === 'fulfilled') {
      pendingInvitations.value = invitationsRes.value.data?.data?.items || invitationsRes.value.data?.data || []
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

onMounted(async () => {
  if (authStore.isAuthenticated && !authStore.user) {
    await authStore.fetchUser()
  }
  await fetchData()
})
</script>
