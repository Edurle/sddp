<template>
  <div>
    <label v-if="label" :for="inputId">{{ label }}</label>
    <input
      :id="inputId"
      :data-testid="testId"
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      v-bind="$attrs"
    />
  </div>
</template>

<script setup lang="ts">
import { useId } from 'vue'

defineOptions({ inheritAttrs: false })

defineProps<{
  testId?: string
  label?: string
  type?: string
  modelValue?: string
  placeholder?: string
  disabled?: boolean
}>()

defineEmits(['update:modelValue'])

const inputId = useId()
</script>

<style scoped>
div {
  margin-bottom: 1rem;
}

label {
  color: #666;
  font-size: 13px;
  margin-bottom: 4px;
  display: block;
}

input {
  width: 100%;
  box-sizing: border-box;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  padding: 9px 14px;
  font-family: inherit;
  font-size: inherit;
  outline: none;
  transition: all 0.2s ease;
}

input:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}

input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
