<template>
  <!-- 위젯 제목 -->
  <el-form-item label="위젯 제목">
    <el-input v-model="form.title" placeholder="위젯 제목을 입력하세요" maxlength="100" show-word-limit />
  </el-form-item>

  <!-- 위젯 유형 -->
  <el-form-item label="위젯 유형">
    <el-radio-group v-model="form.widgetType" class="widget-type-group">
      <el-radio-button value="table"><el-icon><Grid /></el-icon> 테이블</el-radio-button>
      <el-radio-button value="bar"><el-icon><DataAnalysis /></el-icon> Bar</el-radio-button>
      <el-radio-button value="hbar"><el-icon><DataAnalysis style="transform: rotate(90deg)" /></el-icon> H-Bar</el-radio-button>
      <el-radio-button value="line"><el-icon><TrendCharts /></el-icon> Line</el-radio-button>
      <el-radio-button value="pie"><el-icon><PieChart /></el-icon> Pie</el-radio-button>
      <el-radio-button value="scatter"><el-icon><DataLine /></el-icon> Scatter</el-radio-button>
      <el-radio-button value="kpi"><el-icon><Odometer /></el-icon> KPI</el-radio-button>
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

  <!-- 테이블 미리보기 -->
  <el-form-item v-if="form.widgetType === 'table' && rows.length > 0" label="실행 결과">
    <div class="preview-table-wrap">
      <el-table :data="rows.slice(0, 5)" size="small" max-height="180" style="width: 100%">
        <el-table-column v-for="col in columns" :key="col" :prop="col" :label="col" :min-width="80" show-overflow-tooltip />
      </el-table>
      <div v-if="rows.length > 5" class="overflow-notice">... 외 {{ rows.length - 5 }}건</div>
    </div>
  </el-form-item>
</template>

<script setup>
import { toRef } from 'vue'
import { Grid, DataAnalysis, TrendCharts, PieChart, DataLine, Odometer } from '@element-plus/icons-vue'
import { useWidgetForm, CHART_PALETTES } from '@/composables/useWidgetForm'
import WidgetChart from './widgets/WidgetChart.vue'
import WidgetKpi from './widgets/WidgetKpi.vue'

const props = defineProps({
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] }
})

const columnsRef = toRef(props, 'columns')
const rowsRef = toRef(props, 'rows')

const {
  form, aliasInputs, computedAliases,
  numericCols, isChartType,
  previewChartConfig, canPreview, isFormValid,
  initForm, initAliases, autoDetectColumns, buildChartConfig
} = useWidgetForm(columnsRef, rowsRef)

defineExpose({
  form, computedAliases, isChartType, isFormValid,
  initForm, initAliases, autoDetectColumns, buildChartConfig
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.widget-type-group {
  :deep(.el-radio-button__inner) {
    display: inline-flex;
    align-items: center;
    gap: 4px;

    .el-icon {
      font-size: 14px;
    }
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
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  overflow: hidden;
}

.preview-table-wrap {
  width: 100%;
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  overflow: hidden;
}

.overflow-notice {
  text-align: center;
  padding: 6px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  border-top: 1px solid var(--el-border-color-lighter);
}
</style>
