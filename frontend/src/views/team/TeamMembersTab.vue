<template>
  <div class="team-members-tab">
    <div class="toolbar">
      <select data-testid="team-members-sel-role-filter" v-model="roleFilter" @change="fetchMembers">
        <option value="">全部角色</option>
        <option v-for="r in roles" :key="r.id" :value="r.id">{{ r.name }}</option>
      </select>
      <button data-testid="team-members-btn-invite" @click="showInviteDialog = true">邀请成员</button>
    </div>

    <table data-testid="team-members-tbl-members">
      <thead>
        <tr>
          <th>昵称</th>
          <th>邮箱</th>
          <th>角色</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in filteredMembers" :key="m.user_id">
          <td data-testid="team-members-txt-nickname">{{ m.nickname }}</td>
          <td data-testid="team-members-txt-email">{{ m.email }}</td>
          <td data-testid="team-members-txt-roles">{{ m.roles?.join(', ') || m.role_name || '' }}</td>
          <td>
            <button
              v-if="!m.is_owner"
              :data-testid="`team-members-btn-remove-${m.user_id}`"
              @click="confirmRemoveMember = m"
            >移除</button>
            <button
              v-if="m.is_owner"
              data-testid="team-members-btn-remove-owner"
              style="display:none"
            >移除</button>
            <button
              :data-testid="`team-members-btn-roles-${m.user_id}`"
              @click="openRoleDialog(m)"
            >分配角色</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div v-if="successMsg" class="success-message" data-testid="team-members-txt-success">{{ successMsg }}</div>

    <div v-if="showInviteDialog" class="dialog-overlay" @click.self="showInviteDialog = false">
      <div data-testid="team-members-dlg-invite" class="dialog">
        <h3>邀请成员</h3>
        <input
          v-model="inviteIdentifier"
          data-testid="team-members-dlg-invite-inp-identifier"
          placeholder="输入邮箱或用户名"
        />
        <div v-if="inviteError" class="error-message" data-testid="team-members-dlg-invite-txt-error">{{ inviteError }}</div>
        <button data-testid="team-members-dlg-invite-btn-submit" @click="inviteMember">发送邀请</button>
        <button @click="showInviteDialog = false">取消</button>
      </div>
    </div>

    <div v-if="confirmRemoveMember" class="dialog-overlay" @click.self="confirmRemoveMember = null">
      <div data-testid="team-members-dlg-confirm" class="dialog">
        <h3>确认移除</h3>
        <p>确定要移除该成员吗？</p>
        <button data-testid="team-members-dlg-confirm-btn-confirm" @click="removeMember(confirmRemoveMember.user_id)">确认</button>
        <button @click="confirmRemoveMember = null">取消</button>
      </div>
    </div>

    <div v-if="showRoleDialog" class="dialog-overlay" @click.self="showRoleDialog = false">
      <div data-testid="team-members-dlg-roles" class="dialog">
        <h3>分配角色</h3>
        <div v-for="r in roles" :key="r.id">
          <label>
            <input
              type="checkbox"
              :data-testid="`team-members-dlg-roles-chk-role-${r.id}`"
              :value="r.id"
              v-model="selectedRoleIds"
            />
            {{ r.name }}
          </label>
        </div>
        <button data-testid="team-members-dlg-roles-btn-save" @click="saveRoles">保存</button>
        <button @click="showRoleDialog = false">取消</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { apiClient } from '@/api/client'

const props = defineProps<{ teamId: string }>()

interface Member {
  user_id: number | string
  nickname: string
  email: string
  roles?: string[]
  role_name?: string
  is_owner?: boolean
}

interface Role {
  id: string
  name: string
}

const members = ref<Member[]>([])
const roles = ref<Role[]>([])
const roleFilter = ref('')
const showInviteDialog = ref(false)
const inviteIdentifier = ref('')
const inviteError = ref('')
const successMsg = ref('')
const confirmRemoveMember = ref<Member | null>(null)
const showRoleDialog = ref(false)
const selectedRoleIds = ref<string[]>([])
const currentRoleMemberId = ref<number | string | null>(null)

const filteredMembers = computed(() => {
  if (!roleFilter.value) return members.value
  return members.value
})

async function fetchMembers() {
  try {
    const params: Record<string, unknown> = {}
    if (roleFilter.value) params.role_id = roleFilter.value
    const res = await apiClient.get(`/api/v1/teams/${props.teamId}/members`, { params })
    const data = res.data?.data
    members.value = data?.items || data?.list || data || []
  } catch {
    members.value = []
  }
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

async function inviteMember() {
  inviteError.value = ''
  successMsg.value = ''
  try {
    await apiClient.post(`/api/v1/teams/${props.teamId}/members/invite`, {
      identifier: inviteIdentifier.value,
    })
    showInviteDialog.value = false
    inviteIdentifier.value = ''
    successMsg.value = '邀请已发送'
    await fetchMembers()
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '邀请失败'
    if (msg.includes('不存在')) {
      inviteError.value = '用户不存在'
    } else if (msg.includes('已在团队')) {
      inviteError.value = '用户已在团队中'
    } else {
      inviteError.value = msg
    }
  }
}

async function removeMember(userId: number | string) {
  try {
    await apiClient.delete(`/api/v1/teams/${props.teamId}/members/${userId}`)
    confirmRemoveMember.value = null
    await fetchMembers()
  } catch {
    // ignore
  }
}

function openRoleDialog(member: Member) {
  currentRoleMemberId.value = member.user_id
  selectedRoleIds.value = member.roles as string[] || []
  showRoleDialog.value = true
}

async function saveRoles() {
  try {
    await apiClient.put(`/api/v1/teams/${props.teamId}/members/${currentRoleMemberId.value}/roles`, {
      role_ids: selectedRoleIds.value,
    })
    showRoleDialog.value = false
    await fetchMembers()
  } catch {
    // ignore
  }
}

watch(() => props.teamId, () => {
  fetchMembers()
  fetchRoles()
})

onMounted(() => {
  fetchMembers()
  fetchRoles()
})
</script>
