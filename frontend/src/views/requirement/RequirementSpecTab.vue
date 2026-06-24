<template>
  <div class="tab-panel">
    <div class="spec-toolbar">
      <span class="spec-hint">{{ hasSectionContent('entity_definition') ? '规范内容预览（由 Agent 填写）' : '暂无规范内容' }}</span>
      <div class="spec-actions">
        <button v-if="status === 'drafting_spec'" data-testid="req-detail-btn-submit-spec-review" @click="$emit('submit-review')">提交规范审核</button>
      </div>
    </div>

    <div v-if="!hasSectionContent('entity_definition')" class="spec-empty">
      <p>该需求尚未编写规范，请通过 Agent 提交规范内容。</p>
    </div>

    <template v-if="hasSectionContent('entity_definition')">
      <div class="spec-section">
        <h3 class="section-title">实体定义</h3>
        <p v-if="getFieldText('entity_definition', 'description')" class="spec-description">{{ getFieldText('entity_definition', 'description') }}</p>
        <table v-if="getFieldList('entity_definition', 'fields').length" class="spec-table">
          <thead><tr><th>字段名</th><th>类型</th><th>描述</th><th>约束</th></tr></thead>
          <tbody>
            <tr v-for="(f, i) in getFieldList('entity_definition', 'fields')" :key="i">
              <td><code>{{ f.name }}</code></td>
              <td><span class="spec-type">{{ f.type }}</span></td>
              <td>{{ f.description || '' }}</td>
              <td>
                <span v-for="c in (f.constraints || [])" :key="c" class="spec-tag" :style="constraintStyle(c)">{{ c }}</span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="hasSectionContent('table_design')" class="spec-section">
        <h3 class="section-title">数据表设计</h3>
        <div v-for="(tbl, ti) in getFieldList('table_design', 'tables')" :key="ti" class="spec-card">
          <div class="spec-card-header">
            <strong>{{ tbl.name }}</strong>
            <span v-if="tbl.description" class="spec-card-desc">— {{ tbl.description }}</span>
          </div>
          <table class="spec-table nested">
            <thead><tr><th>字段</th><th>类型</th><th>可空</th><th>默认</th><th>说明</th><th>属性</th></tr></thead>
            <tbody>
              <tr v-for="(col, ci) in tbl.fields" :key="ci">
                <td><code>{{ col.name }}</code></td>
                <td><span class="spec-type">{{ col.type }}</span></td>
                <td>{{ col.nullable ? 'YES' : 'NO' }}</td>
                <td><code v-if="col.default != null">{{ col.default }}</code><span v-else class="spec-muted">—</span></td>
                <td>{{ col.comment || '' }}</td>
                <td>
                  <span v-if="col.primary_key" class="spec-tag" style="background:var(--intent-info-bg);color:var(--color-primary)">PK</span>
                  <span v-if="col.unique" class="spec-tag" style="background:var(--intent-success-bg);color:var(--intent-success-text)">UNIQUE</span>
                  <span v-if="col.auto_increment" class="spec-tag" style="background:var(--intent-review-bg);color:var(--intent-review-text)">自增</span>
                  <code v-if="col.foreign_key" class="spec-fk">→ {{ col.foreign_key }}</code>
                </td>
              </tr>
            </tbody>
          </table>
          <div v-if="tbl.indexes && tbl.indexes.length" class="spec-indexes">
            <span class="spec-index-label">索引：</span>
            <span v-for="(idx, ii) in tbl.indexes" :key="ii" class="spec-index-item">
              <code>{{ idx.name }}</code><span v-if="idx.unique" class="spec-tag" style="background:var(--intent-warning-bg);color:var(--intent-warning-text);font-size:var(--text-2xs)">UNIQUE</span>
              ({{ (idx.fields || []).join(', ') }})
            </span>
          </div>
        </div>
      </div>

      <div v-if="hasSectionContent('page_structure')" class="spec-section">
        <h3 class="section-title">页面结构</h3>
        <div v-for="(pg, pi) in getFieldList('page_structure', 'pages')" :key="pi" class="spec-card">
          <div class="spec-card-header">
            <strong>{{ pg.name }}</strong>
            <code class="spec-badge">{{ pg.code }}</code>
            <code v-if="pg.route" class="spec-route">{{ pg.route }}</code>
          </div>
          <table class="spec-table nested">
            <thead><tr><th>元素编码</th><th>类型</th><th>标签</th><th>角色</th><th>可访问名称</th><th>交互</th></tr></thead>
            <tbody>
              <tr v-for="(el, ei) in (pg.elements || [])" :key="ei">
                <td><code>{{ el.code }}</code></td>
                <td>{{ el.type }}</td>
                <td>{{ el.label }}</td>
                <td><code v-if="el.role">{{ el.role }}</code><span v-else class="spec-empty">-</span></td>
                <td>{{ el.accessible_name || '-' }}</td>
                <td>{{ el.interaction || '' }}</td>
              </tr>
            </tbody>
          </table>
          <div v-if="pg.interactions && pg.interactions.length" class="spec-interactions">
            <span class="spec-index-label">交互行为：</span>
            <div v-for="(ia, ii) in pg.interactions" :key="ii" class="spec-interaction-item">
              <code class="spec-trigger">{{ ia.trigger }}</code>
              <span>{{ ia.behavior }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-if="hasSectionContent('api_design')" class="spec-section">
        <h3 class="section-title">API 设计</h3>
        <div v-for="(ep, ei) in getFieldList('api_design', 'endpoints')" :key="ei" class="spec-card">
          <div class="spec-card-header">
            <span class="spec-method" :style="methodStyle(ep.method)">{{ ep.method }}</span>
            <code>{{ ep.path }}</code>
            <span class="spec-card-desc">— {{ ep.description }}</span>
          </div>
          <div class="spec-card-body">
            <div v-if="ep.request_params && ep.request_params.length" class="spec-sub">
              <div class="spec-sub-title">请求参数</div>
              <table class="spec-table nested">
                <thead><tr><th>参数</th><th>位置</th><th>类型</th><th>必填</th><th>说明</th></tr></thead>
                <tbody>
                  <tr v-for="(p, pi2) in ep.request_params" :key="pi2">
                    <td><code>{{ p.name }}</code></td>
                    <td><span class="spec-tag" :style="paramInStyle(p.in)">{{ p.in }}</span></td>
                    <td><span class="spec-type">{{ p.type }}</span></td>
                    <td>{{ p.required ? '是' : '否' }}</td>
                    <td>{{ p.description || '' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="ep.response" class="spec-sub">
              <div class="spec-sub-title">响应</div>
              <div class="spec-json-tree">
                <div class="json-line"><span class="spec-key">code</span>: <span class="spec-val">{{ ep.response.status_code ?? ep.response.code }}</span></div>
                <div class="json-line"><span class="spec-key">message</span>: <span class="spec-val">"{{ ep.response.message }}"</span></div>
                <template v-if="ep.response.data">
                  <div class="json-line"><span class="spec-key">data</span>: <JsonTree :value="ep.response.data" :indent="1" /></div>
                </template>
              </div>
            </div>
            <div v-if="ep.errors && ep.errors.length" class="spec-sub">
              <div class="spec-sub-title">错误码</div>
              <div class="spec-error-row" v-for="(err, erri) in ep.errors" :key="erri">
                <span class="spec-error-code">{{ err.status_code ?? err.code }}</span>
                <span>{{ err.message }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="hasSectionContent('constraints')" class="spec-section">
        <h3 class="section-title">其他约束</h3>
        <div v-if="getFieldText('constraints', 'directory_structure')" class="spec-sub">
          <div class="spec-sub-title">目录结构</div>
          <pre class="spec-code-block">{{ getFieldText('constraints', 'directory_structure') }}</pre>
        </div>
        <div v-if="getFieldText('constraints', 'naming_conventions')" class="spec-sub">
          <div class="spec-sub-title">命名规范</div>
          <pre class="spec-code-block">{{ getFieldText('constraints', 'naming_conventions') }}</pre>
        </div>
        <div v-if="getFieldText('constraints', 'other')" class="spec-sub">
          <div class="spec-sub-title">其他约束</div>
          <pre class="spec-code-block">{{ getFieldText('constraints', 'other') }}</pre>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import JsonTree from '@/components/JsonTree.vue'

const props = defineProps<{ specRawContent: Record<string, any>; status: string }>()
defineEmits<{ 'submit-review': [] }>()

function getSpecField(sectionName: string, fieldName: string): any {
  return props.specRawContent[sectionName]?.[fieldName]
}

function getFieldList(sectionName: string, fieldName: string): any[] {
  const val = getSpecField(sectionName, fieldName)
  if (Array.isArray(val)) return val
  if (typeof val === 'string') {
    try { return JSON.parse(val) } catch { return [] }
  }
  return []
}

function getFieldText(sectionName: string, fieldName: string): string {
  const val = getSpecField(sectionName, fieldName)
  if (typeof val === 'string') return val
  return ''
}

function hasSectionContent(sectionName: string): boolean {
  const sectionData = props.specRawContent[sectionName]
  if (!sectionData || typeof sectionData !== 'object') return false
  return Object.values(sectionData).some(v => {
    if (v == null) return false
    if (typeof v === 'string') return v.trim().length > 0
    if (Array.isArray(v)) return v.length > 0
    return true
  })
}

const CONSTRAINT_COLORS: Record<string, string> = {
  required: 'background:var(--intent-danger-bg);color:var(--color-danger)',
  unique: 'background:var(--intent-success-bg);color:var(--intent-success-text)',
  primary_key: 'background:var(--intent-info-bg);color:var(--color-primary)',
  auto_increment: 'background:var(--intent-review-bg);color:var(--intent-review-text)',
}

function constraintStyle(c: string): string {
  return CONSTRAINT_COLORS[c] || 'background:var(--color-surface-muted);color:var(--color-text-muted)'
}

const METHOD_COLORS: Record<string, string> = {
  GET: 'background:var(--intent-success-bg);color:var(--intent-success-text)',
  POST: 'background:var(--intent-info-bg);color:var(--intent-info-text)',
  PUT: 'background:var(--intent-warning-bg);color:var(--intent-warning-text)',
  DELETE: 'background:var(--intent-danger-bg);color:var(--intent-danger-text)',
  PATCH: 'background:var(--intent-review-bg);color:var(--intent-review-text)',
}

function methodStyle(m: string): string {
  return METHOD_COLORS[m] || 'background:var(--color-surface-muted);color:var(--color-text-muted)'
}

function paramInStyle(p: string): string {
  const map: Record<string, string> = {
    query: 'background:var(--intent-info-bg);color:var(--intent-info-text)',
    body: 'background:var(--intent-warning-bg);color:var(--intent-warning-text)',
    path: 'background:var(--intent-success-bg);color:var(--intent-success-text)',
    header: 'background:var(--intent-review-bg);color:var(--intent-review-text)',
  }
  return map[p] || 'background:var(--color-surface-muted);color:var(--color-text-muted)'
}
</script>

<style scoped>
.tab-panel {
  flex: 1;
}
.spec-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: rgba(0, 0, 0, 0.02);
  border-radius: var(--radius-md);
  margin-bottom: 0.75rem;
  border: 1px solid var(--color-border);
}
.spec-hint {
  font-size: var(--text-xs);
  color: var(--color-text-subtle);
}
.spec-actions {
  display: flex;
  gap: 6px;
}
.spec-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--color-text-subtle);
  font-size: var(--text-base);
}
.spec-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
}
.section-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 0.75rem 0;
}
.spec-description {
  color: var(--color-text-muted);
  line-height: 1.6;
  margin-bottom: 1rem;
  font-size: var(--text-base);
}
.spec-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--text-sm);
}
.spec-table th {
  background: var(--color-surface-muted);
  text-align: left;
  padding: 10px 12px;
  border-bottom: 2px solid var(--color-border);
  font-weight: 600;
  color: var(--color-text-muted);
  white-space: nowrap;
}
.spec-table td {
  padding: 9px 12px;
  border-bottom: 1px solid var(--color-border);
  vertical-align: top;
}
.spec-table tr:hover td {
  background: var(--color-surface-muted);
}
.spec-table.nested th {
  background: var(--color-surface-muted);
  font-size: var(--text-xs);
  padding: 8px 10px;
}
.spec-table.nested td {
  font-size: var(--text-xs);
  padding: 8px 10px;
}
.spec-table code,
.spec-card-header code,
.spec-trigger {
  font-family: 'SF Mono', 'Menlo', monospace;
  font-weight: 600;
  color: var(--color-text);
  font-size: var(--text-xs);
}
.spec-type {
  font-family: 'SF Mono', 'Menlo', monospace;
  color: var(--color-primary);
  font-size: var(--text-xs);
}
.spec-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: var(--radius-md);
  font-size: var(--text-2xs);
  font-weight: 500;
  margin-right: var(--space-1);
  white-space: nowrap;
}
.spec-muted {
  color: var(--color-text-subtle);
}
.spec-fk {
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: var(--text-2xs);
  color: var(--intent-warning-text);
  background: var(--intent-warning-bg);
  padding: 1px 6px;
  border-radius: var(--radius-xs);
}
.spec-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: var(--space-3);
  overflow: hidden;
}
.spec-card-header {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 12px 16px;
  background: var(--color-surface-muted);
  border-bottom: 1px solid var(--color-border);
  flex-wrap: wrap;
}
.spec-card-desc {
  color: var(--color-text-subtle);
  font-size: var(--text-sm);
}
.spec-card-body {
  padding: var(--space-4);
}
.spec-sub {
  margin-bottom: var(--space-3);
}
.spec-sub:last-child {
  margin-bottom: 0;
}
.spec-sub-title {
  font-size: var(--text-xs);
  font-weight: 600;
  color: var(--color-text-subtle);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--space-2);
}
.spec-method {
  font-family: monospace;
  font-weight: 700;
  font-size: var(--text-xs);
  padding: 3px 10px;
  border-radius: var(--radius-xs);
  white-space: nowrap;
}
.spec-badge {
  font-size: var(--text-xs);
  color: var(--color-primary);
  background: var(--intent-info-bg);
  padding: 2px 8px;
  border-radius: var(--radius-xs);
}
.spec-route {
  color: var(--color-text-subtle);
  font-size: var(--text-xs);
}
.spec-json-tree {
  background: var(--color-surface-muted);
  border-radius: var(--radius-sm);
  padding: 12px 14px;
  font-size: var(--text-sm);
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  line-height: 1.6;
}
.spec-json-tree .json-line {
  margin-bottom: 2px;
}
.spec-key {
  color: var(--color-primary);
  font-weight: 500;
}
.spec-val {
  color: var(--color-text);
}
.spec-error-row {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: 5px 0;
  font-size: var(--text-sm);
}
.spec-error-code {
  font-family: monospace;
  font-weight: 700;
  color: var(--color-danger);
  background: var(--intent-danger-bg);
  padding: 2px 8px;
  border-radius: var(--radius-xs);
  font-size: var(--text-xs);
}
.spec-indexes {
  padding: 10px 16px;
  background: var(--color-surface-muted);
  border-top: 1px solid var(--color-border);
  font-size: var(--text-xs);
}
.spec-index-label {
  font-weight: 600;
  color: var(--color-text-subtle);
  margin-right: var(--space-1);
}
.spec-index-item {
  margin-right: var(--space-4);
}
.spec-index-item code {
  color: var(--color-primary);
}
.spec-interactions {
  padding: 10px 16px;
  border-top: 1px solid var(--color-border);
}
.spec-interaction-item {
  display: flex;
  gap: var(--space-2);
  padding: 5px 0;
  font-size: var(--text-xs);
  border-bottom: 1px solid var(--color-border);
}
.spec-interaction-item:last-child {
  border-bottom: none;
}
.spec-trigger {
  color: var(--intent-warning-text);
  font-weight: 500;
  white-space: nowrap;
}
.spec-code-block {
  background: var(--color-surface-muted);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: var(--text-xs);
  line-height: 1.6;
  white-space: pre-wrap;
  color: var(--color-text);
  margin: 0;
}
</style>
