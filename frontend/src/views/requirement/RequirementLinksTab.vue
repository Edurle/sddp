<template>
  <div class="tab-panel">
    <div class="tab-toolbar">
      <button data-testid="req-detail-btn-add-link" @click="$emit('add')">添加关联</button>
    </div>
    <table data-testid="req-detail-tbl-links">
      <thead>
        <tr><th>方向</th><th>类型</th><th>关联需求</th><th>创建时间</th><th>操作</th></tr>
      </thead>
      <tbody>
        <tr v-for="link in links" :key="link.id">
          <td>
            <span class="link-direction" :class="link.direction">{{ link.direction === 'outgoing' ? '→ 指向' : '← 来自' }}</span>
          </td>
          <td>
            <span class="spec-tag" :style="linkTypeStyle(link.link_type)">{{ linkTypeLabel(link.link_type) }}</span>
          </td>
          <td>
            <router-link :to="`/requirements/${link.related_req_id}`" class="task-link">需求 #{{ link.related_req_id }}</router-link>
          </td>
          <td>{{ formatTime(link.created_at) }}</td>
          <td>
            <button v-if="link.link_type === 'relates_to'" class="btn-danger" data-testid="req-detail-btn-unlink" :disabled="deleting" @click="$emit('delete', link.id)">删除</button>
            <span v-else class="spec-muted">系统关联</span>
          </td>
        </tr>
      </tbody>
    </table>
    <div v-if="links.length === 0" class="spec-empty">暂无关联需求</div>
  </div>
</template>

<script setup lang="ts">
import { formatTime } from '@/utils/date'

interface LinkItem {
  id: number
  source_id: number
  target_id: number
  link_type: string
  direction: 'incoming' | 'outgoing'
  related_req_id: number
  created_by: number
  created_at: string | null
}

defineProps<{ links: LinkItem[]; deleting?: boolean }>()
defineEmits<{ add: []; delete: [id: number] }>()

function linkTypeLabel(type: string): string {
  const map: Record<string, string> = { supersede: '变更', relates_to: '关联' }
  return map[type] || type
}

function linkTypeStyle(type: string): string {
  const map: Record<string, string> = {
    supersede: 'background:var(--intent-warning-bg);color:var(--intent-warning-text)',
    relates_to: 'background:var(--intent-info-bg);color:var(--color-primary)',
  }
  return map[type] || 'background:var(--color-surface-muted);color:var(--color-text-muted)'
}
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
.spec-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--color-text-subtle);
  font-size: var(--text-base);
}
.link-direction {
  font-size: var(--text-xs);
  font-weight: 500;
  padding: 2px 8px;
  border-radius: var(--radius-md);
}
.link-direction.outgoing {
  background: var(--intent-info-bg);
  color: var(--color-primary);
}
.link-direction.incoming {
  background: var(--intent-success-bg);
  color: var(--intent-success-text);
}
.spec-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-md);
  font-size: var(--text-2xs);
  font-weight: 500;
  margin-right: var(--space-1);
  white-space: nowrap;
}
.spec-muted {
  color: var(--color-text-subtle);
}
</style>
