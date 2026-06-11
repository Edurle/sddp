<template>
  <div v-if="flow.dslType === 'plain'" class="tc-dsl-plain">
    <div v-if="rawPrecondition" class="tc-dsl-plain-section">
      <div class="tc-phase-label">前置条件</div>
      <pre class="tc-plain-text">{{ rawPrecondition }}</pre>
    </div>
    <div v-if="rawSteps" class="tc-dsl-plain-section">
      <div class="tc-phase-label">步骤</div>
      <pre class="tc-plain-text">{{ rawSteps }}</pre>
    </div>
    <div v-if="rawExpected" class="tc-dsl-plain-section">
      <div class="tc-phase-label">预期结果</div>
      <pre class="tc-plain-text">{{ rawExpected }}</pre>
    </div>
  </div>
  <div v-else class="tc-dsl-flow">
    <div v-if="flow.role" class="tc-flow-role">
      <span class="tc-role-badge">👤 {{ flow.role }}</span>
    </div>

    <div v-if="flow.setup.length" class="tc-flow-phase">
      <div class="tc-phase-label">SETUP</div>
      <div class="tc-phase-items">
        <template v-for="(item, i) in flow.setup" :key="'s' + i">
          <ApiCallCard v-if="item.kind === 'api_call'" :item="item" :index="i" phase="setup" />
          <UiActionCard v-if="item.kind === 'ui_action'" :item="item" :index="i" phase="setup" />
        </template>
      </div>
    </div>

    <div v-if="flow.steps.length" class="tc-flow-phase">
      <div class="tc-phase-label">STEPS</div>
      <div class="tc-phase-items">
        <template v-for="(item, i) in flow.steps" :key="'t' + i">
          <ApiCallCard v-if="item.kind === 'api_call'" :item="item" :index="i" phase="step" />
          <UiActionCard v-if="item.kind === 'ui_action'" :item="item" :index="i" phase="step" />
        </template>
      </div>
    </div>

    <div v-if="flow.asserts.length" class="tc-flow-phase">
      <div class="tc-phase-label">ASSERT</div>
      <div class="tc-phase-items">
        <ResponseAssertCard
          v-for="(item, i) in flow.asserts"
          :key="'a' + i"
          :item="item"
          :dsl-type="flow.dslType"
          :index="i"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { parseTestDsl, type FlowLine } from '@/utils/parseTestDsl'
import ApiCallCard from './dsl/ApiCallCard.vue'
import UiActionCard from './dsl/UiActionCard.vue'
import ResponseAssertCard from './dsl/ResponseAssertCard.vue'

const props = defineProps<{
  caseType: string
  precondition: string | null | undefined
  steps: string | null | undefined
  expectedResult: string | null | undefined
}>()

const flow = computed<FlowLine>(() =>
  parseTestDsl(props.caseType, props.precondition, props.steps, props.expectedResult),
)

const rawPrecondition = computed(() => props.precondition || '')
const rawSteps = computed(() => props.steps || '')
const rawExpected = computed(() => props.expectedResult || '')
</script>

<style scoped>
.tc-dsl-flow {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.tc-dsl-plain {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.tc-dsl-plain-section {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}
.tc-plain-text {
  margin: 0;
  padding: 0.6rem 0.75rem;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  color: #374151;
  background: #fafbfc;
  max-height: 200px;
  overflow-y: auto;
}
.tc-flow-role {
  padding: 0 0 0.25rem;
}
.tc-role-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  background: #f3f4f6;
  padding: 3px 10px;
  border-radius: 12px;
}
.tc-flow-phase {
}
.tc-phase-label {
  font-size: 11px;
  font-weight: 700;
  color: #9ca3af;
  letter-spacing: 1px;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
}
.tc-phase-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
</style>
