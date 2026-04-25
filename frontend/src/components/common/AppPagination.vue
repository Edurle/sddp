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
  gap: 12px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 10px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.app-pagination button {
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid rgba(0, 0, 0, 0.08);
  border-radius: 8px;
  padding: 6px 14px;
  color: #333;
  font-size: 12px;
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
  font-size: 13px;
  color: #666;
}
</style>
