<template>
  <el-collapse>
    <el-collapse-item v-if="sql" title="실행된 SQL 쿼리" name="sql">
      <pre class="sql-code">{{ sql }}</pre>
    </el-collapse-item>
    <el-collapse-item v-if="sqlResult" title="조회 결과" name="result">
      <div class="result-summary">
        총 {{ sqlResult.row_count }}개 행 조회됨
        <span v-if="sqlResult.execution_time_ms">
          ({{ sqlResult.execution_time_ms }}ms)
        </span>
      </div>
      <el-table
        v-if="sqlResult.rows.length > 0"
        :data="sqlResult.rows.slice(0, maxRows)"
        size="small"
        border
        max-height="500"
      >
        <el-table-column
          v-for="col in sqlResult.columns"
          :key="col"
          :prop="col"
          :label="col"
          min-width="100"
        />
      </el-table>
      <div v-if="sqlResult.row_count > maxRows" class="more-rows">
        ... 외 {{ sqlResult.row_count - maxRows }}개 행
      </div>
      <ChartBuilder
        ref="chartBuilderRef"
        v-if="sqlResult.rows.length > 0"
        :columns="sqlResult.columns"
        :rows="sqlResult.rows"
      />
      <div v-if="showExport" class="export-bar">
        <el-button size="small" :icon="Download" :loading="exporting" @click="exportToExcel">
          Excel 다운로드
        </el-button>
      </div>
      <div v-if="sqlResult.rows?.length === 0" class="no-results">
        조회 결과가 없습니다.
      </div>
    </el-collapse-item>
  </el-collapse>
</template>

<script setup>
import { ref } from 'vue'
import { Download } from '@element-plus/icons-vue'
import ChartBuilder from '../chart/ChartBuilder.vue'
import searchApi from '@/api/search'
import { ElMessage } from 'element-plus'

const props = defineProps({
  sql: { type: String, default: '' },
  sqlResult: { type: Object, default: null },
  showExport: { type: Boolean, default: false },
  query: { type: String, default: '' },
  maxRows: { type: Number, default: 1000 }
})

const chartBuilderRef = ref(null)
const exporting = ref(false)

const exportToExcel = async () => {
  exporting.value = true
  try {
    const cb = chartBuilderRef.value
    const includeChart = cb?.chartGenerated || false
    await searchApi.exportExcel({
      columns: props.sqlResult.columns,
      rows: props.sqlResult.rows,
      question: props.query,
      sql: props.sql || '',
      answer: props.query,
      execution_time_ms: props.sqlResult.execution_time_ms || 0,
      include_chart: includeChart,
      chart_config: includeChart ? {
        chart_type: cb.chartType,
        x_column: cb.xAxisColumn,
        y_columns: cb.yAxisColumns,
        pie_top_n: cb.pieTopN
      } : null
    })
    ElMessage.success('Excel 파일이 다운로드되었습니다.')
  } catch {
    ElMessage.error('Excel 다운로드에 실패했습니다.')
  } finally {
    exporting.value = false
  }
}

defineExpose({ chartBuilderRef })
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.sql-code {
  @include mx.sql-code-block;
}

.result-summary {
  @include mx.result-summary;
}

.more-rows {
  @include mx.more-rows;
}

.export-bar {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
}

.no-results {
  font-size: 12px;
  color: var(--text-color-placeholder);
  text-align: center;
  padding: 12px;
}
</style>
