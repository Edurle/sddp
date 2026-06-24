<template>
  <div class="app-layout">
    <header class="app-layout-header">
      <router-link to="/dashboard" class="app-layout-brand">SDD Platform</router-link>
      <div class="app-layout-user" v-if="authStore.isAuthenticated">
        <span>{{ authStore.user?.nickname || authStore.user?.email }}</span>
        <button @click="handleLogout">退出</button>
      </div>
      <div v-else class="app-layout-user">
        <router-link to="/login">登录</router-link>
      </div>
    </header>
    <nav class="app-layout-nav" v-if="authStore.isAuthenticated">
      <router-link to="/dashboard">仪表盘</router-link>
      <router-link to="/teams">我的团队</router-link>
      <router-link to="/profile/api-keys">API Keys</router-link>
      <router-link v-if="authStore.user?.is_admin" to="/admin/users">管理</router-link>
    </nav>
    <div v-if="authStore.isAuthenticated && breadcrumbItems.length > 0" class="breadcrumb-bar">
      <router-link to="/dashboard">仪表盘</router-link>
      <template v-for="(item, i) in breadcrumbItems" :key="i">
        <span class="breadcrumb-sep">/</span>
        <router-link v-if="i < breadcrumbItems.length - 1" :to="item.to">{{ item.label }}</router-link>
        <span v-else class="breadcrumb-current">{{ item.label }}</span>
      </template>
    </div>
    <main class="app-layout-main">
      <router-view />
    </main>
    <transition name="toast-slide">
      <div v-if="notification.visible" class="notification-toast" :class="notification.type" role="alert">
        <span class="toast-msg">{{ notification.message }}</span>
        <button class="toast-close" aria-label="关闭" @click="notification.hide()">×</button>
      </div>
    </transition>
    <ConfirmDialog />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import ConfirmDialog from '@/components/common/ConfirmDialog.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const notification = useNotificationStore()

const breadcrumbLabels: Record<string, string> = {
  teams: '团队', projects: '项目', iterations: '迭代',
  requirements: '需求', tasks: '任务',
}

const breadcrumbItems = computed(() => {
  const items: { label: string; to: string }[] = []
  const path = route.path
  const matches = path.match(/\/(teams|projects|iterations|requirements|tasks)\/(\d+)/g)
  if (!matches) return items
  for (const m of matches) {
    const parts = m.match(/\/(\w+)\/(\d+)/)
    if (!parts) continue
    const type = parts[1]
    const id = parts[2]
    items.push({ label: `${breadcrumbLabels[type] || type} #${id}`, to: m })
  }
  return items
})

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  background: var(--color-bg);
}
.app-layout-header {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  padding: 0 1.5rem;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.app-layout-brand {
  font-weight: 700;
  font-size: 1.1rem;
  color: #111;
  text-decoration: none;
  letter-spacing: -0.02em;
}
.app-layout-user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.app-layout-nav {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  padding: 0.5rem 1.5rem;
  display: flex;
  gap: 0.5rem;
}
.app-layout-nav a {
  color: #666;
  text-decoration: none;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 13px;
  transition: all 0.2s ease;
}
.app-layout-nav a:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}
.app-layout-nav a.router-link-active {
  background: var(--color-primary);
  color: #fff;
}
.app-layout-main {
  flex: 1;
  padding: 1.5rem;
}
.notification-toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px 12px 18px;
  border-radius: 10px;
  font-size: 14px;
  z-index: 1100;
  max-width: min(90vw, 480px);
  box-shadow: 0 6px 24px rgba(15, 23, 42, 0.16);
}
.toast-msg {
  flex: 1;
}
.toast-close {
  flex-shrink: 0;
  margin: 0;
  padding: 0;
  width: 20px;
  height: 20px;
  line-height: 1;
  font-size: 18px;
  background: transparent;
  border: none;
  color: inherit;
  opacity: 0.55;
  cursor: pointer;
}
.toast-close:hover {
  opacity: 1;
  background: transparent;
  box-shadow: none;
}
.notification-toast.error {
  background: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}
.notification-toast.success {
  background: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}
.toast-slide-enter-active,
.toast-slide-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.toast-slide-enter-from,
.toast-slide-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-12px);
}
.breadcrumb-bar {
  padding: 8px 24px;
  font-size: 13px;
  color: #888;
  display: flex;
  align-items: center;
  gap: 6px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
}
.breadcrumb-bar a {
  color: #666;
  text-decoration: none;
}
.breadcrumb-bar a:hover { color: var(--color-primary); }
.breadcrumb-sep { color: #ccc; }
.breadcrumb-current { color: #333; font-weight: 500; }
</style>
