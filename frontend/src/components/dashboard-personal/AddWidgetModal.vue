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
    </el-tabs>

    <!-- 공통: 실행 결과 미리보기 + 위젯 설정 (결과가 있을 때만) -->
    <el-form v-if="hasResult" label-position="top" style="margin-top: 8px">
      <!-- 대시보드 선택 -->
      <el-form-item v-if="dashboardOptions.length > 1" label="대시보드">
        <el-select v-model="selectedDashboardId" placeholder="저장할 대시보드 선택" style="width: 100%">
          <el-option
            v-for="db in dashboardOptions"
            :key="db.dashboard_id"
            :label="db.name + (db.is_default ? ' (기본)' : '')"
            :value="db.dashboard_id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="실행 결과">
        <div class="result-preview">
          <el-table :data="resultRows.slice(0, 5)" size="small" border max-height="180">
            <el-table-column v-for="col in resultColumns" :key="col" :prop="col" :label="col" :min-width="80" show-overflow-tooltip />
          </el-table>
          <div v-if="resultRows.length > 5" class="overflow-notice">... 외 {{ resultRows.length - 5 }}건</div>
        </div>
      </el-form-item>

      <!-- 위젯 제목 -->
      <el-form-item label="위젯 제목">
        <el-input v-model="form.title" placeholder="위젯 제목" maxlength="100" show-word-limit />
      </el-form-item>

      <!-- 위젯 유형 -->
      <el-form-item label="위젯 유형">
        <el-radio-group v-model="form.widgetType">
          <el-radio-button value="table">테이블</el-radio-button>
          <el-radio-button value="bar">Bar</el-radio-button>
          <el-radio-button value="hbar">H-Bar</el-radio-button>
          <el-radio-button value="line">Line</el-radio-button>
          <el-radio-button value="pie">Pie</el-radio-button>
          <el-radio-button value="scatter">Scatter</el-radio-button>
          <el-radio-button value="kpi">KPI</el-radio-button>
        </el-radio-group>
      </el-form-item>

      <!-- 차트 설정 -->
      <template v-if="isChartType">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item :label="form.widgetType === 'pie' ? '항목' : 'X축 컬럼'">
              <el-select v-model="form.xColumn" style="width: 100%">
                <el-option v-for="col in resultColumns" :key="col" :label="col" :value="col" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="form.widgetType === 'pie' ? '값' : 'Y축 컬럼'">
              <el-select v-model="form.yColumns" :multiple="form.widgetType !== 'pie'" collapse-tags style="width: 100%">
                <el-option v-for="col in numericCols" :key="col" :label="col" :value="col" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="16">
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

      <template v-if="form.widgetType === 'kpi'">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="값 컬럼">
              <el-select v-model="form.kpiColumn" style="width: 100%">
                <el-option v-for="col in numericCols" :key="col" :label="col" :value="col" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="단위">
              <el-input v-model="form.kpiSuffix" placeholder="명, %" />
            </el-form-item>
          </el-col>
        </el-row>
      </template>
    </el-form>

    <template #footer>
      <el-button @click="visible = false">취소</el-button>
      <el-button type="primary" :disabled="!canSave" @click="handleSave">추가</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useStore } from 'vuex'
import { ElMessage } from 'element-plus'
import { Loading, CircleCheckFilled } from '@element-plus/icons-vue'
import { detectColumnTypes, CHART_PALETTES } from '@/composables/useChartOptions'
import historyApi from '@/api/history'
import searchApi from '@/api/search'

const props = defineProps({
  modelValue: { type: Boolean, default: false }
})

const emit = defineEmits(['update:modelValue', 'saved'])
const store = useStore()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const dashboardOptions = computed(() => store.state.dashboard.dashboards || [])
const selectedDashboardId = ref(null)

const activeTab = ref('history')

const form = ref({
  queryText: '',
  title: '',
  widgetType: 'bar',
  xColumn: '',
  yColumns: [],
  pieTopN: 10,
  kpiColumn: '',
  kpiSuffix: '',
  colorPalette: 'default'
})

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
// 공통 결과 데이터
// ============================
const resultColumns = ref([])
const resultRows = ref([])
const selectedSql = ref('')
const hasResult = computed(() => resultColumns.value.length > 0)

// 다이얼로그 열릴 때 세션 목록 로드 + 기본 대시보드 선택
watch(visible, async (val) => {
  if (val) {
    const defaultDb = dashboardOptions.value.find(d => d.is_default)
    selectedDashboardId.value = defaultDb?.dashboard_id || (dashboardOptions.value[0]?.dashboard_id ?? null)
    await loadSessions()
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
  setResult(msg.columns, msg.rows, msg.sql, msg.question)
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
    { query: directQuery.value, mode: 'nl2sql' },
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
            directQuery.value
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
// 공통 유틸
// ============================
const clearResult = () => {
  resultColumns.value = []
  resultRows.value = []
  selectedSql.value = ''
}

const setResult = (columns, rows, sql, query) => {
  resultColumns.value = columns
  resultRows.value = rows
  selectedSql.value = sql || ''
  form.value.queryText = query
  form.value.title = query.slice(0, 100)

  const { numeric, text } = detectColumnTypes(columns, rows)
  form.value.xColumn = text[0] || columns[0] || ''
  form.value.yColumns = numeric.length > 0 ? [numeric[0]] : []
  form.value.kpiColumn = numeric[0] || ''
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

const numericCols = computed(() => {
  const { numeric } = detectColumnTypes(resultColumns.value, resultRows.value)
  return numeric.length > 0 ? numeric : resultColumns.value
})

const isChartType = computed(() => ['bar', 'hbar', 'line', 'pie', 'scatter'].includes(form.value.widgetType))

watch(() => form.value.widgetType, (newType) => {
  if (newType === 'pie') {
    if (Array.isArray(form.value.yColumns)) form.value.yColumns = form.value.yColumns[0] || ''
  } else if (['bar', 'hbar', 'line', 'scatter'].includes(newType)) {
    if (!Array.isArray(form.value.yColumns)) form.value.yColumns = form.value.yColumns ? [form.value.yColumns] : []
  }
})

const canSave = computed(() => {
  if (!hasResult.value || !form.value.title.trim()) return false
  if (form.value.widgetType === 'kpi') return !!form.value.kpiColumn
  if (isChartType.value) {
    const hasY = Array.isArray(form.value.yColumns) ? form.value.yColumns.length > 0 : !!form.value.yColumns
    return !!form.value.xColumn && hasY
  }
  return true
})

const handleSave = async () => {
  const widgetConfig = {
    dashboard_id: selectedDashboardId.value,
    title: form.value.title.trim(),
    widget_type: form.value.widgetType,
    query: form.value.queryText,
    sql: selectedSql.value || '',
    chart_config: {
      x_column: form.value.xColumn || null,
      y_columns: Array.isArray(form.value.yColumns) ? form.value.yColumns : (form.value.yColumns ? [form.value.yColumns] : null),
      pie_top_n: form.value.widgetType === 'pie' ? form.value.pieTopN : null,
      kpi_column: form.value.widgetType === 'kpi' ? form.value.kpiColumn : null,
      kpi_suffix: form.value.widgetType === 'kpi' ? form.value.kpiSuffix : null,
      color_palette: isChartType.value ? form.value.colorPalette : null
    },
    cached_data: {
      columns: resultColumns.value,
      rows: resultRows.value,
      row_count: resultRows.value.length,
      cached_at: new Date().toISOString()
    }
  }

  await store.dispatch('dashboard/saveWidget', widgetConfig)
  ElMessage.success('위젯이 추가되었습니다')
  emit('saved')
  visible.value = false
}

const handleClose = () => {
  handleCancelQuery()
  form.value.queryText = ''
  form.value.title = ''
  selectedSessionKey.value = null
  selectedMessageIndex.value = null
  nlsqlMessages.value = []
  clearResult()
  sessionLoaded.value = false
  directQuery.value = ''
  queryStages.value = []
  queryError.value = ''
  visible.value = false
}
</script>

<style lang="scss" scoped>
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

.result-preview {
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
