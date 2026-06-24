<template>
  <div class="dsl-api-card">
    <div class="dsl-api-header">
      <span class="dsl-method" :style="{ background: mColor, color: '#fff' }">{{ method }}</span>
      <code class="dsl-path">{{ path }}</code>
      <span v-if="item.service" class="dsl-service">{{ item.service }}</span>
      <span v-if="phaseLabel" class="dsl-phase-tag">{{ phaseLabel }}</span>
    </div>
    <div v-if="item.body && Object.keys(item.body).length" class="dsl-api-section">
      <span class="dsl-field-key">body</span>
      <div class="dsl-field-obj">
        <div v-for="(val, key) in item.body" :key="key" class="dsl-kv-row">
          <span class="dsl-kv-key">{{ key }}</span>
          <span class="dsl-kv-val">{{ formatVal(val) }}</span>
        </div>
      </div>
    </div>
    <div v-if="setupData.save && Object.keys(setupData.save).length" class="dsl-api-section">
      <span class="dsl-field-key">save</span>
      <div class="dsl-field-obj">
        <div v-for="(val, key) in setupData.save" :key="key" class="dsl-kv-row">
          <span class="dsl-kv-key">{{ key }}</span>
          <span class="dsl-kv-val dsl-kv-path">{{ val }}</span>
        </div>
      </div>
    </div>
    <div v-if="setupData.cleanup" class="dsl-api-section">
      <span class="dsl-field-key">cleanup</span>
      <span class="dsl-field-value">{{ setupData.cleanup }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ApiSetupItem, ApiStepItem } from '@/utils/parseTestDsl'
import { methodColor } from '@/utils/parseTestDsl'

const props = defineProps<{
  item: ApiSetupItem | ApiStepItem
  index: number
  phase: 'setup' | 'step'
}>()

const method = computed(() => props.item.method.toUpperCase())
const path = computed(() => props.item.path)
const mColor = computed(() => methodColor(props.item.method))
const phaseLabel = computed(() => (props.phase === 'setup' ? `SETUP #${props.index + 1}` : `#${props.index + 1}`))
const setupData = computed(() => {
  if (props.item.kind === 'api_call' && 'save' in props.item) return props.item as ApiSetupItem
  return {} as ApiSetupItem
})

function formatVal(v: unknown): string {
  if (typeof v === 'string') return v
  if (typeof v === 'boolean' || typeof v === 'number') return String(v)
  if (v === null || v === undefined) return 'null'
  return JSON.stringify(v)
}
</script>

<style scoped>
.dsl-api-card {
  border: 1px solid var(--color-border);
  border-radius: 8px;
  overflow: hidden;
  background: var(--color-surface);
}
.dsl-api-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}
.dsl-method {
  font-size: 11px;
  font-weight: 700;
  padding: 2px 8px;
  border-radius: 4px;
  letter-spacing: 0.5px;
  flex-shrink: 0;
}
.dsl-path {
  font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
  font-size: 13px;
  color: var(--color-text);
  word-break: break-all;
}
.dsl-service {
  font-size: 11px;
  color: var(--color-text-muted);
  background: var(--color-surface-muted);
  padding: 1px 6px;
  border-radius: 4px;
  margin-left: auto;
}
.dsl-phase-tag {
  font-size: 10px;
  color: var(--color-text-subtle);
  font-weight: 600;
}
.dsl-api-section {
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
  min-width: 36px;
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
  color: var(--color-primary);
  font-weight: 500;
  min-width: 60px;
  flex-shrink: 0;
}
.dsl-kv-val {
  color: var(--color-text);
  word-break: break-all;
}
.dsl-kv-path {
  font-family: 'SF Mono', 'Menlo', monospace;
  color: var(--intent-review-text);
  font-size: 12px;
}
</style>
