<template>
  <nav :data-testid="testId" class="app-breadcrumb">
    <slot />
  </nav>
</template>

<script setup lang="ts">
defineProps<{ testId?: string }>()
</script>

<style scoped>
.app-breadcrumb {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-text-muted);
}

.app-breadcrumb :deep(a) {
  color: var(--color-text-muted);
  text-decoration: none;
  transition: color 0.2s ease;
}

.app-breadcrumb :deep(a:hover) {
  color: var(--color-text);
}

.app-breadcrumb :deep(span) {
  color: var(--color-text);
  font-weight: 500;
}
</style>
