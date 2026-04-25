<template>
  <div :data-testid="testId" class="app-list">
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ testId?: string }>()
</script>

<style scoped>
.app-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
</style>
