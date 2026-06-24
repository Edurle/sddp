<template>
  <div :data-testid="testId" class="app-card">
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ testId?: string }>()
</script>

<style scoped>
.app-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05);
  border-radius: 14px;
  padding: 1.25rem;
}
</style>
