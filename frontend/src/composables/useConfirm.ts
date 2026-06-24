import { useConfirmStore } from '@/stores/confirm'
import type { ConfirmOptions } from '@/stores/confirm'

/**
 * Returns an async `confirm()` that opens the app's custom confirm dialog
 * and resolves to true/false — a drop-in replacement for window.confirm().
 *
 *   const confirm = useConfirm()
 *   if (!(await confirm({ message: '确定删除？', danger: true }))) return
 */
export function useConfirm(): (opts: ConfirmOptions | string) => Promise<boolean> {
  return useConfirmStore().confirm
}
