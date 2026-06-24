export function reqStatusLabel(status: string): string {
  const map: Record<string, string> = {
    drafting_req: '草稿', reviewing_req: '需求审核', drafting_spec: '编写规范',
    reviewing_spec: '规范审核', drafting_tests: '编写测试', reviewing_tests: '测试审核',
    approved: '已通过',
    deprecated: '已废弃',
  }
  return map[status] || status
}

export function taskStatusLabel(status: string): string {
  const map: Record<string, string> = {
    pending: '待执行', coding: '编码中', testing: '测试中', completed: '已完成',
  }
  return map[status] || status
}

export function iterStatusLabel(status: string): string {
  const map: Record<string, string> = {
    planning: '规划中', in_progress: '进行中', completed: '已完成',
  }
  return map[status] || status
}

export function projectStatusLabel(status: string): string {
  const map: Record<string, string> = {
    active: '进行中',
    archived: '已归档',
  }
  return map[status] || status
}

/** Semantic colour intents — map to the --intent-* tokens in main.css. */
export type BadgeIntent =
  | 'neutral'
  | 'info'
  | 'review'
  | 'success'
  | 'warning'
  | 'danger'

export function reqStatusIntent(status: string): BadgeIntent {
  const map: Record<string, BadgeIntent> = {
    drafting_req: 'neutral',
    drafting_spec: 'info',
    drafting_tests: 'warning',
    reviewing_req: 'review',
    reviewing_spec: 'review',
    reviewing_tests: 'review',
    approved: 'success',
    deprecated: 'danger',
  }
  return map[status] || 'neutral'
}

export function taskStatusIntent(status: string): BadgeIntent {
  const map: Record<string, BadgeIntent> = {
    pending: 'neutral',
    coding: 'info',
    testing: 'warning',
    completed: 'success',
  }
  return map[status] || 'neutral'
}

export function iterStatusIntent(status: string): BadgeIntent {
  const map: Record<string, BadgeIntent> = {
    planning: 'neutral',
    in_progress: 'info',
    completed: 'success',
  }
  return map[status] || 'neutral'
}

/** Kanban column / coarse req status keys (draft, in_review, in_progress…). */
export function mappedReqStatusIntent(mapped: string): BadgeIntent {
  const map: Record<string, BadgeIntent> = {
    draft: 'neutral',
    in_review: 'review',
    approved: 'success',
    in_progress: 'info',
    completed: 'success',
    deprecated: 'danger',
  }
  return map[mapped] || 'neutral'
}

export type PriorityLevel = 'high' | 'medium' | 'low'

/** Priority is stored as 1 (low) / 2 (medium) / 3 (high). */
export function priorityLevel(priority: string | number): PriorityLevel {
  const p = Number(priority)
  if (p >= 3) return 'high'
  if (p === 2) return 'medium'
  return 'low'
}

export function priorityLabel(priority: string | number): string {
  return { high: '高', medium: '中', low: '低' }[priorityLevel(priority)]
}

export function priorityIntent(priority: string | number): BadgeIntent {
  return { high: 'danger', medium: 'warning', low: 'success' }[
    priorityLevel(priority)
  ] as BadgeIntent
}
