<template>
  <div :data-testid="testId" class="app-pagination">
    <button :disabled="page <= 1" @click="$emit('update:page', page - 1)">上一页</button>
    <span>第 {{ page }} / {{ totalPages }} 页</span>
    <button :disabled="page >= totalPages" @click="$emit('update:page', page + 1)">下一页</button>
  </div>
</template>

<script setup lang="ts">
defineProps<{ testId?: string; page: number; totalPages: number }>()
defineEmits(['update:page'])
</script>

<style scoped>
.app-pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  padding: 10px 16px;
  background: var(--color-surface);
  backdrop-filter: blur(16px);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.app-pagination button {
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 6px 14px;
  color: var(--color-text);
  font-size: var(--text-xs);
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
}

.app-pagination button:hover:not(:disabled) {
  background: rgba(0, 0, 0, 0.08);
}

.app-pagination button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.app-pagination span {
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}
</style>
