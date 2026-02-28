<template>
  <el-dialog
    v-model="visible"
    title="위젯 수정"
    width="680px"
    :close-on-click-modal="false"
    destroy-on-close
    @close="handleClose"
  >
    <el-form label-position="top" :model="form">
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
                <el-option v-for="col in currentColumns" :key="col" :label="col" :value="col" />
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
      <el-collapse v-if="currentColumns.length > 0" class="section-collapse">
        <el-collapse-item title="컬럼 표시명 설정" name="aliases">
          <div class="alias-grid">
            <div v-for="col in currentColumns" :key="col" class="alias-row">
              <span class="alias-col-name">{{ col }}</span>
              <el-input v-model="aliasInputs[col]" :placeholder="col" size="small" clearable />
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>

      <!-- 쿼리 정보 + SQL 편집 -->
      <el-collapse class="section-collapse">
        <el-collapse-item title="쿼리 정보 / SQL 편집" name="query-info">
          <div class="query-info">
            <!-- 원본 질문 (읽기 전용) -->
            <div class="query-field">
              <span class="field-label">원본 질문</span>
              <span class="field-value">{{ widget?.query || '(없음)' }}</span>
            </div>
            <!-- SQL 편집 -->
            <div class="query-field">
              <div class="sql-header">
                <span class="field-label">SQL</span>
                <div class="sql-actions">
                  <el-button size="small" :loading="sqlExecuting" @click="handleExecuteSql">
                    SQL 실행
                  </el-button>
                  <el-button size="small" @click="handleResetSql">초기화</el-button>
                </div>
              </div>
              <el-input
                v-model="form.sql"
                type="textarea"
                :rows="4"
                placeholder="SELECT ..."
                class="sql-textarea"
              />
              <div v-if="sqlModified && !sqlExecuted" class="sql-warning">
                SQL이 수정되었습니다. 저장 전 [SQL 실행]으로 결과를 확인하세요.
              </div>
            </div>
            <!-- SQL 실행 결과 미리보기 -->
            <div v-if="previewData" class="query-field">
              <span class="field-label">실행 결과 ({{ previewData.row_count }}행, {{ previewData.execution_time_ms }}ms)</span>
              <div class="preview-table-wrap">
                <el-table :data="previewData.rows.slice(0, 10)" size="small" max-height="200" style="width: 100%">
                  <el-table-column
                    v-for="col in previewData.columns"
                    :key="col"
                    :prop="col"
                    :label="col"
                    :min-width="100"
                    show-overflow-tooltip
                  />
                </el-table>
              </div>
            </div>
          </div>
        </el-collapse-item>
      </el-collapse>
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { detectColumnTypes, CHART_PALETTES } from '@/composables/useChartOptions'
import personalDashboardApi from '@/api/personalDashboard'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  widget: { type: Object, default: null }
})

const emit = defineEmits(['update:modelValue', 'saved'])
const store = useStore()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const form = ref({
  title: '',
  widgetType: 'table',
  xColumn: '',
  yColumns: [],
  pieTopN: 10,
  kpiColumn: '',
  kpiSuffix: '',
  colorPalette: 'default',
  sql: ''
})

const aliasInputs = reactive({})
const originalSql = ref('')
const sqlExecuting = ref(false)
const sqlExecuted = ref(false)
const previewData = ref(null)

// SQL 수정 여부 감지
const sqlModified = computed(() => form.value.sql !== originalSql.value)

// 현재 사용할 columns (SQL 재실행 시 previewData 우선)
const currentColumns = computed(() => {
  if (previewData.value) return previewData.value.columns
  return props.widget?.cached_data?.columns || []
})

const currentRows = computed(() => {
  if (previewData.value) return previewData.value.rows
  return props.widget?.cached_data?.rows || []
})

const columnTypes = computed(() => detectColumnTypes(currentColumns.value, currentRows.value))
const numericCols = computed(() => columnTypes.value.numeric.length > 0 ? columnTypes.value.numeric : currentColumns.value)
const isChartType = computed(() => ['bar', 'hbar', 'line', 'pie', 'scatter'].includes(form.value.widgetType))

// 비어있지 않은 별칭만 추출
const computedAliases = computed(() => {
  const result = {}
  for (const [col, alias] of Object.entries(aliasInputs)) {
    if (alias && alias.trim()) result[col] = alias.trim()
  }
  return Object.keys(result).length > 0 ? result : null
})

// 위젯 데이터로 폼 초기화
watch(visible, (val) => {
  if (val && props.widget) {
    const config = props.widget.chart_config || {}
    form.value.title = props.widget.title
    form.value.widgetType = props.widget.widget_type
    form.value.xColumn = config.x_column || ''
    form.value.yColumns = config.y_columns || []
    form.value.pieTopN = config.pie_top_n ?? 10
    form.value.kpiColumn = config.kpi_column || ''
    form.value.kpiSuffix = config.kpi_suffix || ''
    form.value.colorPalette = config.color_palette || 'default'
    form.value.sql = props.widget.sql || ''
    originalSql.value = props.widget.sql || ''
    sqlExecuted.value = false
    previewData.value = null

    if (form.value.widgetType === 'pie' && Array.isArray(form.value.yColumns)) {
      form.value.yColumns = form.value.yColumns[0] || ''
    }

    // 별칭 초기화
    Object.keys(aliasInputs).forEach(k => delete aliasInputs[k])
    const existingAliases = config.column_aliases || {}
    const cols = props.widget.cached_data?.columns || []
    cols.forEach(col => { aliasInputs[col] = existingAliases[col] || '' })
  }
})

watch(() => form.value.widgetType, (newType) => {
  if (newType === 'pie') {
    if (Array.isArray(form.value.yColumns)) form.value.yColumns = form.value.yColumns[0] || ''
  } else if (['bar', 'hbar', 'line', 'scatter'].includes(newType)) {
    if (!Array.isArray(form.value.yColumns)) form.value.yColumns = form.value.yColumns ? [form.value.yColumns] : []
  }
})

const canSave = computed(() => {
  if (!form.value.title.trim()) return false
  if (form.value.widgetType === 'kpi') return !!form.value.kpiColumn
  if (isChartType.value) {
    const hasY = Array.isArray(form.value.yColumns) ? form.value.yColumns.length > 0 : !!form.value.yColumns
    return !!form.value.xColumn && hasY
  }
  return true
})

// SQL 실행
const handleExecuteSql = async () => {
  if (!form.value.sql.trim()) {
    ElMessage.warning('SQL을 입력하세요')
    return
  }
  sqlExecuting.value = true
  try {
    const result = await personalDashboardApi.executeSql(form.value.sql)
    previewData.value = result
    sqlExecuted.value = true

    // 새 columns로 별칭 교차 검증
    const oldAliases = { ...aliasInputs }
    Object.keys(aliasInputs).forEach(k => delete aliasInputs[k])
    result.columns.forEach(col => {
      aliasInputs[col] = oldAliases[col] || ''
    })

    ElMessage.success(`실행 완료: ${result.row_count}행 (${result.execution_time_ms}ms)`)
  } catch (err) {
    ElMessage.error(err?.message || 'SQL 실행 실패')
  } finally {
    sqlExecuting.value = false
  }
}

// SQL 초기화
const handleResetSql = () => {
  form.value.sql = originalSql.value
  sqlExecuted.value = false
  previewData.value = null
}

const handleSave = async () => {
  // SQL 수정 후 미실행 경고
  if (sqlModified.value && !sqlExecuted.value) {
    try {
      await ElMessageBox.confirm(
        'SQL이 수정되었지만 실행하지 않았습니다. 이전 데이터로 저장하시겠습니까?',
        '확인',
        { confirmButtonText: '저장', cancelButtonText: '취소', type: 'warning' }
      )
    } catch {
      return
    }
  }

  const updates = {
    title: form.value.title.trim(),
    widget_type: form.value.widgetType,
    chart_config: {
      x_column: form.value.xColumn || null,
      y_columns: Array.isArray(form.value.yColumns) ? form.value.yColumns : (form.value.yColumns ? [form.value.yColumns] : null),
      pie_top_n: form.value.widgetType === 'pie' ? form.value.pieTopN : null,
      kpi_column: form.value.widgetType === 'kpi' ? form.value.kpiColumn : null,
      kpi_suffix: form.value.widgetType === 'kpi' ? form.value.kpiSuffix : null,
      color_palette: isChartType.value ? form.value.colorPalette : null,
      column_aliases: computedAliases.value
    }
  }

  // SQL이 변경되었으면 업데이트 포함
  if (sqlModified.value) {
    updates.sql = form.value.sql
  }

  // SQL 재실행으로 새 데이터가 있으면 cached_data도 업데이트
  if (previewData.value) {
    updates.cached_data = {
      columns: previewData.value.columns,
      rows: previewData.value.rows,
      row_count: previewData.value.row_count
    }
  }

  await store.dispatch('dashboard/updateWidget', { widgetId: props.widget.widget_id, updates })
  ElMessage.success('위젯이 수정되었습니다')
  emit('saved')
  visible.value = false
}

const handleClose = () => {
  visible.value = false
}
</script>

<style lang="scss" scoped>
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

.section-collapse {
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

.query-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.query-field {
  .field-label {
    display: block;
    font-size: 12px;
    font-weight: 600;
    color: var(--el-text-color-secondary);
    margin-bottom: 4px;
  }

  .field-value {
    font-size: 13px;
    color: var(--el-text-color-primary);
  }
}

.sql-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.sql-actions {
  display: flex;
  gap: 4px;
}

.sql-textarea {
  :deep(.el-textarea__inner) {
    font-family: 'SF Mono', 'Consolas', monospace;
    font-size: 12px;
  }
}

.sql-warning {
  margin-top: 4px;
  padding: 6px 10px;
  font-size: 12px;
  color: var(--el-color-warning);
  background: var(--el-color-warning-light-9);
  border-radius: 4px;
}

.preview-table-wrap {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  overflow: hidden;
}
</style>
