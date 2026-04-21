<template>
  <textarea
    :data-testid="testId"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    @input="$emit('update:modelValue', ($event.target as HTMLTextAreaElement).value)"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
defineProps<{ testId?: string; modelValue?: string; placeholder?: string; disabled?: boolean }>()
defineEmits(['update:modelValue'])
</script>
