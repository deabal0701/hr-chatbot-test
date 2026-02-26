<template>
  <div class="widget-chart">
    <v-chart :option="chartOption" autoresize class="chart-canvas" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart, PieChart, ScatterChart } from 'echarts/charts'
import {
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DataZoomComponent
} from 'echarts/components'
import { buildChartOption } from '@/composables/useChartOptions'

use([CanvasRenderer, BarChart, LineChart, PieChart, ScatterChart, TooltipComponent, LegendComponent, GridComponent, DataZoomComponent])

const props = defineProps({
  chartType: { type: String, required: true },
  chartConfig: { type: Object, default: () => ({}) },
  rows: { type: Array, default: () => [] },
  darkMode: { type: Boolean, default: null },
  colorPalette: { type: String, default: null }
})

const chartOption = computed(() => {
  if (!props.rows.length) return {}

  return buildChartOption({
    chartType: props.chartType,
    xColumn: props.chartConfig.x_column,
    yColumns: props.chartConfig.y_columns,
    rows: props.rows,
    pieTopN: props.chartConfig.pie_top_n || 10,
    darkMode: props.darkMode,
    colorPalette: props.colorPalette
  })
})
</script>

<style lang="scss" scoped>
.widget-chart {
  width: 100%;
  height: 100%;
}

.chart-canvas {
  width: 100%;
  height: 100%;
}
</style>
