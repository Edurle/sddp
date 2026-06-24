<template>
  <div class="dashboard-page">
    <div v-if="isLoading" class="loading-state">加载中...</div>
    <template v-else>
    <div class="user-info">
      <span data-testid="dashboard-txt-nickname">{{ user?.nickname || '' }}</span>
      <span data-testid="dashboard-txt-email">{{ user?.email || '' }}</span>
    </div>

    <div class="tabs">
      <button data-testid="dashboard-tab-projects" :class="{ active: activeTab === 'projects' }" @click="activeTab = 'projects'">项目总览</button>
      <button data-testid="dashboard-tab-progress" :class="{ active: activeTab === 'progress' }" @click="activeTab = 'progress'">进度</button>
      <button data-testid="dashboard-tab-teams" :class="{ active: activeTab === 'teams' }" @click="activeTab = 'teams'">我的团队</button>
      <button data-testid="dashboard-tab-pending" :class="{ active: activeTab === 'pending' }" @click="activeTab = 'pending'">待办事项</button>
      <button data-testid="dashboard-tab-profile" :class="{ active: activeTab === 'profile' }" @click="activeTab = 'profile'">个人资料</button>
    </div>

    <div v-if="activeTab === 'projects'">
      <div v-if="projectsTree.length === 0" class="empty-state">暂无项目，前往 <router-link to="/teams">团队页面</router-link> 查看或创建项目</div>
      <div v-for="proj in projectsTree" :key="proj.id" class="tree-project">
        <div class="tree-node project-node" @click="toggleExpand('p', proj.id)">
          <span class="expand-icon">{{ isExpanded('p', proj.id) ? '▼' : '▶' }}</span>
          <span class="node-icon">📁</span>
          <span class="node-title">{{ proj.name }}</span>
          <span class="node-status" :class="'status-' + proj.status">{{ proj.status }}</span>
        </div>
        <div v-if="isExpanded('p', proj.id)" class="tree-children">
          <div v-if="proj.iterations.length === 0" class="tree-empty">暂无迭代</div>
          <div v-for="iter in proj.iterations" :key="iter.id" class="tree-iteration">
            <div class="tree-node iteration-node" @click="toggleExpand('i', iter.id)">
              <span class="expand-icon">{{ isExpanded('i', iter.id) ? '▼' : '▶' }}</span>
              <span class="node-icon">🔄</span>
              <span class="node-title">{{ iter.name }}</span>
              <span class="node-status" :class="'status-' + iter.status">{{ iterStatusLabel(iter.status) }}</span>
              <span class="node-date">{{ iter.start_date }} ~ {{ iter.end_date }}</span>
              <span class="node-count">{{ iter.requirements.length }} 个需求</span>
            </div>
            <div v-if="isExpanded('i', iter.id)" class="tree-children">
              <div v-if="iter.requirements.length === 0" class="tree-empty">暂无需求</div>
              <div v-for="req in iter.requirements" :key="req.id" class="tree-requirement">
                <router-link :to="`/requirements/${req.id}`" class="req-link">
                  <span class="node-icon">{{ reqTypeIcon(req.req_type) }}</span>
                  <span class="node-title">{{ req.title }}</span>
                  <span class="req-status-tag" :class="'req-status-' + req.status">{{ reqStatusLabel(req.status) }}</span>
                  <span class="priority-dot" :class="'priority-' + req.priority"></span>
                </router-link>
                <div v-if="req.tasks.length > 0" class="task-list">
                  <div v-for="task in req.tasks" :key="task.id" class="task-item">
                    <router-link :to="`/tasks/${task.id}`" class="task-link">
                      <span class="task-status-dot" :class="'task-' + task.status"></span>
                      {{ task.title }}
                    </router-link>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'progress'">
      <div class="stat-cards">
        <div class="stat-card stat-draft">
          <div class="stat-number">{{ progressStats.drafting }}</div>
          <div class="stat-label">草稿中</div>
        </div>
        <div class="stat-card stat-review">
          <div class="stat-number">{{ progressStats.reviewing }}</div>
          <div class="stat-label">审核中</div>
        </div>
        <div class="stat-card stat-work">
          <div class="stat-number">{{ progressStats.working }}</div>
          <div class="stat-label">起草中</div>
        </div>
        <div class="stat-card stat-approved">
          <div class="stat-number">{{ progressStats.approved }}</div>
          <div class="stat-label">已通过</div>
        </div>
      </div>

      <div v-if="flatRequirements.length === 0" class="empty-state">暂无需求</div>
      <div v-for="group in iterationGroups" :key="group.iterationName" class="progress-iteration-group">
        <div class="progress-iteration-label">{{ group.iterationName }}</div>
        <div class="progress-req-list">
          <div v-for="req in group.items" :key="req.id" class="progress-req-card">
            <div class="progress-req-header" @click="toggleExpand('pr', req.id)">
              <span class="expand-icon">{{ isExpanded('pr', req.id) ? '▼' : '▶' }}</span>
              <router-link :to="`/requirements/${req.id}`" class="progress-req-title" @click.stop>{{ req.title }}</router-link>
              <span class="progress-req-status" :class="'prs-' + req.status">{{ reqStatusLabel(req.status) }}</span>
              <span class="priority-indicator" :class="'pi-' + req.priority"></span>
            </div>
            <div v-if="isExpanded('pr', req.id)" class="progress-req-detail">
              <div class="progress-stages">
                <template v-for="(s, i) in lifecycleStages" :key="i">
                  <span class="stage-item" :class="stageClass(req.status, s.status)">{{ s.label }}</span>
                  <span v-if="i < lifecycleStages.length - 1" class="stage-arrow">→</span>
                </template>
              </div>
              <div v-if="req.tasks && req.tasks.length > 0" class="progress-task-summary">
                {{ req.tasks.length }}个任务 · {{ completedTasks(req) }}已完成
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'teams'">
      <div data-testid="dashboard-list-my-teams">
        <h3>我的团队</h3>
        <div v-if="myTeams.length === 0" class="empty-state">
          暂无团队
          <router-link to="/teams">创建团队</router-link>
        </div>
        <div v-for="team in myTeams" :key="team.id">
          <router-link :to="`/teams/${team.id}`" :data-testid="`dashboard-link-team-${team.id}`">{{ team.name }}</router-link>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'pending'">
      <div class="sub-tabs">
        <button data-testid="dashboard-tab-pending-reviews" :class="{ active: pendingSubTab === 'reviews' }" @click="pendingSubTab = 'reviews'">待审核</button>
        <button data-testid="dashboard-tab-pending-tasks" :class="{ active: pendingSubTab === 'tasks' }" @click="pendingSubTab = 'tasks'">待执行任务</button>
        <button data-testid="dashboard-tab-pending-invitations" :class="{ active: pendingSubTab === 'invitations' }" @click="pendingSubTab = 'invitations'">待处理邀请</button>
      </div>

      <div v-show="pendingSubTab === 'reviews'" data-testid="dashboard-list-pending-reviews">
        <h3>待审核列表</h3>
        <div v-if="pendingReviews.length === 0" class="empty-state">暂无待审核项</div>
        <div v-for="item in pendingReviews" :key="item.id">
          <router-link :to="`/requirements/${(item as any).requirement_id || item.id}`" class="pending-item">
            {{ (item as any).requirement_title || item.title }}
            <span class="pending-badge">{{ (item as any).review_type || '审核' }}</span>
          </router-link>
        </div>
      </div>

      <div v-show="pendingSubTab === 'tasks'" data-testid="dashboard-list-pending-tasks">
        <h3>待办任务列表</h3>
        <div v-if="pendingTasks.length === 0" class="empty-state">暂无待办任务</div>
        <div v-for="item in pendingTasks" :key="item.id">
          <router-link :to="`/tasks/${item.id}`" class="pending-item">
            {{ item.title }}
            <span class="pending-badge">{{ (item as any).status || '待办' }}</span>
          </router-link>
        </div>
      </div>

      <div v-show="pendingSubTab === 'invitations'" data-testid="dashboard-list-pending-invitations">
        <h3>待处理邀请列表</h3>
        <div v-if="pendingInvitations.length === 0" class="empty-state">暂无待处理邀请</div>
        <div v-for="item in pendingInvitations" :key="item.id">
          {{ item.team_name || item.name }}
          <button :data-testid="`dashboard-btn-accept-invitation-${item.id}`" @click="acceptInvitation(item.id)">接受</button>
          <button class="btn-danger" :data-testid="`dashboard-btn-reject-invitation-${item.id}`" @click="rejectInvitation(item.id)">拒绝</button>
        </div>
      </div>
    </div>

    <div v-if="activeTab === 'profile'">
      <div class="form-group">
        <label>昵称</label>
        <input v-model="profileNickname" data-testid="dashboard-inp-nickname" />
      </div>
      <div v-if="profileSuccess" class="success-message">{{ profileSuccess }}</div>
      <button data-testid="dashboard-btn-save-profile" @click="saveProfile">保存</button>
      <button data-testid="dashboard-btn-change-password" @click="showPasswordDialog = true">修改密码</button>

      <div v-if="showPasswordDialog" class="dialog-overlay" @click.self="showPasswordDialog = false">
        <div data-testid="dashboard-dlg-password" class="dialog">
          <h3>修改密码</h3>
          <div class="form-group">
            <label>旧密码</label>
            <input v-model="passwordForm.old" type="password" data-testid="dashboard-dlg-password-inp-old" />
          </div>
          <div class="form-group">
            <label>新密码</label>
            <input v-model="passwordForm.newPassword" type="password" data-testid="dashboard-dlg-password-inp-new" />
          </div>
          <div class="form-group">
            <label>确认新密码</label>
            <input v-model="passwordForm.confirm" type="password" data-testid="dashboard-dlg-password-inp-confirm" />
          </div>
          <div v-if="passwordError" class="error-message">{{ passwordError }}</div>
          <div v-if="passwordSuccess" class="success-message">{{ passwordSuccess }}</div>
          <button data-testid="dashboard-dlg-password-btn-submit" @click="changePassword">提交</button>
          <button @click="showPasswordDialog = false">取消</button>
        </div>
      </div>
    </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useNotificationStore } from '@/stores/notification'
import { apiClient } from '@/api/client'
import { reqStatusLabel, iterStatusLabel } from '@/utils/status'

const authStore = useAuthStore()
const notification = useNotificationStore()
const user = computed(() => authStore.user)
const myTeams = computed(() => (user.value as any)?.teams || [])

const activeTab = ref('projects')
const pendingSubTab = ref('reviews')
const profileNickname = ref('')
const isLoading = ref(true)
const profileSuccess = ref('')
const showPasswordDialog = ref(false)
const passwordError = ref('')
const passwordSuccess = ref('')
const passwordForm = reactive({ old: '', newPassword: '', confirm: '' })

const pendingReviews = ref<Array<{ id: number; title: string }>>([])
const pendingTasks = ref<Array<{ id: number; title: string }>>([])
const pendingInvitations = ref<Array<{ id: number; team_name?: string; name?: string }>>([])

const expandedNodes = ref<Set<string>>(new Set())

interface TaskItem { id: number; title: string; status: string; assignee_id: number | null }
interface ReqItem { id: number; title: string; status: string; req_type: string; priority: number; tasks: TaskItem[] }
interface IterItem { id: number; name: string; status: string; start_date: string | null; end_date: string | null; requirements: ReqItem[] }
interface ProjItem { id: number; name: string; description: string; status: string; team_id: number; iterations: IterItem[] }

const projectsTree = ref<ProjItem[]>([])

function toggleExpand(prefix: string, id: number) {
  const key = `${prefix}-${id}`
  const s = new Set(expandedNodes.value)
  if (s.has(key)) s.delete(key)
  else s.add(key)
  expandedNodes.value = s
}

function isExpanded(prefix: string, id: number): boolean {
  return expandedNodes.value.has(`${prefix}-${id}`)
}

function reqTypeIcon(t: string) { return t === 'bug' ? '🐛' : t === 'optimization' ? '⚡' : '📋' }

const lifecycleStages = [
  { status: 'drafting_req', label: '草稿' },
  { status: 'reviewing_req', label: '需求审核' },
  { status: 'drafting_spec', label: '编写规范' },
  { status: 'reviewing_spec', label: '规范审核' },
  { status: 'drafting_tests', label: '编写测试' },
  { status: 'reviewing_tests', label: '测试审核' },
  { status: 'approved', label: '已通过' },
]

const flatRequirements = computed(() => {
  const items: any[] = []
  for (const proj of projectsTree.value) {
    for (const iter of proj.iterations) {
      for (const req of iter.requirements) {
        items.push({ ...req, _iterationName: iter.name })
      }
    }
  }
  return items
})

const iterationGroups = computed(() => {
  const map = new Map<string, any[]>()
  for (const req of flatRequirements.value) {
    const key = req._iterationName
    if (!map.has(key)) map.set(key, [])
    map.get(key)!.push(req)
  }
  return Array.from(map.entries()).map(([iterationName, items]) => ({ iterationName, items }))
})

const progressStats = computed(() => {
  const all = flatRequirements.value
  return {
    drafting: all.filter(r => ['drafting_req', 'drafting_spec', 'drafting_tests'].includes(r.status)).length,
    reviewing: all.filter(r => ['reviewing_req', 'reviewing_spec', 'reviewing_tests'].includes(r.status)).length,
    working: all.filter(r => ['drafting_spec', 'drafting_tests'].includes(r.status)).length,
    approved: all.filter(r => r.status === 'approved').length,
  }
})

function stageClass(currentStatus: string, stageStatus: string): string {
  const order = lifecycleStages.map(s => s.status)
  const currentIdx = order.indexOf(currentStatus)
  const stageIdx = order.indexOf(stageStatus)
  if (stageIdx < currentIdx) return 'stage-done'
  if (stageIdx === currentIdx) return 'stage-current'
  return 'stage-pending'
}

function completedTasks(req: any): number {
  if (!req.tasks) return 0
  return req.tasks.filter((t: any) => t.status === 'completed').length
}

watch(() => user.value, (u) => {
  if (u) profileNickname.value = (u as any).nickname || ''
}, { immediate: true })

async function fetchProjectsTree() {
  try {
    const res = await apiClient.get('/api/v1/users/me/projects-tree')
    projectsTree.value = res.data?.data || []
    if (projectsTree.value.length > 0 && expandedNodes.value.size === 0) {
      const s = new Set<string>()
      s.add(`p-${projectsTree.value[0].id}`)
      if (projectsTree.value[0].iterations.length > 0) {
        s.add(`i-${projectsTree.value[0].iterations[0].id}`)
      }
      expandedNodes.value = s
    }
  } catch {
    projectsTree.value = []
    notification.showError('获取项目数据失败')
  }
}

async function fetchData() {
  try {
    const res = await apiClient.get('/api/v1/users/me/pending')
    const data = res.data?.data
    if (data) {
      pendingReviews.value = data.pending_reviews || []
      pendingTasks.value = data.pending_tasks || []
      pendingInvitations.value = data.pending_invitations || []
    }
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '操作失败')
  }
}

async function acceptInvitation(id: number) {
  try {
    await apiClient.put(`/api/v1/invitations/${id}`, { action: 'accept' })
    pendingInvitations.value = pendingInvitations.value.filter(i => i.id !== id)
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '操作失败')
  }
}

async function rejectInvitation(id: number) {
  try {
    await apiClient.put(`/api/v1/invitations/${id}`, { action: 'reject' })
    pendingInvitations.value = pendingInvitations.value.filter(i => i.id !== id)
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '操作失败')
  }
}

async function saveProfile() {
  profileSuccess.value = ''
  try {
    await apiClient.put('/api/v1/users/me', { nickname: profileNickname.value })
    await authStore.fetchUser()
    profileSuccess.value = '保存成功'
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '操作失败')
  }
}

async function changePassword() {
  passwordError.value = ''
  passwordSuccess.value = ''
  if (passwordForm.newPassword !== passwordForm.confirm) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }
  try {
    await apiClient.put('/api/v1/users/me/password', {
      old_password: passwordForm.old,
      new_password: passwordForm.newPassword,
    })
    passwordSuccess.value = '密码修改成功'
    passwordForm.old = ''
    passwordForm.newPassword = ''
    passwordForm.confirm = ''
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : '修改失败'
    if (msg.includes('旧密码') || msg.includes('原密码') || msg.includes('old password') || msg.includes('incorrect')) {
      passwordError.value = '旧密码错误'
    } else {
      passwordError.value = msg
    }
  }
}

onMounted(async () => {
  isLoading.value = true
  try {
    if (authStore.isAuthenticated) {
      await authStore.fetchUser()
    }
    await Promise.all([fetchData(), fetchProjectsTree()])
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.dashboard-page {
  padding: 1.5rem;
  max-width: 960px;
  margin: 0 auto;
}
.user-info {
  margin-bottom: 1rem;
  display: flex;
  gap: 1rem;
  font-size: 13px;
  color: #666;
}
.tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid rgba(0, 0, 0, 0.06);
  margin-bottom: 1.5rem;
}
.tabs button {
  padding: 8px 20px;
  font-size: 14px;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  background: transparent;
  color: #999;
  cursor: pointer;
  font-weight: 500;
  font-family: inherit;
}
.tabs button:hover { color: #2563eb; }
.tabs button.active {
  color: #fff;
  background: #2563eb;
  border-bottom-color: #2563eb;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.25);
}
.sub-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.sub-tabs button {
  padding: 6px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #fff;
  color: #666;
  font-size: 13px;
  cursor: pointer;
}
.sub-tabs button.active {
  background: var(--color-primary);
  color: #fff;
  border-color: var(--color-primary);
}
.empty-state {
  padding: 2rem;
  text-align: center;
  color: #999;
  font-size: 14px;
}
.tree-empty {
  padding: 0.75rem 1rem;
  color: #bbb;
  font-size: 12px;
  font-style: italic;
}
.tree-project { margin-bottom: 4px; }
.tree-children { margin-left: 20px; }
.tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s;
  font-size: 14px;
}
.tree-node:hover { background: rgba(0, 0, 0, 0.03); }
.expand-icon {
  font-size: 10px;
  color: #bbb;
  width: 14px;
  text-align: center;
  flex-shrink: 0;
}
.node-icon { flex-shrink: 0; }
.node-title { font-weight: 600; color: #111; }
.node-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
  margin-left: 4px;
  white-space: nowrap;
}
.status-active, .status-in_progress { background: #dcfce7; color: #166534; }
.status-planning { background: #fef3c7; color: #92400e; }
.status-completed { background: #e0e7ff; color: #3730a3; }
.node-date {
  font-size: 12px;
  color: #aaa;
  margin-left: 4px;
}
.node-count {
  font-size: 11px;
  color: #888;
  background: #f3f4f6;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: 4px;
}
.tree-requirement {
  margin-left: 20px;
  padding: 4px 0;
}
.req-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 6px;
  text-decoration: none;
  color: #333;
  font-size: 13px;
  transition: background 0.15s;
}
.req-link:hover { background: rgba(79, 70, 229, 0.04); }
.req-status-tag {
  font-size: 10px;
  padding: 2px 7px;
  border-radius: 8px;
  font-weight: 500;
  white-space: nowrap;
}
.req-status-drafting_req { background: #f3f4f6; color: #666; }
.req-status-reviewing_req, .req-status-reviewing_spec, .req-status-reviewing_tests { background: #f3e8ff; color: #6b21a8; }
.req-status-drafting_spec { background: #eff6ff; color: #1e40af; }
.req-status-drafting_tests { background: #fef3c7; color: #92400e; }
.req-status-approved { background: #dcfce7; color: #166534; }
.req-status-deprecated { background: #fee2e2; color: #991b1b; text-decoration: line-through; }
.priority-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-left: auto;
  flex-shrink: 0;
}
.priority-3 { background: #ef4444; }
.priority-2 { background: #f59e0b; }
.priority-1 { background: #22c55e; }
.task-list {
  margin-left: 34px;
  padding: 2px 0 4px;
}
.task-item { padding: 2px 0; }
.task-link {
  display: flex;
  align-items: center;
  gap: 6px;
  text-decoration: none;
  color: #666;
  font-size: 12px;
  padding: 3px 8px;
  border-radius: 4px;
  transition: background 0.15s;
}
.task-link:hover { background: rgba(0, 0, 0, 0.02); color: #333; }
.task-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.task-pending { background: #9ca3af; }
.task-coding { background: #3b82f6; }
.task-testing { background: #f59e0b; }
.task-completed { background: #22c55e; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; font-size: 13px; color: #555; margin-bottom: 4px; }
.form-group input { width: 100%; padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 14px; }
.success-message { color: #22c55e; font-size: 13px; margin-bottom: 0.5rem; }
.error-message { color: #ef4444; font-size: 13px; margin-bottom: 0.5rem; }
.dialog-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.dialog {
  background: #fff; padding: 24px; border-radius: 12px; width: 360px; max-width: 90vw;
}
.dialog h3 { margin-bottom: 16px; }
.stat-cards {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  flex: 1;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}
.stat-number {
  font-size: 28px;
  font-weight: 700;
}
.stat-label {
  font-size: 13px;
  margin-top: 4px;
}
.stat-draft { background: #f3f4f6; color: #4b5563; }
.stat-review { background: #fef3c7; color: #92400e; }
.stat-work { background: #eff6ff; color: #1e40af; }
.stat-approved { background: #f0fdf4; color: #166534; }
.progress-iteration-group {
  margin-bottom: 24px;
}
.progress-iteration-label {
  font-size: 14px;
  font-weight: 600;
  color: #666;
  margin-bottom: 12px;
  padding-left: 4px;
}
.progress-req-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.progress-req-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
}
.progress-req-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
}
.progress-req-title {
  font-weight: 600;
  color: #111;
  text-decoration: none;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
}
.progress-req-title:hover { color: #4f46e5; }
.progress-req-status {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 500;
  flex-shrink: 0;
}
.prs-drafting_req, .prs-drafting_spec, .prs-drafting_tests { background: #f3f4f6; color: #666; }
.prs-reviewing_req, .prs-reviewing_spec, .prs-reviewing_tests { background: #fef3c7; color: #92400e; }
.prs-approved { background: #dcfce7; color: #166534; }
.priority-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-left: auto;
  flex-shrink: 0;
}
.pi-3 { background: #ef4444; }
.pi-2 { background: #f59e0b; }
.pi-1 { background: #22c55e; }
.progress-req-detail {
  padding: 0 16px 16px 40px;
  border-top: 1px solid #f3f4f6;
}
.progress-stages {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: nowrap;
  overflow-x: auto;
  padding-top: 12px;
  margin-bottom: 8px;
}
.stage-item {
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 6px;
  white-space: nowrap;
  flex-shrink: 0;
}
.stage-done { background: #dcfce7; color: #166534; }
.stage-current { background: #3b82f6; color: white; font-weight: 600; }
.stage-pending { background: #f3f4f6; color: #aaa; }
.stage-arrow {
  font-size: 11px;
  color: #d1d5db;
  flex-shrink: 0;
}
.progress-task-summary {
  font-size: 12px;
  color: #888;
}
.pending-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 6px;
  text-decoration: none;
  color: #333;
  transition: background 0.15s;
}
.pending-item:hover { background: rgba(0, 0, 0, 0.03); }
.pending-badge {
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 4px;
  background: #f3f4f6;
  color: #666;
}
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: #999;
  font-size: 14px;
}
</style>
