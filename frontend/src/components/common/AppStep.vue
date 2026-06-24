<template>
  <div :data-testid="testId" class="app-step" :class="{ active: active, completed: completed }">
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ testId?: string; active?: boolean; completed?: boolean }>()
</script>

<style scoped>
.app-step {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  transition: all 0.2s ease;
}

.app-step.active {
  background: var(--color-primary-soft);
  border-color: var(--color-primary);
  color: var(--color-primary);
  font-weight: 600;
}

.app-step.completed {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: #fff;
}
</style>
