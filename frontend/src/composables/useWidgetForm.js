import { ref, reactive, computed, watch } from 'vue'
import { detectColumnTypes, CHART_PALETTES } from '@/composables/useChartOptions'

export { CHART_PALETTES }

export function useWidgetForm(columnsRef, rowsRef) {
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

  const computedAliases = computed(() => {
    const result = {}
    for (const [col, alias] of Object.entries(aliasInputs)) {
      if (alias && alias.trim()) result[col] = alias.trim()
    }
    return Object.keys(result).length > 0 ? result : null
  })

  const columnTypes = computed(() => detectColumnTypes(columnsRef.value, rowsRef.value))
  const numericCols = computed(() => columnTypes.value.numeric.length > 0 ? columnTypes.value.numeric : columnsRef.value)
  const isChartType = computed(() => ['bar', 'hbar', 'line', 'pie', 'scatter'].includes(form.value.widgetType))

  const previewChartConfig = computed(() => ({
    x_column: form.value.xColumn,
    y_columns: Array.isArray(form.value.yColumns) ? form.value.yColumns : [form.value.yColumns],
    pie_top_n: form.value.pieTopN
  }))

  const canPreview = computed(() => {
    if (columnsRef.value.length === 0) return false
    if (form.value.widgetType === 'kpi') return !!form.value.kpiColumn
    if (isChartType.value) {
      const hasY = Array.isArray(form.value.yColumns) ? form.value.yColumns.length > 0 : !!form.value.yColumns
      return !!form.value.xColumn && hasY
    }
    return false
  })

  const isFormValid = computed(() => {
    if (!form.value.title.trim()) return false
    if (form.value.widgetType === 'kpi') return !!form.value.kpiColumn
    if (isChartType.value) {
      const hasY = Array.isArray(form.value.yColumns) ? form.value.yColumns.length > 0 : !!form.value.yColumns
      return !!form.value.xColumn && hasY
    }
    return true
  })

  // widgetType 변경 시 yColumns 형태 조정
  watch(() => form.value.widgetType, (newType) => {
    if (newType === 'pie') {
      if (Array.isArray(form.value.yColumns)) form.value.yColumns = form.value.yColumns[0] || ''
    } else if (['bar', 'hbar', 'line', 'scatter'].includes(newType)) {
      if (!Array.isArray(form.value.yColumns)) form.value.yColumns = form.value.yColumns ? [form.value.yColumns] : []
    }
  })

  /** 외부에서 form 값 초기화 */
  function initForm(config = {}) {
    form.value.title = config.title || ''
    form.value.widgetType = config.widgetType || 'table'
    form.value.xColumn = config.xColumn || ''
    form.value.yColumns = config.yColumns || []
    form.value.pieTopN = config.pieTopN ?? 10
    form.value.kpiColumn = config.kpiColumn || ''
    form.value.kpiSuffix = config.kpiSuffix || ''
    form.value.colorPalette = config.colorPalette || 'default'

    // pie 일 때 yColumns 단일값 보정
    if (form.value.widgetType === 'pie' && Array.isArray(form.value.yColumns)) {
      form.value.yColumns = form.value.yColumns[0] || ''
    }
  }

  /** 별칭 초기화 (columns 변경 시 호출) */
  function initAliases(columns, existingAliases = {}) {
    Object.keys(aliasInputs).forEach(k => delete aliasInputs[k])
    columns.forEach(col => { aliasInputs[col] = existingAliases[col] || '' })
  }

  /** columns/rows 기반으로 차트 초기값 자동 설정 */
  function autoDetectColumns(columns, rows, overrides = {}) {
    const { numeric, text } = detectColumnTypes(columns, rows)
    form.value.xColumn = overrides.xColumn || (text.length > 0 ? text[0] : columns[0] || '')
    if (overrides.yColumns && (Array.isArray(overrides.yColumns) ? overrides.yColumns.length : overrides.yColumns)) {
      form.value.yColumns = overrides.yColumns
    } else {
      form.value.yColumns = numeric.length > 0 ? [numeric[0]] : []
    }
    form.value.kpiColumn = numeric.length > 0 ? numeric[0] : ''
  }

  /** handleSave용 chart_config 객체 조립 */
  function buildChartConfig() {
    return {
      x_column: form.value.xColumn || null,
      y_columns: Array.isArray(form.value.yColumns) ? form.value.yColumns : (form.value.yColumns ? [form.value.yColumns] : null),
      pie_top_n: form.value.widgetType === 'pie' ? form.value.pieTopN : null,
      kpi_column: form.value.widgetType === 'kpi' ? form.value.kpiColumn : null,
      kpi_suffix: form.value.widgetType === 'kpi' ? form.value.kpiSuffix : null,
      color_palette: isChartType.value ? form.value.colorPalette : null,
      column_aliases: computedAliases.value
    }
  }

  return {
    form, aliasInputs, computedAliases,
    columnTypes, numericCols, isChartType,
    previewChartConfig, canPreview, isFormValid,
    initForm, initAliases, autoDetectColumns, buildChartConfig
  }
}
