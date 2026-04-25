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
  gap: 8px;
  font-size: 13px;
  color: #666;
}

.app-breadcrumb :deep(a) {
  color: #666;
  text-decoration: none;
  transition: color 0.2s ease;
}

.app-breadcrumb :deep(a:hover) {
  color: #111;
}

.app-breadcrumb :deep(span) {
  color: #111;
  font-weight: 500;
}
</style>
