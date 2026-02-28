<template>
  <div class="content-card request-type-chart" v-loading="loading">
    <div class="card-header">
      <h3>검색 유형 분포</h3>
    </div>
    <div class="chart-area">
      <v-chart :option="chartOption" autoresize style="height: 320px;" />
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import {
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'

use([CanvasRenderer, PieChart, TooltipComponent, LegendComponent])

const props = defineProps({
  kpi: {
    type: Object,
    default: () => ({ total_requests: 0, nl2sql_count: 0, rag_count: 0 })
  },
  loading: { type: Boolean, default: false }
})

const chartOption = computed(() => {
  const total = props.kpi.total_requests || 0

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c}건 ({d}%)',
    },
    legend: {
      orient: 'horizontal',
      bottom: 0,
    },
    series: [
      {
        type: 'pie',
        radius: ['45%', '70%'],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        label: {
          show: true,
          formatter: '{b}\n{d}%',
          fontSize: 12,
        },
        emphasis: {
          label: { show: true, fontSize: 14, fontWeight: 'bold' },
        },
        data: [
          { value: props.kpi.nl2sql_count || 0, name: 'NL2SQL', itemStyle: { color: '#67c23a' } },
          { value: props.kpi.rag_count || 0, name: 'RAG', itemStyle: { color: '#e6a23c' } },
        ],
        // 도넛 중앙 텍스트 (graphic으로 대체)
      },
    ],
    graphic: [
      {
        type: 'text',
        left: 'center',
        top: '40%',
        style: {
          text: total.toLocaleString(),
          fontSize: 22,
          fontWeight: 'bold',
          fill: 'var(--text-color-primary, #303133)',
          textAlign: 'center',
        },
      },
      {
        type: 'text',
        left: 'center',
        top: '48%',
        style: {
          text: '총 요청',
          fontSize: 12,
          fill: 'var(--text-color-secondary, #909399)',
          textAlign: 'center',
        },
      },
    ],
  }
})
</script>

<style lang="scss" scoped>
.request-type-chart {
  min-height: 360px;
}
</style>
