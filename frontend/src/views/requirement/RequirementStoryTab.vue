<template>
  <div class="tab-panel">
    <div v-if="description" class="markdown-body" v-html="renderedDescription"></div>
    <EmptyState v-else text="暂无需求描述" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import EmptyState from '@/components/common/EmptyState.vue'

const props = defineProps<{ description?: string }>()

const renderedDescription = computed(() => {
  if (!props.description) return ''
  return marked.parse(props.description, { breaks: true })
})
</script>

<style scoped>
.markdown-body {
  font-size: var(--text-base);
  line-height: 1.75;
  color: var(--color-text);
  max-width: 800px;
}
.markdown-body h1,
.markdown-body h2,
.markdown-body h3,
.markdown-body h4 {
  color: var(--color-text);
  margin: 1.5em 0 0.75em;
  font-weight: 600;
}
.markdown-body h1 { font-size: 1.5em; }
.markdown-body h2 { font-size: 1.3em; }
.markdown-body h3 { font-size: 1.15em; }
.markdown-body h4 { font-size: 1em; }
.markdown-body p {
  margin: 0.75em 0;
}
.markdown-body ul,
.markdown-body ol {
  padding-left: 1.5em;
  margin: 0.75em 0;
}
.markdown-body li {
  margin-bottom: 0.35em;
}
.markdown-body code {
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 0.9em;
  background: var(--color-surface-muted);
  padding: 2px 6px;
  border-radius: var(--radius-xs);
  color: var(--color-code);
}
.markdown-body pre {
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 1em;
  overflow-x: auto;
  margin: 1em 0;
}
.markdown-body pre code {
  background: none;
  padding: 0;
  color: var(--color-text);
  font-size: var(--text-sm);
  line-height: 1.6;
}
.markdown-body blockquote {
  border-left: 4px solid var(--color-border);
  margin: 1em 0;
  padding: 0.5em 1em;
  color: var(--color-text-muted);
  background: var(--color-surface-muted);
  border-radius: 0 6px 6px 0;
}
.markdown-body a {
  color: var(--color-primary);
  text-decoration: none;
}
.markdown-body a:hover {
  text-decoration: underline;
}
.markdown-body strong {
  font-weight: 600;
  color: var(--color-text);
}
.markdown-body hr {
  border: none;
  border-top: 1px solid var(--color-border);
  margin: 1.5em 0;
}
.markdown-body table {
  width: 100%;
  border-collapse: collapse;
  margin: 1em 0;
  font-size: var(--text-sm);
}
.markdown-body th,
.markdown-body td {
  border: 1px solid var(--color-border);
  padding: 8px 12px;
  text-align: left;
}
.markdown-body th {
  background: var(--color-surface-muted);
  font-weight: 600;
}
.markdown-body img {
  max-width: 100%;
  border-radius: var(--radius-sm);
}
</style>
