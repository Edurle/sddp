<template>
  <form :data-testid="testId" @submit.prevent="$emit('submit')">
    <slot />
  </form>
</template>

<script setup lang="ts">
defineProps<{ testId?: string }>()
defineEmits(['submit'])
</script>

<style scoped>
form {
  display: flex;
  flex-direction: column;
  gap: 0;
}
</style>
