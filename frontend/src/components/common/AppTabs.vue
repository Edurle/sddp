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
