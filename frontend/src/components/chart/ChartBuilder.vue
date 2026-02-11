<template>
  <div class="chart-builder">
    <!-- 차트 생성 토글 버튼 -->
    <button class="chart-toggle-btn" @click="showConfig = !showConfig">
      <el-icon><TrendCharts /></el-icon>
      <span>차트 생성</span>
      <el-icon class="toggle-arrow" :class="{ expanded: showConfig }">
        <ArrowDown />
      </el-icon>
    </button>

    <!-- 차트 설정 패널 -->
    <div v-show="showConfig" class="chart-config">
      <div class="config-row">
        <!-- 차트 유형 -->
        <div class="config-item">
          <span class="config-label">차트 유형</span>
          <el-radio-group v-model="chartType" size="small">
            <el-radio-button value="bar">Bar</el-radio-button>
            <el-radio-button value="line">Line</el-radio-button>
            <el-radio-button value="pie">Pie</el-radio-button>
          </el-radio-group>
        </div>

        <!-- X축 컬럼 -->
        <div class="config-item">
          <span class="config-label">{{ chartType === 'pie' ? '항목 (Label)' : 'X축 컬럼' }}</span>
          <el-select v-model="xAxisColumn" size="small" placeholder="컬럼 선택" style="min-width: 180px;">
            <el-option
              v-for="col in columns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>

        <!-- Y축 컬럼 -->
        <div class="config-item">
          <span class="config-label">{{ chartType === 'pie' ? '값 (Value)' : 'Y축 컬럼' }}</span>
          <el-select
            v-model="yAxisColumns"
            size="small"
            :multiple="chartType !== 'pie'"
            :placeholder="chartType === 'pie' ? '컬럼 선택' : '컬럼 선택 (복수)'"
            collapse-tags
            style="min-width: 180px;"
          >
            <el-option
              v-for="col in numericColumns"
              :key="col"
              :label="col"
              :value="col"
            />
          </el-select>
        </div>

        <!-- Pie: 상위 N개 표시 -->
        <div v-if="chartType === 'pie'" class="config-item">
          <span class="config-label">표시 개수</span>
          <el-select v-model="pieTopN" size="small" style="min-width: 100px;">
            <el-option label="Top 5" :value="5" />
            <el-option label="Top 10" :value="10" />
            <el-option label="Top 15" :value="15" />
            <el-option label="Top 20" :value="20" />
            <el-option label="전체" :value="0" />
          </el-select>
        </div>

        <!-- 차트 생성 버튼 -->
        <div class="config-item config-action">
          <el-button type="primary" size="small" @click="generateChart" :disabled="!canGenerate">
            생성
          </el-button>
        </div>
      </div>
    </div>

    <!-- 차트 렌더링 영역 -->
    <div v-if="chartGenerated" class="chart-area" :class="{ 'white-bg': whiteBg }">
      <button class="bg-toggle-btn" :title="whiteBg ? '다크 배경' : '흰색 배경'" @click="toggleBg">
        <el-icon><Sunny v-if="whiteBg" /><Moon v-else /></el-icon>
      </button>
      <v-chart :option="chartOption" autoresize class="chart-canvas" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { TrendCharts, ArrowDown, Sunny, Moon } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
} from 'echarts/components'

// ECharts 모듈 등록
use([
  CanvasRenderer,
  BarChart,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
])

const props = defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, required: true }
})

const showConfig = ref(false)
const chartType = ref('bar')
const xAxisColumn = ref('')
const yAxisColumns = ref([])
const chartGenerated = ref(false)
const pieTopN = ref(10)
const whiteBg = ref(false)

const toggleBg = () => {
  whiteBg.value = !whiteBg.value
  if (chartGenerated.value) generateChart()
}

// 숫자 컬럼 자동 감지
const columnTypes = computed(() => {
  if (!props.rows || props.rows.length === 0) return { numeric: [], text: [] }

  const sampleSize = Math.min(props.rows.length, 10)
  const numeric = []
  const text = []

  for (const col of props.columns) {
    let numCount = 0
    for (let i = 0; i < sampleSize; i++) {
      const val = props.rows[i][col]
      if (val !== null && val !== undefined && val !== '' && !isNaN(Number(val))) {
        numCount++
      }
    }
    if (numCount > sampleSize * 0.5) {
      numeric.push(col)
    } else {
      text.push(col)
    }
  }

  return { numeric, text }
})

const numericColumns = computed(() => {
  // Y축에는 숫자 컬럼만 표시하되, 숫자 컬럼이 없으면 전체 컬럼 표시
  return columnTypes.value.numeric.length > 0 ? columnTypes.value.numeric : props.columns
})

// 스마트 기본값 설정
const initDefaults = () => {
  const { numeric, text } = columnTypes.value
  xAxisColumn.value = text.length > 0 ? text[0] : (props.columns[0] || '')
  if (numeric.length > 0) {
    yAxisColumns.value = chartType.value === 'pie' ? numeric[0] : [numeric[0]]
  } else if (props.columns.length > 1) {
    yAxisColumns.value = chartType.value === 'pie' ? props.columns[1] : [props.columns[1]]
  }
}

onMounted(() => {
  if (props.columns.length > 0) initDefaults()
})

// chartType 변경 시 yAxisColumns 형태 조정
watch(chartType, (newType) => {
  if (newType === 'pie') {
    // 복수 → 단일 (첫 번째 값만 유지)
    if (Array.isArray(yAxisColumns.value)) {
      yAxisColumns.value = yAxisColumns.value[0] || ''
    }
  } else {
    // 단일 → 복수 배열
    if (!Array.isArray(yAxisColumns.value)) {
      yAxisColumns.value = yAxisColumns.value ? [yAxisColumns.value] : []
    }
  }
})

// 생성 가능 여부
const canGenerate = computed(() => {
  if (!xAxisColumn.value) return false
  if (chartType.value === 'pie') {
    return !!yAxisColumns.value
  }
  return Array.isArray(yAxisColumns.value) && yAxisColumns.value.length > 0
})

// 다크모드 텍스트 색상 가져오기
const getThemeColor = (varName) => {
  return getComputedStyle(document.documentElement).getPropertyValue(varName).trim() || '#333'
}

// 차트 옵션 생성
const chartOption = ref({})

const generateChart = () => {
  const textColor = whiteBg.value ? '#333333' : getThemeColor('--text-color-primary')
  const subTextColor = whiteBg.value ? '#666666' : getThemeColor('--text-color-secondary')
  const borderColor = whiteBg.value ? '#dcdcdc' : getThemeColor('--border-color-lighter')

  const baseStyle = {
    textStyle: { color: textColor },
    backgroundColor: whiteBg.value ? '#ffffff' : 'transparent'
  }

  if (chartType.value === 'pie') {
    // 전체 데이터를 값 기준 내림차순 정렬
    let pieData = props.rows
      .map(r => ({
        name: String(r[xAxisColumn.value] ?? ''),
        value: Number(r[yAxisColumns.value]) || 0
      }))
      .sort((a, b) => b.value - a.value)

    // Top N 적용: 나머지를 "기타"로 묶기
    if (pieTopN.value > 0 && pieData.length > pieTopN.value) {
      const topItems = pieData.slice(0, pieTopN.value)
      const otherSum = pieData.slice(pieTopN.value).reduce((sum, d) => sum + d.value, 0)
      const otherCount = pieData.length - pieTopN.value
      topItems.push({ name: `기타 (${otherCount}건)`, value: otherSum })
      pieData = topItems
    }

    // 전체 합계 (비율 계산용)
    const totalValue = pieData.reduce((sum, d) => sum + d.value, 0)

    chartOption.value = {
      ...baseStyle,
      tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
      legend: {
        type: 'scroll',
        orient: 'horizontal',
        bottom: 0,
        pageIconColor: subTextColor,
        pageTextStyle: { color: subTextColor },
        textStyle: { color: subTextColor, fontSize: 11 }
      },
      series: [{
        type: 'pie',
        radius: ['35%', '65%'],
        center: ['50%', '42%'],
        label: {
          color: textColor,
          fontSize: 11,
          formatter: (params) => {
            const pct = totalValue > 0 ? ((params.value / totalValue) * 100) : 0
            return pct >= 3 ? `${params.name}` : ''
          }
        },
        labelLine: {
          show: true,
          length: 10,
          length2: 8
        },
        emphasis: {
          label: { show: true, fontSize: 13, fontWeight: 'bold' },
          itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.3)' }
        },
        data: pieData
      }]
    }
  } else {
    const yColumns = Array.isArray(yAxisColumns.value) ? yAxisColumns.value : [yAxisColumns.value]
    const xData = props.rows.map(r => String(r[xAxisColumn.value] ?? ''))

    const needZoom = xData.length > 30
    chartOption.value = {
      ...baseStyle,
      tooltip: { trigger: 'axis' },
      legend: {
        data: yColumns,
        bottom: needZoom ? 30 : 0,
        textStyle: { color: subTextColor, fontSize: 12 }
      },
      grid: { left: '3%', right: '4%', bottom: needZoom ? '20%' : '15%', top: '10%', containLabel: true },
      ...(needZoom ? {
        dataZoom: [{
          type: 'slider',
          bottom: 5,
          height: 20,
          start: 0,
          end: Math.min(100, (30 / xData.length) * 100),
          textStyle: { color: subTextColor }
        }]
      } : {}),
      xAxis: {
        type: 'category',
        data: xData,
        axisLabel: {
          color: subTextColor,
          fontSize: 11,
          rotate: xData.length > 15 ? 90 : xData.length > 8 ? 45 : 0,
          interval: 0
        },
        axisLine: { lineStyle: { color: borderColor } },
        axisTick: { lineStyle: { color: borderColor } }
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: subTextColor, fontSize: 11 },
        axisLine: { lineStyle: { color: borderColor } },
        splitLine: { lineStyle: { color: borderColor, type: 'dashed' } }
      },
      series: yColumns.map(col => ({
        name: col,
        type: chartType.value,
        data: props.rows.map(r => Number(r[col]) || 0),
        smooth: chartType.value === 'line'
      }))
    }
  }

  chartGenerated.value = true
}

// 부모 컴포넌트에서 차트 상태 및 설정값 접근 가능하도록 노출
defineExpose({ chartGenerated, chartType, xAxisColumn, yAxisColumns, pieTopN })
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.chart-builder {
  @include mx.chart-builder-container;
}

.chart-toggle-btn {
  @include mx.chart-toggle-btn;

  .toggle-arrow {
    transition: transform 0.2s;
    margin-left: 4px;

    &.expanded {
      transform: rotate(180deg);
    }
  }
}

.chart-config {
  @include mx.chart-config-panel;

  .config-row {
    display: flex;
    flex-wrap: wrap;
    gap: 16px;
    align-items: stretch;
    width: 100%;
  }

  .config-item {
    @include mx.chart-config-item;

    &.config-action {
      margin-left: auto;
      justify-content: flex-end;
      min-width: unset;
    }
  }
}

.chart-area {
  @include mx.chart-render-area(400px);
  margin-top: 12px;
  position: relative;
  transition: background-color 0.2s;

  &.white-bg {
    background-color: #ffffff;
  }

  .bg-toggle-btn {
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 10;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-color-overlay, rgba(0, 0, 0, 0.3));
    border: 1px solid var(--border-color-lighter);
    border-radius: 6px;
    color: var(--text-color-secondary);
    cursor: pointer;
    transition: all 0.2s;
    padding: 0;
    font-size: 14px;

    &:hover {
      color: var(--text-color-primary);
      background: var(--bg-color-hover, rgba(0, 0, 0, 0.5));
    }
  }

  &.white-bg .bg-toggle-btn {
    background: rgba(0, 0, 0, 0.06);
    border-color: #ddd;
    color: #666;

    &:hover {
      background: rgba(0, 0, 0, 0.12);
      color: #333;
    }
  }

  .chart-canvas {
    width: 100%;
    height: 100%;
  }
}

// 모바일 반응형
@media (max-width: 768px) {
  .chart-config {
    padding: 10px;

    .config-row {
      flex-direction: column;
      gap: 10px;
    }

    .config-item {
      width: 100%;
      min-width: unset;

      &.config-action {
        margin-left: 0;
      }
    }
  }

  .chart-area {
    height: 300px;
    min-height: 250px;
  }
}
</style>
