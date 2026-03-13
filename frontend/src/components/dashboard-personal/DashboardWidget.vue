<template>
  <div ref="widgetRef" class="dashboard-widget" :class="{ 'is-edit-mode': editMode }">
    <!-- 제목바 (편집 모드에서 전체 헤더가 드래그 핸들) -->
    <div class="widget-header" :class="{ 'drag-handle': editMode }">
      <div class="widget-title-area">
        <el-icon v-if="editMode" class="drag-icon"><Rank /></el-icon>
        <el-icon v-else class="widget-type-icon">
          <component :is="typeIcon" />
        </el-icon>
        <span class="widget-title">{{ widget.title }}</span>
      </div>
      <div class="widget-actions export-exclude">
        <template v-if="editMode">
          <el-tooltip content="수정" placement="top">
            <el-button :icon="Edit" circle size="small" @click="$emit('edit', widget)" />
          </el-tooltip>
          <el-popconfirm
            title="이 위젯을 삭제하시겠습니까?"
            confirm-button-text="삭제"
            cancel-button-text="취소"
            :width="240"
            :popper-class="popconfirmClass"
            confirm-button-type="danger"
            @confirm="$emit('delete', widget.widget_id)"
          >
            <template #reference>
              <el-button :icon="Delete" circle size="small" />
            </template>
          </el-popconfirm>
        </template>
        <template v-else>
          <!-- 뷰 전환 토글 (표/차트) -->
          <el-tooltip v-if="canToggleView" :content="viewMode === 'table' ? '차트 보기' : '표 보기'" placement="top">
            <el-button
              :icon="viewMode === 'table' ? toggleChartIcon : Grid"
              circle
              size="small"
              :class="{ 'is-toggled': viewMode === 'table' }"
              @click="toggleViewMode"
            />
          </el-tooltip>
          <!-- 이미지 다운로드 -->
          <el-tooltip content="이미지 저장" placement="top">
            <el-button :icon="Download" circle size="small" :loading="isCapturing" @click="handleCapturePng" />
          </el-tooltip>
          <el-tooltip content="새로고침" placement="top">
            <el-button :icon="Refresh" circle size="small" :loading="isRefreshing" @click="$emit('refresh', widget.widget_id)" />
          </el-tooltip>
        </template>
      </div>
    </div>

    <!-- 콘텐츠 -->
    <div class="widget-content" v-loading="isRefreshing">
      <!-- 표 보기 모드 -->
      <WidgetTable
        v-if="showTable"
        :columns="cachedData.columns"
        :rows="cachedData.rows"
        :row-count="cachedData.row_count"
        :max-height="contentHeight - 20"
        :dark-mode="darkMode"
        :column-aliases="widget.chart_config?.column_aliases"
      />
      <!-- 차트 보기 모드 -->
      <WidgetChart
        v-else-if="showChart"
        :chart-type="effectiveChartType"
        :chart-config="effectiveChartConfig"
        :rows="cachedData.rows"
        :dark-mode="darkMode"
        :color-palette="widget.chart_config?.color_palette"
        :column-aliases="widget.chart_config?.column_aliases"
      />
      <!-- KPI 보기 모드 -->
      <WidgetKpi
        v-else-if="widget.widget_type === 'kpi' && viewMode === 'default'"
        :rows="cachedData.rows"
        :kpi-column="widget.chart_config?.kpi_column"
        :kpi-suffix="widget.chart_config?.kpi_suffix"
        :column-aliases="widget.chart_config?.column_aliases"
      />
    </div>

    <!-- 하단 타임스탬프 -->
    <div v-if="!editMode" class="widget-footer">
      <span class="refresh-time">{{ refreshTimeLabel }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Edit, Delete, Refresh, Rank, DataAnalysis, Grid, PieChart, TrendCharts, Odometer, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { detectColumnTypes } from '@/composables/useChartOptions'
import { captureElementPng, sanitizeFilename, formatTimestamp } from '@/utils/exportUtils'
import WidgetTable from './widgets/WidgetTable.vue'
import WidgetChart from './widgets/WidgetChart.vue'
import WidgetKpi from './widgets/WidgetKpi.vue'

const props = defineProps({
  widget: { type: Object, required: true },
  editMode: { type: Boolean, default: false },
  isRefreshing: { type: Boolean, default: false },
  contentHeight: { type: Number, default: 260 },
  darkMode: { type: Boolean, default: false },
  readOnly: { type: Boolean, default: false }
})

defineEmits(['edit', 'delete', 'refresh'])

const popconfirmClass = computed(() =>
  props.darkMode ? 'widget-delete-popconfirm widget-delete-dark' : 'widget-delete-popconfirm'
)

const widgetRef = ref(null)
const isCapturing = ref(false)
const viewMode = ref('default') // 'default' | 'table'

// 위젯 이미지 다운로드
const handleCapturePng = async () => {
  if (!widgetRef.value) return
  isCapturing.value = true
  try {
    const name = sanitizeFilename(props.widget.title || 'widget')
    const filename = `${name}_${formatTimestamp()}.png`
    await captureElementPng(widgetRef.value, filename)
    ElMessage.success('이미지가 저장되었습니다')
  } catch (err) {
    console.error('[DashboardWidget] 이미지 저장 실패:', err)
    ElMessage.error('이미지 저장에 실패했습니다')
  } finally {
    isCapturing.value = false
  }
}

const cachedData = computed(() => props.widget.cached_data || { columns: [], rows: [], row_count: 0 })

const isChartType = computed(() => ['bar', 'hbar', 'line', 'pie', 'scatter'].includes(props.widget.widget_type))

// 표/차트 토글 가능 여부 (데이터가 있는 모든 위젯)
const canToggleView = computed(() => {
  return cachedData.value.columns.length > 0 && cachedData.value.rows.length > 0
})

// 현재 무엇을 보여줄지 결정
const showTable = computed(() => {
  if (viewMode.value === 'table') return true
  if (props.widget.widget_type === 'table' && viewMode.value === 'default') return true
  return false
})

const showChart = computed(() => {
  if (viewMode.value === 'table') return false
  if (isChartType.value && viewMode.value === 'default') return true
  // table 위젯에서 차트로 전환 시
  if (props.widget.widget_type === 'table' && viewMode.value === 'chart') return true
  return false
})

// table 위젯에서 차트 전환 시 자동 추론
const autoChartConfig = computed(() => {
  if (props.widget.widget_type !== 'table') return null
  const { numeric, text } = detectColumnTypes(cachedData.value.columns, cachedData.value.rows)
  return {
    x_column: text[0] || cachedData.value.columns[0] || '',
    y_columns: numeric.length > 0 ? [numeric[0]] : [cachedData.value.columns[1] || '']
  }
})

const effectiveChartType = computed(() => {
  if (isChartType.value) return props.widget.widget_type
  return 'bar' // table → chart 전환 시 기본 bar
})

const effectiveChartConfig = computed(() => {
  if (isChartType.value) return props.widget.chart_config
  return autoChartConfig.value
})

// 토글 버튼의 차트 아이콘 (원래 위젯 타입에 따라)
const toggleChartIcon = computed(() => {
  const map = { bar: DataAnalysis, hbar: DataAnalysis, line: TrendCharts, pie: PieChart, scatter: DataAnalysis, kpi: Odometer }
  return map[props.widget.widget_type] || DataAnalysis
})

const toggleViewMode = () => {
  if (viewMode.value === 'default') {
    // default → table (차트/KPI를 표로)
    // table 위젯은 default → chart
    viewMode.value = props.widget.widget_type === 'table' ? 'chart' : 'table'
  } else {
    viewMode.value = 'default'
  }
}

const typeIcon = computed(() => {
  const map = { table: Grid, bar: DataAnalysis, hbar: DataAnalysis, line: TrendCharts, pie: PieChart, scatter: DataAnalysis, kpi: Odometer }
  return map[props.widget.widget_type] || DataAnalysis
})

const refreshTimeLabel = computed(() => {
  if (!props.widget.last_refreshed_at) return ''
  const diff = Date.now() - new Date(props.widget.last_refreshed_at).getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return '방금 전'
  if (minutes < 60) return `${minutes}분 전`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}시간 전`
  return new Date(props.widget.last_refreshed_at).toLocaleDateString('ko-KR')
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.dashboard-widget {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--dashboard-card);
  border: 1px solid var(--dashboard-border);
  border-radius: 10px;
  overflow: hidden;
  transition: all 0.2s;
  box-shadow: var(--dashboard-shadow);

  &:hover {
    box-shadow: var(--dashboard-shadow-hover);
  }

  &.is-edit-mode {
    border: 2px dashed var(--dashboard-edit-border);
    cursor: grab;
    box-shadow: var(--dashboard-edit-shadow);

    &:active { cursor: grabbing; }
  }
}

.widget-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--dashboard-border);
  flex-shrink: 0;
  min-height: 44px;

  &.drag-handle {
    cursor: grab;
    user-select: none;
    background: var(--dashboard-edit-bg);

    &:active { cursor: grabbing; }
  }
}

.widget-title-area {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;

  .drag-icon {
    color: var(--dashboard-text-muted);
    font-size: 16px;
    flex-shrink: 0;
  }

  .widget-type-icon {
    color: var(--el-color-primary);
    font-size: 16px;
    flex-shrink: 0;
  }

  .widget-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--dashboard-text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.widget-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;

  .is-toggled {
    color: var(--el-color-primary);
    border-color: var(--el-color-primary);
  }
}

.widget-content {
  flex: 1;
  padding: 10px 14px;
  overflow: hidden;
  min-height: 0;
}

.widget-footer {
  display: flex;
  justify-content: flex-end;
  padding: 4px 14px 8px;
  flex-shrink: 0;

  .refresh-time {
    font-size: 11px;
    color: var(--dashboard-text-muted);
  }
}
</style>

<!-- 전역 스타일: teleported popconfirm은 body에 렌더링되므로 scoped 불가 -->
<style lang="scss">
.widget-delete-popconfirm {
  background: #ffffff !important;
  border: 1px solid #e8ecf1 !important;

  .el-popconfirm__main {
    color: #1d2129;
    font-size: 13px;
    padding-top: 14px;
  }

  .el-popconfirm__action {
    margin-top: 10px;
  }

  .el-popper__arrow::before {
    background: #ffffff !important;
    border-color: #e8ecf1 !important;
  }

  .el-button--default {
    background: #f5f7fa;
    border-color: #dcdfe6;
    color: #606266;

    &:hover {
      background: #ecf5ff;
      border-color: #c6e2ff;
      color: #409eff;
    }
  }

  // 다크모드
  &.widget-delete-dark {
    background: #1f1f1f !important;
    border: 1px solid #555555 !important;

    .el-popconfirm__main {
      color: #e5e5e5;
    }

    .el-popper__arrow::before {
      background: #1f1f1f !important;
      border-color: #555555 !important;
    }

    .el-button--default {
      background: #2c2c2c;
      border-color: #4c4d4f;
      color: #d0d0d0;

      &:hover {
        background: #383838;
        border-color: #606060;
        color: #ffffff;
      }
    }
  }
}
</style>
