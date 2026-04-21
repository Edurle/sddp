<template>
  <div :data-testid="testId" class="app-list">
    <slot />
  </div>
</template>

<script setup lang="ts">
defineProps<{ testId?: string }>()
</script>
