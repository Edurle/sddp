<template>
  <table :data-testid="testId">
    <slot />
  </table>
</template>

<script setup lang="ts">
defineProps<{ testId?: string }>()
</script>

<style scoped>
table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--color-border);
}
th {
  background: rgba(0, 0, 0, 0.03);
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  font-size: var(--text-xs);
  color: var(--color-text-muted);
  border-bottom: 1px solid var(--color-border);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
  font-size: var(--text-sm);
  color: var(--color-text);
}
tr:last-child td {
  border-bottom: none;
}
</style>
