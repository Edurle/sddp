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
    </nav>
    <main class="app-layout-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

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
}
.app-layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 1rem;
  height: 48px;
  border-bottom: 1px solid #e0e0e0;
  background: #fff;
}
.app-layout-brand {
  font-weight: bold;
  font-size: 1.1rem;
  color: inherit;
  text-decoration: none;
}
.app-layout-user {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.app-layout-nav {
  padding: 0.5rem 1rem;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  gap: 1rem;
}
.app-layout-nav a {
  color: #333;
  text-decoration: none;
  padding: 4px 8px;
  border-radius: 4px;
}
.app-layout-nav a:hover {
  background: #f0f0f0;
}
.app-layout-nav a.router-link-active {
  background: #1890ff;
  color: #fff;
}
.app-layout-main {
  flex: 1;
  padding: 1rem;
}
</style>
