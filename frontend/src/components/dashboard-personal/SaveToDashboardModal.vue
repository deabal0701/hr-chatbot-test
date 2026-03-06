<template>
  <el-dialog
    v-model="visible"
    title="대시보드에 추가"
    width="680px"
    class="dashboard-dark"
    :close-on-click-modal="false"
    destroy-on-close
    @close="handleClose"
  >
    <!-- 로딩 중 -->
    <div v-if="isLoadingDashboards" class="dashboard-loading">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>대시보드 목록을 불러오는 중...</span>
    </div>

    <!-- 대시보드 없음 안내 -->
    <div v-else-if="noDashboard" class="no-dashboard-notice">
      <el-icon :size="40"><WarningFilled /></el-icon>
      <p>저장할 대시보드가 없습니다.</p>
      <p class="sub-text">대시보드 페이지에서 먼저 대시보드를 생성해주세요.</p>
      <el-button type="primary" @click="goToDashboard">대시보드로 이동</el-button>
    </div>

    <el-form v-else label-position="top">
      <!-- 대시보드 선택 -->
      <el-form-item label="대시보드">
        <el-select v-model="selectedDashboardId" placeholder="저장할 대시보드 선택" style="width: 100%">
          <el-option
            v-for="db in dashboardOptions"
            :key="db.dashboard_id"
            :label="db.name + (db.is_default ? ' (기본)' : '')"
            :value="db.dashboard_id"
          />
        </el-select>
      </el-form-item>

      <!-- 위젯 설정 (공통 컴포넌트) -->
      <WidgetConfigForm ref="configRef" :columns="columns" :rows="rows" />
    </el-form>

    <template #footer>
      <el-button @click="visible = false">{{ noDashboard ? '닫기' : '취소' }}</el-button>
      <el-button v-if="!noDashboard && !isLoadingDashboards" type="primary" :disabled="!canSave" @click="handleSave">저장</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Loading, WarningFilled } from '@element-plus/icons-vue'
import WidgetConfigForm from './WidgetConfigForm.vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  query: { type: String, default: '' },
  sql: { type: String, default: '' },
  columns: { type: Array, default: () => [] },
  rows: { type: Array, default: () => [] },
  rowCount: { type: Number, default: 0 },
  initialChartType: { type: String, default: '' },
  initialXColumn: { type: String, default: '' },
  initialYColumns: { type: [String, Array], default: () => [] }
})

const emit = defineEmits(['update:modelValue', 'saved'])

const store = useStore()
const router = useRouter()
const configRef = ref(null)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const dashboardOptions = computed(() => store.state.dashboard.dashboards || [])
const selectedDashboardId = ref(null)
const isLoadingDashboards = ref(false)
const noDashboard = computed(() => !isLoadingDashboards.value && dashboardOptions.value.length === 0)

const canSave = computed(() => {
  if (!selectedDashboardId.value) return false
  return configRef.value?.isFormValid ?? false
})

function initDashboardSelection() {
  const defaultDb = dashboardOptions.value.find(d => d.is_default)
  selectedDashboardId.value = defaultDb?.dashboard_id || (dashboardOptions.value[0]?.dashboard_id ?? null)
}

watch(visible, async (val) => {
  if (val) {
    if (dashboardOptions.value.length === 0) {
      isLoadingDashboards.value = true
      try {
        await store.dispatch('dashboard/fetchDashboards')
      } finally {
        isLoadingDashboards.value = false
      }
    }
    initDashboardSelection()

    // destroy-on-close로 인해 컴포넌트 마운트 대기 필요
    await nextTick()

    // WidgetConfigForm 초기화
    configRef.value?.initForm({
      title: props.query.slice(0, 100),
      widgetType: props.initialChartType || 'table',
      colorPalette: 'default',
      kpiSuffix: ''
    })
    configRef.value?.autoDetectColumns(props.columns, props.rows, {
      xColumn: props.initialXColumn,
      yColumns: props.initialYColumns
    })
    configRef.value?.initAliases(props.columns)
  }
})

const handleSave = async () => {
  const form = configRef.value.form
  const widgetConfig = {
    dashboard_id: selectedDashboardId.value,
    title: form.title.trim(),
    widget_type: form.widgetType,
    query: props.query,
    sql: props.sql,
    chart_config: configRef.value.buildChartConfig(),
    cached_data: {
      columns: props.columns,
      rows: props.rows.slice(0, 500),
      row_count: props.rowCount || props.rows.length,
      cached_at: new Date().toISOString()
    }
  }

  try {
    await store.dispatch('dashboard/saveWidget', widgetConfig)
    ElMessage.success('위젯이 대시보드에 추가되었습니다')
    emit('saved')
    visible.value = false
  } catch (err) {
    ElMessage.error('위젯 저장에 실패했습니다')
  }
}

const goToDashboard = () => {
  visible.value = false
  router.push('/dashboard')
}

const handleClose = () => {
  visible.value = false
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.dashboard-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 0;
  color: var(--el-text-color-secondary);
}

.no-dashboard-notice {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 32px 0;
  text-align: center;

  .el-icon {
    color: var(--el-color-warning);
    margin-bottom: 16px;
  }

  p {
    margin: 0 0 4px;
    font-size: 15px;
    font-weight: 500;
    color: var(--el-text-color-primary);
  }

  .sub-text {
    font-size: 13px;
    font-weight: 400;
    color: var(--el-text-color-secondary);
    margin-bottom: 20px;
  }
}
</style>
