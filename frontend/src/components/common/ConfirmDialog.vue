<template>
  <transition name="confirm-fade">
    <div
      v-if="store.visible"
      class="dialog-overlay"
      data-testid="confirm-dialog"
      @click.self="store.respond(false)"
    >
      <div
        class="dialog confirm-dialog"
        role="dialog"
        aria-modal="true"
        :aria-label="store.options.title || '确认'"
      >
        <h3 v-if="store.options.title">{{ store.options.title }}</h3>
        <p>{{ store.options.message }}</p>
        <div class="confirm-actions">
          <button
            type="button"
            class="confirm-cancel"
            data-testid="confirm-dialog-btn-cancel"
            @click="store.respond(false)"
          >
            {{ store.options.cancelText || '取消' }}
          </button>
          <button
            ref="confirmBtn"
            type="button"
            :class="{ 'btn-danger': store.options.danger }"
            data-testid="confirm-dialog-btn-confirm"
            @click="store.respond(true)"
          >
            {{ store.options.confirmText || '确定' }}
          </button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useConfirmStore } from '@/stores/confirm'

const store = useConfirmStore()
const confirmBtn = ref<HTMLButtonElement | null>(null)

watch(
  () => store.visible,
  async (v) => {
    if (v) {
      await nextTick()
      confirmBtn.value?.focus()
    }
  },
)

function onKeydown(e: KeyboardEvent) {
  if (store.visible && e.key === 'Escape') store.respond(false)
}
onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.confirm-dialog {
  min-width: 360px;
  max-width: 440px;
}
.confirm-dialog p {
  color: var(--color-text-muted);
  margin-bottom: 1.25rem;
}
.confirm-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-2);
}
.confirm-actions button {
  margin: 0;
}
.confirm-cancel {
  background: var(--color-surface-muted);
  color: var(--color-text);
  border-color: var(--color-border);
}
.confirm-cancel:hover {
  background: var(--color-bg);
  border-color: var(--color-border-strong);
  box-shadow: none;
}
.confirm-fade-enter-active,
.confirm-fade-leave-active {
  transition: opacity 0.15s ease;
}
.confirm-fade-enter-from,
.confirm-fade-leave-to {
  opacity: 0;
}
</style>
