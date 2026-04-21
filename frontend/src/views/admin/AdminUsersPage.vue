<template>
  <div class="admin-users-page">
    <div v-if="accessDenied" class="error-message">无权限</div>
    <template v-else>
    <h1>用户管理</h1>
    <div class="toolbar">
      <input
        v-model="search"
        type="text"
        placeholder="搜索用户"
        data-testid="user-mgmt-inp-search"
        @input="onSearch"
      />
      <button data-testid="user-mgmt-btn-create" @click="showCreateDialog = true">创建用户</button>
    </div>
    <table data-testid="user-mgmt-tbl-users">
      <thead>
        <tr>
          <th>ID</th>
          <th>邮箱</th>
          <th>昵称</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id">
          <td>{{ u.id }}</td>
          <td>{{ u.email }}</td>
          <td>{{ u.nickname }}</td>
          <td>
            <button
              :data-testid="`user-mgmt-btn-toggle-status-${u.id}`"
              @click="toggleStatus(u)"
            >
              {{ u.is_active ? '禁用' : '启用' }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
    <div data-testid="user-mgmt-pag-list">
      <button :disabled="page <= 1" @click="page--; fetchUsers()">上一页</button>
      <span>第 {{ page }} 页</span>
      <button v-show="page * pageSize < total" @click="page++; fetchUsers()">下一页</button>
    </div>

    <dialog :open="showCreateDialog" data-testid="user-mgmt-dlg-create">
      <div>
        <h3>创建用户</h3>
        <div class="form-group">
          <label>邮箱</label>
          <input v-model="newUser.email" data-testid="admin-users-dlg-create-inp-email" type="email" />
        </div>
        <div class="form-group">
          <label>昵称</label>
          <input v-model="newUser.nickname" data-testid="admin-users-dlg-create-inp-nickname" type="text" />
        </div>
        <div class="form-group">
          <label>密码</label>
          <input v-model="newUser.password" data-testid="admin-users-dlg-create-inp-password" type="password" />
        </div>
        <div v-if="createError" class="error-message">{{ createError }}</div>
        <button data-testid="admin-users-dlg-create-btn-submit" @click="createUser">确认创建</button>
        <button @click="showCreateDialog = false">关闭</button>
      </div>
    </dialog>
    <div v-if="errorMsg" class="error-message">{{ errorMsg }}</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { apiClient } from '@/api/client'

interface UserItem {
  id: number
  email: string
  nickname: string
  is_active: boolean
  is_admin: boolean
}

const search = ref('')
const users = ref<UserItem[]>([])
const page = ref(1)
const total = ref(0)
const pageSize = 20
const showCreateDialog = ref(false)
const errorMsg = ref('')
const createError = ref('')
const accessDenied = ref(false)

const newUser = reactive({ email: '', nickname: '', password: '' })

let searchTimer: ReturnType<typeof setTimeout> | null = null

function onSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    fetchUsers()
  }, 300)
}

async function fetchUsers() {
  try {
    const params: Record<string, unknown> = { page: page.value, page_size: 20 }
    if (search.value) params.search = search.value
    const res = await apiClient.get('/api/v1/admin/users', { params })
    const data = res.data?.data
    users.value = data?.items || data?.list || data || []
    total.value = data?.total || 0
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '获取失败'
    if (msg.includes('无权限') || msg.includes('forbidden') || msg.includes('403')) {
      accessDenied.value = true
    }
    users.value = []
  }
}

async function createUser() {
  createError.value = ''
  if (!newUser.email || !newUser.nickname || !newUser.password) {
    createError.value = '所有字段必填，不能为空'
    return
  }
  try {
    await apiClient.post('/api/v1/admin/users', newUser)
    showCreateDialog.value = false
    newUser.email = ''
    newUser.nickname = ''
    newUser.password = ''
    await fetchUsers()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '创建失败'
    if (msg.includes('已注册') || msg.includes('已存在')) {
      createError.value = '邮箱已注册'
    } else {
      createError.value = msg
    }
  }
}

async function toggleStatus(u: UserItem) {
  errorMsg.value = ''
  try {
    const newIsActive = !u.is_active
    await apiClient.put(`/api/v1/admin/users/${u.id}/status`, { is_active: newIsActive })
    u.is_active = newIsActive
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '操作失败'
    if (msg.includes('不能禁用自己') || msg.includes('不能禁用自身')) {
      errorMsg.value = '不能禁用自己'
    } else {
      errorMsg.value = msg
    }
  }
}

onMounted(() => fetchUsers())
</script>
