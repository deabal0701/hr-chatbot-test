<template>
  <div class="widget-kpi">
    <div class="kpi-value">{{ formattedValue }}</div>
    <div v-if="suffix" class="kpi-suffix">{{ suffix }}</div>
    <div class="kpi-column-name">{{ columnName }}</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  rows: { type: Array, default: () => [] },
  kpiColumn: { type: String, default: '' },
  kpiSuffix: { type: String, default: '' },
  columnAliases: { type: Object, default: null }
})

const rawValue = computed(() => {
  if (!props.rows.length) return 0
  const row = props.rows[0]
  if (props.kpiColumn && row[props.kpiColumn] !== undefined) {
    return Number(row[props.kpiColumn]) || 0
  }
  // kpiColumn 미지정 시 첫 번째 숫자 값
  for (const key of Object.keys(row)) {
    const val = row[key]
    if (val !== null && val !== undefined && !isNaN(Number(val))) {
      return Number(val)
    }
  }
  return 0
})

const columnName = computed(() => {
  const raw = props.kpiColumn || (props.rows.length ? Object.keys(props.rows[0])[0] : '')
  return props.columnAliases?.[raw] || raw
})

const suffix = computed(() => props.kpiSuffix || '')

const formattedValue = computed(() => {
  const v = rawValue.value
  return v.toLocaleString()
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.widget-kpi {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  gap: 4px;
}

.kpi-value {
  font-size: 42px;
  font-weight: 700;
  color: var(--dashboard-text-primary);
  line-height: 1.1;
}

.kpi-suffix {
  font-size: 18px;
  font-weight: 500;
  color: var(--dashboard-text-secondary);
}

.kpi-column-name {
  font-size: 12px;
  color: var(--dashboard-text-muted);
  margin-top: 4px;
}
</style>
