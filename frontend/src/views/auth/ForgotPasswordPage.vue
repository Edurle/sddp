<template>
  <div class="forgot-password-page">
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="email">邮箱</label>
        <input
          id="email"
          v-model="email"
          type="email"
          data-testid="forgot-inp-email"
        />
        <div v-if="error" class="error-message">{{ error }}</div>
      </div>
      <div v-if="success" class="success-message">重置邮件已发送，请检查您的邮箱</div>
      <button type="submit" data-testid="forgot-btn-submit">发送重置链接</button>
    </form>
    <router-link to="/login" data-testid="forgot-link-login">返回登录</router-link>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { apiClient } from '@/api/client'

const email = ref('')
const error = ref('')
const success = ref(false)

async function handleSubmit() {
  error.value = ''
  success.value = false

  if (!email.value || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    error.value = '邮箱格式不正确'
    return
  }

  try {
    await apiClient.post('/api/v1/auth/forgot-password', { email: email.value })
    success.value = true
  } catch {
    success.value = true
  }
}
</script>
