<template>
  <div class="login-page">
    <form @submit.prevent="handleLogin">
      <div class="form-group">
        <label for="email">邮箱</label>
        <input
          id="email"
          v-model="email"
          type="email"
          data-testid="login-inp-email"
        />
      </div>
      <div class="form-group">
        <label for="password">密码</label>
        <input
          id="password"
          v-model="password"
          type="password"
          data-testid="login-inp-password"
        />
      </div>
      <div class="form-group">
        <input
          id="remember"
          v-model="remember"
          type="checkbox"
          data-testid="login-chk-remember"
        />
        <label for="remember">记住我</label>
      </div>
      <div v-if="error" class="error-message">{{ error }}</div>
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
const error = ref('')

async function handleLogin() {
  error.value = ''
  try {
    await authStore.login(email.value, password.value, remember.value)
    router.push('/dashboard')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '登录失败'
    if (msg.includes('密码错误') || msg.includes('密码不正确')) {
      error.value = '邮箱或密码错误'
    } else if (msg.includes('未验证') || msg.includes('未激活')) {
      error.value = '邮箱未验证'
    } else if (msg.includes('不存在') || msg.includes('未注册')) {
      error.value = '邮箱或密码错误'
    } else {
      error.value = msg
    }
  }
}
</script>
