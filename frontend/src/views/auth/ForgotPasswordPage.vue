<template>
  <div class="forgot-password-page">
    <form @submit.prevent="handleSubmit">
      <div>
        <label for="email">邮箱</label>
        <input
          id="email"
          v-model="email"
          type="email"
          data-testid="forgot-inp-email"
        />
      </div>
      <button type="submit" data-testid="forgot-btn-submit">发送重置链接</button>
    </form>
    <router-link to="/login" data-testid="forgot-link-login">返回登录</router-link>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { apiClient } from '@/api/client'

const email = ref('')

async function handleSubmit() {
  await apiClient.post('/api/v1/auth/forgot-password', { email: email.value })
}
</script>

<style scoped>
</style>
