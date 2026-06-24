<template>
  <aside class="task-sidebar" data-testid="task-detail-sidebar">
    <div class="sidebar-section">
      <div class="sidebar-label">进度</div>
      <div class="step-list" data-testid="task-detail-step-progress">
        <div
          v-for="step in steps"
          :key="step.key"
          :data-testid="`task-detail-step-progress-step-${step.key}`"
          class="step-item"
          :class="stepClass(step.key)"
        >
          <span class="step-circle">{{ stepCircle(step.key) }}</span>
          <span class="step-text">{{ step.label }}</span>
        </div>
      </div>
    </div>

    <div class="sidebar-section sidebar-actions">
      <div class="sidebar-label">操作</div>
      <div class="action-buttons">
        <button v-if="task.status === 'pending' && !editing" data-testid="task-detail-btn-start" class="btn-primary" :disabled="transitioning" @click="$emit('start-coding')">开始编码</button>
        <button v-if="task.status === 'coding' && !editing" data-testid="task-detail-btn-start-testing" class="btn-primary" :disabled="transitioning" @click="$emit('start-testing')">提交测试</button>
        <button v-if="task.status === 'testing' && !editing" data-testid="task-detail-btn-complete" class="btn-success" :disabled="transitioning" @click="$emit('complete')">完成任务</button>
        <button v-if="!editing" data-testid="task-detail-btn-edit" class="btn-default" @click="$emit('edit')">编辑</button>
        <button v-if="!editing" data-testid="task-detail-btn-delete" class="btn-danger" :disabled="deleting" @click="$emit('delete')">删除</button>
        <button v-if="editing" data-testid="task-detail-btn-save" class="btn-primary" :disabled="saving" @click="$emit('save')">保存</button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
interface TaskData {
  id: number
  status: string
}

const props = defineProps<{
  task: TaskData
  editing: boolean
  saving?: boolean
  deleting?: boolean
  transitioning?: boolean
}>()

defineEmits(['edit', 'save', 'delete', 'start-coding', 'start-testing', 'complete'])

const steps = [
  { key: 'pending', label: '未开始' },
  { key: 'coding', label: '编码中' },
  { key: 'testing', label: '测试中' },
  { key: 'completed', label: '已完成' },
]

function stepClass(step: string) {
  const statusOrder = ['pending', 'coding', 'testing', 'completed']
  const currentIdx = statusOrder.indexOf(props.task.status)
  const stepIdx = statusOrder.indexOf(step)

  if (stepIdx < currentIdx) return 'done'
  if (stepIdx === currentIdx) return 'current'
  return 'waiting'
}

function stepCircle(step: string) {
  const cls = stepClass(step)
  if (cls === 'done') return '✓'
  const idx = steps.findIndex((s) => s.key === step)
  return String(idx + 1)
}
</script>

<style scoped>
.task-sidebar {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid var(--color-border);
  padding: 1.25rem 1rem;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.01);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.sidebar-label {
  font-size: 11px;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  font-weight: 600;
}
.step-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.step-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  background: var(--color-surface-muted);
  color: var(--color-text-subtle);
  transition: all 0.2s;
}
.step-circle {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  font-weight: 700;
  background: var(--color-border);
  color: var(--color-text-subtle);
  flex-shrink: 0;
}
.step-item.done {
  background: var(--color-primary);
  color: #fff;
}
.step-item.done .step-circle {
  background: var(--color-surface);
  color: var(--color-primary);
}
.step-item.current {
  background: var(--color-current);
  color: #fff;
}
.step-item.current .step-circle {
  background: rgba(255, 255, 255, 0.3);
  color: #fff;
}
.step-item.waiting {
  background: var(--color-surface-muted);
  color: var(--color-text-subtle);
}
.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.action-buttons button {
  width: 100%;
  margin: 0;
  font-size: 12px;
  padding: 7px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-family: inherit;
  font-weight: 500;
  border: 1px solid transparent;
  transition: all 0.15s;
}
.btn-primary {
  background: var(--color-primary);
  color: #fff !important;
  border-color: var(--color-primary) !important;
}
.btn-primary:hover {
  background: var(--color-primary-hover);
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.3);
}
.btn-success {
  background: var(--intent-success-solid);
  color: #fff !important;
  border-color: var(--intent-success-solid) !important;
}
.btn-success:hover {
  background: #73d13d;
}
.btn-default {
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-text) !important;
  border: 1px solid var(--color-border) !important;
}
.btn-default:hover {
  background: rgba(0, 0, 0, 0.07);
  border-color: var(--color-border-strong) !important;
}
.btn-danger {
  background: var(--color-danger) !important;
  color: #fff !important;
  border: 1px solid var(--color-danger) !important;
}
.btn-danger:hover {
  background: var(--color-danger-hover) !important;
  border-color: var(--color-danger-hover) !important;
}

@media (max-width: 768px) {
  .task-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--color-border);
  }
}
</style>
