<template>
  <transition name="dialog-fade">
    <div v-if="open" class="dialog-overlay" @click.self="$emit('close')">
      <div
        ref="dialogEl"
        :data-testid="testId"
        class="dialog"
        role="dialog"
        aria-modal="true"
        tabindex="-1"
        @keydown="onKeydown"
      >
        <slot />
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = defineProps<{ open?: boolean; testId?: string }>()
const emit = defineEmits(['close'])

const dialogEl = ref<HTMLElement | null>(null)
let lastFocused: HTMLElement | null = null

watch(
  () => props.open,
  async (open) => {
    if (open) {
      lastFocused = (document.activeElement as HTMLElement) || null
      await nextTick()
      focusFirst()
    } else if (lastFocused) {
      lastFocused.focus?.()
      lastFocused = null
    }
  },
)

function focusable(): HTMLElement[] {
  if (!dialogEl.value) return []
  const sel =
    'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
  return Array.from(dialogEl.value.querySelectorAll<HTMLElement>(sel)).filter(
    (el) => el.getClientRects().length > 0,
  )
}

function focusFirst() {
  const f = focusable()
  ;(f[0] || dialogEl.value)?.focus()
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    emit('close')
    return
  }
  if (e.key === 'Tab') {
    const f = focusable()
    if (f.length === 0) {
      e.preventDefault()
      return
    }
    const first = f[0]
    const last = f[f.length - 1]
    const active = document.activeElement as HTMLElement
    if (e.shiftKey && active === first) {
      e.preventDefault()
      last.focus()
    } else if (!e.shiftKey && active === last) {
      e.preventDefault()
      first.focus()
    }
  }
}
</script>

<style scoped>
.dialog-fade-enter-active,
.dialog-fade-leave-active {
  transition: opacity 0.15s ease;
}
.dialog-fade-enter-from,
.dialog-fade-leave-to {
  opacity: 0;
}
</style>
