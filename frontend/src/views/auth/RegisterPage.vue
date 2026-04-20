<template>
  <div class="register-page">
    <form @submit.prevent="handleRegister">
      <div>
        <label for="email">邮箱</label>
        <input
          id="email"
          v-model="email"
          type="email"
          data-testid="register-inp-email"
        />
      </div>
      <div>
        <label for="password">密码</label>
        <input
          id="password"
          v-model="password"
          type="password"
          data-testid="register-inp-password"
        />
      </div>
      <div>
        <label for="nickname">昵称</label>
        <input
          id="nickname"
          v-model="nickname"
          type="text"
          data-testid="register-inp-nickname"
        />
      </div>
      <button type="submit" data-testid="register-btn-submit">注册</button>
    </form>
    <router-link to="/login" data-testid="register-link-login">已有账号？去登录</router-link>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/api/client'

const router = useRouter()

const email = ref('')
const password = ref('')
const nickname = ref('')

async function handleRegister() {
  await apiClient.post('/api/v1/auth/register', {
    email: email.value,
    password: password.value,
    nickname: nickname.value,
  })
  router.push('/login')
}
</script>

<style scoped>
</style>
