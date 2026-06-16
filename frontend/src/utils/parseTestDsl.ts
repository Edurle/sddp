import yaml from 'js-yaml'

export type DslType = 'api' | 'ui' | 'plain'

export interface FlowLine {
  dslType: DslType
  role?: string
  setup: SetupItem[]
  steps: StepItem[]
  asserts: AssertItem[]
}

export type SetupItem = ApiSetupItem | UiSetupItem

export interface ApiSetupItem {
  kind: 'api_call'
  method: string
  path: string
  service?: string
  body?: Record<string, unknown>
  save?: Record<string, string>
  cleanup?: string
}

export interface UiSetupItem {
  kind: 'ui_action'
  action: string
  trigger?: Record<string, unknown>
  title?: string
}

export type StepItem = ApiStepItem | UiStepItem

export interface ApiStepItem {
  kind: 'api_call'
  method: string
  path: string
  service?: string
  body?: Record<string, unknown>
}

export interface UiStepItem {
  kind: 'ui_action'
  action: string
  target: Record<string, unknown>
  value?: string
}

export type AssertItem = ApiAssertItem | UiAssertItem

export interface ApiAssertItem {
  kind: 'response'
  success?: boolean
  data_type?: string
  data_not_empty?: boolean
  status?: number
  [key: string]: unknown
}

export interface UiAssertItem {
  kind: 'ui_assert'
  assert: string
  target?: Record<string, unknown>
  value?: string
}

function safeYaml(text: string | null | undefined): unknown {
  if (!text || !text.trim()) return null
  try {
    return yaml.load(text)
  } catch {
    return null
  }
}

function extractApiSetup(pre: any): { role?: string; items: ApiSetupItem[] } {
  const role = typeof pre?.role === 'string' ? pre.role : undefined
  const items: ApiSetupItem[] = []
  const exists: any[] = pre?.data?.exists || pre?.data || []
  const arr = Array.isArray(exists) ? exists : [exists]
  for (const item of arr) {
    if (!item?.via?.call) continue
    const parts = String(item.via.call).split(' ')
    items.push({
      kind: 'api_call',
      method: parts[0] || '',
      path: parts.slice(1).join(' ') || '',
      service: item.via.service,
      body: item.via.body,
      save: item.via.save,
      cleanup: item.via.cleanup,
    })
  }
  return { role, items }
}

function extractUiSetup(pre: any): { role?: string; items: UiSetupItem[] } {
  const role = typeof pre?.role === 'string' ? pre.role : undefined
  const items: UiSetupItem[] = []
  const setup: any[] = Array.isArray(pre?.setup) ? pre.setup : []
  for (const s of setup) {
    if (!s?.action) continue
    items.push({
      kind: 'ui_action',
      action: s.action,
      trigger: s.trigger,
      title: s.title,
    })
  }
  return { role, items }
}

function extractApiSteps(stepsRaw: any): ApiStepItem[] {
  const arr = Array.isArray(stepsRaw) ? stepsRaw : stepsRaw ? [stepsRaw] : []
  return arr
    .filter((s: any) => s?.call)
    .map((s: any) => {
      const parts = String(s.call).split(' ')
      return {
        kind: 'api_call' as const,
        method: parts[0] || '',
        path: parts.slice(1).join(' ') || '',
        service: s.service,
        body: s.body,
      }
    })
}

function extractUiSteps(stepsRaw: any): UiStepItem[] {
  const arr = Array.isArray(stepsRaw) ? stepsRaw : stepsRaw ? [stepsRaw] : []
  return arr
    .filter((s: any) => s?.action)
    .map((s: any) => ({
      kind: 'ui_action' as const,
      action: s.action,
      target: s.target || {},
      value: s.value,
    }))
}

function extractApiAsserts(expectedRaw: any): ApiAssertItem[] {
  const arr = Array.isArray(expectedRaw) ? expectedRaw : expectedRaw ? [expectedRaw] : []
  return arr
    .filter((e: any) => e?.response || e?.success !== undefined)
    .map((e: any) => {
      const r = e.response || e
      return {
        kind: 'response' as const,
        success: r.success,
        data_type: r.data_type,
        data_not_empty: r.data_not_empty,
        status: r.status,
      }
    })
}

function extractUiAsserts(expectedRaw: any): UiAssertItem[] {
  const arr = Array.isArray(expectedRaw) ? expectedRaw : expectedRaw ? [expectedRaw] : []
  return arr
    .filter((e: any) => e?.assert)
    .map((e: any) => ({
      kind: 'ui_assert' as const,
      assert: e.assert,
      target: e.target,
      value: e.value,
    }))
}

export function parseTestDsl(
  caseType: string,
  precondition: string | null | undefined,
  steps: string | null | undefined,
  expectedResult: string | null | undefined,
): FlowLine {
  const pre = safeYaml(precondition)
  const stepsRaw = safeYaml(steps)
  const expectedRaw = safeYaml(expectedResult)

  if (pre === null && stepsRaw === null && expectedRaw === null) {
    return { dslType: 'plain', setup: [], steps: [], asserts: [] }
  }

  if (caseType === 'ui_test') {
    const { role, items } = extractUiSetup(pre)
    return {
      dslType: 'ui',
      role,
      setup: items,
      steps: extractUiSteps(stepsRaw),
      asserts: extractUiAsserts(expectedRaw),
    }
  }

  const { role, items } = extractApiSetup(pre)
  const apiSteps = extractApiSteps(stepsRaw)
  const uiSteps = extractUiSteps(stepsRaw)
  if (apiSteps.length > 0 || items.length > 0) {
    return {
      dslType: 'api',
      role,
      setup: items,
      steps: apiSteps,
      asserts: extractApiAsserts(expectedRaw),
    }
  }
  if (uiSteps.length > 0) {
    const { role: r2, items: i2 } = extractUiSetup(pre)
    return {
      dslType: 'ui',
      role: r2,
      setup: i2,
      steps: uiSteps,
      asserts: extractUiAsserts(expectedRaw),
    }
  }

  return { dslType: 'plain', setup: [], steps: [], asserts: [] }
}

export function methodColor(method: string): string {
  const m = method.toUpperCase()
  if (m === 'GET') return '#22c55e'
  if (m === 'POST') return '#3b82f6'
  if (m === 'PUT' || m === 'PATCH') return '#f59e0b'
  if (m === 'DELETE') return '#ef4444'
  return '#6b7280'
}
