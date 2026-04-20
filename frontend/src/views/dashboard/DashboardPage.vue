<template>
  <div class="dashboard-page">
    <h1>仪表盘</h1>
    <div>
      <span data-testid="dashboard-txt-nickname">{{ user?.nickname }}</span>
      <span data-testid="dashboard-txt-email">{{ user?.email }}</span>
    </div>
    <div>
      <router-link to="/change-password" data-testid="dashboard-link-change-password">修改密码</router-link>
      <router-link to="/edit-profile" data-testid="dashboard-link-edit-profile">编辑资料</router-link>
    </div>
    <div>
      <div data-testid="dashboard-list-pending-reviews">待审核列表</div>
      <div data-testid="dashboard-list-pending-tasks">待办任务列表</div>
      <div data-testid="dashboard-list-pending-invitations">待处理邀请列表</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const user = computed(() => authStore.user)
</script>

<style scoped>
</style>
