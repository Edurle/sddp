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

<style scoped>
textarea {
  width: 100%;
  box-sizing: border-box;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  padding: 9px 14px;
  font-family: inherit;
  font-size: inherit;
  outline: none;
  resize: vertical;
  min-height: 80px;
  transition: all 0.2s ease;
}

textarea:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
