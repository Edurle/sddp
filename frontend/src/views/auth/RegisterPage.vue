<template>
  <div class="register-page">
    <form @submit.prevent="handleRegister" novalidate>
      <div class="form-group">
        <label for="email">邮箱</label>
        <input
          id="email"
          v-model="email"
          type="email"
          data-testid="register-inp-email"
        />
        <div v-if="errors.email" class="error-message">{{ errors.email }}</div>
      </div>
      <div class="form-group">
        <label for="password">密码</label>
        <input
          id="password"
          v-model="password"
          type="password"
          data-testid="register-inp-password"
        />
        <div v-if="errors.password" class="error-message">{{ errors.password }}</div>
      </div>
      <div class="form-group">
        <label for="nickname">昵称</label>
        <input
          id="nickname"
          v-model="nickname"
          type="text"
          data-testid="register-inp-nickname"
        />
        <div v-if="errors.nickname" class="error-message">{{ errors.nickname }}</div>
      </div>
      <div v-if="errors.general" class="error-message">{{ errors.general }}</div>
      <button type="submit" data-testid="register-btn-submit">注册</button>
    </form>
    <router-link to="/login" data-testid="register-link-login">已有账号？去登录</router-link>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { apiClient } from '@/api/client'

const router = useRouter()

const email = ref('')
const password = ref('')
const nickname = ref('')
const errors = reactive({ email: '', password: '', nickname: '', general: '' })

function validate(): boolean {
  let valid = true
  errors.email = ''
  errors.password = ''
  errors.nickname = ''
  errors.general = ''

  if (!email.value || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value)) {
    errors.email = '邮箱格式不正确'
    valid = false
  }
  if (!password.value || password.value.length < 8) {
    errors.password = '密码太短，至少需要8个字符'
    valid = false
  }
  if (!nickname.value || nickname.value.length < 2) {
    errors.nickname = '昵称太短，至少需要2个字符'
    valid = false
  }
  return valid
}

async function handleRegister() {
  if (!validate()) return
  try {
    await apiClient.post('/api/v1/auth/register', {
      email: email.value,
      password: password.value,
      nickname: nickname.value,
    })
    router.push('/login')
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '注册失败'
    if (msg.includes('已注册') || msg.includes('已存在')) {
      errors.general = '邮箱已注册'
    } else {
      errors.general = msg
    }
  }
}
</script>
