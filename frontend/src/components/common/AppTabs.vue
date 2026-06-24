<template>
  <div :data-testid="testId">
    <div class="tab-buttons">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :data-testid="tab.testId"
        :class="{ active: modelValue === tab.key }"
        @click="$emit('update:modelValue', tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>
    <div class="tab-content">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  testId?: string
  modelValue: string
  tabs: Array<{ key: string; label: string; testId?: string }>
}>()
defineEmits(['update:modelValue'])
</script>

<style scoped>
.tab-buttons {
  display: flex;
  gap: var(--space-1);
  background: rgba(0, 0, 0, 0.03);
  padding: var(--space-1);
  border-radius: var(--radius-md);
  margin-bottom: 1rem;
}

.tab-buttons button {
  padding: 7px 16px;
  border-radius: var(--radius-md);
  border: none;
  background: transparent;
  color: var(--color-text) !important;
  cursor: pointer;
  font-size: var(--text-sm);
  font-family: inherit;
  transition: all 0.2s ease;
}

.tab-buttons button.active {
  background: var(--color-primary);
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tab-buttons button:hover:not(.active) {
  background: var(--color-primary-soft);
  color: var(--color-text);
}
</style>
