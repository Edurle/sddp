<template>
  <div class="empty-state" :data-testid="testId">
    <slot>{{ text }}</slot>
  </div>
</template>

<script setup lang="ts">
defineProps<{ text?: string; testId?: string }>()
</script>

<style scoped>
.empty-state {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--color-text-subtle);
  font-size: var(--text-base);
}
.empty-state :deep(p) {
  margin: 0;
}
</style>
