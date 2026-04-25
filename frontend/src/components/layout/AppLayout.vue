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
  background: #fff;
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
  background: rgba(0, 0, 0, 0.04);
  color: #111;
}
.app-layout-nav a.router-link-active {
  background: #111;
  color: #fff;
}
.app-layout-main {
  flex: 1;
  padding: 1.5rem;
}
</style>
