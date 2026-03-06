<template>
  <el-dialog
    v-model="visible"
    title="위젯 수정"
    width="680px"
    class="dashboard-dark"
    :close-on-click-modal="false"
    destroy-on-close
    @close="handleClose"
  >
    <el-form label-position="top">
      <!-- 위젯 설정 (공통 컴포넌트) -->
      <WidgetConfigForm ref="configRef" :columns="currentColumns" :rows="currentRows" />

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
                v-model="sqlText"
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
import { ref, computed, watch, nextTick } from 'vue'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import WidgetConfigForm from './WidgetConfigForm.vue'
import personalDashboardApi from '@/api/personalDashboard'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  widget: { type: Object, default: null }
})

const emit = defineEmits(['update:modelValue', 'saved'])
const store = useStore()
const configRef = ref(null)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const sqlText = ref('')
const originalSql = ref('')
const sqlExecuting = ref(false)
const sqlExecuted = ref(false)
const previewData = ref(null)

const sqlModified = computed(() => sqlText.value !== originalSql.value)

const currentColumns = computed(() => {
  if (previewData.value) return previewData.value.columns
  return props.widget?.cached_data?.columns || []
})

const currentRows = computed(() => {
  if (previewData.value) return previewData.value.rows
  return props.widget?.cached_data?.rows || []
})

const canSave = computed(() => configRef.value?.isFormValid ?? false)

// 위젯 데이터로 폼 초기화
watch(visible, async (val) => {
  if (val && props.widget) {
    const config = props.widget.chart_config || {}
    sqlText.value = props.widget.sql || ''
    originalSql.value = props.widget.sql || ''
    sqlExecuted.value = false
    previewData.value = null

    // destroy-on-close로 인해 컴포넌트 마운트 대기 필요
    await nextTick()

    // WidgetConfigForm 초기화
    configRef.value?.initForm({
      title: props.widget.title,
      widgetType: props.widget.widget_type,
      xColumn: config.x_column || '',
      yColumns: config.y_columns || [],
      pieTopN: config.pie_top_n ?? 10,
      kpiColumn: config.kpi_column || '',
      kpiSuffix: config.kpi_suffix || '',
      colorPalette: config.color_palette || 'default'
    })
    configRef.value?.initAliases(
      props.widget.cached_data?.columns || [],
      config.column_aliases || {}
    )
  }
})

// SQL 실행
const handleExecuteSql = async () => {
  if (!sqlText.value.trim()) {
    ElMessage.warning('SQL을 입력하세요')
    return
  }
  sqlExecuting.value = true
  try {
    const result = await personalDashboardApi.executeSql(sqlText.value)
    previewData.value = result
    sqlExecuted.value = true

    // 새 columns로 별칭 교차 검증
    const oldForm = configRef.value?.form
    const oldAliases = {}
    if (oldForm) {
      const currentAliases = configRef.value.computedAliases || {}
      Object.assign(oldAliases, currentAliases)
    }
    configRef.value?.initAliases(result.columns, oldAliases)

    ElMessage.success(`실행 완료: ${result.row_count}행 (${result.execution_time_ms}ms)`)
  } catch (err) {
    ElMessage.error(err?.detail || err?.message || 'SQL 실행 실패')
  } finally {
    sqlExecuting.value = false
  }
}

// SQL 초기화
const handleResetSql = () => {
  sqlText.value = originalSql.value
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

  const form = configRef.value.form
  const updates = {
    title: form.title.trim(),
    widget_type: form.widgetType,
    chart_config: configRef.value.buildChartConfig()
  }

  if (sqlModified.value) {
    updates.sql = sqlText.value
  }

  if (previewData.value) {
    updates.cached_data = {
      columns: previewData.value.columns,
      rows: previewData.value.rows.slice(0, 500),
      row_count: previewData.value.row_count,
      cached_at: new Date().toISOString()
    }
  }

  try {
    await store.dispatch('dashboard/updateWidget', { widgetId: props.widget.widget_id, updates })
    ElMessage.success('위젯이 수정되었습니다')
    emit('saved')
    visible.value = false
  } catch (err) {
    ElMessage.error('위젯 수정에 실패했습니다')
  }
}

const handleClose = () => {
  visible.value = false
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

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
