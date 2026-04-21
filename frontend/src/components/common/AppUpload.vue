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
