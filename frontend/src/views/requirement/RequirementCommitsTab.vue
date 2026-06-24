<template>
  <div class="tab-panel">
    <table data-testid="req-detail-tbl-commits">
      <thead>
        <tr><th>Commit</th><th>消息</th><th>作者</th><th>任务</th><th>提交时间</th></tr>
      </thead>
      <tbody>
        <tr v-for="c in commits" :key="c.id">
          <td><code>{{ c.commit_sha }}</code></td>
          <td>{{ c.message || '' }}</td>
          <td>{{ c.author || '' }}</td>
          <td>
            <router-link :to="`/tasks/${c.task_id}`" class="task-link">任务 #{{ c.task_id }}</router-link>
          </td>
          <td>{{ formatTime(c.committed_at) }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="commits.length === 0" class="spec-empty">暂无提交记录</div>
  </div>
</template>

<script setup lang="ts">
import { formatTime } from '@/utils/date'

interface CommitItem {
  id: number
  task_id: number
  commit_sha: string
  message: string | null
  author: string | null
  committed_at: string | null
  created_at: string | null
}

defineProps<{ commits: CommitItem[] }>()
</script>

<style scoped>
.task-link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}
.task-link:hover {
  text-decoration: underline;
}
.spec-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--color-text-subtle);
  font-size: var(--text-base);
}
</style>
