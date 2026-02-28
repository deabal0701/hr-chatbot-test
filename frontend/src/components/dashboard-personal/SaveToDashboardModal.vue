<template>
  <el-dialog
    v-model="visible"
    title="대시보드에 추가"
    width="620px"
    :close-on-click-modal="false"
    destroy-on-close
    @close="handleClose"
  >
    <el-form label-position="top" :model="form">
      <!-- 대시보드 선택 -->
      <el-form-item v-if="dashboardOptions.length > 1" label="대시보드">
        <el-select v-model="selectedDashboardId" placeholder="저장할 대시보드 선택" style="width: 100%">
          <el-option
            v-for="db in dashboardOptions"
            :key="db.dashboard_id"
            :label="db.name + (db.is_default ? ' (기본)' : '')"
            :value="db.dashboard_id"
          />
        </el-select>
      </el-form-item>

      <!-- 위젯 제목 -->
      <el-form-item label="위젯 제목">
        <el-input v-model="form.title" placeholder="위젯 제목을 입력하세요" maxlength="100" show-word-limit />
      </el-form-item>

      <!-- 위젯 유형 -->
      <el-form-item label="위젯 유형">
        <el-radio-group v-model="form.widgetType">
          <el-radio-button value="table">테이블</el-radio-button>
          <el-radio-button value="bar">Bar</el-radio-button>
          <el-radio-button value="line">Line</el-radio-button>
          <el-radio-button value="pie">Pie</el-radio-button>
          <el-radio-button value="kpi">KPI</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <!-- 차트 설정 (Bar/Line/Pie) -->
      <template v-if="isChartType">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item :label="form.widgetType === 'pie' ? '항목 (Label)' : 'X축 컬럼'">
              <el-select v-model="form.xColumn" placeholder="컬럼 선택" style="width: 100%">
                <el-option v-for="col in columns" :key="col" :label="col" :value="col" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="form.widgetType === 'pie' ? '값 (Value)' : 'Y축 컬럼'">
              <el-select
                v-model="form.yColumns"
                :multiple="form.widgetType !== 'pie'"
                placeholder="컬럼 선택"
                collapse-tags
                style="width: 100%"
              >
                <el-option v-for="col in numericCols" :key="col" :label="col" :value="col" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item v-if="form.widgetType === 'pie'" label="표시 개수">
          <el-select v-model="form.pieTopN" style="width: 160px">
            <el-option label="Top 5" :value="5" />
            <el-option label="Top 10" :value="10" />
            <el-option label="Top 15" :value="15" />
            <el-option label="Top 20" :value="20" />
            <el-option label="전체" :value="0" />
          </el-select>
        </el-form-item>
      </template>

      <!-- KPI 설정 -->
      <template v-if="form.widgetType === 'kpi'">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="값 컬럼">
              <el-select v-model="form.kpiColumn" placeholder="컬럼 선택" style="width: 100%">
                <el-option v-for="col in numericCols" :key="col" :label="col" :value="col" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="단위 접미사">
              <el-input v-model="form.kpiSuffix" placeholder="명, %, 원 등" />
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <!-- 컬럼 표시명 (별칭) -->
      <el-collapse v-if="columns.length > 0" class="alias-collapse">
        <el-collapse-item title="컬럼 표시명 설정" name="aliases">
          <div class="alias-grid">
            <div v-for="col in columns" :key="col" class="alias-row">
              <span class="alias-col-name">{{ col }}</span>
              <el-input v-model="aliasInputs[col]" :placeholder="col" size="small" clearable />
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <!-- 미리보기 -->
      <el-form-item v-if="canPreview" label="미리보기">
        <div class="preview-area">
          <WidgetChart
            v-if="isChartType"
            :chart-type="form.widgetType"
            :chart-config="previewChartConfig"
            :rows="rows"
            :dark-mode="false"
            :color-palette="null"
            :column-aliases="computedAliases"
          />
          <WidgetKpi
            v-else-if="form.widgetType === 'kpi'"
            :rows="rows"
            :kpi-column="form.kpiColumn"
            :kpi-suffix="form.kpiSuffix"
            :column-aliases="computedAliases"
          />
        </div>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">취소</el-button>
      <el-button type="primary" :disabled="!canSave" @click="handleSave">저장</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { detectColumnTypes } from '@/composables/useChartOptions'
import WidgetChart from './widgets/WidgetChart.vue'
import WidgetKpi from './widgets/WidgetKpi.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // 저장할 NL2SQL 결과 데이터
  query: { type: String, default: '' },
  sql: { type: String, default: '' },
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  rowCount: { type: Number, default: 0 },
  // ChartBuilder에서 이미 설정한 값이 있으면 전달
  initialChartType: { type: String, default: '' },
  initialXColumn: { type: String, default: '' },
  initialYColumns: { type: [String, Array], default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'saved'])

const store = useStore()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const dashboardOptions = computed(() => store.state.dashboard.dashboards || [])
const selectedDashboardId = ref(null)

const form = ref({
  title: '',
  widgetType: 'table',
  xColumn: '',
  yColumns: [],
  pieTopN: 10,
  kpiColumn: '',
  kpiSuffix: ''
})

const aliasInputs = reactive({})

// 비어있지 않은 별칭만 추출
const computedAliases = computed(() => {
  const result = {}
  for (const [col, alias] of Object.entries(aliasInputs)) {
    if (alias && alias.trim()) result[col] = alias.trim()
  }
  return Object.keys(result).length > 0 ? result : null
})

// 모달 열릴 때 초기값 설정
watch(visible, (val) => {
  if (val) {
    // 기본 대시보드 선택
    const defaultDb = dashboardOptions.value.find(d => d.is_default)
    selectedDashboardId.value = defaultDb?.dashboard_id || (dashboardOptions.value[0]?.dashboard_id ?? null)

    const { numeric, text } = detectColumnTypes(props.columns, props.rows)
    form.value.title = props.query.slice(0, 100)
    form.value.widgetType = props.initialChartType || 'table'

    // 차트 초기값
    form.value.xColumn = props.initialXColumn || (text.length > 0 ? text[0] : props.columns[0] || '')
    if (props.initialYColumns && (Array.isArray(props.initialYColumns) ? props.initialYColumns.length : props.initialYColumns)) {
      form.value.yColumns = props.initialYColumns
    } else {
      form.value.yColumns = numeric.length > 0 ? [numeric[0]] : []
    }

    // KPI 초기값
    form.value.kpiColumn = numeric.length > 0 ? numeric[0] : ''
    form.value.kpiSuffix = ''

    // 별칭 초기화
    Object.keys(aliasInputs).forEach(k => delete aliasInputs[k])
    props.columns.forEach(col => { aliasInputs[col] = '' })
  }
})

// widgetType 변경 시 yColumns 형태 조정
watch(() => form.value.widgetType, (newType) => {
  if (newType === 'pie') {
    if (Array.isArray(form.value.yColumns)) {
      form.value.yColumns = form.value.yColumns[0] || ''
    }
  } else if (['bar', 'line'].includes(newType)) {
    if (!Array.isArray(form.value.yColumns)) {
      form.value.yColumns = form.value.yColumns ? [form.value.yColumns] : []
    }
  }
})

const columnTypes = computed(() => detectColumnTypes(props.columns, props.rows))
const numericCols = computed(() => columnTypes.value.numeric.length > 0 ? columnTypes.value.numeric : props.columns)

const isChartType = computed(() => ['bar', 'line', 'pie'].includes(form.value.widgetType))

const previewChartConfig = computed(() => ({
  x_column: form.value.xColumn,
  y_columns: Array.isArray(form.value.yColumns) ? form.value.yColumns : [form.value.yColumns],
  pie_top_n: form.value.pieTopN
}))

const canPreview = computed(() => {
  if (form.value.widgetType === 'kpi') return !!form.value.kpiColumn
  if (isChartType.value) {
    const hasY = Array.isArray(form.value.yColumns) ? form.value.yColumns.length > 0 : !!form.value.yColumns
    return !!form.value.xColumn && hasY
  }
  return false
})

const canSave = computed(() => {
  if (!form.value.title.trim()) return false
  if (form.value.widgetType === 'kpi') return !!form.value.kpiColumn
  if (isChartType.value) {
    const hasY = Array.isArray(form.value.yColumns) ? form.value.yColumns.length > 0 : !!form.value.yColumns
    return !!form.value.xColumn && hasY
  }
  return true // table은 항상 가능
})

const handleSave = () => {
  const widgetConfig = {
    dashboard_id: selectedDashboardId.value,
    title: form.value.title.trim(),
    widget_type: form.value.widgetType,
    query: props.query,
    sql: props.sql,
    chart_config: {
      x_column: form.value.xColumn || null,
      y_columns: Array.isArray(form.value.yColumns) ? form.value.yColumns : (form.value.yColumns ? [form.value.yColumns] : null),
      pie_top_n: form.value.widgetType === 'pie' ? form.value.pieTopN : null,
      kpi_column: form.value.widgetType === 'kpi' ? form.value.kpiColumn : null,
      kpi_suffix: form.value.widgetType === 'kpi' ? form.value.kpiSuffix : null,
      column_aliases: computedAliases.value
    },
    cached_data: {
      columns: props.columns,
      rows: props.rows.slice(0, 500),
      row_count: props.rowCount || props.rows.length,
      cached_at: new Date().toISOString()
    }
  }

  store.dispatch('dashboard/saveWidget', widgetConfig)
  ElMessage.success('위젯이 대시보드에 추가되었습니다')
  emit('saved')
  visible.value = false
}

const handleClose = () => {
  visible.value = false
}
</script>

<style lang="scss" scoped>
.alias-collapse {
  margin-bottom: 16px;
  border: none;

  :deep(.el-collapse-item__header) {
    font-size: 13px;
    color: var(--el-text-color-secondary);
    height: 36px;
    line-height: 36px;
  }

  :deep(.el-collapse-item__wrap) {
    border-bottom: none;
  }
}

.alias-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.alias-row {
  display: flex;
  align-items: center;
  gap: 8px;

  .alias-col-name {
    font-size: 12px;
    color: var(--el-text-color-secondary);
    min-width: 80px;
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex-shrink: 0;
  }
}

.preview-area {
  width: 100%;
  height: 280px;
  border: 1px solid var(--border-color-lighter);
  border-radius: 8px;
  overflow: hidden;
}
</style>
