<template>
  <div class="team-members-tab">
    <div class="toolbar">
      <select data-testid="team-members-sel-role-filter" v-model="roleFilter">
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
          <td data-testid="team-members-txt-nickname">{{ m.user?.nickname || m.nickname || '' }}</td>
          <td data-testid="team-members-txt-email">{{ m.user?.email || m.email || '' }}</td>
          <td data-testid="team-members-txt-roles">{{ getMemberRoles(m) }}</td>
          <td>
            <template v-if="isOwner(m)">
              <button
                data-testid="team-members-btn-remove-owner"
                style="display:none"
              >移除</button>
            </template>
            <template v-else>
              <button
                :data-testid="`team-members-btn-remove-user-${m.user_id}`"
                @click="confirmRemoveMember = m"
              >移除</button>
            </template>
            <button
              :data-testid="`team-members-btn-roles-user-${m.user_id}`"
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
              :data-testid="`team-members-dlg-roles-chk-role-${r.slug || r.id}`"
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
import { useNotificationStore } from '@/stores/notification'

const props = defineProps<{ teamId: string }>()
const notification = useNotificationStore()

interface MemberUser {
  id?: number
  nickname?: string
  email?: string
}

interface Member {
  user_id: number | string
  nickname?: string
  email?: string
  roles?: string[]
  role_ids?: (number | string)[]
  role_names?: string[]
  role_name?: string
  is_owner?: boolean
  user?: MemberUser | null
}

interface Role {
  id: string | number
  name: string
  slug?: string
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
const selectedRoleIds = ref<(string | number)[]>([])
const currentRoleMemberId = ref<number | string | null>(null)

const teamOwnerId = ref<number | null>(null)

const filteredMembers = computed(() => {
  if (!roleFilter.value) return members.value
  const filterVal = Number(roleFilter.value)
  return members.value.filter((m) => {
    const ids = m.role_ids || []
    return ids.some(rid => Number(rid) === filterVal)
  })
})

function isOwner(m: Member): boolean {
  return m.is_owner || m.user_id === teamOwnerId.value
}

function getMemberRoles(m: Member): string {
  if (m.role_names && m.role_names.length > 0) return m.role_names.join(', ')
  if (m.roles && m.roles.length > 0) return m.roles.join(', ')
  if (m.role_name) return m.role_name
  return ''
}

async function fetchTeamOwner() {
  try {
    const res = await apiClient.get(`/api/v1/teams/${props.teamId}`)
    const data = res.data?.data || res.data
    teamOwnerId.value = data?.owner_id || null
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '获取团队信息失败')
  }
}

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
    await apiClient.post(`/api/v1/teams/${props.teamId}/invitations`, {
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
    } else if (msg.includes('已在团队') || msg.includes('已是团队')) {
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
    members.value = members.value.filter(m => String(m.user_id) !== String(userId))
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '移除成员失败')
  }
}

function openRoleDialog(member: Member) {
  currentRoleMemberId.value = member.user_id
  selectedRoleIds.value = (member as unknown as Record<string, unknown>).role_ids as (string | number)[] || (member.roles as (string | number)[]) || []
  showRoleDialog.value = true
}

async function saveRoles() {
  try {
    await apiClient.put(`/api/v1/teams/${props.teamId}/members/${currentRoleMemberId.value}/roles`, {
      role_ids: selectedRoleIds.value.map(Number),
    })
    showRoleDialog.value = false
    await fetchMembers()
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '保存角色失败')
  }
}

watch(() => props.teamId, () => {
  fetchMembers()
  fetchRoles()
  fetchTeamOwner()
})

onMounted(() => {
  fetchMembers()
  fetchRoles()
  fetchTeamOwner()
})
</script>

<style scoped>
input[type="checkbox"] {
  appearance: none;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(0, 0, 0, 0.15);
  border-radius: 5px;
  background: rgba(0, 0, 0, 0.02);
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
  vertical-align: middle;
}

input[type="checkbox"]:checked {
  background: #111;
  border-color: #111;
}

input[type="checkbox"]:checked::after {
  content: '✓';
  color: #fff;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
}

.dialog label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #333;
  margin-bottom: 6px;
}
</style>
