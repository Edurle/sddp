<template>
  <div class="app-layout">
    <header class="app-layout-header">
      <span class="app-layout-brand">SDD Platform</span>
      <div class="app-layout-user" v-if="authStore.isAuthenticated">
        <span>{{ authStore.user?.nickname || authStore.user?.email }}</span>
        <button @click="handleLogout">退出</button>
      </div>
    </header>
    <nav class="app-layout-nav" v-if="authStore.isAuthenticated">
      <router-link to="/dashboard">仪表盘</router-link>
    </nav>
    <main class="app-layout-main">
      <slot />
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
.app-layout-main {
  flex: 1;
  padding: 1rem;
}
</style>
