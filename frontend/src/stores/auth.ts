import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { apiClient } from '@/api/client'

interface User {
  id: number
  email: string
  nickname: string
  role?: string
  status?: string
  is_admin?: boolean
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('token') || sessionStorage.getItem('token'))

  const isAuthenticated = computed(() => !!token.value)

  async function login(email: string, password: string, remember: boolean = false) {
    const response = await apiClient.post('/api/v1/auth/login', { email, password })
    const body = response.data
    const tokenVal = body.data?.token || body.data?.access_token
    const userVal = body.data?.user
    token.value = tokenVal
    user.value = userVal || null
    if (remember) {
      localStorage.setItem('token', tokenVal)
    } else {
      sessionStorage.setItem('token', tokenVal)
    }
  }

  function logout() {
    user.value = null
    token.value = null
    localStorage.removeItem('token')
    sessionStorage.removeItem('token')
  }

  async function fetchUser() {
    if (!token.value) return
    try {
      const response = await apiClient.get('/api/v1/users/me')
      user.value = response.data.data || response.data
    } catch {
      logout()
    }
  }

  return { user, token, isAuthenticated, login, logout, fetchUser }
})
