<template>
  <div class="info-card">
    <template v-if="!editing">
      <h2 class="info-title" data-testid="task-detail-txt-title">{{ task.title }}</h2>
      <p class="info-desc" data-testid="task-detail-txt-description">{{ task.description }}</p>
      <div class="info-row">
        <span class="info-row-label">状态</span>
        <span :class="['status-badge', `badge-${task.status}`]" data-testid="task-detail-txt-status">{{ taskStatusLabel(task.status) }}</span>
      </div>
      <div class="info-row">
        <span class="info-row-label">指派人</span>
        <span class="info-row-value" data-testid="task-detail-txt-assignee">{{ assigneeName }}</span>
      </div>
      <div class="info-row">
        <span class="info-row-label">需求</span>
        <router-link
          v-if="task.requirement"
          :to="`/requirements/${task.requirement.id}`"
          class="info-link"
          data-testid="task-detail-txt-linked-requirement"
        >{{ task.requirement.title }}</router-link>
        <span v-else data-testid="task-detail-txt-linked-requirement"></span>
      </div>
      <div v-if="task.git_branch" class="info-row">
        <span class="info-row-label">分支</span>
        <span class="info-row-value">{{ task.git_branch }}</span>
      </div>
      <div v-if="task.commit_sha" class="info-row">
        <span class="info-row-label">提交</span>
        <span class="info-row-value mono">{{ task.commit_sha.slice(0, 7) }}</span>
      </div>
      <div v-if="task.pr_url" class="info-row">
        <span class="info-row-label">PR</span>
        <a class="info-link" :href="task.pr_url" target="_blank">查看 PR</a>
      </div>
    </template>
    <template v-else>
      <div class="form-group">
        <label>标题</label>
        <input v-model="editForm.title" data-testid="task-detail-inp-title" />
      </div>
      <div class="form-group">
        <label>描述</label>
        <textarea v-model="editForm.description" data-testid="task-detail-txtarea-description"></textarea>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { taskStatusLabel } from '@/utils/status'

interface Assignee {
  id?: number
  nickname?: string
  email?: string
}

interface Requirement {
  id: number
  title: string
}

interface TaskData {
  id: number
  title: string
  description: string
  status: string
  assignee?: Assignee | null
  requirement?: Requirement | null
  git_branch?: string | null
  commit_sha?: string | null
  pr_url?: string | null
}

const props = defineProps<{
  task: TaskData
  editing: boolean
  editForm: { title: string; description: string }
}>()

const assigneeName = computed(() => {
  if (props.task.assignee?.nickname) return props.task.assignee.nickname
  if (props.task.assignee?.email) return props.task.assignee.email
  return ''
})
</script>

<style scoped>
.info-card {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  padding: 0.85rem;
}
.info-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #111;
}
.info-desc {
  color: #666;
  font-size: 13px;
  line-height: 1.6;
  margin-bottom: 10px;
}
.info-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: 12px;
}
.info-row:last-child {
  margin-bottom: 0;
}
.info-row-label {
  color: #999;
  min-width: 50px;
}
.info-row-value {
  color: #333;
}
.info-row-value.mono {
  font-family: monospace;
  font-size: 11px;
  background: #f5f5f5;
  padding: 1px 6px;
  border-radius: 3px;
}
.info-link {
  color: #1677ff;
  text-decoration: none;
  font-weight: 500;
}
.info-link:hover {
  text-decoration: underline;
}
.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
}
.badge-pending {
  background: #f0f0f0;
  color: #666;
}
.badge-coding {
  background: #f9f0ff;
  color: #722ed1;
}
.badge-testing {
  background: #fff7e6;
  color: #d48806;
}
.badge-completed {
  background: #f6ffed;
  color: #52c41a;
}
</style>
