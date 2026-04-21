<template>
  <button :data-testid="testId" :type="type" :disabled="disabled" v-bind="$attrs">
    <slot />
  </button>
</template>

<script setup lang="ts">
defineProps<{ testId?: string; type?: 'button' | 'submit'; disabled?: boolean }>()
</script>
