export function reqStatusLabel(status: string): string {
  const map: Record<string, string> = {
    drafting_req: '草稿', reviewing_req: '需求审核', drafting_spec: '编写规范',
    reviewing_spec: '规范审核', drafting_tests: '编写测试', reviewing_tests: '测试审核',
    approved: '已通过',
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
