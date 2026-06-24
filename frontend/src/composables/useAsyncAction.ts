import { reactive } from 'vue'

/**
 * Tracks in-flight async actions by key so buttons can disable themselves
 * while their request runs — preventing double-submit and giving feedback.
 *
 * One instance per component handles all its actions:
 *
 *   const { isPending, run } = useAsyncAction()
 *
 *   async function createUser() {
 *     await run('createUser', async () => {
 *       try { await apiClient.post(...) } catch (e) { ... }
 *     })
 *   }
 *
 *   <button :disabled="isPending('createUser')">创建</button>
 */
export function useAsyncAction() {
  const pending = reactive<Record<string, boolean>>({})

  function isPending(key = 'default'): boolean {
    return !!pending[key]
  }

  async function run<T>(key: string, fn: () => Promise<T>): Promise<T | undefined> {
    if (pending[key]) return
    pending[key] = true
    try {
      return await fn()
    } finally {
      pending[key] = false
    }
  }

  return { pending, isPending, run }
}
