<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <h1>SDD</h1>
        <p>Spec-Driven Development</p>
      </div>
      <form @submit.prevent="handleLogin" novalidate>
        <div class="form-group">
          <label for="email">邮箱</label>
          <input
            id="email"
            v-model="email"
            type="email"
            placeholder="请输入邮箱"
            data-testid="login-inp-email"
          />
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <div class="password-wrapper">
            <input
              id="password"
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              placeholder="请输入密码"
              data-testid="login-inp-password"
            />
            <button type="button" class="toggle-pw" @click="showPassword = !showPassword" :aria-label="showPassword ? '隐藏密码' : '显示密码'">
              <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/><path d="M14.12 14.12a3 3 0 1 1-4.24-4.24"/></svg>
            </button>
          </div>
        </div>
        <div class="login-options">
          <label class="remember-label">
            <input
              id="remember"
              v-model="remember"
              type="checkbox"
              data-testid="login-chk-remember"
            />
            <span>记住我</span>
          </label>
        </div>
        <div v-if="error" class="error-message">{{ error }}</div>
        <button type="submit" class="login-btn" data-testid="login-btn-submit" :disabled="isPending('handleLogin')">登录</button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useAsyncAction } from '@/composables/useAsyncAction'

const router = useRouter()
const authStore = useAuthStore()
const { isPending, run } = useAsyncAction()

const email = ref('')
const password = ref('')
const remember = ref(false)
const error = ref('')
const showPassword = ref(false)

async function handleLogin() {
  await run('handleLogin', async () => {
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
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #fafafa 0%, #f0f0f0 50%, #e8e8e8 100%);
  padding: 1rem;
}

.login-card {
  width: 100%;
  max-width: 440px;
  background: var(--color-surface);
  backdrop-filter: blur(24px);
  border-radius: 20px;
  border: 1px solid var(--color-border);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.06),
    0 1px 3px rgba(0, 0, 0, 0.04);
  padding: 2.5rem 2rem 2rem;
}

.login-header {
  text-align: center;
  margin-bottom: 2rem;
}

.login-header h1 {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: -0.04em;
  color: var(--color-text);
  margin: 0;
}

.login-header p {
  color: var(--color-text-subtle);
  font-size: 13px;
  margin-top: 4px;
  letter-spacing: 0.02em;
}

.login-card .form-group {
  margin-bottom: 1.25rem;
}

.login-card .form-group input[type="email"],
.login-card .form-group input[type="password"] {
  width: 100%;
  padding: 11px 14px;
  border: 1px solid var(--color-border-strong);
  border-radius: 10px;
  background: var(--color-surface);
  font-size: 14px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.login-card .form-group input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  background: var(--color-surface);
}

.login-options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
  font-size: 13px;
}

.remember-label {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: var(--color-text-muted);
}

.remember-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: var(--color-primary);
  cursor: pointer;
}

.login-btn {
  width: 100%;
  padding: 14px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s, box-shadow 0.2s, transform 0.1s;
  margin: 0;
  display: block;
}

.login-btn:hover {
  background: var(--color-primary-hover);
  color: #fff;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
}

.login-btn:active {
  transform: translateY(0.5px);
}

.password-wrapper {
  position: relative;
}

.password-wrapper input {
  width: 100%;
  padding-right: 42px;
}

.toggle-pw {
  position: absolute;
  right: 4px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--color-text-subtle);
  cursor: pointer;
  padding: 6px;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-pw:hover {
  color: var(--color-text);
  background: none;
  box-shadow: none;
}
</style>
