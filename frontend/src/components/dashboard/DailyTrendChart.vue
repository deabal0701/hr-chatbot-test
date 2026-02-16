<template>
  <div class="content-card daily-trend-chart" v-loading="loading">
    <div class="card-header">
      <h3>일별 요청 추이</h3>
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
import { BarChart } from 'echarts/charts'
import {
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'

use([CanvasRenderer, BarChart, TooltipComponent, LegendComponent, GridComponent])

const props = defineProps({
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

const chartOption = computed(() => {
  const dates = props.data.map(d => {
    const parts = d.date.split('-')
    return `${parts[1]}/${parts[2]}`
  })

  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter(params) {
        let html = `<strong>${params[0].axisValue}</strong><br/>`
        let total = 0
        params.forEach(p => {
          html += `${p.marker} ${p.seriesName}: <strong>${p.value}</strong><br/>`
          total += p.value
        })
        html += `합계: <strong>${total}</strong>`
        return html
      }
    },
    legend: {
      data: ['NL2SQL', 'RAG'],
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      top: '10%',
      bottom: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: dates,
    },
    yAxis: {
      type: 'value',
      minInterval: 1,
    },
    series: [
      {
        name: 'NL2SQL',
        type: 'bar',
        stack: 'total',
        data: props.data.map(d => d.nl2sql),
        itemStyle: { color: '#67c23a' },
        barMaxWidth: 40,
      },
      {
        name: 'RAG',
        type: 'bar',
        stack: 'total',
        data: props.data.map(d => d.rag),
        itemStyle: { color: '#e6a23c' },
        barMaxWidth: 40,
      },
    ],
  }
})
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.daily-trend-chart {
  @include mx.content-card;
  min-height: 360px;

  .card-header {
    @include mx.content-header;
  }
}
</style>
