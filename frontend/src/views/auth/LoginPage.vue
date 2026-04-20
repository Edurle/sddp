<template>
  <div class="login-page">
    <form @submit.prevent="handleLogin">
      <div>
        <label for="email">邮箱</label>
        <input
          id="email"
          v-model="email"
          type="email"
          data-testid="login-inp-email"
        />
      </div>
      <div>
        <label for="password">密码</label>
        <input
          id="password"
          v-model="password"
          type="password"
          data-testid="login-inp-password"
        />
      </div>
      <div>
        <input
          id="remember"
          v-model="remember"
          type="checkbox"
          data-testid="login-chk-remember"
        />
        <label for="remember">记住我</label>
      </div>
      <button type="submit" data-testid="login-btn-submit">登录</button>
    </form>
    <router-link to="/register" data-testid="login-link-register">注册账号</router-link>
    <router-link to="/forgot-password" data-testid="login-link-forgot">忘记密码</router-link>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const remember = ref(false)

async function handleLogin() {
  await authStore.login(email.value, password.value, remember.value)
  router.push('/dashboard')
}
</script>

<style scoped>
</style>
