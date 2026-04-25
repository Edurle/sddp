<template>
  <span :data-testid="testId" class="app-badge">{{ text }}</span>
</template>

<script setup lang="ts">
defineProps<{ testId?: string; text?: string }>()
</script>

<style scoped>
.app-badge {
  display: inline-block;
  padding: 3px 12px;
  border-radius: 20px;
  font-size: 0.8em;
  font-weight: 500;
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid rgba(0, 0, 0, 0.1);
  color: #333;
  letter-spacing: 0.01em;
}
</style>
