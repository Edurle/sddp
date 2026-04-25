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
  gap: 4px;
  background: rgba(0, 0, 0, 0.03);
  padding: 4px;
  border-radius: 10px;
  margin-bottom: 1rem;
}

.tab-buttons button {
  padding: 7px 16px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: #111 !important;
  cursor: pointer;
  font-size: 13px;
  font-family: inherit;
  transition: all 0.2s ease;
}

.tab-buttons button.active {
  background: #111;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.tab-buttons button:hover:not(.active) {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
}
</style>
