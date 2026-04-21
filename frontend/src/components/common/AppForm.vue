<template>
  <form :data-testid="testId" @submit.prevent="$emit('submit')">
    <slot />
  </form>
</template>

<script setup lang="ts">
defineProps<{ testId?: string }>()
defineEmits(['submit'])
</script>
