<template>
  <button :data-testid="testId" :type="type" :disabled="disabled" v-bind="$attrs">
    <slot />
  </button>
</template>

<script setup lang="ts">
defineProps<{ testId?: string; type?: 'button' | 'submit'; disabled?: boolean }>()
</script>

<style scoped>
button {
  font-family: inherit;
  font-size: inherit;
  transition: all 0.2s ease;
}

button[type="submit"] {
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  padding: 9px 20px;
  font-weight: 500;
  cursor: pointer;
}

button[type="submit"]:hover {
  background: var(--color-primary-hover);
}

button[type="submit"]:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

button[type="button"] {
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 9px 20px;
  cursor: pointer;
}

button[type="button"]:hover {
  background: rgba(0, 0, 0, 0.08);
  border-color: var(--color-border-strong);
}
</style>
