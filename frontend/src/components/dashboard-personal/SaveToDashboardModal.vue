<template>
  <el-dialog
    v-model="visible"
    title="대시보드에 추가"
    width="620px"
    :close-on-click-modal="false"
    destroy-on-close
    @close="handleClose"
  >
    <!-- 로딩 중 -->
    <div v-if="isLoadingDashboards" class="dashboard-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>대시보드 목록을 불러오는 중...</span>
    </div>

    <!-- 대시보드 없음 안내 -->
    <div v-else-if="noDashboard" class="no-dashboard-notice">
      <el-icon :size="40"><WarningFilled /></el-icon>
      <p>저장할 대시보드가 없습니다.</p>
      <p class="sub-text">대시보드 페이지에서 먼저 대시보드를 생성해주세요.</p>
      <el-button type="primary" @click="goToDashboard">대시보드로 이동</el-button>
    </div>

    <el-form v-else label-position="top" :model="form">
      <!-- 대시보드 선택 -->
      <el-form-item label="대시보드">
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
          <el-radio-button value="hbar">H-Bar</el-radio-button>
          <el-radio-button value="line">Line</el-radio-button>
          <el-radio-button value="pie">Pie</el-radio-button>
          <el-radio-button value="scatter">Scatter</el-radio-button>
          <el-radio-button value="kpi">KPI</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <!-- 차트 설정 (Bar/HBar/Line/Pie/Scatter) -->
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
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item v-if="form.widgetType === 'pie'" label="표시 개수">
              <el-select v-model="form.pieTopN" style="width: 100%">
                <el-option label="Top 5" :value="5" />
                <el-option label="Top 10" :value="10" />
                <el-option label="Top 15" :value="15" />
                <el-option label="Top 20" :value="20" />
                <el-option label="전체" :value="0" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="컬러 팔레트">
              <el-select v-model="form.colorPalette" style="width: 100%">
                <el-option
                  v-for="(palette, key) in CHART_PALETTES"
                  :key="key"
                  :label="palette.label"
                  :value="key"
                >
                  <div class="palette-option">
                    <span>{{ palette.label }}</span>
                    <span class="palette-preview">
                      <span v-for="(c, i) in palette.colors.slice(0, 5)" :key="i" class="palette-dot" :style="{ background: c }" />
                    </span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
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
            :color-palette="form.colorPalette"
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
      <el-button @click="visible = false">{{ noDashboard ? '닫기' : '취소' }}</el-button>
      <el-button v-if="!noDashboard && !isLoadingDashboards" type="primary" :disabled="!canSave" @click="handleSave">저장</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, WarningFilled } from '@element-plus/icons-vue'
import { detectColumnTypes, CHART_PALETTES } from '@/composables/useChartOptions'
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
const router = useRouter()

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
  kpiSuffix: '',
  colorPalette: 'default'
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

const isLoadingDashboards = ref(false)
const noDashboard = computed(() => !isLoadingDashboards.value && dashboardOptions.value.length === 0)

// 대시보드 목록 선택 초기화
function initDashboardSelection() {
  const defaultDb = dashboardOptions.value.find(d => d.is_default)
  selectedDashboardId.value = defaultDb?.dashboard_id || (dashboardOptions.value[0]?.dashboard_id ?? null)
}

// 모달 열릴 때 초기값 설정
watch(visible, async (val) => {
  if (val) {
    // 대시보드 목록이 비어있으면 로드
    if (dashboardOptions.value.length === 0) {
      isLoadingDashboards.value = true
      try {
        await store.dispatch('dashboard/fetchDashboards')
      } finally {
        isLoadingDashboards.value = false
      }
    }
    // 기본 대시보드 선택
    initDashboardSelection()

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
    form.value.colorPalette = 'default'

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
  } else if (['bar', 'hbar', 'line', 'scatter'].includes(newType)) {
    if (!Array.isArray(form.value.yColumns)) {
      form.value.yColumns = form.value.yColumns ? [form.value.yColumns] : []
    }
  }
})

const columnTypes = computed(() => detectColumnTypes(props.columns, props.rows))
const numericCols = computed(() => columnTypes.value.numeric.length > 0 ? columnTypes.value.numeric : props.columns)

const isChartType = computed(() => ['bar', 'hbar', 'line', 'pie', 'scatter'].includes(form.value.widgetType))

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
  if (!selectedDashboardId.value) return false
  if (!form.value.title.trim()) return false
  if (form.value.widgetType === 'kpi') return !!form.value.kpiColumn
  if (isChartType.value) {
    const hasY = Array.isArray(form.value.yColumns) ? form.value.yColumns.length > 0 : !!form.value.yColumns
    return !!form.value.xColumn && hasY
  }
  return true // table은 항상 가능
})

const handleSave = async () => {
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
      color_palette: isChartType.value ? form.value.colorPalette : null,
      column_aliases: computedAliases.value
    },
    cached_data: {
      columns: props.columns,
      rows: props.rows.slice(0, 500),
      row_count: props.rowCount || props.rows.length,
      cached_at: new Date().toISOString()
    }
  }

  try {
    await store.dispatch('dashboard/saveWidget', widgetConfig)
    ElMessage.success('위젯이 대시보드에 추가되었습니다')
    emit('saved')
    visible.value = false
  } catch (err) {
    ElMessage.error('위젯 저장에 실패했습니다')
  }
}

const goToDashboard = () => {
  visible.value = false
  router.push('/dashboard')
}

const handleClose = () => {
  visible.value = false
}
</script>

<style lang="scss" scoped>
.dashboard-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 0;
  color: var(--el-text-color-secondary);
}

.no-dashboard-notice {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 0;
  text-align: center;

  .el-icon {
    color: var(--el-color-warning);
    margin-bottom: 16px;
  }

  p {
    margin: 0 0 4px;
    font-size: 15px;
    font-weight: 500;
    color: var(--el-text-color-primary);
  }

  .sub-text {
    font-size: 13px;
    font-weight: 400;
    color: var(--el-text-color-secondary);
    margin-bottom: 20px;
  }
}

.palette-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.palette-preview {
  display: flex;
  gap: 3px;
}

.palette-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

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
  margin-top: 8px;
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
