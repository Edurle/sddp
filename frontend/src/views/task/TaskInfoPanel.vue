<template>
  <div class="info-card">
    <template v-if="!editing">
      <h2 class="info-title" data-testid="task-detail-txt-title">{{ task.title }}</h2>
      <p class="info-desc" data-testid="task-detail-txt-description">{{ task.description }}</p>
      <div class="info-row">
        <span class="info-row-label">状态</span>
        <StatusBadge test-id="task-detail-txt-status" :intent="taskStatusIntent(task.status)" :label="taskStatusLabel(task.status)" />
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
import { taskStatusLabel, taskStatusIntent } from '@/utils/status'
import StatusBadge from '@/components/common/StatusBadge.vue'

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
  background: var(--color-surface);
  backdrop-filter: blur(20px);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.85rem;
}
.info-title {
  font-size: var(--text-lg);
  font-weight: 600;
  margin-bottom: var(--space-2);
  color: var(--color-text);
}
.info-desc {
  color: var(--color-text-muted);
  font-size: var(--text-sm);
  line-height: 1.6;
  margin-bottom: 10px;
}
.info-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
  font-size: var(--text-xs);
}
.info-row:last-child {
  margin-bottom: 0;
}
.info-row-label {
  color: var(--color-text-subtle);
  min-width: 50px;
}
.info-row-value {
  color: var(--color-text);
}
.info-row-value.mono {
  font-family: monospace;
  font-size: var(--text-2xs);
  background: var(--color-surface-muted);
  padding: 1px 6px;
  border-radius: var(--radius-xs);
}
.info-link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}
.info-link:hover {
  text-decoration: underline;
}
</style>
