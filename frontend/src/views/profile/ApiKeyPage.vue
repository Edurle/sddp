<template>
  <div class="api-key-page">
    <h1>API Key 管理</h1>
    <p class="page-desc">创建 API Key 用于 CLI 工具或其他程序化访问。创建后请立即保存，密钥仅显示一次。</p>

    <div class="toolbar">
      <button @click="showCreateDialog = true">创建 API Key</button>
    </div>

    <div v-if="keys.length === 0" class="empty-state">
      <p>还没有 API Key</p>
    </div>

    <table v-else>
      <thead>
        <tr>
          <th>名称</th>
          <th>前缀</th>
          <th>状态</th>
          <th>过期时间</th>
          <th>创建时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="k in keys" :key="k.id">
          <td>{{ k.name }}</td>
          <td><code>{{ k.key_prefix }}...</code></td>
          <td>
            <span :class="k.is_active ? 'status-active' : 'status-revoked'">
              {{ k.is_active ? '活跃' : '已撤销' }}
            </span>
          </td>
          <td>{{ k.expires_at || '永不过期' }}</td>
          <td>{{ formatDate(k.created_at) }}</td>
          <td>
            <button
              v-if="k.is_active"
              class="btn-danger"
              :disabled="isPending(`revokeKey-${k.id}`)"
              @click="revokeKey(k.id)"
            >撤销</button>
          </td>
        </tr>
      </tbody>
    </table>

    <AppDialog :open="showCreateDialog" @close="showCreateDialog = false">
        <h3>创建 API Key</h3>
        <div class="form-group">
          <label>名称</label>
          <input v-model="newKey.name" placeholder="例如: my-cli-key" />
        </div>
        <div class="form-group">
          <label>过期时间（可选）</label>
          <input v-model="newKey.expires_at" type="datetime-local" />
        </div>
        <div v-if="createError" class="error-message">{{ createError }}</div>
        <button :disabled="isPending('createKey')" @click="createKey">创建</button>
        <button @click="showCreateDialog = false">取消</button>
    </AppDialog>

    <AppDialog :open="showRawKey" dialog-class="dialog-md" @close="closeRawKeyDialog">
        <h3>API Key 已创建</h3>
        <p class="raw-key-warning">请立即保存以下密钥，关闭后无法再次查看。</p>
        <div class="raw-key-box">
          <code>{{ rawKeyValue }}</code>
          <button class="btn-copy" @click="copyKey">复制</button>
        </div>
        <div v-if="copied" class="success-message">已复制到剪贴板</div>
        <button @click="closeRawKeyDialog">关闭</button>
    </AppDialog>

    <div v-if="errorMsg" class="error-message">{{ errorMsg }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { apiClient } from '@/api/client'
import { useAsyncAction } from '@/composables/useAsyncAction'
import AppDialog from '@/components/common/AppDialog.vue'

interface ApiKeyItem {
  id: number
  name: string
  key_prefix: string
  is_active: boolean
  expires_at: string | null
  created_at: string | null
}

const { isPending, run } = useAsyncAction()

const keys = ref<ApiKeyItem[]>([])
const showCreateDialog = ref(false)
const showRawKey = ref(false)
const rawKeyValue = ref('')
const copied = ref(false)
const errorMsg = ref('')
const createError = ref('')

const newKey = reactive({ name: '', expires_at: '' })

async function fetchKeys() {
  try {
    const res = await apiClient.get('/api/v1/users/me/api-keys')
    keys.value = res.data?.data || []
  } catch {
    keys.value = []
  }
}

async function createKey() {
  await run('createKey', async () => {
    createError.value = ''
    if (!newKey.name.trim()) {
      createError.value = '名称不能为空'
      return
    }
    try {
      const body: Record<string, string> = { name: newKey.name }
      if (newKey.expires_at) {
        body.expires_at = new Date(newKey.expires_at).toISOString()
      }
      const res = await apiClient.post('/api/v1/users/me/api-keys', body)
      const data = res.data?.data
      if (data?.raw_key) {
        rawKeyValue.value = data.raw_key
        showCreateDialog.value = false
        showRawKey.value = true
        copied.value = false
      }
      newKey.name = ''
      newKey.expires_at = ''
      await fetchKeys()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '创建失败'
      createError.value = msg
    }
  })
}

async function revokeKey(id: number) {
  await run(`revokeKey-${id}`, async () => {
    errorMsg.value = ''
    try {
      await apiClient.delete(`/api/v1/users/me/api-keys/${id}`)
      await fetchKeys()
    } catch (e: unknown) {
      errorMsg.value = e instanceof Error ? e.message : '撤销失败'
    }
  })
}

function copyKey() {
  navigator.clipboard.writeText(rawKeyValue.value).then(() => {
    copied.value = true
  })
}

function closeRawKeyDialog() {
  showRawKey.value = false
  rawKeyValue.value = ''
  copied.value = false
}

function formatDate(d: string | null): string {
  if (!d) return ''
  return new Date(d).toLocaleString('zh-CN')
}

onMounted(fetchKeys)
</script>

<style scoped>
.api-key-page {
  max-width: 800px;
}
.page-desc {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  margin-bottom: 1rem;
}
code {
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 6px;
  border-radius: var(--radius-xs);
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  font-size: var(--text-xs);
}
.status-active {
  color: var(--intent-success-text);
  font-weight: 500;
}
.status-revoked {
  color: var(--color-text-subtle);
}
.btn-danger {
  background: var(--color-danger);
  color: #fff;
  border-color: var(--color-danger);
  padding: 4px 12px;
  font-size: var(--text-xs);
}
.btn-danger:hover {
  background: var(--color-danger-hover);
  border-color: var(--color-danger-hover);
}
.raw-key-warning {
  color: var(--color-danger);
  font-size: var(--text-sm);
  margin-bottom: 1rem;
}
.raw-key-box {
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: var(--space-3);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: 1rem;
  word-break: break-all;
}
.raw-key-box code {
  flex: 1;
  background: none;
  padding: 0;
  font-size: var(--text-sm);
}
.btn-copy {
  background: var(--color-surface);
  color: var(--color-text);
  border-color: var(--color-border-strong);
  padding: 4px 12px;
  font-size: var(--text-xs);
  white-space: nowrap;
  flex-shrink: 0;
}
.btn-copy:hover {
  background: var(--color-surface-muted);
  box-shadow: none;
}
</style>
