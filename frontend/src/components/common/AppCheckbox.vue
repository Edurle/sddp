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

<style scoped>
label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: #333;
}

input[type="checkbox"] {
  appearance: none;
  width: 18px;
  height: 18px;
  border: 2px solid rgba(0, 0, 0, 0.15);
  border-radius: 5px;
  background: rgba(0, 0, 0, 0.02);
  cursor: pointer;
  position: relative;
  transition: all 0.2s ease;
  flex-shrink: 0;
}

input[type="checkbox"]:checked {
  background: var(--color-primary);
  border-color: var(--color-primary);
}

input[type="checkbox"]:checked::after {
  content: '✓';
  color: #fff;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  font-size: 12px;
}

span {
  color: #333;
}
</style>
