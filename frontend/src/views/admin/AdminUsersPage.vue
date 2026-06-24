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
          <td class="action-cell">
            <button
              :data-testid="`user-mgmt-btn-toggle-status-${u.id}`"
              :disabled="isPending(`toggleStatus-${u.id}`)"
              @click="toggleStatus(u)"
            >
              {{ u.is_active ? '禁用' : '启用' }}
            </button>
            <button
              :data-testid="`user-mgmt-btn-reset-pw-${u.id}`"
              class="btn-reset-pw"
              @click="openResetDialog(u)"
            >
              重置密码
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

    <div v-if="showCreateDialog" class="dialog-overlay" @click.self="showCreateDialog = false">
      <div class="dialog" data-testid="user-mgmt-dlg-create">
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
        <div class="dialog-actions">
          <button data-testid="admin-users-dlg-create-btn-submit" :disabled="isPending('createUser')" @click="createUser">确认创建</button>
          <button class="btn-cancel" @click="showCreateDialog = false">关闭</button>
        </div>
      </div>
    </div>

    <div v-if="showResetDialog" class="dialog-overlay" @click.self="showResetDialog = false">
      <div class="dialog" data-testid="user-mgmt-dlg-reset-pw">
        <h3>重置密码 — {{ resetTargetUser?.email }}</h3>
        <div class="form-group">
          <label>新密码</label>
          <input v-model="resetPw.newPassword" type="password" placeholder="至少 8 位" />
        </div>
        <div class="form-group">
          <label>确认密码</label>
          <input v-model="resetPw.confirmPassword" type="password" placeholder="再次输入新密码" />
        </div>
        <div v-if="resetError" class="error-message">{{ resetError }}</div>
        <div v-if="resetSuccess" class="success-message">密码已重置</div>
        <div class="dialog-actions">
          <button :disabled="isPending('resetPassword')" @click="resetPassword">确认重置</button>
          <button class="btn-cancel" @click="showResetDialog = false">关闭</button>
        </div>
      </div>
    </div>

    <div v-if="errorMsg" class="error-message">{{ errorMsg }}</div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { apiClient } from '@/api/client'
import { useAsyncAction } from '@/composables/useAsyncAction'

interface UserItem {
  id: number
  email: string
  nickname: string
  is_active: boolean
  is_admin: boolean
}

const { isPending, run } = useAsyncAction()

const search = ref('')
const users = ref<UserItem[]>([])
const page = ref(1)
const total = ref(0)
const pageSize = 20
const showCreateDialog = ref(false)
const showResetDialog = ref(false)
const errorMsg = ref('')
const createError = ref('')
const resetError = ref('')
const resetSuccess = ref(false)
const accessDenied = ref(false)
const resetTargetUser = ref<UserItem | null>(null)

const newUser = reactive({ email: '', nickname: '', password: '' })
const resetPw = reactive({ newPassword: '', confirmPassword: '' })

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
  await run('createUser', async () => {
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
  })
}

async function toggleStatus(u: UserItem) {
  await run(`toggleStatus-${u.id}`, async () => {
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
  })
}

function openResetDialog(u: UserItem) {
  resetTargetUser.value = u
  resetPw.newPassword = ''
  resetPw.confirmPassword = ''
  resetError.value = ''
  resetSuccess.value = false
  showResetDialog.value = true
}

async function resetPassword() {
  await run('resetPassword', async () => {
    resetError.value = ''
    resetSuccess.value = false
    if (!resetPw.newPassword || resetPw.newPassword.length < 8) {
      resetError.value = '密码至少 8 位'
      return
    }
    if (resetPw.newPassword !== resetPw.confirmPassword) {
      resetError.value = '两次密码不一致'
      return
    }
    try {
      await apiClient.put(`/api/v1/admin/users/${resetTargetUser.value!.id}/password`, {
        new_password: resetPw.newPassword,
      })
      resetSuccess.value = true
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '重置失败'
      resetError.value = msg
    }
  })
}

onMounted(() => fetchUsers())
</script>

<style scoped>
.admin-users-page {
  padding: 2rem;
  max-width: 900px;
  margin: 0 auto;
}

h1 {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
}

.toolbar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.toolbar input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
}

table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 1rem;
}

th, td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
  font-size: var(--text-base);
}

.action-cell {
  display: flex;
  gap: 0.5rem;
}

.action-cell button {
  font-size: var(--text-sm);
  padding: 4px 10px;
  border-radius: var(--radius-xs);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;
  margin: 0;
}

.action-cell button:hover {
  border-color: var(--color-border-strong);
}

.btn-reset-pw {
  color: var(--color-primary) !important;
  border-color: var(--color-primary) !important;
}

.btn-reset-pw:hover {
  background: var(--color-primary) !important;
  color: #fff !important;
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  min-width: 360px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.12);
}

.dialog h3 {
  margin: 0 0 1rem;
  font-size: 1.1rem;
}

.dialog-actions {
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-3);
}

.dialog-actions button {
  padding: 8px 20px;
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
  cursor: pointer;
}

.btn-cancel {
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.btn-cancel:hover {
  border-color: var(--color-border-strong);
}

.form-group {
  margin-bottom: 0.75rem;
}

.form-group label {
  display: block;
  font-size: var(--text-sm);
  margin-bottom: var(--space-1);
  color: var(--color-text-muted);
}

.form-group input {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: var(--text-base);
  box-sizing: border-box;
}



.error-message {
  color: var(--color-danger);
  font-size: var(--text-sm);
  margin-top: var(--space-2);
}

.success-message {
  color: var(--intent-success-text);
  font-size: var(--text-sm);
  margin-top: var(--space-2);
}
</style>
