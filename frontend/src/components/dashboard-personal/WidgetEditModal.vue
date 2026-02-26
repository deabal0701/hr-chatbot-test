<template>
  <el-dialog
    v-model="visible"
    title="위젯 수정"
    width="620px"
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

      <!-- 쿼리 정보 (접기/펼치기) -->
      <el-collapse>
        <el-collapse-item title="쿼리 정보" name="query-info">
          <div class="query-info">
            <div class="query-field">
              <span class="field-label">원본 질문</span>
              <span class="field-value">{{ widget?.query }}</span>
            </div>
            <div class="query-field">
              <span class="field-label">생성 SQL</span>
              <pre class="sql-code">{{ widget?.sql }}</pre>
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
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { detectColumnTypes, CHART_PALETTES } from '@/composables/useChartOptions'

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
  colorPalette: 'default'
})

const columns = computed(() => props.widget?.cached_data?.columns || [])
const rows = computed(() => props.widget?.cached_data?.rows || [])
const columnTypes = computed(() => detectColumnTypes(columns.value, rows.value))
const numericCols = computed(() => columnTypes.value.numeric.length > 0 ? columnTypes.value.numeric : columns.value)
const isChartType = computed(() => ['bar', 'hbar', 'line', 'pie', 'scatter'].includes(form.value.widgetType))

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

    if (form.value.widgetType === 'pie' && Array.isArray(form.value.yColumns)) {
      form.value.yColumns = form.value.yColumns[0] || ''
    }
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

const handleSave = () => {
  const updates = {
    title: form.value.title.trim(),
    widget_type: form.value.widgetType,
    chart_config: {
      x_column: form.value.xColumn || null,
      y_columns: Array.isArray(form.value.yColumns) ? form.value.yColumns : (form.value.yColumns ? [form.value.yColumns] : null),
      pie_top_n: form.value.widgetType === 'pie' ? form.value.pieTopN : null,
      kpi_column: form.value.widgetType === 'kpi' ? form.value.kpiColumn : null,
      kpi_suffix: form.value.widgetType === 'kpi' ? form.value.kpiSuffix : null,
      color_palette: isChartType.value ? form.value.colorPalette : null
    }
  }

  store.dispatch('dashboard/updateWidget', { widgetId: props.widget.widget_id, updates })
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
    color: var(--text-color-secondary);
    margin-bottom: 4px;
  }

  .field-value {
    font-size: 13px;
    color: var(--text-color-primary);
  }

  .sql-code {
    background: var(--bg-color-page);
    border: 1px solid var(--border-color-lighter);
    border-radius: 6px;
    padding: 10px;
    font-size: 12px;
    color: var(--text-color-primary);
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
  }
}
</style>
