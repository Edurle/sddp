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

<style scoped>
select {
  width: 100%;
  box-sizing: border-box;
  background: rgba(0, 0, 0, 0.03);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 10px;
  padding: 9px 14px;
  font-family: inherit;
  font-size: inherit;
  outline: none;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2 4l4 4 4-4' stroke='%23666' stroke-width='1.5' fill='none' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 12px center;
  padding-right: 36px;
  cursor: pointer;
  transition: all 0.2s ease;
}

select:focus {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-ring);
  outline: none;
}
</style>
