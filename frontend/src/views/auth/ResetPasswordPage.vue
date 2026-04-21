<template>
  <div class="reset-password-page">
    <form @submit.prevent="handleSubmit">
      <div class="form-group">
        <label for="password">新密码</label>
        <input
          id="password"
          v-model="password"
          type="password"
          data-testid="reset-inp-password"
        />
      </div>
      <div class="form-group">
        <label for="confirm">确认密码</label>
        <input
          id="confirm"
          v-model="confirm"
          type="password"
          data-testid="reset-inp-confirm"
        />
      </div>
      <div v-if="error" class="error-message">{{ error }}</div>
      <button type="submit" data-testid="reset-btn-submit">重置密码</button>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/api/client'

const router = useRouter()

const password = ref('')
const confirm = ref('')
const error = ref('')

async function handleSubmit() {
  error.value = ''

  if (password.value.length < 6) {
    error.value = '密码太短，至少需要6个字符'
    return
  }

  if (password.value !== confirm.value) {
    error.value = '两次输入的密码不一致'
    return
  }

  const token = new URLSearchParams(window.location.search).get('token')
  try {
    await apiClient.post('/api/v1/auth/reset-password', {
      token,
      new_password: password.value,
    })
    router.push('/login')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '重置失败'
    if (msg.includes('无效') || msg.includes('过期') || msg.includes('expired')) {
      error.value = '链接无效或已过期'
    } else {
      error.value = msg
    }
  }
}
</script>
