<template>
  <div class="dashboard-empty-wrapper">
    <div class="dashboard-empty">
      <!-- 장식용 ECharts 미니 차트 -->
      <div class="empty-chart-preview">
        <v-chart :option="decorativeOption" :autoresize="true" />
      </div>

      <h3>{{ readOnly ? '공유 대시보드에 위젯이 없습니다' : '위젯이 없습니다' }}</h3>
      <p v-if="readOnly">이 공유 대시보드에는 아직 위젯이 추가되지 않았습니다.</p>
      <p v-else>대화에서 NL2SQL 결과를 대시보드에 추가하거나,<br>아래 버튼으로 데모 위젯을 불러올 수 있습니다.</p>
      <div v-if="!readOnly" class="empty-actions">
        <el-button type="primary" @click="$emit('go-chat')">
          <el-icon><ChatDotRound /></el-icon>
          <span>대화로 이동</span>
        </el-button>
        <el-button @click="$emit('load-demo')">
          <el-icon><MagicStick /></el-icon>
          <span>데모 위젯 불러오기</span>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ChatDotRound, MagicStick } from '@element-plus/icons-vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, LineChart } from 'echarts/charts'
import { GridComponent } from 'echarts/components'

use([CanvasRenderer, BarChart, LineChart, GridComponent])

defineProps({
  readOnly: { type: Boolean, default: false }
})

defineEmits(['go-chat', 'load-demo'])

const decorativeOption = {
  animation: true,
  animationDuration: 1200,
  animationEasing: 'cubicOut',
  grid: { left: 8, right: 8, top: 8, bottom: 8, containLabel: false },
  xAxis: { show: false, type: 'category', data: ['A', 'B', 'C', 'D', 'E', 'F', 'G'] },
  yAxis: { show: false, type: 'value', min: 0, max: 100 },
  series: [
    {
      type: 'bar',
      data: [35, 62, 48, 78, 55, 88, 42],
      itemStyle: {
        borderRadius: [3, 3, 0, 0],
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(64, 158, 255, 0.6)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.15)' }
          ]
        }
      },
      barWidth: '50%'
    },
    {
      type: 'line',
      data: [30, 58, 45, 72, 50, 82, 38],
      smooth: true,
      symbol: 'none',
      lineStyle: { color: 'rgba(64, 158, 255, 0.5)', width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(64, 158, 255, 0.15)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0)' }
          ]
        }
      }
    }
  ]
}
</script>

<style lang="scss" scoped>
.dashboard-empty-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 120px);
}

.dashboard-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px 48px;
  background: var(--dashboard-card);
  border-radius: 12px;
  border: 1px solid var(--dashboard-border);
  max-width: 480px;
  width: 100%;

  .empty-chart-preview {
    width: 180px;
    height: 120px;
    margin-bottom: 24px;
    opacity: 0.7;
    pointer-events: none;
  }

  h3 {
    margin: 0 0 8px;
    font-size: 20px;
    font-weight: 600;
    color: var(--dashboard-text-primary);
  }

  p {
    margin: 0 0 28px;
    font-size: 14px;
    color: var(--dashboard-text-secondary);
    line-height: 1.6;
  }

  .empty-actions {
    display: flex;
    gap: 12px;
  }
}
</style>
