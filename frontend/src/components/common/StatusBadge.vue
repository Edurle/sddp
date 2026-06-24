<template>
  <span
    v-if="variant === 'dot'"
    :data-testid="testId"
    class="status-dot"
    :class="`intent-${intent}`"
    :title="label"
  />
  <span
    v-else
    :data-testid="testId"
    class="status-badge"
    :class="[`intent-${intent}`, { 'is-strike': strike }]"
  >{{ label }}</span>
</template>

<script setup lang="ts">
import type { BadgeIntent } from '@/utils/status'

withDefaults(
  defineProps<{
    /** Semantic colour intent (maps to --intent-* tokens). */
    intent: BadgeIntent
    /** Pill text. Not used by the dot variant. */
    label?: string
    /** 'pill' (default) renders a coloured pill; 'dot' renders a small circle. */
    variant?: 'pill' | 'dot'
    /** Strike-through, e.g. deprecated items. */
    strike?: boolean
    testId?: string
  }>(),
  { variant: 'pill', label: '', strike: false },
)
</script>

<style scoped>
.status-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: var(--radius-pill);
  font-size: var(--text-xs);
  font-weight: var(--font-medium);
  line-height: 1.5;
  letter-spacing: 0.01em;
  white-space: nowrap;
}
.status-badge.is-strike {
  text-decoration: line-through;
}
.status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Pill colours */
.status-badge.intent-neutral { background: var(--intent-neutral-bg); color: var(--intent-neutral-text); }
.status-badge.intent-info    { background: var(--intent-info-bg);    color: var(--intent-info-text); }
.status-badge.intent-review  { background: var(--intent-review-bg);  color: var(--intent-review-text); }
.status-badge.intent-success { background: var(--intent-success-bg); color: var(--intent-success-text); }
.status-badge.intent-warning { background: var(--intent-warning-bg); color: var(--intent-warning-text); }
.status-badge.intent-danger  { background: var(--intent-danger-bg);  color: var(--intent-danger-text); }

/* Dot colours (solid) */
.status-dot.intent-neutral { background: var(--intent-neutral-solid); }
.status-dot.intent-info    { background: var(--intent-info-solid); }
.status-dot.intent-review  { background: var(--intent-review-solid); }
.status-dot.intent-success { background: var(--intent-success-solid); }
.status-dot.intent-warning { background: var(--intent-warning-solid); }
.status-dot.intent-danger  { background: var(--intent-danger-solid); }
</style>
