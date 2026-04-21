<template>
  <div :data-testid="testId" class="app-card">
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ testId?: string }>()
</script>
