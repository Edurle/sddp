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

    <div class="sidebar-section">
      <div class="sidebar-label">基本信息</div>
      <div class="info-card">
        <template v-if="!editing">
          <h2 class="info-title" data-testid="task-detail-txt-title">{{ task.title }}</h2>
          <p class="info-desc" data-testid="task-detail-txt-description">{{ task.description }}</p>
          <div class="info-row">
            <span class="info-row-label">状态</span>
            <span :class="['status-badge', `badge-${task.status}`]" data-testid="task-detail-txt-status">{{ statusLabel(task.status) }}</span>
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
    </div>

    <div class="sidebar-section sidebar-actions">
      <div class="sidebar-label">操作</div>
      <div class="action-buttons">
        <button v-if="task.status === 'pending' && !editing" data-testid="task-detail-btn-start" class="btn-primary" @click="$emit('start-coding')">开始编码</button>
        <button v-if="task.status === 'coding' && !editing" data-testid="task-detail-btn-start-testing" class="btn-primary" @click="$emit('start-testing')">提交测试</button>
        <button v-if="task.status === 'testing' && !editing" data-testid="task-detail-btn-complete" class="btn-success" @click="$emit('complete')">完成任务</button>
        <button v-if="!editing" data-testid="task-detail-btn-edit" class="btn-default" @click="$emit('edit')">编辑</button>
        <button v-if="!editing" data-testid="task-detail-btn-delete" class="btn-danger" @click="$emit('delete')">删除</button>
        <button v-if="editing" data-testid="task-detail-btn-save" class="btn-primary" @click="$emit('save')">保存</button>
      </div>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { computed } from 'vue'

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
}

const props = defineProps<{
  task: TaskData
  editing: boolean
  editForm: { title: string; description: string }
}>()

defineEmits(['edit', 'save', 'delete', 'start-coding', 'start-testing', 'complete'])

const steps = [
  { key: 'pending', label: '未开始' },
  { key: 'coding', label: '编码中' },
  { key: 'testing', label: '测试中' },
  { key: 'completed', label: '已完成' },
]

const assigneeName = computed(() => {
  if (props.task.assignee?.nickname) return props.task.assignee.nickname
  if (props.task.assignee?.email) return props.task.assignee.email
  return ''
})

function statusLabel(status: string) {
  const map: Record<string, string> = {
    pending: '未开始',
    coding: '编码中',
    testing: '测试中',
    completed: '已完成',
  }
  return map[status] || status
}

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
  border-right: 1px solid rgba(0, 0, 0, 0.06);
  padding: 1.25rem 1rem;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.01);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.sidebar-label {
  font-size: 11px;
  color: #999;
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
  background: #f0f0f0;
  color: #999;
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
  background: #ddd;
  color: #999;
  flex-shrink: 0;
}
.step-item.done {
  background: #111;
  color: #fff;
}
.step-item.done .step-circle {
  background: #fff;
  color: #111;
}
.step-item.current {
  background: #1677ff;
  color: #fff;
}
.step-item.current .step-circle {
  background: rgba(255, 255, 255, 0.3);
  color: #fff;
}
.step-item.waiting {
  background: #f0f0f0;
  color: #bbb;
}
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
  background: #1677ff;
  color: #fff !important;
  border-color: #1677ff !important;
}
.btn-primary:hover {
  background: #4096ff;
  box-shadow: 0 2px 8px rgba(22, 119, 255, 0.3);
}
.btn-success {
  background: #52c41a;
  color: #fff !important;
  border-color: #52c41a !important;
}
.btn-success:hover {
  background: #73d13d;
}
.btn-default {
  background: rgba(0, 0, 0, 0.04);
  color: #333 !important;
  border: 1px solid rgba(0, 0, 0, 0.08) !important;
}
.btn-default:hover {
  background: rgba(0, 0, 0, 0.07);
  border-color: rgba(0, 0, 0, 0.14) !important;
}
.btn-danger {
  background: #fff;
  color: #ff4d4f !important;
  border: 1px solid #ffccc7 !important;
}
.btn-danger:hover {
  background: #fff1f0;
}

@media (max-width: 768px) {
  .task-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  }
}
</style>
