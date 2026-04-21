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
  display: inline-block;
  padding: 4px 12px;
  border-radius: 4px;
  background: #f0f0f0;
}
.app-step.active {
  background: #1890ff;
  color: white;
}
.app-step.completed {
  background: #52c41a;
  color: white;
}
</style>
