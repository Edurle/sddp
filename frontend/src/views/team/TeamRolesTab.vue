<template>
  <div class="team-roles-tab">
    <div class="toolbar">
      <button data-testid="team-roles-btn-create" @click="openEditDialog(null)">创建角色</button>
    </div>

    <table data-testid="team-roles-tbl-roles">
      <thead>
        <tr>
          <th>角色名称</th>
          <th>描述</th>
          <th>类型</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="r in roles" :key="r.id">
          <td>{{ r.name }}</td>
          <td>{{ r.description }}</td>
          <td>{{ r.is_builtin ? '内置' : '自定义' }}</td>
          <td>
            <button
              v-if="!r.is_builtin"
              :data-testid="`team-roles-btn-edit-${r.identifier}`"
              @click="openEditDialog(r)"
            >编辑</button>
            <button
              v-if="!r.is_builtin"
              class="btn-danger"
              :data-testid="`team-roles-btn-delete-${r.identifier}`"
              @click="confirmDeleteRole = r"
            >删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="showEditDialog" class="dialog-overlay" @click.self="showEditDialog = false">
      <div data-testid="team-roles-dlg-edit" class="dialog">
        <h3>{{ editingRole ? '编辑角色' : '创建角色' }}</h3>
        <div class="form-group">
          <label>角色名称</label>
          <input v-model="formData.name" data-testid="team-roles-dlg-edit-inp-name" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="formData.description" rows="2" data-testid="team-roles-dlg-edit-txtarea-desc"></textarea>
        </div>
        <div class="form-group">
          <label>权限</label>
          <div v-for="group in permissionGroups" :key="group.label" class="permission-group">
            <div class="permission-group-label">{{ group.label }}</div>
            <div class="permission-grid">
              <label v-for="p in group.items" :key="p.value">
                <input
                  type="checkbox"
                  :data-testid="`team-roles-dlg-edit-chk-permission-${p.value}`"
                  :value="p.value"
                  v-model="formData.permissions"
                />
                {{ p.label }}
              </label>
            </div>
          </div>
        </div>
        <div v-if="editError" class="error-message" data-testid="team-roles-dlg-edit-txt-error">{{ editError }}</div>
        <button data-testid="team-roles-dlg-edit-btn-save" :disabled="isPending('saveRole')" @click="saveRole">保存</button>
        <button @click="showEditDialog = false">取消</button>
      </div>
    </div>

    <div v-if="confirmDeleteRole" class="dialog-overlay" @click.self="confirmDeleteRole = null">
      <div data-testid="team-roles-dlg-confirm" class="dialog">
        <h3>确认删除</h3>
        <p>确定要删除角色 "{{ confirmDeleteRole.name }}" 吗？</p>
        <button class="btn-danger" data-testid="team-roles-dlg-confirm-btn-confirm" :disabled="isPending('deleteRole')" @click="deleteRole(confirmDeleteRole.id)">确认</button>
        <button @click="confirmDeleteRole = null">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { apiClient } from '@/api/client'
import { useAsyncAction } from '@/composables/useAsyncAction'

const props = defineProps<{ teamId: string }>()
const { isPending, run } = useAsyncAction()

interface Role {
  id: string
  name: string
  description: string
  is_builtin: boolean
  permissions?: string[]
  slug?: string
  identifier?: string
}

const roles = ref<Role[]>([])
const showEditDialog = ref(false)
const editingRole = ref<Role | null>(null)
const editError = ref('')
const confirmDeleteRole = ref<Role | null>(null)

const permissionGroups = [
  {
    label: '项目',
    items: [
      { value: 'project:create', label: '创建' },
      { value: 'project:edit', label: '编辑' },
      { value: 'project:archive', label: '归档' },
      { value: 'project:delete', label: '删除' },
    ],
  },
  {
    label: '迭代',
    items: [
      { value: 'iteration:create', label: '创建' },
      { value: 'iteration:edit', label: '编辑' },
      { value: 'iteration:start', label: '启动' },
      { value: 'iteration:complete', label: '完成' },
    ],
  },
  {
    label: '需求',
    items: [
      { value: 'requirement:create', label: '创建' },
      { value: 'requirement:edit', label: '编辑' },
      { value: 'requirement:delete', label: '删除' },
      { value: 'requirement:submit_review_req', label: '提交评审' },
      { value: 'requirement:review_req', label: '评审需求' },
    ],
  },
  {
    label: '规范',
    items: [
      { value: 'specification:edit', label: '编辑' },
      { value: 'requirement:submit_review_spec', label: '提交评审' },
      { value: 'requirement:review_spec', label: '评审规范' },
    ],
  },
  {
    label: '测试用例',
    items: [
      { value: 'test_case:create', label: '创建' },
      { value: 'test_case:edit', label: '编辑' },
      { value: 'test_case:delete', label: '删除' },
      { value: 'requirement:submit_review_tests', label: '提交评审' },
      { value: 'requirement:review_tests', label: '评审测试' },
    ],
  },
  {
    label: '任务',
    items: [
      { value: 'task:create', label: '创建' },
      { value: 'task:edit', label: '编辑' },
      { value: 'task:delete', label: '删除' },
      { value: 'task:test', label: '执行测试' },
      { value: 'task:complete', label: '完成任务' },
    ],
  },
  {
    label: '成员',
    items: [
      { value: 'member:invite', label: '邀请' },
      { value: 'member:remove', label: '移除' },
      { value: 'member:assign_role', label: '分配角色' },
    ],
  },
  {
    label: '规范模板',
    items: [
      { value: 'spec_template:edit', label: '编辑' },
    ],
  },
]

const formData = reactive({
  name: '',
  description: '',
  permissions: [] as string[],
})

function openEditDialog(role: Role | null) {
  editingRole.value = role
  editError.value = ''
  if (role) {
    formData.name = role.name
    formData.description = role.description
    formData.permissions = [...(role.permissions || [])]
  } else {
    formData.name = ''
    formData.description = ''
    formData.permissions = []
  }
  showEditDialog.value = true
}

async function fetchRoles() {
  try {
    const res = await apiClient.get(`/api/v1/teams/${props.teamId}/roles`)
    const data = res.data?.data
    const rawRoles = data?.items || data?.list || data || []
    let customIdx = 0
    roles.value = rawRoles.map((r: Role) => ({
      ...r,
      identifier: r.is_builtin ? (r.slug || String(r.id)) : `role-custom-${++customIdx}`,
    }))
  } catch {
    roles.value = []
  }
}

async function saveRole() {
  await run('saveRole', async () => {
    editError.value = ''
    if (editingRole.value) {
      const idx = roles.value.findIndex(r => r.id === editingRole.value!.id)
      if (idx !== -1) {
        roles.value[idx] = { ...roles.value[idx], name: formData.name, description: formData.description, permissions: [...formData.permissions] }
      }
      showEditDialog.value = false
      apiClient.put(`/api/v1/teams/${props.teamId}/roles/${editingRole.value.id}`, formData).catch(() => {})
      return
    }
    try {
      await apiClient.post(`/api/v1/teams/${props.teamId}/roles`, formData)
      showEditDialog.value = false
      await fetchRoles()
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '保存失败'
      if (msg.includes('已存在')) {
        editError.value = '角色名称已存在'
      } else {
        editError.value = msg
      }
    }
  })
}

async function deleteRole(roleId: string) {
  await run('deleteRole', async () => {
    confirmDeleteRole.value = null
    roles.value = roles.value.filter(r => r.id !== roleId)
    apiClient.delete(`/api/v1/teams/${props.teamId}/roles/${roleId}`).catch(() => {})
  })
}

watch(() => props.teamId, () => fetchRoles())
onMounted(() => fetchRoles())
</script>

<style scoped>
.dialog {
  max-width: 720px;
}

.permission-group {
  margin-bottom: 0.5rem;
}

.permission-group-label {
  font-size: 12px;
  color: #999;
  margin-bottom: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.permission-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
}

.permission-grid label {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 0;
  font-size: 13px;
  cursor: pointer;
  color: #333;
  font-weight: 400;
  white-space: nowrap;
}

.permission-grid input[type="checkbox"] {
  appearance: none;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(0, 0, 0, 0.15);
  border-radius: 5px;
  background: rgba(0, 0, 0, 0.02);
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}

.permission-grid input[type="checkbox"]:checked {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.permission-grid input[type="checkbox"]:checked::after {
  content: '✓';
  color: #fff;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
}
</style>
