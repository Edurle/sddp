<template>
  <table :data-testid="testId">
    <slot />
  </table>
</template>

<script setup lang="ts">
defineProps<{ testId?: string }>()
</script>
