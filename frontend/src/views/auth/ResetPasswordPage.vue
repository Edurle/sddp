<template>
  <div class="reset-password-page">
    <form @submit.prevent="handleSubmit">
      <div>
        <label for="password">新密码</label>
        <input
          id="password"
          v-model="password"
          type="password"
          data-testid="reset-inp-password"
        />
      </div>
      <div>
        <label for="confirm">确认密码</label>
        <input
          id="confirm"
          v-model="confirm"
          type="password"
          data-testid="reset-inp-confirm"
        />
      </div>
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

async function handleSubmit() {
  const token = new URLSearchParams(window.location.search).get('token')
  await apiClient.post('/api/v1/auth/reset-password', {
    token,
    new_password: password.value,
  })
  router.push('/login')
}
</script>

<style scoped>
</style>
