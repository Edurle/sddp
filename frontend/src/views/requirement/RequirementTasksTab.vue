<template>
  <div class="tab-panel">
    <div class="tab-toolbar">
      <button data-testid="req-detail-btn-add-task" @click="$emit('add')">添加任务</button>
    </div>
    <table data-testid="req-detail-tbl-tasks">
      <thead>
        <tr><th>标题</th><th>状态</th></tr>
      </thead>
      <tbody>
        <tr v-for="task in tasks" :key="task.id">
          <td><router-link :to="`/tasks/${task.id}`" class="task-link">{{ task.title }}</router-link></td>
          <td>{{ taskStatusLabel(task.status) }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import { taskStatusLabel } from '@/utils/status'

interface TaskItem {
  id: number
  title: string
  status: string
  description?: string
}

defineProps<{ tasks: TaskItem[] }>()
defineEmits<{ add: [] }>()
</script>

<style scoped>
.tab-toolbar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.75rem;
}
.task-link {
  color: var(--color-primary);
  text-decoration: none;
  font-weight: 500;
}
.task-link:hover {
  text-decoration: underline;
}
</style>
