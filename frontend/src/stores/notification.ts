import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNotificationStore = defineStore('notification', () => {
  const message = ref('')
  const type = ref<'error' | 'success'>('error')
  const visible = ref(false)
  let timer: ReturnType<typeof setTimeout> | null = null

  function show(msg: string, t: 'error' | 'success' = 'error') {
    if (timer) clearTimeout(timer)
    message.value = msg
    type.value = t
    visible.value = true
    // Errors stay longer so users can actually read them.
    const duration = t === 'error' ? 6000 : 3000
    timer = setTimeout(() => { visible.value = false; timer = null }, duration)
  }

  function hide() {
    if (timer) { clearTimeout(timer); timer = null }
    visible.value = false
  }

  function showError(msg: string) { show(msg, 'error') }
  function showSuccess(msg: string) { show(msg, 'success') }

  return { message, type, visible, showError, showSuccess, hide }
})
