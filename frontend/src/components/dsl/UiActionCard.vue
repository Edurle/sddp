<template>
  <div class="dsl-ui-card">
    <div class="dsl-ui-header">
      <span class="dsl-action-badge">{{ actionLabel }}</span>
      <span v-if="targetDesc" class="dsl-target-desc">{{ targetDesc }}</span>
      <span class="dsl-phase-tag">{{ phase === 'setup' ? 'SETUP' : `#${index + 1}` }}</span>
    </div>
    <div v-if="triggerObj && Object.keys(triggerObj).length" class="dsl-ui-section">
      <span class="dsl-field-key">trigger</span>
      <div class="dsl-field-obj">
        <div v-for="(val, key) in triggerObj" :key="key" class="dsl-kv-row">
          <span class="dsl-kv-key">{{ key }}</span>
          <span class="dsl-kv-val">{{ val }}</span>
        </div>
      </div>
    </div>
    <div v-if="targetObj && Object.keys(targetObj).length" class="dsl-ui-section">
      <span class="dsl-field-key">target</span>
      <div class="dsl-field-obj">
        <div v-for="(val, key) in targetObj" :key="key" class="dsl-kv-row">
          <span class="dsl-kv-key">{{ key }}</span>
          <span class="dsl-kv-val">{{ val }}</span>
        </div>
      </div>
    </div>
    <div v-if="valueProp !== undefined && valueProp !== ''" class="dsl-ui-section">
      <span class="dsl-field-key">value</span>
      <code class="dsl-value-code">{{ valueProp }}</code>
    </div>
    <div v-if="titleProp" class="dsl-ui-section">
      <span class="dsl-field-key">title</span>
      <span class="dsl-field-value">{{ titleProp }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { UiSetupItem, UiStepItem } from '@/utils/parseTestDsl'

const props = defineProps<{
  item: UiSetupItem | UiStepItem
  index: number
  phase: 'setup' | 'step'
}>()

const actionLabel = computed(() => {
  const a = props.item.action
  const map: Record<string, string> = {
    click: '🖱 click',
    fill: '⌨ fill',
    select: '📋 select',
    open_dialog: '📂 open',
    hover: '👆 hover',
    type: '⌨ type',
    wait: '⏳ wait',
  }
  return map[a] || a
})

const isSetup = computed(() => props.item.kind === 'ui_action' && 'trigger' in props.item)
const isStep = computed(() => props.item.kind === 'ui_action' && 'target' in props.item)

const triggerObj = computed(() => isSetup.value ? (props.item as UiSetupItem).trigger : undefined)
const targetObj = computed(() => isStep.value ? (props.item as UiStepItem).target : undefined)
const valueProp = computed(() => isStep.value ? (props.item as UiStepItem).value : undefined)
const titleProp = computed(() => isSetup.value ? (props.item as UiSetupItem).title : undefined)

const targetDesc = computed(() => {
  const t = targetObj.value || triggerObj.value
  if (!t) return ''
  const parts: string[] = []
  if (t.component) parts.push(String(t.component))
  if (t.label) parts.push(`"${t.label}"`)
  if (t.text) parts.push(`"${t.text}"`)
  return parts.join(' · ')
})
</script>

<style scoped>
.dsl-ui-card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-surface);
}
.dsl-ui-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}
.dsl-action-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--intent-info-bg);
  color: var(--color-primary);
  flex-shrink: 0;
}
.dsl-target-desc {
  font-size: 13px;
  color: var(--color-text);
  word-break: break-all;
}
.dsl-phase-tag {
  font-size: 10px;
  color: var(--color-text-subtle);
  font-weight: 600;
  margin-left: auto;
}
.dsl-ui-section {
  padding: 6px 12px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  border-top: 1px solid var(--color-border);
}
.dsl-field-key {
  font-size: 11px;
  color: var(--color-text-subtle);
  font-weight: 600;
  min-width: 40px;
  padding-top: 2px;
  flex-shrink: 0;
}
.dsl-field-value {
  font-size: 13px;
  color: var(--color-text);
}
.dsl-field-obj {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.dsl-kv-row {
  display: flex;
  gap: 6px;
  font-size: 13px;
  line-height: 1.5;
}
.dsl-kv-key {
  color: var(--intent-review-text);
  font-weight: 500;
  min-width: 60px;
  flex-shrink: 0;
}
.dsl-kv-val {
  color: var(--color-text);
  word-break: break-all;
}
.dsl-value-code {
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 12px;
  color: var(--color-text);
  background: var(--color-surface-muted);
  padding: 1px 6px;
  border-radius: 4px;
}
</style>
