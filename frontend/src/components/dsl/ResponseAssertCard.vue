<template>
  <div v-if="dslType === 'ui'" class="dsl-assert-card">
    <div class="dsl-assert-header">
      <span class="dsl-assert-check">✓</span>
      <span class="dsl-assert-name">{{ (item as UiAssertItem).assert }}</span>
      <span class="dsl-phase-tag">#{{ index + 1 }}</span>
    </div>
    <div v-if="(item as UiAssertItem).target && Object.keys((item as UiAssertItem).target!).length" class="dsl-assert-section">
      <span class="dsl-field-key">target</span>
      <div class="dsl-field-obj">
        <div v-for="(val, key) in (item as UiAssertItem).target" :key="key" class="dsl-kv-row">
          <span class="dsl-kv-key">{{ key }}</span>
          <span class="dsl-kv-val">{{ val }}</span>
        </div>
      </div>
    </div>
    <div v-if="(item as UiAssertItem).value" class="dsl-assert-section">
      <span class="dsl-field-key">value</span>
      <code class="dsl-value-code">{{ (item as UiAssertItem).value }}</code>
    </div>
  </div>
  <div v-else class="dsl-assert-card">
    <div class="dsl-assert-header">
      <span class="dsl-assert-check">✓</span>
      <span class="dsl-assert-name">{{ assertName }}</span>
      <span class="dsl-phase-tag">#{{ index + 1 }}</span>
    </div>
    <div class="dsl-assert-items">
      <div v-for="key in assertKeys" :key="key" class="dsl-assert-row">
        <span class="dsl-assert-key">{{ key }}</span>
        <span class="dsl-assert-val" :class="{ 'is-true': assertVal(key) === true, 'is-false': assertVal(key) === false }">
          {{ formatVal(assertVal(key)) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ApiAssertItem, UiAssertItem } from '@/utils/parseTestDsl'

const props = defineProps<{
  item: ApiAssertItem | UiAssertItem
  dslType: 'api' | 'ui'
  index: number
}>()

const displayKeys = ['success', 'status', 'data_type', 'data_not_empty', 'error.message_contains', 'error.type']

const assertName = computed(() => {
  if (props.dslType === 'ui') return ''
  const obj = props.item as ApiAssertItem
  return obj.error ? 'error' : 'response'
})

const assertKeys = computed(() => {
  if (props.dslType === 'ui') return []
  return displayKeys.filter((k) => assertVal(k) !== undefined && assertVal(k) !== null)
})

function assertVal(key: string): unknown {
  const obj = props.item as ApiAssertItem
  if (key.includes('.')) {
    const [head, tail] = key.split('.')
    const sub = (obj as Record<string, unknown>)[head] as Record<string, unknown> | undefined
    return sub?.[tail]
  }
  return obj[key]
}

function formatVal(v: unknown): string {
  if (typeof v === 'boolean') return v ? 'true' : 'false'
  return String(v)
}
</script>

<style scoped>
.dsl-assert-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  background: var(--color-surface);
}
.dsl-assert-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 8px 12px;
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-border);
}
.dsl-assert-check {
  color: var(--intent-success-text);
  font-weight: 700;
  font-size: var(--text-base);
}
.dsl-assert-name {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--color-text);
}
.dsl-phase-tag {
  font-size: var(--text-2xs);
  color: var(--color-text-subtle);
  font-weight: 600;
  margin-left: auto;
}
.dsl-assert-items {
  padding: 6px 12px;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}
.dsl-assert-row {
  display: flex;
  gap: var(--space-2);
  font-size: var(--text-sm);
  line-height: 1.5;
}
.dsl-assert-key {
  color: var(--color-text-muted);
  font-weight: 500;
  min-width: 90px;
}
.dsl-assert-val {
  color: var(--color-text);
}
.dsl-assert-val.is-true {
  color: var(--intent-success-text);
  font-weight: 600;
}
.dsl-assert-val.is-false {
  color: var(--color-danger);
  font-weight: 600;
}
.dsl-assert-section {
  padding: 6px 12px;
  display: flex;
  align-items: flex-start;
  gap: var(--space-2);
  border-top: 1px solid var(--color-border);
}
.dsl-field-key {
  font-size: var(--text-2xs);
  color: var(--color-text-subtle);
  font-weight: 600;
  min-width: 40px;
  padding-top: 2px;
  flex-shrink: 0;
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
  font-size: var(--text-sm);
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
  font-size: var(--text-xs);
  color: var(--color-text);
  background: var(--color-surface-muted);
  padding: 1px 6px;
  border-radius: var(--radius-xs);
}
</style>
