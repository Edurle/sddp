import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface ConfirmOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  /** Render the confirm button in red for destructive actions. */
  danger?: boolean
}

export const useConfirmStore = defineStore('confirm', () => {
  const visible = ref(false)
  const options = ref<ConfirmOptions>({ message: '' })
  let resolver: ((value: boolean) => void) | null = null

  /** Open the confirm dialog and resolve to true (confirm) / false (cancel). */
  function confirm(opts: ConfirmOptions | string): Promise<boolean> {
    options.value = typeof opts === 'string' ? { message: opts } : opts
    visible.value = true
    return new Promise<boolean>((resolve) => {
      resolver = resolve
    })
  }

  function respond(value: boolean) {
    if (!visible.value) return
    visible.value = false
    const r = resolver
    resolver = null
    r?.(value)
  }

  return { visible, options, confirm, respond }
})
