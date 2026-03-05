<template>
  <el-dialog
    v-model="visible"
    title="위젯 추가"
    width="680px"
    class="dashboard-dark"
    :close-on-click-modal="false"
    destroy-on-close
    @close="handleClose"
  >
    <el-tabs v-model="activeTab">
      <!-- 탭 1: 대화 히스토리 -->
      <el-tab-pane label="대화 히스토리" name="history">
        <el-form label-position="top">
          <!-- 대화 히스토리 선택 -->
          <el-form-item label="대화 히스토리">
            <el-select
              v-model="selectedSessionKey"
              placeholder="대화를 선택하세요"
              filterable
              :loading="isLoadingSessions"
              style="width: 100%"
              @change="handleSessionSelect"
            >
              <el-option
                v-for="session in sessionList"
                :key="session.session_key"
                :label="session.title"
                :value="session.session_key"
              >
                <div class="session-option">
                  <span class="session-title">{{ session.title }}</span>
                  <span class="session-meta">
                    <el-tag size="small" :type="session.request_type === 'nl2sql' ? 'primary' : 'info'" disable-transitions>
                      {{ session.request_type }}
                    </el-tag>
                    <span class="session-date">{{ formatDate(session.last_activity || session.created_at) }}</span>
                  </span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <!-- 세션 내 메시지 선택 -->
          <el-form-item v-if="nlsqlMessages.length > 0" label="쿼리 결과 선택">
            <el-select
              v-model="selectedMessageIndex"
              placeholder="쿼리 결과를 선택하세요"
              style="width: 100%"
              @change="handleMessageSelect"
            >
              <el-option
                v-for="(msg, idx) in nlsqlMessages"
                :key="idx"
                :label="msg.question"
                :value="idx"
              >
                <div class="session-option">
                  <span class="session-title">{{ msg.question }}</span>
                  <span class="session-meta">
                    <span class="session-date">{{ msg.rowCount }}건</span>
                  </span>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <!-- 로딩 -->
          <div v-if="isLoadingSession" class="loading-placeholder">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>대화 내용을 불러오는 중...</span>
          </div>

          <!-- 결과 없음 -->
          <el-alert
            v-if="selectedSessionKey && !isLoadingSession && nlsqlMessages.length === 0 && sessionLoaded"
            title="이 대화에는 NL2SQL 쿼리 결과가 없습니다."
            type="info"
            :closable="false"
            show-icon
          />
        </el-form>
      </el-tab-pane>

      <!-- 탭 2: 직접 질문하기 -->
      <el-tab-pane label="직접 질문하기" name="direct">
        <el-form label-position="top">
          <el-form-item label="질문">
            <div class="direct-query-row">
              <el-input
                v-model="directQuery"
                placeholder="예: 부서별 직원 수를 알려줘"
                :disabled="isQuerying"
                @keydown.enter.prevent="handleDirectQuery"
              />
              <el-button
                type="primary"
                :loading="isQuerying"
                :disabled="!directQuery.trim()"
                @click="handleDirectQuery"
              >
                실행
              </el-button>
              <el-button
                v-if="isQuerying"
                @click="handleCancelQuery"
              >
                취소
              </el-button>
            </div>
          </el-form-item>

          <!-- SSE 진행 상황 -->
          <div v-if="queryStages.length > 0" class="query-progress">
            <div v-for="(stage, idx) in queryStages" :key="idx" class="stage-item" :class="{ 'is-active': idx === queryStages.length - 1 && isQuerying }">
              <el-icon v-if="idx < queryStages.length - 1 || !isQuerying" class="stage-icon done"><CircleCheckFilled /></el-icon>
              <el-icon v-else class="stage-icon loading is-loading"><Loading /></el-icon>
              <span class="stage-label">{{ stage }}</span>
            </div>
          </div>

          <!-- 에러 -->
          <el-alert
            v-if="queryError"
            :title="queryError"
            type="error"
            :closable="true"
            show-icon
            @close="queryError = ''"
            style="margin-bottom: 12px"
          />
        </el-form>
      </el-tab-pane>

      <!-- 탭 3: 위젯 가져오기 -->
      <el-tab-pane label="위젯 가져오기" name="import">
        <el-form label-position="top">
          <!-- 대시보드 선택 -->
          <el-form-item label="대시보드">
            <el-select
              v-model="importDashboardId"
              placeholder="대시보드를 선택하세요"
              :loading="isLoadingImportDashboards"
              style="width: 100%"
              @change="handleImportDashboardSelect"
            >
              <el-option-group v-if="importMyDashboards.length > 0" label="내 대시보드">
                <el-option
                  v-for="db in importMyDashboards"
                  :key="db.dashboard_id"
                  :label="db.name + (db.is_default ? ' (기본)' : '')"
                  :value="db.dashboard_id"
                />
              </el-option-group>
              <el-option-group v-if="importSharedDashboards.length > 0" label="공유 대시보드">
                <el-option
                  v-for="db in importSharedDashboards"
                  :key="db.dashboard_id"
                  :label="db.name + ' (' + (db.owner_name || '') + ')'"
                  :value="db.dashboard_id"
                />
              </el-option-group>
            </el-select>
          </el-form-item>

          <!-- 로딩 -->
          <div v-if="isLoadingImportWidgets" class="loading-placeholder">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>위젯 목록을 불러오는 중...</span>
          </div>

          <!-- 위젯 카드 그리드 -->
          <div v-else-if="importWidgets.length > 0" class="import-widget-grid">
            <div
              v-for="w in importWidgets"
              :key="w.widget_id"
              class="import-widget-card"
              :class="{ 'is-selected': selectedImportWidgetId === w.widget_id }"
              @click="handleImportWidgetSelect(w)"
            >
              <div class="widget-card-header">
                <el-icon :size="16"><component :is="WIDGET_TYPE_MAP[w.widget_type]?.icon" /></el-icon>
                <span>{{ WIDGET_TYPE_MAP[w.widget_type]?.label || w.widget_type }}</span>
              </div>
              <div class="widget-card-title">{{ w.title }}</div>
              <div class="widget-card-meta">
                {{ w.cached_data?.row_count || 0 }}건 · {{ (w.cached_data?.columns || []).length }}컬럼
              </div>
            </div>
          </div>

          <!-- 빈 상태 -->
          <el-empty
            v-else-if="importDashboardId && !isLoadingImportWidgets"
            description="이 대시보드에 위젯이 없습니다."
            :image-size="60"
          />
        </el-form>
      </el-tab-pane>
    </el-tabs>

    <!-- 공통: 실행 결과 + 위젯 설정 (결과가 있을 때만) -->
    <el-form v-if="hasResult" label-position="top" style="margin-top: 8px">
      <WidgetConfigForm ref="configRef" :columns="resultColumns" :rows="resultRows" />
    </el-form>

    <template #footer>
      <el-button @click="visible = false">취소</el-button>
      <el-button type="primary" :disabled="!canSave" @click="handleSave">추가</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { Loading, CircleCheckFilled, Grid, DataAnalysis, TrendCharts, PieChart, DataLine, Odometer } from '@element-plus/icons-vue'
import WidgetConfigForm from './WidgetConfigForm.vue'
import historyApi from '@/api/history'
import searchApi from '@/api/search'
import personalDashboardApi from '@/api/personalDashboard'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'saved'])
const store = useStore()
const configRef = ref(null)

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const activeTab = ref('history')

// ============================
// 탭 1: 히스토리
// ============================
const sessionList = ref([])
const isLoadingSessions = ref(false)
const selectedSessionKey = ref(null)
const isLoadingSession = ref(false)
const sessionLoaded = ref(false)
const nlsqlMessages = ref([])
const selectedMessageIndex = ref(null)

// ============================
// 탭 2: 직접 질문
// ============================
const directQuery = ref('')
const isQuerying = ref(false)
const queryStages = ref([])
const queryError = ref('')
let streamController = null

// ============================
// 탭 3: 위젯 가져오기
// ============================
const WIDGET_TYPE_MAP = {
  table: { label: '테이블', icon: Grid },
  bar: { label: 'Bar', icon: DataAnalysis },
  hbar: { label: 'H-Bar', icon: DataAnalysis },
  line: { label: 'Line', icon: TrendCharts },
  pie: { label: 'Pie', icon: PieChart },
  scatter: { label: 'Scatter', icon: DataLine },
  kpi: { label: 'KPI', icon: Odometer }
}
const importDashboardsLoaded = ref(false)
const isLoadingImportDashboards = ref(false)
const importMyDashboards = ref([])
const importSharedDashboards = ref([])
const importDashboardId = ref(null)
const isLoadingImportWidgets = ref(false)
const importWidgets = ref([])
const selectedImportWidgetId = ref(null)

// ============================
// 공통 결과 데이터
// ============================
const resultColumns = ref([])
const resultRows = ref([])
const resultRowCount = ref(0)
const selectedSql = ref('')
const queryText = ref('')
const hasResult = computed(() => resultColumns.value.length > 0)

const canSave = computed(() => {
  if (!hasResult.value) return false
  return configRef.value?.isFormValid ?? false
})

// 다이얼로그 열릴 때 세션 목록 로드 + 위젯 가져오기 캐시 리셋
watch(visible, async (val) => {
  if (val) {
    importDashboardsLoaded.value = false
    activeTab.value = 'history'
    await loadSessions()
  }
})

// 탭 전환 시 이전 결과 초기화 + 위젯 가져오기 탭 대시보드 로드
watch(activeTab, async (val) => {
  clearResult()
  selectedImportWidgetId.value = null
  if (val === 'import' && !importDashboardsLoaded.value) {
    await loadImportDashboards()
  }
})

// ============================
// 히스토리 탭 로직
// ============================
const loadSessions = async () => {
  isLoadingSessions.value = true
  try {
    const response = await historyApi.listSessions({ limit: 100, offset: 0 })
    sessionList.value = (response.items || []).filter(s =>
      s.request_type === 'nl2sql' || s.request_type === 'agent'
    )
  } catch (error) {
    console.error('[AddWidget] Failed to load sessions:', error)
    sessionList.value = []
  } finally {
    isLoadingSessions.value = false
  }
}

const handleSessionSelect = async (sessionKey) => {
  if (!sessionKey) return

  nlsqlMessages.value = []
  selectedMessageIndex.value = null
  clearResult()
  sessionLoaded.value = false
  isLoadingSession.value = true

  try {
    const response = await historyApi.getSessionHistory(sessionKey)
    const records = response.items || []

    const filtered = records
      .filter(r => r.request_type === 'nl2sql' && r.trace_data?.sql_result?.columns?.length > 0)
      .map(r => ({
        question: r.question,
        sql: r.trace_data.sql,
        columns: r.trace_data.sql_result.columns,
        rows: r.trace_data.sql_result.rows,
        rowCount: r.trace_data.sql_result.row_count || r.trace_data.sql_result.rows?.length || 0
      }))

    nlsqlMessages.value = filtered

    if (filtered.length === 1) {
      selectedMessageIndex.value = 0
      handleMessageSelect(0)
    }
  } catch {
    ElMessage.error('대화 내용을 불러오지 못했습니다.')
  } finally {
    isLoadingSession.value = false
    sessionLoaded.value = true
  }
}

const handleMessageSelect = (idx) => {
  const msg = nlsqlMessages.value[idx]
  if (!msg) return
  setResult(msg.columns, msg.rows, msg.sql, msg.question, msg.rowCount)
}

// ============================
// 직접 질문 탭 로직
// ============================
const handleDirectQuery = () => {
  if (!directQuery.value.trim() || isQuerying.value) return

  isQuerying.value = true
  queryStages.value = []
  queryError.value = ''
  clearResult()

  streamController = searchApi.searchStream(
    { query: directQuery.value, mode: 'nl2sql', skipAnswer: true },
    {
      onNodeStart: (event) => {
        if (event.label) {
          queryStages.value = [...queryStages.value, event.label]
        }
      },
      onNodeComplete: () => {},
      onComplete: (event) => {
        isQuerying.value = false
        streamController = null

        const data = event.data || event
        if (data.sql_result?.columns?.length > 0) {
          setResult(
            data.sql_result.columns,
            data.sql_result.rows,
            data.sql,
            directQuery.value,
            data.sql_result.row_count || data.sql_result.rows?.length || 0
          )
        } else {
          queryError.value = data.answer || '쿼리 결과가 없습니다.'
        }
      },
      onError: (error) => {
        isQuerying.value = false
        streamController = null
        queryError.value = error.message || 'SSE 스트리밍 오류가 발생했습니다.'
      }
    }
  )
}

const handleCancelQuery = () => {
  if (streamController) {
    streamController.abort()
    streamController = null
  }
  isQuerying.value = false
  queryStages.value = []
}

// ============================
// 위젯 가져오기 탭 로직
// ============================
const loadImportDashboards = async () => {
  isLoadingImportDashboards.value = true
  try {
    const res = await personalDashboardApi.getDashboards()
    const currentId = store.state.dashboard.currentDashboardId
    importMyDashboards.value = (res.my_dashboards || []).filter(d => d.dashboard_id !== currentId)
    importSharedDashboards.value = (res.shared_dashboards || []).filter(d => d.dashboard_id !== currentId)
  } catch {
    importMyDashboards.value = []
    importSharedDashboards.value = []
  } finally {
    isLoadingImportDashboards.value = false
    importDashboardsLoaded.value = true
  }
}

const handleImportDashboardSelect = async (dashboardId) => {
  if (!dashboardId) return
  importWidgets.value = []
  selectedImportWidgetId.value = null
  clearResult()
  isLoadingImportWidgets.value = true
  try {
    const res = await personalDashboardApi.getWidgets(dashboardId)
    importWidgets.value = (res.items || []).filter(w => w.cached_data?.columns?.length > 0)
  } catch {
    ElMessage.error('위젯 목록을 불러오지 못했습니다.')
    importWidgets.value = []
  } finally {
    isLoadingImportWidgets.value = false
  }
}

const handleImportWidgetSelect = async (widget) => {
  selectedImportWidgetId.value = widget.widget_id
  const cached = widget.cached_data || {}
  const config = widget.chart_config || {}

  resultColumns.value = cached.columns || []
  resultRows.value = cached.rows || []
  resultRowCount.value = cached.row_count || (cached.rows || []).length
  selectedSql.value = widget.sql || ''
  queryText.value = widget.query || ''

  await nextTick()
  configRef.value?.initForm({
    title: (widget.title + ' (복사)').slice(0, 100),
    widgetType: widget.widget_type || 'table',
    xColumn: config.x_column || '',
    yColumns: config.y_columns || [],
    pieTopN: config.pie_top_n ?? 10,
    kpiColumn: config.kpi_column || '',
    kpiSuffix: config.kpi_suffix || '',
    colorPalette: config.color_palette || 'default'
  })
  configRef.value?.initAliases(cached.columns || [], config.column_aliases || {})
}

// ============================
// 공통 유틸
// ============================
const clearResult = () => {
  resultColumns.value = []
  resultRows.value = []
  resultRowCount.value = 0
  selectedSql.value = ''
  queryText.value = ''
}

const setResult = (columns, rows, sql, query, rowCount) => {
  resultColumns.value = columns
  resultRows.value = rows
  resultRowCount.value = rowCount || rows.length
  selectedSql.value = sql || ''
  queryText.value = query

  // WidgetConfigForm 초기화 (nextTick 이후 configRef가 렌더링됨)
  setTimeout(() => {
    configRef.value?.initForm({
      title: query.slice(0, 100),
      widgetType: 'table',
      kpiSuffix: '',
      colorPalette: 'default',
      pieTopN: 10
    })
    configRef.value?.autoDetectColumns(columns, rows)
    configRef.value?.initAliases(columns)
  }, 0)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${mi}`
}

const handleSave = async () => {
  const form = configRef.value.form
  const widgetConfig = {
    title: form.title.trim(),
    widget_type: form.widgetType,
    query: queryText.value,
    sql: selectedSql.value || '',
    chart_config: configRef.value.buildChartConfig(),
    cached_data: {
      columns: resultColumns.value,
      rows: resultRows.value.slice(0, 500),
      row_count: resultRowCount.value || resultRows.value.length,
      cached_at: new Date().toISOString()
    }
  }

  try {
    await store.dispatch('dashboard/saveWidget', widgetConfig)
    ElMessage.success('위젯이 추가되었습니다')
    emit('saved')
    visible.value = false
  } catch (err) {
    ElMessage.error('위젯 저장에 실패했습니다')
  }
}

const handleClose = () => {
  handleCancelQuery()
  selectedSessionKey.value = null
  selectedMessageIndex.value = null
  nlsqlMessages.value = []
  clearResult()
  sessionLoaded.value = false
  directQuery.value = ''
  queryStages.value = []
  queryError.value = ''
  // import 탭 초기화
  importDashboardsLoaded.value = false
  importDashboardId.value = null
  importWidgets.value = []
  selectedImportWidgetId.value = null
  importMyDashboards.value = []
  importSharedDashboards.value = []
  visible.value = false
}
</script>

<style lang="scss" scoped>
.session-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;

  .session-title {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-right: 8px;
  }

  .session-meta {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-shrink: 0;

    .session-date {
      font-size: 12px;
      color: var(--el-text-color-secondary);
    }
  }
}

.loading-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 20px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.direct-query-row {
  display: flex;
  gap: 8px;
  width: 100%;

  .el-input {
    flex: 1;
  }
}

.query-progress {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}

.stage-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  padding: 2px 8px;
  background: var(--el-fill-color-light);
  border-radius: 10px;

  &.is-active {
    color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
  }

  .stage-icon {
    font-size: 14px;

    &.done {
      color: var(--el-color-success);
    }

    &.loading {
      color: var(--el-color-primary);
    }
  }
}

.import-widget-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 4px;
}

.import-widget-card {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    border-color: var(--el-color-primary-light-5);
    background: var(--el-color-primary-light-9);
  }

  &.is-selected {
    border-color: var(--el-color-primary);
    background: var(--el-color-primary-light-9);
    box-shadow: 0 0 0 1px var(--el-color-primary);
  }

  .widget-card-header {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: 6px;
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }

  .widget-card-title {
    font-size: 13px;
    font-weight: 500;
    color: var(--el-text-color-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-bottom: 4px;
  }

  .widget-card-meta {
    font-size: 11px;
    color: var(--el-text-color-secondary);
  }
}
</style>
