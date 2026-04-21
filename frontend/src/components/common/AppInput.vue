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
