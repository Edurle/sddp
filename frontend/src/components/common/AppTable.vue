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
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(0, 0, 0, 0.06);
}
th {
  background: rgba(0, 0, 0, 0.03);
  padding: 10px 14px;
  text-align: left;
  font-weight: 600;
  font-size: 12px;
  color: #666;
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
td {
  padding: 10px 14px;
  text-align: left;
  border-bottom: 1px solid rgba(0, 0, 0, 0.04);
  font-size: 13px;
  color: #333;
}
tr:last-child td {
  border-bottom: none;
}
</style>
