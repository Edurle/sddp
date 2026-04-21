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
