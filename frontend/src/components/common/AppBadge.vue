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
  border-radius: var(--radius-pill);
  font-size: 0.8em;
  font-weight: 500;
  background: rgba(0, 0, 0, 0.05);
  border: 1px solid var(--color-border-strong);
  color: var(--color-text);
  letter-spacing: 0.01em;
}
</style>
