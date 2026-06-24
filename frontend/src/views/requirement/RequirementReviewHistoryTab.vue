<template>
  <div class="tab-panel">
    <div v-if="reviewComments.length === 0" class="spec-empty">暂无审核记录</div>
    <div v-else class="review-history-list" data-testid="req-detail-list-review-history">
      <div v-for="rc in reviewComments" :key="rc.id" class="review-history-item">
        <div class="review-history-dot" :class="rc.action === 'approve' ? 'dot-approve' : 'dot-reject'"></div>
        <div class="review-history-body">
          <div class="review-history-header">
            <span class="review-history-action" :class="rc.action">{{ rc.action === 'approve' ? '通过' : '拒绝' }}</span>
            <span v-if="reviewTypeLabel(rc.review_type)" class="review-history-type">{{ reviewTypeLabel(rc.review_type) }}</span>
            <span class="review-history-time">{{ formatTime(rc.created_at) }}</span>
          </div>
          <div v-if="rc.comment" class="review-history-comment">{{ rc.comment }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { formatTime } from '@/utils/date'

interface ReviewComment {
  id: number
  reviewer_id: number
  review_type?: string
  action: string
  comment: string | null
  created_at: string
}

defineProps<{ reviewComments: ReviewComment[] }>()

function reviewTypeLabel(type?: string): string {
  const map: Record<string, string> = {
    requirement: '需求审核',
    specification: '规范审核',
    test_case: '测试审核',
  }
  return type ? (map[type] || type) : ''
}
</script>

<style scoped>
.spec-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--color-text-subtle);
  font-size: var(--text-base);
}
.review-history-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.review-history-item {
  display: flex;
  gap: var(--space-3);
  padding: 0.75rem 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.review-history-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  margin-top: var(--space-1);
  flex-shrink: 0;
}
.dot-approve { background: var(--intent-success-solid); }
.dot-reject { background: var(--intent-danger-solid); }
.review-history-body {
  flex: 1;
  min-width: 0;
}
.review-history-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  margin-bottom: var(--space-1);
}
.review-history-action {
  font-size: var(--text-xs);
  font-weight: 600;
  padding: 2px 8px;
  border-radius: var(--radius-md);
  white-space: nowrap;
}
.review-history-action.approve {
  background: var(--intent-success-bg);
  color: var(--intent-success-text);
}
.review-history-action.reject {
  background: var(--intent-danger-bg);
  color: var(--intent-danger-text);
}
.review-history-type {
  font-size: var(--text-xs);
  font-weight: 500;
  padding: 2px 8px;
  border-radius: var(--radius-md);
  white-space: nowrap;
  background: var(--intent-neutral-bg);
  color: var(--color-text-muted);
}
.review-history-time {
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
  white-space: nowrap;
}
.review-history-comment {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
  line-height: 1.6;
  word-break: break-word;
  padding: 0.5rem 0.75rem;
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-sm);
  margin-top: var(--space-1);
}
</style>
