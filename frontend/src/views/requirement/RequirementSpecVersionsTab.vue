<template>
  <div class="tab-panel">
    <div data-testid="req-detail-list-spec-versions" class="version-list">
      <div
        v-for="(ver, idx) in specVersions"
        :key="idx"
        class="version-card"
        :class="{ selected: selectedVersionContent === getVersionContent(ver) }"
        @click="viewSpecVersion(ver)"
      >
        <div class="version-header">
          <span class="version-num">v{{ ver.version || idx + 1 }}</span>
        </div>
        <div class="version-preview">{{ getVersionPreview(ver) }}</div>
        <button :data-testid="`req-detail-btn-spec-version-${ver.version || idx + 1}`" class="version-view-btn">查看</button>
      </div>
    </div>
    <div v-if="selectedVersionContent" data-testid="req-detail-txt-spec-version-content" class="version-content">
      <template v-if="typeof selectedVersionContent === 'string'"><pre>{{ selectedVersionContent }}</pre></template>
      <JsonTree v-else :value="selectedVersionContent" :indent="1" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import JsonTree from '@/components/JsonTree.vue'

interface SpecVersion {
  id?: number
  content?: any
  version?: number
}

const props = defineProps<{ specVersions: SpecVersion[] }>()

const selectedVersionContent = ref<any>(null)

function getVersionContent(ver: SpecVersion): any {
  return ver.content || null
}

function getVersionPreview(ver: SpecVersion): string {
  const content = ver.content
  if (!content) return ''
  const text = typeof content === 'string' ? content : JSON.stringify(content)
  return text.length > 100 ? text.slice(0, 100) + '...' : text
}

function viewSpecVersion(ver: SpecVersion) {
  selectedVersionContent.value = getVersionContent(ver)
}

// Auto-select the latest version once the list arrives.
watch(
  () => props.specVersions,
  (vers) => {
    if (vers.length > 0 && !selectedVersionContent.value) {
      viewSpecVersion(vers[vers.length - 1])
    }
  },
  { immediate: true },
)
</script>

<style scoped>
.version-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.version-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
}
.version-card:hover {
  border-color: var(--color-border-strong);
}
.version-card.selected {
  border-color: var(--color-primary);
  background: var(--color-primary-soft);
}
.version-num {
  font-weight: 600;
  font-size: var(--text-base);
  color: var(--color-text);
  min-width: 40px;
}
.version-preview {
  flex: 1;
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.version-view-btn {
  background: transparent;
  color: var(--color-primary);
  border: 1px solid var(--color-primary);
  padding: 2px 10px;
  border-radius: var(--radius-xs);
  font-size: var(--text-2xs);
  cursor: pointer;
  margin: 0;
}
.version-content {
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 1rem;
  font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
  font-size: var(--text-sm);
  line-height: 1.8;
  white-space: pre-wrap;
}
.version-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
