<template>
  <select
    :data-testid="testId"
    :value="modelValue"
    @change="$emit('update:modelValue', ($event.target as HTMLSelectElement).value)"
    v-bind="$attrs"
  >
    <slot />
  </select>
</template>

<script setup lang="ts">
defineProps<{ testId?: string; modelValue?: string }>()
defineEmits(['update:modelValue'])
</script>
