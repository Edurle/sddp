<template>
  <span :data-testid="testId" class="app-badge">{{ text }}</span>
</template>

<script setup lang="ts">
defineProps<{ testId?: string; text?: string }>()
</script>

<style scoped>
.app-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.85em;
  background: #e0e0e0;
}
</style>
