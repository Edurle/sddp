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
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}
.app-dialog {
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(24px);
  border: 1px solid rgba(0, 0, 0, 0.08);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.12);
  border-radius: 16px;
  padding: 1.5rem;
  min-width: 440px;
  max-width: 600px;
}
</style>
