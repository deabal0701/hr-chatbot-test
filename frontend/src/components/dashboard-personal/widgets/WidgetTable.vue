<template>
  <div class="widget-table">
    <el-table
      :data="displayRows"
      size="small"
      :max-height="maxHeight"
      :style="{ width: '100%' }"
      :header-cell-style="headerStyle"
      :cell-style="cellStyle"
      :row-style="rowStyle"
    >
      <el-table-column
        v-for="col in columns"
        :key="col"
        :prop="col"
        :label="col"
        :min-width="120"
        :align="isNumericColumn(col) ? 'right' : 'left'"
        show-overflow-tooltip
      >
        <template #default="{ row }">
          <span :class="{ 'numeric-cell': isNumericColumn(col) }">
            {{ formatCell(row[col], col) }}
          </span>
        </template>
      </el-table-column>
    </el-table>
    <div v-if="overflowCount > 0" class="overflow-notice">
      ... 외 {{ overflowCount }}건
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  rowCount: { type: Number, default: 0 },
  maxHeight: { type: Number, default: 280 },
  darkMode: { type: Boolean, default: false }
})

const MAX_DISPLAY = 100

const displayRows = computed(() => props.rows.slice(0, MAX_DISPLAY))
const overflowCount = computed(() => Math.max(0, props.rowCount - MAX_DISPLAY))

// 숫자 컬럼 감지
const numericColumns = computed(() => {
  if (!props.rows.length) return new Set()
  const nums = new Set()
  for (const col of props.columns) {
    const val = props.rows[0][col]
    if (val !== null && val !== undefined && typeof val === 'number') {
      nums.add(col)
    }
  }
  return nums
})

const isNumericColumn = (col) => numericColumns.value.has(col)

const formatCell = (value, col) => {
  if (value === null || value === undefined) return '-'
  if (isNumericColumn(col) && typeof value === 'number') {
    return value.toLocaleString()
  }
  return value
}

// 다크/라이트 모드에 따른 색상 (CSS 변수 대신 직접 지정 - Element Plus 다크모드 충돌 방지)
const colors = computed(() => props.darkMode ? {
  card: '#1f1f1f', stripe: '#262626', headerBg: '#262626',
  textPrimary: '#e5e5e5', textSecondary: '#8c8c8c', border: '#303030'
} : {
  card: '#ffffff', stripe: '#f7f8fa', headerBg: '#f5f7fa',
  textPrimary: '#1d2129', textSecondary: '#86909c', border: '#ebeef5'
})

const headerStyle = computed(() => ({
  backgroundColor: colors.value.headerBg,
  color: colors.value.textSecondary,
  fontSize: '12px',
  fontWeight: '600',
  padding: '8px 12px',
  borderBottom: `1px solid ${colors.value.border}`
}))

const cellStyle = computed(() => ({
  padding: '7px 12px',
  fontSize: '13px',
  color: colors.value.textPrimary,
  backgroundColor: colors.value.card
}))

const rowStyle = computed(() => ({ rowIndex }) => ({
  backgroundColor: rowIndex % 2 === 1 ? colors.value.stripe : colors.value.card
}))
</script>

<style lang="scss" scoped>
.widget-table {
  width: 100%;
  height: 100%;
  overflow: hidden;
  border-radius: 6px;
  border: 1px solid var(--dashboard-border);

  // Element Plus 다크모드(html.dark)를 무시 - 인라인 스타일로 색상 제어
  :deep(.el-table) {
    --el-table-border-color: transparent !important;
    --el-fill-color-lighter: transparent !important;
    --el-table-header-bg-color: transparent !important;
    --el-table-bg-color: transparent !important;
    --el-table-tr-bg-color: transparent !important;
    background-color: transparent !important;

    // 하단 보더라인 제거
    &::before,
    .el-table__inner-wrapper::before,
    .el-table__border-left-patch {
      display: none !important;
    }

    // 행 구분선 연하게
    .el-table__cell {
      border-bottom-color: var(--dashboard-border) !important;
    }

    // 셀 내부 패딩 - show-overflow-tooltip과 호환
    .cell {
      padding: 0 20px 0 12px !important;
    }
  }

  .numeric-cell {
    font-variant-numeric: tabular-nums;
    font-family: 'SF Mono', 'Consolas', monospace;
  }
}

.overflow-notice {
  text-align: center;
  padding: 6px;
  font-size: 11px;
  color: var(--dashboard-text-muted);
  background: var(--dashboard-card);
  border-top: 1px solid var(--dashboard-border);
}
</style>
