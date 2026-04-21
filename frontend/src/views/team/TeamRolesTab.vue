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
              :data-testid="`team-roles-btn-edit-${r.id}`"
              @click="openEditDialog(r)"
            >编辑</button>
            <button
              v-if="!r.is_builtin"
              :data-testid="`team-roles-btn-delete-${r.id}`"
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
          <textarea v-model="formData.description" data-testid="team-roles-dlg-edit-txtarea-desc"></textarea>
        </div>
        <div class="form-group">
          <label>权限</label>
          <div v-for="p in allPermissions" :key="p">
            <label>
              <input
                type="checkbox"
                :data-testid="`team-roles-dlg-edit-chk-permission-${p}`"
                :value="p"
                v-model="formData.permissions"
              />
              {{ p }}
            </label>
          </div>
        </div>
        <div v-if="editError" class="error-message" data-testid="team-roles-dlg-edit-txt-error">{{ editError }}</div>
        <button data-testid="team-roles-dlg-edit-btn-save" @click="saveRole">保存</button>
        <button @click="showEditDialog = false">取消</button>
      </div>
    </div>

    <div v-if="confirmDeleteRole" class="dialog-overlay" @click.self="confirmDeleteRole = null">
      <div data-testid="team-roles-dlg-confirm" class="dialog">
        <h3>确认删除</h3>
        <p>确定要删除角色 "{{ confirmDeleteRole.name }}" 吗？</p>
        <button data-testid="team-roles-dlg-confirm-btn-confirm" @click="deleteRole(confirmDeleteRole.id)">确认</button>
        <button @click="confirmDeleteRole = null">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { apiClient } from '@/api/client'

const props = defineProps<{ teamId: string }>()

interface Role {
  id: string
  name: string
  description: string
  is_builtin: boolean
  permissions?: string[]
}

const roles = ref<Role[]>([])
const showEditDialog = ref(false)
const editingRole = ref<Role | null>(null)
const editError = ref('')
const confirmDeleteRole = ref<Role | null>(null)

const allPermissions = [
  'task:create', 'task:edit', 'task:delete',
  'requirement:create', 'requirement:edit', 'requirement:delete',
  'member:invite', 'member:remove',
  'role:create', 'role:edit', 'role:delete',
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
    roles.value = data?.items || data?.list || data || []
  } catch {
    roles.value = []
  }
}

async function saveRole() {
  editError.value = ''
  try {
    if (editingRole.value) {
      await apiClient.put(`/api/v1/teams/${props.teamId}/roles/${editingRole.value.id}`, formData)
    } else {
      await apiClient.post(`/api/v1/teams/${props.teamId}/roles`, formData)
    }
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
}

async function deleteRole(roleId: string) {
  try {
    await apiClient.delete(`/api/v1/teams/${props.teamId}/roles/${roleId}`)
    confirmDeleteRole.value = null
    await fetchRoles()
  } catch {
    // ignore
  }
}

watch(() => props.teamId, () => fetchRoles())
onMounted(() => fetchRoles())
</script>
