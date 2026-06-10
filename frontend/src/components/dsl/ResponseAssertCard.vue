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
      <span class="dsl-assert-name">response</span>
      <span class="dsl-phase-tag">#{{ index + 1 }}</span>
    </div>
    <div class="dsl-assert-items">
      <div v-for="key in assertKeys" :key="key" class="dsl-assert-row">
        <span class="dsl-assert-key">{{ key }}</span>
        <span class="dsl-assert-val" :class="{ 'is-true': (item as ApiAssertItem)[key] === true, 'is-false': (item as ApiAssertItem)[key] === false }">
          {{ formatVal((item as ApiAssertItem)[key]) }}
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

const displayKeys = ['success', 'status', 'data_type', 'data_not_empty']

const assertKeys = computed(() => {
  if (props.dslType === 'ui') return []
  const obj = props.item as ApiAssertItem
  return displayKeys.filter((k) => obj[k] !== undefined && obj[k] !== null)
})

function formatVal(v: unknown): string {
  if (typeof v === 'boolean') return v ? 'true' : 'false'
  return String(v)
}
</script>

<style scoped>
.dsl-assert-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  background: #fff;
}
.dsl-assert-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: #fafbfc;
  border-bottom: 1px solid #f3f4f6;
}
.dsl-assert-check {
  color: #22c55e;
  font-weight: 700;
  font-size: 14px;
}
.dsl-assert-name {
  font-size: 13px;
  font-weight: 600;
  color: #374151;
}
.dsl-phase-tag {
  font-size: 10px;
  color: #9ca3af;
  font-weight: 600;
  margin-left: auto;
}
.dsl-assert-items {
  padding: 6px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.dsl-assert-row {
  display: flex;
  gap: 8px;
  font-size: 13px;
  line-height: 1.5;
}
.dsl-assert-key {
  color: #6b7280;
  font-weight: 500;
  min-width: 90px;
}
.dsl-assert-val {
  color: #374151;
}
.dsl-assert-val.is-true {
  color: #16a34a;
  font-weight: 600;
}
.dsl-assert-val.is-false {
  color: #dc2626;
  font-weight: 600;
}
.dsl-assert-section {
  padding: 6px 12px;
  display: flex;
  align-items: flex-start;
  gap: 8px;
  border-top: 1px solid #f9fafb;
}
.dsl-field-key {
  font-size: 11px;
  color: #9ca3af;
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
  font-size: 13px;
  line-height: 1.5;
}
.dsl-kv-key {
  color: #7c3aed;
  font-weight: 500;
  min-width: 60px;
  flex-shrink: 0;
}
.dsl-kv-val {
  color: #374151;
  word-break: break-all;
}
.dsl-value-code {
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 12px;
  color: #111;
  background: #f3f4f6;
  padding: 1px 6px;
  border-radius: 4px;
}
</style>
