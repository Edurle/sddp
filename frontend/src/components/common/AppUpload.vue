<template>
  <input type="file" :data-testid="testId" @change="onFileChange" />
</template>

<script setup lang="ts">
defineProps<{ testId?: string }>()
const emit = defineEmits(['update:files'])
function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  emit('update:files', target.files)
}
</script>

<style scoped>
input[type="file"] {
  font-size: 13px;
  color: var(--color-text);
  padding: 8px 0;
}

input[type="file"]::file-selector-button {
  background: rgba(0, 0, 0, 0.04);
  border: 1px solid var(--color-border);
  border-radius: 8px;
  padding: 6px 14px;
  color: var(--color-text);
  cursor: pointer;
  font-family: inherit;
  font-size: 12px;
  margin-right: 10px;
  transition: all 0.2s ease;
}

input[type="file"]::file-selector-button:hover {
  background: rgba(0, 0, 0, 0.08);
}
</style>
