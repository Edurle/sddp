<template>
  <nav :data-testid="testId" class="app-breadcrumb">
    <slot />
  </nav>
</template>

<script setup lang="ts">
defineProps<{ testId?: string }>()
</script>
