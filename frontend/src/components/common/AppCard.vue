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
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(0, 0, 0, 0.06);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
  border-radius: 14px;
  padding: 1.25rem;
}
</style>
