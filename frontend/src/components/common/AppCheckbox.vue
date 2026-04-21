<template>
  <label>
    <input
      type="checkbox"
      :data-testid="testId"
      :checked="modelValue"
      @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
    />
    <span v-if="label">{{ label }}</span>
  </label>
</template>

<script setup lang="ts">
defineProps<{ testId?: string; label?: string; modelValue?: boolean }>()
defineEmits(['update:modelValue'])
</script>
