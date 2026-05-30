<template>
  <div class="requirement-detail-page">
    <div v-if="isLoading" class="loading-state">加载中...</div>
    <div v-else-if="req" class="detail-layout">
      <RequirementSidebar
        :req="req"
        :editing="editingReq"
        :edit-form="editForm"
        @edit="startEditReq"
        @save="saveReq"
        @delete="deleteReq"
        @submit-review="openSubmitReviewDialog"
        @approve="approveReview"
        @reject="showRejectDialog = true"
      />

      <div v-if="reviewComments.length > 0" class="review-timeline">
        <h4>审核历史</h4>
        <div v-for="rc in reviewComments" :key="rc.id" class="review-timeline-item">
          <div class="review-timeline-dot" :class="rc.action === 'approve' ? 'dot-approve' : 'dot-reject'"></div>
          <div class="review-timeline-content">
            <div class="review-timeline-header">
              <span class="review-timeline-action" :class="rc.action">{{ rc.action === 'approve' ? '通过' : '拒绝' }}</span>
              <span class="review-timeline-time">{{ formatTime(rc.created_at) }}</span>
            </div>
            <div v-if="rc.comment" class="review-timeline-comment">{{ rc.comment }}</div>
          </div>
        </div>
      </div>

      <div class="detail-main">
        <div class="detail-tabs">
          <button data-testid="req-detail-tab-spec" :class="['tab-btn', { active: activeTab === 'spec' }]" @click="activeTab = 'spec'">规范</button>
          <button data-testid="req-detail-tab-spec-versions" :class="['tab-btn', { active: activeTab === 'spec-versions' }]" @click="activeTab = 'spec-versions'; fetchSpecVersions()">版本历史 ({{ specVersions.length || 0 }})</button>
          <button data-testid="req-detail-tab-tasks" :class="['tab-btn', { active: activeTab === 'tasks' }]" @click="activeTab = 'tasks'; fetchTasks()">任务 ({{ tasks.length || 0 }})</button>
          <button data-testid="req-detail-tab-test-cases" :class="['tab-btn', { active: activeTab === 'test-cases' }]" @click="activeTab = 'test-cases'; fetchTestCases()">测试用例 ({{ testCases.length || 0 }})</button>
        </div>

        <div v-if="activeTab === 'spec'" class="tab-panel">
          <div class="spec-toolbar">
            <span class="spec-hint">{{ hasSectionContent('entity_definition') ? '规范内容预览（由 Agent 填写）' : '暂无规范内容' }}</span>
            <div class="spec-actions">
              <button v-if="req.status === 'drafting_spec'" data-testid="req-detail-btn-submit-spec-review" @click="openSubmitSpecReviewDialog">提交规范审核</button>
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
                        <span v-if="col.primary_key" class="spec-tag" style="background:#eff6ff;color:#3b82f6">PK</span>
                        <span v-if="col.unique" class="spec-tag" style="background:#f0fdf4;color:#22c55e">UNIQUE</span>
                        <span v-if="col.auto_increment" class="spec-tag" style="background:#f3e8ff;color:#6b21a8">自增</span>
                        <code v-if="col.foreign_key" class="spec-fk">→ {{ col.foreign_key }}</code>
                      </td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="tbl.indexes && tbl.indexes.length" class="spec-indexes">
                  <span class="spec-index-label">索引：</span>
                  <span v-for="(idx, ii) in tbl.indexes" :key="ii" class="spec-index-item">
                    <code>{{ idx.name }}</code><span v-if="idx.unique" class="spec-tag" style="background:#fef3c7;color:#92400e;font-size:10px">UNIQUE</span>
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
                      <div class="json-line"><span class="spec-key">code</span>: <span class="spec-val">{{ ep.response.code }}</span></div>
                      <div class="json-line"><span class="spec-key">message</span>: <span class="spec-val">"{{ ep.response.message }}"</span></div>
                      <template v-if="ep.response.data">
                        <div class="json-line"><span class="spec-key">data</span>: <JsonTree :value="ep.response.data" :indent="1" /></div>
                      </template>
                    </div>
                  </div>
                  <div v-if="ep.errors && ep.errors.length" class="spec-sub">
                    <div class="spec-sub-title">错误码</div>
                    <div class="spec-error-row" v-for="(err, erri) in ep.errors" :key="erri">
                      <span class="spec-error-code">{{ err.code }}</span>
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

        <div v-if="activeTab === 'spec-versions'" class="tab-panel">          <div data-testid="req-detail-list-spec-versions" class="version-list">
            <div v-for="(ver, idx) in specVersions" :key="idx" class="version-card" :class="{ selected: selectedVersionContent === getVersionText(ver) }" @click="viewSpecVersion(ver)">
              <div class="version-header">
                <span class="version-num">v{{ ver.version || idx + 1 }}</span>
              </div>
              <div class="version-preview">{{ getVersionText(ver).slice(0, 100) }}{{ getVersionText(ver).length > 100 ? '...' : '' }}</div>
              <button :data-testid="`req-detail-btn-spec-version-${ver.version || idx + 1}`" class="version-view-btn">查看</button>
            </div>
          </div>
          <div v-if="selectedVersionContent" data-testid="req-detail-txt-spec-version-content" class="version-content">
            <template v-if="typeof selectedVersionContent === 'string'"><pre>{{ selectedVersionContent }}</pre></template>
            <JsonTree v-else :value="selectedVersionContent" :indent="1" />
          </div>
        </div>

        <div v-if="activeTab === 'tasks'" class="tab-panel">
          <div class="tab-toolbar">
            <button data-testid="req-detail-btn-add-task" @click="fetchReviewers(); showAddTaskDialog = true">添加任务</button>
          </div>
          <table data-testid="req-detail-tbl-tasks">
            <thead>
              <tr><th>标题</th><th>状态</th></tr>
            </thead>
            <tbody>
              <tr v-for="task in tasks" :key="task.id">
                <td><router-link :to="`/tasks/${task.id}`" class="task-link">{{ task.title }}</router-link></td>
                <td>{{ taskStatusLabel(task.status) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <div v-if="activeTab === 'test-cases'" class="tab-panel">
          <div class="tab-toolbar">
            <button data-testid="req-detail-btn-add-test-case" @click="showTestCaseDialog = true">添加测试用例</button>
            <select data-testid="req-detail-sel-filter-case-type" v-model="testCaseTypeFilter" @change="fetchTestCases">
              <option value="">全部</option>
              <option value="api">API</option>
              <option value="e2e">E2E</option>
            </select>
            <button data-testid="req-detail-btn-submit-tests-review" @click="openSubmitTestsReviewDialog">提交测试审核</button>
          </div>
          <table data-testid="req-detail-tbl-test-cases">
            <thead>
              <tr><th>编号</th><th>标题</th><th>类型</th><th>最新结果</th><th>操作</th></tr>
            </thead>
            <tbody>
              <tr v-for="tc in filteredTestCases" :key="tc.id">
                <td>{{ tc.case_number }}</td>
                <td>
                  <span class="tc-title" @click="viewTestCase = tc">{{ tc.title }}</span>
                </td>
                <td>{{ tc.case_type }}</td>
                <td>
                  <span v-if="tcExecutionMap[tc.id]" class="spec-tag" :style="resultTagStyle(tcExecutionMap[tc.id].status)">{{ tcResultText(tcExecutionMap[tc.id].status) }}</span>
                  <span v-else class="tc-no-result">未执行</span>
                </td>
                <td>
                  <button @click="openTestCaseDetail(tc)">查看</button>
                  <button :data-testid="`req-detail-btn-edit-test-case-${tc.id}`" @click="openEditTestCase(tc)">编辑</button>
                  <button :data-testid="`req-detail-btn-delete-test-case-${tc.id}`" @click="deleteTestCase(tc.id)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>

          <div class="stat-cards" data-testid="req-detail-txt-test-stats">
            <span data-testid="req-detail-tab-test-stats" style="display: none;"></span>
            <div class="stat-card">
              <div class="stat-num">{{ testStats.total_cases ?? 0 }}</div>
              <div class="stat-label">总用例</div>
            </div>
            <div class="stat-card stat-pass">
              <div class="stat-num" data-testid="req-detail-txt-test-pass-count">{{ testStats.latest_results?.passed ?? 0 }}</div>
              <div class="stat-label">通过</div>
            </div>
            <div class="stat-card stat-fail">
              <div class="stat-num" data-testid="req-detail-txt-test-fail-count">{{ testStats.latest_results?.failed ?? 0 }}</div>
              <div class="stat-label">失败</div>
            </div>
            <div class="stat-card stat-skip">
              <div class="stat-num" data-testid="req-detail-txt-test-skip-count">{{ testStats.latest_results?.skipped ?? 0 }}</div>
              <div class="stat-label">跳过</div>
            </div>
            <div class="stat-card stat-rate">
              <div class="stat-num" data-testid="req-detail-txt-test-total-count">{{ testStats.pass_rate != null ? (testStats.pass_rate * 100).toFixed(0) + '%' : 'N/A' }}</div>
              <div class="stat-label">通过率</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showSubmitReviewDialog" class="dialog-overlay" @click.self="showSubmitReviewDialog = false">
      <div data-testid="req-detail-dlg-submit-review" class="dialog">
        <h3>提交审核</h3>
        <div class="custom-select" data-testid="req-detail-dlg-submit-review-sel-reviewer" @click="toggleDropdown('submitReview')">
          <span>{{ getSelectedReviewerName(submitReviewForm.reviewer_id) || '请选择审核人' }}</span>
          <div v-if="dropdownOpen === 'submitReview'" class="dropdown-options">
            <div v-for="m in reviewers" :key="m.id" class="dropdown-option" @click.stop="submitReviewForm.reviewer_id = String(m.id); dropdownOpen = ''">{{ m.nickname || m.email }}</div>
          </div>
        </div>
        <button data-testid="req-detail-dlg-submit-review-btn-confirm" @click="submitReview">确认</button>
        <button @click="showSubmitReviewDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showRejectDialog" class="dialog-overlay" @click.self="showRejectDialog = false">
      <div data-testid="req-detail-dlg-reject" class="dialog">
        <h3>驳回</h3>
        <textarea v-model="rejectForm.comment" data-testid="req-detail-dlg-reject-txtarea-comment"></textarea>
        <button data-testid="req-detail-dlg-reject-btn-confirm" @click="rejectReview">确认</button>
        <button @click="showRejectDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showSubmitSpecReviewDialog" class="dialog-overlay" @click.self="showSubmitSpecReviewDialog = false">
      <div data-testid="req-detail-dlg-submit-spec-review" class="dialog">
        <h3>提交规范审核</h3>
        <div class="custom-select" data-testid="req-detail-dlg-submit-spec-review-sel-reviewer" @click="toggleDropdown('submitSpecReview')">
          <span>{{ getSelectedReviewerName(submitSpecReviewForm.reviewer_id) || '请选择审核人' }}</span>
          <div v-if="dropdownOpen === 'submitSpecReview'" class="dropdown-options">
            <div v-for="m in reviewers" :key="m.id" class="dropdown-option" @click.stop="submitSpecReviewForm.reviewer_id = String(m.id); dropdownOpen = ''">{{ m.nickname || m.email }}</div>
          </div>
        </div>
        <button data-testid="req-detail-dlg-submit-spec-review-btn-confirm" @click="submitSpecReview">确认</button>
        <button @click="showSubmitSpecReviewDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showSubmitTestsReviewDialog" class="dialog-overlay" @click.self="showSubmitTestsReviewDialog = false">
      <div data-testid="req-detail-dlg-submit-tests-review" class="dialog">
        <h3>提交测试审核</h3>
        <div class="custom-select" data-testid="req-detail-dlg-submit-tests-review-sel-reviewer" @click="toggleDropdown('submitTestsReview')">
          <span>{{ getSelectedReviewerName(submitTestsReviewForm.reviewer_id) || '请选择审核人' }}</span>
          <div v-if="dropdownOpen === 'submitTestsReview'" class="dropdown-options">
            <div v-for="m in reviewers" :key="m.id" class="dropdown-option" @click.stop="submitTestsReviewForm.reviewer_id = String(m.id); dropdownOpen = ''">{{ m.nickname || m.email }}</div>
          </div>
        </div>
        <button data-testid="req-detail-dlg-submit-tests-review-btn-confirm" @click="submitTestsReview">确认</button>
        <button @click="showSubmitTestsReviewDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showAddTaskDialog" class="dialog-overlay" @click.self="showAddTaskDialog = false">
      <div data-testid="req-detail-dlg-add-task" class="dialog">
        <h3>添加任务</h3>
        <div class="form-group">
          <label>标题</label>
          <input v-model="addTaskForm.title" data-testid="req-detail-dlg-add-task-inp-title" />
        </div>
        <div class="form-group">
          <label>描述</label>
          <textarea v-model="addTaskForm.description" data-testid="req-detail-dlg-add-task-txtarea-desc"></textarea>
        </div>
        <div class="form-group">
          <label>指派人</label>
          <div class="custom-select" data-testid="req-detail-dlg-add-task-sel-assignee" @click="toggleDropdown('addTask')">
            <span>{{ getSelectedReviewerName(addTaskForm.assignee_id) || '请选择' }}</span>
            <div v-if="dropdownOpen === 'addTask'" class="dropdown-options">
              <div v-for="m in reviewers" :key="m.id" class="dropdown-option" @click.stop="addTaskForm.assignee_id = String(m.id); dropdownOpen = ''">{{ m.nickname || m.email }}</div>
            </div>
          </div>
        </div>
        <button data-testid="req-detail-dlg-add-task-btn-submit" @click="createTask">提交</button>
        <button @click="showAddTaskDialog = false">取消</button>
      </div>
    </div>

    <div v-if="showTestCaseDialog" class="dialog-overlay" @click.self="showTestCaseDialog = false">
      <div data-testid="req-detail-dlg-test-case" class="dialog">
        <h3>{{ editingTestCase ? '编辑测试用例' : '创建测试用例' }}</h3>
        <div class="form-group">
          <label>标题</label>
          <input v-model="testCaseForm.title" data-testid="req-detail-dlg-test-case-inp-title" />
        </div>
        <div class="form-group">
          <label>类型</label>
          <select v-model="testCaseForm.case_type" data-testid="req-detail-dlg-test-case-sel-type">
            <option value="api">API</option>
            <option value="e2e">E2E</option>
          </select>
        </div>
        <div class="form-group">
          <label>前置条件</label>
          <textarea v-model="testCaseForm.precondition" data-testid="req-detail-dlg-test-case-txtarea-precondition"></textarea>
        </div>
        <div class="form-group">
          <label>步骤</label>
          <textarea v-model="testCaseForm.steps" data-testid="req-detail-dlg-test-case-txtarea-steps"></textarea>
        </div>
        <div class="form-group">
          <label>预期结果</label>
          <textarea v-model="testCaseForm.expected_result" data-testid="req-detail-dlg-test-case-txtarea-expected"></textarea>
        </div>
        <div class="form-group">
          <label>关联 API</label>
          <input v-model="testCaseForm.related_api" data-testid="req-detail-dlg-test-case-inp-related-api" />
        </div>
        <button data-testid="req-detail-dlg-test-case-btn-save" @click="saveTestCase">保存</button>
        <button @click="showTestCaseDialog = false">取消</button>
      </div>
    </div>

    <div v-if="viewTestCase" class="dialog-overlay" @click.self="viewTestCase = null">
      <div class="dialog" style="max-width:640px;">
        <h3>测试用例详情</h3>
        <div class="form-group"><label>标题</label><p class="view-field">{{ viewTestCase.title }}</p></div>
        <div class="form-group"><label>类型</label><p class="view-field">{{ viewTestCase.case_type === 'api' ? 'API' : viewTestCase.case_type === 'functional' ? '功能测试' : viewTestCase.case_type }}</p></div>
        <div class="form-group"><label>前置条件</label><p class="view-field">{{ viewTestCase.precondition || '无' }}</p></div>
        <div class="form-group"><label>步骤</label><pre class="view-field">{{ viewTestCase.steps || '无' }}</pre></div>
        <div class="form-group"><label>预期结果</label><pre class="view-field">{{ viewTestCase.expected_result || '无' }}</pre></div>
        <div class="form-group"><label>关联 API</label><p class="view-field">{{ viewTestCase.related_api || '无' }}</p></div>

        <div v-if="tcExecutionMap[viewTestCase.id]" class="form-group">
          <label>执行记录</label>
          <div v-if="tcExecutionMap[viewTestCase.id].all_results && tcExecutionMap[viewTestCase.id].all_results.length" class="tc-exec-records">
            <div v-for="(rec, ri) in tcExecutionMap[viewTestCase.id].all_results" :key="ri" class="tc-exec-item">
              <div class="tc-exec-header">
                <span class="spec-tag" :style="resultTagStyle(rec.status)">{{ tcResultText(rec.status) }}</span>
                <span class="tc-exec-time">{{ rec.executed_at || '' }}</span>
              </div>
              <div v-if="rec.actual_result" class="tc-exec-field"><strong>实际结果：</strong>{{ rec.actual_result }}</div>
              <div v-if="rec.failure_reason" class="tc-exec-field tc-exec-fail"><strong>失败原因：</strong>{{ rec.failure_reason }}</div>
              <div v-if="rec.duration_ms" class="tc-exec-field"><strong>耗时：</strong>{{ rec.duration_ms }}ms</div>
            </div>
          </div>
          <p v-else class="view-field">暂无执行记录</p>
        </div>
        <div v-else class="form-group"><label>执行记录</label><p class="view-field">暂无执行记录</p></div>

        <button @click="viewTestCase = null">关闭</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiClient } from '@/api/client'
import { useNotificationStore } from '@/stores/notification'
import { taskStatusLabel } from '@/utils/status'
import RequirementSidebar from './RequirementSidebar.vue'
import JsonTree from '@/components/JsonTree.vue'

const route = useRoute()
const router = useRouter()
const reqId = computed(() => route.params.id as string)
const notification = useNotificationStore()

interface TypeDetail {
  reproduce_steps?: string
  environment?: string
  severity?: string
  current_issue?: string
  expected_improvement?: string
  metrics?: string
}

interface Review {
  id?: number
  action?: string
  comment?: string
  reviewer_id?: number
  review_type?: string
  status?: string
}

interface RequirementData {
  id: number
  title: string
  type: string
  priority: string | number
  status: string
  description: string
  type_detail?: TypeDetail | null
  prototype_html?: string | null
  reviews?: Review[]
  tasks?: TaskItem[]
  iteration_id?: number
  req_type?: string
}

interface TaskItem {
  id: number
  title: string
  status: string
  description?: string
}

interface Member {
  id: number
  email: string
  nickname?: string
}

interface SpecVersion {
  id?: number
  content?: string
  version?: number
}

interface TestCaseItem {
  id: number
  case_number?: string
  title: string
  case_type: string
  precondition?: string
  steps?: string
  expected_result?: string
  related_api?: string
  requirement_id?: number
}

interface TestStats {
  total_cases?: number
  latest_results?: { passed: number; failed: number; skipped: number; not_executed: number }
  pass_rate?: number
}

const req = ref<RequirementData | null>(null)
const editingReq = ref(false)
const editForm = reactive({ title: '', description: '', prototype_html: '' })
const showSubmitReviewDialog = ref(false)
const showRejectDialog = ref(false)
const showSubmitSpecReviewDialog = ref(false)
const showSubmitTestsReviewDialog = ref(false)
const showAddTaskDialog = ref(false)
const showTestCaseDialog = ref(false)
const viewTestCase = ref<any>(null)
const submitReviewForm = reactive({ reviewer_id: '' })
const submitSpecReviewForm = reactive({ reviewer_id: '' })
const submitTestsReviewForm = reactive({ reviewer_id: '' })
const rejectForm = reactive({ comment: '' })
const addTaskForm = reactive({ title: '', description: '', assignee_id: '' })
const reviewers = ref<Member[]>([])
const activeTab = ref('')
const specSections = ref<any[]>([
  {
    name: "entity_definition", display_name: "实体定义", required: true,
    fields: [
      { name: "description", display_name: "实体描述", type: "text", required: true, description: "对实体的简要描述" },
      { name: "fields", display_name: "字段列表", type: "list", required: true, description: "实体包含的字段定义" },
    ],
  },
  {
    name: "table_design", display_name: "数据表设计", required: true,
    fields: [
      { name: "tables", display_name: "表列表", type: "list", required: true, description: "每个表的表名、字段、类型、索引" },
    ],
  },
  {
    name: "page_structure", display_name: "页面结构", required: true,
    fields: [
      { name: "pages", display_name: "页面列表", type: "list", required: true, description: "页面名称、编码、元素列表" },
    ],
  },
  {
    name: "api_design", display_name: "API 设计", required: true,
    fields: [
      { name: "endpoints", display_name: "接口列表", type: "list", required: true, description: "每个接口的URL、方法、参数" },
    ],
  },
  {
    name: "constraints", display_name: "其他约束", required: false,
    fields: [
      { name: "directory_structure", display_name: "目录结构", type: "text", required: false, description: "项目目录结构规范" },
      { name: "naming_conventions", display_name: "命名规范", type: "text", required: false, description: "编码命名规范" },
      { name: "other", display_name: "其他约束", type: "text", required: false, description: "其他技术约束" },
    ],
  },
])
const specFormData = ref<Record<string, Record<string, any>>>({})
const specRawContent = ref<Record<string, any>>({})
const specVersions = ref<SpecVersion[]>([])
const selectedVersionContent = ref<any>(null)
const tasks = ref<TaskItem[]>([])
const testCases = ref<TestCaseItem[]>([])
const testCaseTypeFilter = ref('')
const editingTestCase = ref<TestCaseItem | null>(null)
const tcExecutionMap = ref<Record<number, { status: string; all_results: Array<{ status: string; actual_result?: string; failure_reason?: string; duration_ms?: number; executed_at?: string }> }>>({})
const testCaseForm = reactive({
  title: '',
  case_type: 'api',
  precondition: '',
  steps: '',
  expected_result: '',
  related_api: '',
})
const testStats = ref<TestStats>({})
const dropdownOpen = ref('')
const isLoading = ref(true)
const reviewComments = ref<Array<{ id: number; reviewer_id: number; action: string; comment: string | null; created_at: string }>>([])

async function fetchReviewComments() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/review-comments`)
    reviewComments.value = res.data?.data || []
  } catch {
    reviewComments.value = []
  }
}

function formatTime(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth() + 1}/${d.getDate()} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`
}

function toggleDropdown(name: string) {
  const willOpen = dropdownOpen.value !== name
  dropdownOpen.value = willOpen ? name : ''
  if (willOpen) {
    fetchReviewers()
  }
}

function getSelectedReviewerName(id: string | number) {
  if (!id) return ''
  const r = reviewers.value.find((m) => String(m.id) === String(id))
  return r?.nickname || r?.email || ''
}

const filteredTestCases = computed(() => {
  if (!testCaseTypeFilter.value) return testCases.value
  return testCases.value.filter((tc) => tc.case_type === testCaseTypeFilter.value)
})

function getVersionText(ver: SpecVersion): any {
  if (ver.content) return ver.content
  return ''
}

function getSpecField(sectionName: string, fieldName: string): any {
  return specRawContent.value[sectionName]?.[fieldName]
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
  const sectionData = specRawContent.value[sectionName]
  if (!sectionData || typeof sectionData !== 'object') return false
  return Object.values(sectionData).some(v => {
    if (v == null) return false
    if (typeof v === 'string') return v.trim().length > 0
    if (Array.isArray(v)) return v.length > 0
    return true
  })
}

const CONSTRAINT_COLORS: Record<string, string> = {
  required: 'background:#fef2f2;color:#ef4444',
  unique: 'background:#f0fdf4;color:#22c55e',
  primary_key: 'background:#eff6ff;color:#3b82f6',
  auto_increment: 'background:#f3e8ff;color:#6b21a8',
}

function constraintStyle(c: string): string {
  return CONSTRAINT_COLORS[c] || 'background:#f3f4f6;color:#666'
}

const METHOD_COLORS: Record<string, string> = {
  GET: 'background:#dcfce7;color:#166534',
  POST: 'background:#dbeafe;color:#1e40af',
  PUT: 'background:#fef3c7;color:#92400e',
  DELETE: 'background:#fee2e2;color:#991b1b',
  PATCH: 'background:#f3e8ff;color:#6b21a8',
}

function methodStyle(m: string): string {
  return METHOD_COLORS[m] || 'background:#f3f4f6;color:#666'
}

function paramInStyle(p: string): string {
  const map: Record<string, string> = {
    query: 'background:#dbeafe;color:#1e40af',
    body: 'background:#fef3c7;color:#92400e',
    path: 'background:#dcfce7;color:#166534',
    header: 'background:#f3e8ff;color:#6b21a8',
  }
  return map[p] || 'background:#f0f0f0;color:#666'
}

function mapReqData(data: any): RequirementData {
  const prioMap: Record<number, string> = { 3: 'high', 2: 'medium', 1: 'low' }
  const prio = data.priority
  const mappedPrio = typeof prio === 'number' ? (prioMap[prio] || prio) : prio
  return {
    ...data,
    type: data.type || data.req_type,
    priority: mappedPrio,
  }
}

async function fetchReq() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}`)
    const data = res.data?.data || res.data
    req.value = mapReqData(data)
    fetchReviewComments()
    if (!activeTab.value) {
      autoSelectTab(req.value.status)
    }
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '获取需求失败')
  }
}

function autoSelectTab(status: string) {
  if (['drafting_tests', 'reviewing_tests'].includes(status)) {
    activeTab.value = 'test-cases'
    fetchTestCases()
  } else if (status === 'approved') {
    activeTab.value = 'tasks'
    fetchTasks()
  } else {
    activeTab.value = 'spec'
  }
}

async function fetchReviewers() {
  try {
    const res = await apiClient.get('/api/v1/users', { params: { page_size: 100 } })
    const data = res.data?.data
    reviewers.value = data?.items || data?.list || data || []
  } catch {
    try {
      const res = await apiClient.get('/api/v1/admin/users')
      const data = res.data?.data
      reviewers.value = data?.items || data?.list || data || []
    } catch {
      reviewers.value = []
    }
  }
}

async function startEditReq() {
  if (req.value) {
    editForm.title = req.value.title
    editForm.description = req.value.description
    editForm.prototype_html = req.value.prototype_html || ''
  }
  editingReq.value = true
}

async function saveReq() {
  try {
    await apiClient.put(`/api/v1/requirements/${reqId.value}`, editForm)
    editingReq.value = false
    await fetchReq()
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '操作失败')
  }
}

async function deleteReq() {
  if (!confirm('确定要删除此需求吗？')) return
  try {
    await apiClient.delete(`/api/v1/requirements/${reqId.value}`)
    if (req.value?.iteration_id) {
      router.push(`/iterations/${req.value.iteration_id}/kanban`)
    } else {
      router.push('/dashboard')
    }
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '删除失败')
  }
}

async function openSubmitReviewDialog() {
  await fetchReviewers()
  showSubmitReviewDialog.value = true
}

async function submitReview() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/submit-review`, {
      reviewer_id: Number(submitReviewForm.reviewer_id),
    })
    showSubmitReviewDialog.value = false
    await fetchReq()
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '提交审核失败')
  }
}

async function approveReview() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/review`, {
      action: 'approve',
    })
    await fetchReq()
    fetchReviewComments()
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '审核操作失败')
  }
}

async function rejectReview() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/review`, {
      action: 'reject',
      comment: rejectForm.comment,
    })
    showRejectDialog.value = false
    rejectForm.comment = ''
    await fetchReq()
    fetchReviewComments()
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '驳回操作失败')
  }
}

function loadSpecContent(content: Record<string, any>) {
  specRawContent.value = content
  for (const section of specSections.value) {
    if (!specFormData.value[section.name]) {
      specFormData.value[section.name] = {}
    }
    const sectionData = content[section.name] || {}
    for (const field of section.fields) {
      let value = sectionData[field.name]
      specFormData.value[section.name][field.name] = value ?? (field.type === 'list' ? [] : '')
    }
  }
}

async function fetchSpecContent() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/specification`)
    const data = res.data?.data
    loadSpecContent(data?.content || {})
  } catch {
    loadSpecContent({})
  }
}

async function openSubmitSpecReviewDialog() {
  await fetchReviewers()
  showSubmitSpecReviewDialog.value = true
}

async function submitSpecReview() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/submit-review`, {
      reviewer_id: Number(submitSpecReviewForm.reviewer_id),
    })
    showSubmitSpecReviewDialog.value = false
    await fetchReq()
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '提交规范审核失败')
  }
}

async function openSubmitTestsReviewDialog() {
  await fetchReviewers()
  showSubmitTestsReviewDialog.value = true
}

async function submitTestsReview() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/submit-review`, {
      reviewer_id: Number(submitTestsReviewForm.reviewer_id),
    })
    showSubmitTestsReviewDialog.value = false
    await fetchReq()
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '提交测试审核失败')
  }
}

async function fetchSpecVersions() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/specification/versions`)
    const data = res.data?.data
    specVersions.value = data?.items || data?.list || data || []
    if (specVersions.value.length > 0 && !selectedVersionContent.value) {
      viewSpecVersion(specVersions.value[specVersions.value.length - 1])
    }
  } catch {
    specVersions.value = []
  }
}

function viewSpecVersion(ver: SpecVersion) {
  selectedVersionContent.value = getVersionText(ver)
}

async function fetchTasks() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/tasks`)
    const data = res.data?.data
    tasks.value = data?.items || data?.list || data || []
  } catch {
    tasks.value = []
  }
}

async function createTask() {
  try {
    await apiClient.post(`/api/v1/requirements/${reqId.value}/tasks`, {
      title: addTaskForm.title,
      description: addTaskForm.description,
      assignee_id: Number(addTaskForm.assignee_id) || undefined,
    })
    showAddTaskDialog.value = false
    addTaskForm.title = ''
    addTaskForm.description = ''
    addTaskForm.assignee_id = ''
    await fetchTasks()
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '操作失败')
  }
}

async function fetchTestCases() {
  try {
    const params: Record<string, unknown> = {}
    if (testCaseTypeFilter.value) params.case_type = testCaseTypeFilter.value
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/test-cases`, { params })
    const data = res.data?.data
    testCases.value = data?.items || data?.list || data || []
    fetchTestCaseExecutions()
  } catch {
    testCases.value = []
  }
}

async function fetchTestCaseExecutions() {
  try {
    const res = await apiClient.get(`/api/v1/test-cases/requirement/${reqId.value}/execution-results`)
    const items = res.data?.data || []
    const map: Record<number, any> = {}
    for (const item of items) {
      map[item.test_case_id] = item
    }
    tcExecutionMap.value = map
  } catch {
    tcExecutionMap.value = {}
  }
}

function tcResultText(status: string) {
  if (status === 'passed') return '通过'
  if (status === 'failed') return '失败'
  if (status === 'skipped') return '跳过'
  return status
}

function resultTagStyle(status: string) {
  if (status === 'passed') return 'background: #dcfce7; color: #166534'
  if (status === 'failed') return 'background: #fee2e2; color: #991b1b'
  if (status === 'skipped') return 'background: #f3f4f6; color: #6b7280'
  return ''
}

function openTestCaseDetail(tc: TestCaseItem) {
  viewTestCase.value = tc
}

function openEditTestCase(tc: TestCaseItem) {
  editingTestCase.value = tc
  testCaseForm.title = tc.title
  testCaseForm.case_type = tc.case_type
  testCaseForm.precondition = tc.precondition || ''
  testCaseForm.steps = tc.steps || ''
  testCaseForm.expected_result = tc.expected_result || ''
  testCaseForm.related_api = tc.related_api || ''
  showTestCaseDialog.value = true
}

async function saveTestCase() {
  try {
    if (editingTestCase.value) {
      await apiClient.put(`/api/v1/test-cases/${editingTestCase.value.id}`, {
        title: testCaseForm.title,
        case_type: testCaseForm.case_type,
        precondition: testCaseForm.precondition,
        steps: testCaseForm.steps,
        expected_result: testCaseForm.expected_result,
        related_api: testCaseForm.related_api,
      })
    } else {
      await apiClient.post(`/api/v1/requirements/${reqId.value}/test-cases`, {
        title: testCaseForm.title,
        case_type: testCaseForm.case_type,
        precondition: testCaseForm.precondition,
        steps: testCaseForm.steps,
        expected_result: testCaseForm.expected_result,
        related_api: testCaseForm.related_api,
      })
    }
    showTestCaseDialog.value = false
    editingTestCase.value = null
    await fetchTestCases()
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '操作失败')
  }
}

async function deleteTestCase(tcId: number) {
  if (!confirm('确定要删除此测试用例吗？')) return
  try {
    await apiClient.delete(`/api/v1/test-cases/${tcId}`)
    await fetchTestCases()
  } catch (e: any) {
    notification.showError(e?.response?.data?.message || e?.message || '删除失败')
  }
}

async function fetchTestStats() {
  try {
    const res = await apiClient.get(`/api/v1/requirements/${reqId.value}/test-statistics`)
    testStats.value = res.data?.data || {}
  } catch {
    testStats.value = {}
  }
}

onMounted(async () => {
  isLoading.value = true
  try {
    await fetchReq()
    await fetchSpecContent()
    await fetchTestStats()
  } finally {
    isLoading.value = false
  }
})
</script>

<style scoped>
.view-field {
  margin: 0;
  padding: 8px 12px;
  background: #f7f8fa;
  border-radius: 6px;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  color: #333;
}
.tc-title {
  cursor: pointer;
  color: #1677ff;
}
.tc-title:hover {
  text-decoration: underline;
}
.tc-no-result {
  color: #9ca3af;
  font-size: 13px;
}
.tc-exec-records {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.25rem;
}
.tc-exec-item {
  padding: 0.5rem 0.75rem;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}
.tc-exec-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}
.tc-exec-time {
  font-size: 12px;
  color: #9ca3af;
}
.tc-exec-field {
  font-size: 13px;
  color: #374151;
  margin-top: 0.25rem;
}
.tc-exec-fail {
  color: #991b1b;
}
.requirement-detail-page {
  min-height: 100vh;
}
.detail-layout {
  display: flex;
  height: 100%;
}
.detail-main {
  flex: 1;
  padding: 1rem 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.detail-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid rgba(0, 0, 0, 0.06);
  margin-bottom: 1rem;
  flex-shrink: 0;
}
.tab-btn {
  padding: 8px 16px;
  font-size: 13px;
  border: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  background: transparent;
  color: #999;
  cursor: pointer;
  font-weight: 500;
  font-family: inherit;
  transition: all 0.2s;
}
.tab-btn:hover {
  color: #333;
}
.tab-btn.active {
  color: #111;
  border-bottom-color: #111;
  font-weight: 600;
}
.tab-panel {
  flex: 1;
}
.tab-toolbar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.75rem;
}
.spec-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: rgba(0, 0, 0, 0.02);
  border-radius: 8px;
  margin-bottom: 0.75rem;
  border: 1px solid rgba(0, 0, 0, 0.04);
}
.spec-hint {
  font-size: 12px;
  color: #999;
}
.save-msg {
  color: #52c41a;
  font-size: 13px;
  font-weight: 500;
}
.spec-actions {
  display: flex;
  gap: 6px;
}
.spec-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
}
.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #111;
  margin: 0 0 0.75rem 0;
}
.required-mark {
  color: #ff4d4f;
  margin-left: 2px;
}
.field-group {
  margin-bottom: 0.75rem;
}
.field-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}
.field-desc {
  font-size: 11px;
  color: #999;
  margin: 0 0 4px 0;
}
.spec-field-textarea {
  width: 100%;
  min-height: 60px;
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 13px;
  line-height: 1.6;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 6px;
  resize: vertical;
}
.spec-field-json {
  width: 100%;
  min-height: 120px;
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.6;
  padding: 0.5rem;
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 6px;
  resize: vertical;
}
.validation-errors {
  margin-bottom: 0.75rem;
  padding: 0.75rem;
  background: #fff2f0;
  border: 1px solid #ffccc7;
  border-radius: 8px;
}
.validation-error-item {
  font-size: 12px;
  color: #ff4d4f;
  margin-bottom: 4px;
}
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
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.version-card:hover {
  border-color: rgba(0, 0, 0, 0.12);
}
.version-card.selected {
  border-color: #1677ff;
  background: rgba(22, 119, 255, 0.04);
}
.version-num {
  font-weight: 600;
  font-size: 14px;
  color: #111;
  min-width: 40px;
}
.version-preview {
  flex: 1;
  font-size: 12px;
  color: #999;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.version-view-btn {
  background: transparent;
  color: #1677ff;
  border: 1px solid #1677ff;
  padding: 2px 10px;
  border-radius: 4px;
  font-size: 11px;
  cursor: pointer;
  margin: 0;
}
.version-content {
  background: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  padding: 1rem;
  font-family: 'SF Mono', 'Menlo', 'Monaco', monospace;
  font-size: 13px;
  line-height: 1.8;
  white-space: pre-wrap;
}
.stat-cards {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
  margin-top: 1rem;
  flex-shrink: 0;
}
.stat-card {
  background: rgba(255, 255, 255, 0.65);
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 10px;
  padding: 0.75rem;
  text-align: center;
}
.stat-num {
  font-size: 20px;
  font-weight: 700;
  color: #111;
}
.stat-label {
  font-size: 11px;
  color: #999;
  margin-top: 2px;
}
.stat-pass .stat-num { color: #52c41a; }
.stat-fail .stat-num { color: #ff4d4f; }
.stat-skip .stat-num { color: #faad14; }
.stat-rate .stat-num { color: #1677ff; }
.task-link {
  color: #1677ff;
  text-decoration: none;
  font-weight: 500;
}
.task-link:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .detail-layout {
    flex-direction: column;
  }
  .detail-main {
    padding: 1rem;
  }
  .stat-cards {
    grid-template-columns: repeat(3, 1fr);
  }
}
.spec-empty {
  text-align: center;
  padding: 3rem 1rem;
  color: #999;
  font-size: 14px;
}
.spec-description {
  color: #555;
  line-height: 1.6;
  margin-bottom: 1rem;
  font-size: 14px;
}
.spec-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.spec-table th {
  background: #f8f9fa;
  text-align: left;
  padding: 10px 12px;
  border-bottom: 2px solid #e5e7eb;
  font-weight: 600;
  color: #555;
  white-space: nowrap;
}
.spec-table td {
  padding: 9px 12px;
  border-bottom: 1px solid #f0f0f0;
  vertical-align: top;
}
.spec-table tr:hover td {
  background: #fafbfc;
}
.spec-table.nested th {
  background: #f0f1f3;
  font-size: 12px;
  padding: 8px 10px;
}
.spec-table.nested td {
  font-size: 12px;
  padding: 8px 10px;
}
.spec-table code,
.spec-card-header code,
.spec-trigger {
  font-family: 'SF Mono', 'Menlo', monospace;
  font-weight: 600;
  color: #111;
  font-size: 12px;
}
.spec-type {
  font-family: 'SF Mono', 'Menlo', monospace;
  color: #4f46e5;
  font-size: 12px;
}
.spec-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
  margin-right: 4px;
  white-space: nowrap;
}
.spec-muted {
  color: #ccc;
}
.spec-fk {
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 11px;
  color: #f59e0b;
  background: #fffbeb;
  padding: 1px 6px;
  border-radius: 3px;
}
.spec-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  margin-bottom: 12px;
  overflow: hidden;
}
.spec-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: #fafbfc;
  border-bottom: 1px solid #e5e7eb;
  flex-wrap: wrap;
}
.spec-card-desc {
  color: #888;
  font-size: 13px;
}
.spec-card-body {
  padding: 16px;
}
.spec-sub {
  margin-bottom: 12px;
}
.spec-sub:last-child {
  margin-bottom: 0;
}
.spec-sub-title {
  font-size: 12px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 8px;
}
.spec-method {
  font-family: monospace;
  font-weight: 700;
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 4px;
  white-space: nowrap;
}
.spec-badge {
  font-size: 12px;
  color: #4f46e5;
  background: #eff6ff;
  padding: 2px 8px;
  border-radius: 4px;
}
.spec-route {
  color: #888;
  font-size: 12px;
}
.spec-response-block {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 10px 12px;
  font-size: 13px;
}
.spec-json-tree {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 12px 14px;
  font-size: 13px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  line-height: 1.6;
}
.spec-json-tree .json-line {
  margin-bottom: 2px;
}
.spec-key {
  color: #4f46e5;
  font-weight: 500;
}
.spec-val {
  color: #333;
}
.spec-error-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 0;
  font-size: 13px;
}
.spec-error-code {
  font-family: monospace;
  font-weight: 700;
  color: #ef4444;
  background: #fef2f2;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.spec-indexes {
  padding: 10px 16px;
  background: #fafbfc;
  border-top: 1px solid #e5e7eb;
  font-size: 12px;
}
.spec-index-label {
  font-weight: 600;
  color: #888;
  margin-right: 4px;
}
.spec-index-item {
  margin-right: 16px;
}
.spec-index-item code {
  color: #4f46e5;
}
.spec-interactions {
  padding: 10px 16px;
  border-top: 1px solid #f0f0f0;
}
.spec-interaction-item {
  display: flex;
  gap: 8px;
  padding: 5px 0;
  font-size: 12px;
  border-bottom: 1px solid #f5f5f5;
}
.spec-interaction-item:last-child {
  border-bottom: none;
}
.spec-trigger {
  color: #f59e0b;
  font-weight: 500;
  white-space: nowrap;
}
.spec-code-block {
  background: #f8f9fa;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px;
  font-family: 'SF Mono', 'Menlo', monospace;
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  color: #333;
  margin: 0;
}
.version-content pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
}
.review-timeline {
  margin-top: 20px;
  border-top: 1px solid rgba(0, 0, 0, 0.06);
  padding-top: 16px;
}
.review-timeline h4 {
  font-size: 13px;
  color: #666;
  margin-bottom: 12px;
}
.review-timeline-item {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}
.review-timeline-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 5px;
  flex-shrink: 0;
}
.dot-approve { background: #22c55e; }
.dot-reject { background: #ef4444; }
.review-timeline-content {
  flex: 1;
  min-width: 0;
}
.review-timeline-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 2px;
}
.review-timeline-action {
  font-size: 12px;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  white-space: nowrap;
}
.review-timeline-action.approve {
  background: #dcfce7;
  color: #166534;
}
.review-timeline-action.reject {
  background: #fef2f2;
  color: #991b1b;
}
.review-timeline-time {
  font-size: 11px;
  color: #aaa;
  white-space: nowrap;
}
.review-timeline-comment {
  font-size: 13px;
  color: #555;
  word-break: break-word;
}
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: #999;
  font-size: 14px;
}
</style>
