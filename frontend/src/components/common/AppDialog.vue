<template>
  <div v-if="open" class="app-dialog-overlay" @click.self="$emit('close')">
    <div :data-testid="testId" class="app-dialog">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ testId?: string; open?: boolean }>()
defineEmits(['close'])
</script>

<style scoped>
.app-dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.app-dialog {
  background: white;
  padding: 1.5rem;
  border-radius: 8px;
  min-width: 400px;
  max-width: 600px;
}
</style>
