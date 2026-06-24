<template>
  <span v-if="isNull" class="jt-val jt-null">null</span>
  <span v-else-if="isBool" class="jt-val jt-bool">{{ boolStr }}</span>
  <span v-else-if="isNum" class="jt-val jt-num">{{ numStr }}</span>
  <span v-else-if="isStr" class="jt-val jt-str">{{ strVal }}</span>

  <span v-else-if="isArr && arrVal.length === 0" class="jt-val jt-empty">empty</span>
  <div v-else-if="isArr" class="jt-nested">
    <div class="jt-row jt-toggle-row" @click="collapsed = !collapsed">
      <span class="jt-arrow">{{ collapsed ? '▸' : '▾' }}</span>
      <span v-if="isRoot" class="jt-label">ARRAY</span>
      <span class="jt-hint">{{ arrVal.length }} items</span>
    </div>
    <div v-if="!collapsed" class="jt-indent">
      <div v-for="(item, i) in arrVal" :key="i" class="jt-card">
        <div class="jt-card-header">
          <span class="jt-idx">#{{ i }}</span>
          <span v-if="isObject(item)" class="jt-hint">{{ Object.keys(item as Record<string, unknown>).length }} fields</span>
        </div>
        <div v-if="isObject(item)" class="jt-card-body">
          <div v-for="k in Object.keys(item as Record<string, unknown>)" :key="k" class="jt-row">
            <span class="jt-key">{{ k }}</span>
            <JsonTree :value="(item as Record<string, unknown>)[k]" :indent="indent + 1" />
          </div>
        </div>
        <div v-else class="jt-card-body">
          <JsonTree :value="item" :indent="indent + 1" />
        </div>
      </div>
    </div>
  </div>

  <span v-else-if="isObj && objKeys.length === 0" class="jt-val jt-empty">empty</span>
  <div v-else-if="isObj" class="jt-nested">
    <div v-if="isRoot" class="jt-row jt-toggle-row" @click="collapsed = !collapsed">
      <span class="jt-arrow">{{ collapsed ? '▸' : '▾' }}</span>
      <span class="jt-label">OBJECT</span>
      <span class="jt-hint">{{ objKeys.length }} fields</span>
    </div>
    <div v-if="!isRoot || !collapsed" class="jt-indent" :class="{ 'jt-indent-nested': indent > 0 }">
      <template v-for="(k, i) in objKeys" :key="k">
        <div v-if="isObject(objEntries[k]) || isArray(objEntries[k])" class="jt-section">
          <div class="jt-row jt-toggle-row" @click="toggleKey(k)">
            <span class="jt-arrow">{{ isKeyCollapsed(k) ? '▸' : '▾' }}</span>
            <span class="jt-key">{{ k }}</span>
            <span class="jt-hint">{{ isArray(objEntries[k]) ? (objEntries[k] as unknown[]).length + ' items' : Object.keys(objEntries[k] as Record<string, unknown>).length + ' fields' }}</span>
          </div>
          <div v-if="!isKeyCollapsed(k)" class="jt-indent jt-indent-nested">
            <JsonTree :value="objEntries[k]" :indent="indent + 1" />
          </div>
        </div>
        <div v-else class="jt-row">
          <span class="jt-key">{{ k }}</span>
          <JsonTree :value="objEntries[k]" :indent="indent + 1" />
        </div>
        <div v-if="i < objKeys.length - 1" class="jt-divider"></div>
      </template>
    </div>
  </div>

  <span v-else class="jt-val">{{ String(value) }}</span>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'

const props = defineProps<{ value: unknown; indent?: number }>()
const collapsed = ref(false)
const collapsedKeys = reactive<Record<string, boolean>>({})

const indent = computed(() => props.indent ?? 0)
const isRoot = computed(() => indent.value === 0)
const isNull = computed(() => props.value === null || props.value === undefined)
const isBool = computed(() => typeof props.value === 'boolean')
const isNum = computed(() => typeof props.value === 'number')
const isStr = computed(() => typeof props.value === 'string')
const isArr = computed(() => Array.isArray(props.value))
const isObj = computed(() => !isNull.value && !isArr.value && typeof props.value === 'object')

const boolStr = computed(() => isBool.value ? String(props.value) : '')
const numStr = computed(() => isNum.value ? String(props.value) : '')
const strVal = computed(() => isStr.value ? (props.value as string) : '')
const arrVal = computed(() => isArr.value ? (props.value as unknown[]) : [])
const objEntries = computed(() => isObj.value ? (props.value as Record<string, unknown>) : {})
const objKeys = computed(() => Object.keys(objEntries.value))

function isObject(v: unknown): boolean {
  return v !== null && !Array.isArray(v) && typeof v === 'object'
}
function isArray(v: unknown): boolean {
  return Array.isArray(v)
}
function toggleKey(k: string) {
  collapsedKeys[k] = !collapsedKeys[k]
}
function isKeyCollapsed(k: string): boolean {
  return collapsedKeys[k] === true
}
</script>

<style scoped>
.jt-val { font-size: 13px; }
.jt-null { color: var(--color-text-subtle); }
.jt-bool { color: var(--intent-warning-text); }
.jt-num { color: var(--intent-warning-text); }
.jt-str { color: var(--color-text); }
.jt-empty { color: var(--color-text-subtle); font-style: italic; }

.jt-nested { width: 100%; }

.jt-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  font-size: 13px;
  line-height: 1.5;
}

.jt-toggle-row {
  cursor: pointer;
  user-select: none;
  border-radius: 4px;
}
.jt-toggle-row:hover {
  background: var(--color-surface-muted);
}

.jt-arrow {
  font-size: 10px;
  color: var(--color-primary);
  margin-right: 6px;
  width: 12px;
  display: inline-block;
}

.jt-key {
  color: var(--color-primary);
  font-weight: 500;
}

.jt-hint {
  color: var(--color-text-subtle);
  font-size: 11px;
  margin-left: 8px;
}

.jt-label {
  color: var(--color-text-subtle);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.jt-divider {
  border-bottom: 1px solid var(--color-border);
  margin: 0 12px;
}

.jt-indent {
  margin-left: 12px;
  border-left: 3px solid var(--color-border);
  border-radius: 2px;
}
.jt-indent-nested {
  border-left-color: var(--color-primary);
}

.jt-section {
  margin: 2px 0;
}

.jt-card {
  background: var(--color-surface);
  margin: 4px 0;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  overflow: hidden;
}
.jt-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 10px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-surface-muted);
}
.jt-card-body {
  padding: 4px 8px;
}
.jt-card-body .jt-row {
  padding: 4px 8px;
}

.jt-idx {
  color: var(--color-text-subtle);
  font-size: 11px;
  font-weight: 600;
}
</style>
