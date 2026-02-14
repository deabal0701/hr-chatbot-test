<template>
  <div class="history-view">
    <!-- 헤더 영역 -->
    <div class="page-header">
      <div>
        <h2>검색 이력</h2>
        <p class="subtitle">검색 요청 이력을 조회하고 분석합니다.</p>
      </div>
      <el-button type="danger" plain :icon="Delete" @click="showCleanupDialog">
        이력 정리
      </el-button>
    </div>

    <!-- 통계 카드 (숨김 처리) -->
    <el-row v-if="showStats" :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon" style="background-color: #ecf5ff">
            <el-icon :size="24" color="#409eff"><List /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatNumber(stats.total_requests) }}</div>
            <div class="stat-label">전체 요청</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon" style="background-color: #f0f9eb">
            <el-icon :size="24" color="#67c23a"><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.success_rate }}%</div>
            <div class="stat-label">성공률 (에러 {{ stats.error_count }}건)</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon" style="background-color: #fdf6ec">
            <el-icon :size="24" color="#e6a23c"><Timer /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ formatResponseTime(stats.avg_response_time_ms) }}</div>
            <div class="stat-label">평균 응답시간</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon request-type-stats">
            <div class="type-item">
              <span class="type-badge agent">A</span>
              <span>{{ stats.agent_count }}</span>
            </div>
            <div class="type-item">
              <span class="type-badge nl2sql">S</span>
              <span>{{ stats.nl2sql_count }}</span>
            </div>
            <div class="type-item">
              <span class="type-badge rag">R</span>
              <span>{{ stats.rag_count }}</span>
            </div>
          </div>
          <div class="stat-content">
            <div class="stat-label">타입별 현황</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 필터 및 액션 -->
    <div class="content-card filter-section">
      <div class="filter-row">
        <el-select
          v-model="filters.request_type"
          placeholder="요청 타입"
          clearable
          style="width: 120px"
          @change="handleFilterChange"
        >
          <el-option label="Agent" value="agent" />
          <el-option label="NL2SQL" value="nl2sql" />
          <el-option label="RAG" value="rag" />
        </el-select>

        <el-select
          v-model="filters.success_only"
          placeholder="성공/실패"
          clearable
          style="width: 120px"
          @change="handleFilterChange"
        >
          <el-option label="성공" :value="true" />
          <el-option label="실패" :value="false" />
        </el-select>

        <el-date-picker
          v-model="dateRange"
          type="daterange"
          range-separator="~"
          start-placeholder="시작일"
          end-placeholder="종료일"
          value-format="YYYY-MM-DDTHH:mm:ss"
          style="width: 280px"
          @change="handleDateRangeChange"
        />

        <el-button :icon="Refresh" @click="resetFilters">
          필터 초기화
        </el-button>

        <div class="flex-1" />

        <!-- 세션 필터 표시 (세션 ID로 필터링 중일 때) -->
        <el-tag
          v-if="filters.session_id"
          type="info"
          closable
          @close="clearSessionFilter"
        >
          세션: {{ filters.session_id }}
        </el-tag>

        <el-input
          v-model="filters.session_id"
          placeholder="세션 ID 검색"
          clearable
          style="width: 180px"
          @clear="handleFilterChange"
          @keyup.enter="handleFilterChange"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 이력 목록 -->
    <div class="content-card">
      <el-table
        v-loading="isLoading"
        :data="historyList"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="70" />

        <el-table-column prop="question" label="질문" min-width="200">
          <template #default="{ row }">
            <span class="title-link" :title="row.question" @click="goToDetail(row)">{{ row.question }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="request_id" label="요청ID" width="100">
          <template #default="{ row }">
            <span class="request-id" :title="row.request_id">{{ row.request_id }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="request_type" label="타입" width="90" align="center">
          <template #default="{ row }">
            <el-tag :type="getTypeTag(row.request_type)" size="small">
              {{ getTypeLabel(row.request_type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="user_name" label="사용자" width="100">
          <template #default="{ row }">
            <span v-if="row.user_name || row.user_id">
              {{ row.user_name || row.user_id }}
            </span>
            <span v-else class="text-muted">익명</span>
          </template>
        </el-table-column>

        <el-table-column prop="success" label="성공" width="70" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.success" color="#67c23a" :size="18"><CircleCheck /></el-icon>
            <el-icon v-else color="#f56c6c" :size="18"><CircleClose /></el-icon>
          </template>
        </el-table-column>

        <el-table-column prop="response_time_ms" label="응답시간" width="90" align="right">
          <template #default="{ row }">
            {{ formatResponseTime(row.response_time_ms) }}
          </template>
        </el-table-column>

        <el-table-column prop="requested_at" label="요청시간" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.requested_at) }}
          </template>
        </el-table-column>

        <el-table-column label="작업" width="70" align="center">
          <template #default="{ row }">
            <el-button
              type="danger"
              text
              :icon="Delete"
              size="small"
              @click.stop="handleDeleteRow(row)"
            />
          </template>
        </el-table-column>
      </el-table>

      <!-- 페이지네이션 -->
      <div class="pagination-wrapper">
        <el-pagination
          :current-page="currentPage"
          :page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalCount"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </div>

    <!-- 이력 정리 다이얼로그 -->
    <el-dialog
      v-model="cleanupDialogVisible"
      title="오래된 이력 정리"
      width="400px"
    >
      <el-form label-width="100px">
        <el-form-item label="보관 기간">
          <el-input-number
            v-model="cleanupDays"
            :min="7"
            :max="365"
            :step="30"
          />
          <span style="margin-left: 8px">일</span>
        </el-form-item>
        <el-alert
          type="warning"
          :closable="false"
          show-icon
        >
          {{ cleanupDays }}일 이전의 이력이 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
        </el-alert>
      </el-form>
      <template #footer>
        <el-button @click="cleanupDialogVisible = false">취소</el-button>
        <el-button type="danger" @click="executeCleanup" :loading="isCleaningUp">
          삭제 실행
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  List,
  CircleCheck,
  CircleClose,
  Timer,
  Delete,
  Refresh,
  Search
} from '@element-plus/icons-vue'
import historyApi from '@/api/history'

const router = useRouter()
const route = useRoute()

// 상태
const isLoading = ref(false)
const historyList = ref([])
const totalCount = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)

// 통계
const stats = ref({
  total_requests: 0,
  success_count: 0,
  error_count: 0,
  success_rate: 0,
  avg_response_time_ms: 0,
  agent_count: 0,
  nl2sql_count: 0,
  rag_count: 0
})

// 필터
const filters = reactive({
  request_type: null,
  success_only: null,
  session_id: '',
  from_date: null,
  to_date: null
})
const dateRange = ref(null)

// 통계 카드 표시 여부
const showStats = ref(false)

// 정리 다이얼로그
const cleanupDialogVisible = ref(false)
const cleanupDays = ref(90)
const isCleaningUp = ref(false)

// 계산된 offset
const offset = computed(() => (currentPage.value - 1) * pageSize.value)

// 데이터 로드
const loadData = async () => {
  isLoading.value = true
  try {
    const params = {
      limit: pageSize.value,
      offset: offset.value
    }

    if (filters.request_type) params.request_type = filters.request_type
    if (filters.success_only !== null) params.success_only = filters.success_only
    if (filters.session_id) params.session_id = filters.session_id
    if (filters.from_date) params.from_date = filters.from_date
    if (filters.to_date) params.to_date = filters.to_date

    const result = await historyApi.list(params)
    historyList.value = result.items || []
    totalCount.value = result.total || 0
  } catch (error) {
    console.error('Failed to load history:', error)
    ElMessage.error('이력 조회에 실패했습니다.')
  } finally {
    isLoading.value = false
  }
}

// 통계 로드
const loadStatistics = async () => {
  try {
    const params = {}
    if (filters.from_date) params.from_date = filters.from_date
    if (filters.to_date) params.to_date = filters.to_date

    const result = await historyApi.getStatistics(params)
    stats.value = {
      total_requests: result.total_requests || 0,
      success_count: result.success_count || 0,
      error_count: result.error_count || 0,
      success_rate: result.success_rate || 0,
      avg_response_time_ms: result.avg_response_time_ms || 0,
      agent_count: result.agent_count || 0,
      nl2sql_count: result.nl2sql_count || 0,
      rag_count: result.rag_count || 0
    }
  } catch (error) {
    console.error('Failed to load statistics:', error)
  }
}

// 필터 변경 핸들러
const handleFilterChange = () => {
  currentPage.value = 1
  // URL 쿼리 파라미터 업데이트 (세션 ID)
  if (filters.session_id) {
    router.replace({ query: { session_id: filters.session_id } })
  } else {
    router.replace({ query: {} })
  }
  loadData()
}

// 날짜 범위 변경
const handleDateRangeChange = (range) => {
  if (range) {
    filters.from_date = range[0]
    filters.to_date = range[1]
  } else {
    filters.from_date = null
    filters.to_date = null
  }
  handleFilterChange()
  loadStatistics()
}

// 세션 필터 제거
const clearSessionFilter = () => {
  filters.session_id = ''
  router.replace({ query: {} })
  loadData()
}

// 필터 초기화
const resetFilters = () => {
  filters.request_type = null
  filters.success_only = null
  filters.session_id = ''
  filters.from_date = null
  filters.to_date = null
  dateRange.value = null
  currentPage.value = 1
  router.replace({ query: {} })
  loadData()
  loadStatistics()
}

// 페이지 변경
const handlePageChange = (page) => {
  currentPage.value = page
  loadData()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
  loadData()
}

// 개별 이력 삭제
const handleDeleteRow = async (row) => {
  try {
    await ElMessageBox.confirm(
      '이 검색 이력을 삭제하시겠습니까? 삭제된 이력은 복구할 수 없습니다.',
      '이력 삭제 확인',
      { type: 'warning', confirmButtonText: '삭제', cancelButtonText: '취소' }
    )

    await historyApi.delete(row.request_id)
    ElMessage.success('이력이 삭제되었습니다.')
    loadData()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete history:', error)
      ElMessage.error('이력 삭제에 실패했습니다.')
    }
  }
}

// 상세 페이지로 이동
const goToDetail = (row) => {
  router.push({
    name: 'AdminHistoryDetail',
    params: { requestId: row.request_id }
  })
}

// 정리 다이얼로그
const showCleanupDialog = () => {
  cleanupDays.value = 90
  cleanupDialogVisible.value = true
}

// 정리 실행
const executeCleanup = async () => {
  try {
    await ElMessageBox.confirm(
      `정말로 ${cleanupDays.value}일 이전의 이력을 삭제하시겠습니까?`,
      '확인',
      { type: 'warning' }
    )

    isCleaningUp.value = true
    const result = await historyApi.cleanup(cleanupDays.value)
    ElMessage.success(`${result.deleted_count}건의 이력이 삭제되었습니다.`)
    cleanupDialogVisible.value = false
    loadData()
    loadStatistics()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Cleanup failed:', error)
      ElMessage.error('이력 정리에 실패했습니다.')
    }
  } finally {
    isCleaningUp.value = false
  }
}

// 유틸리티 함수
const getTypeTag = (type) => {
  const tags = {
    agent: 'primary',
    nl2sql: 'success',
    rag: 'warning'
  }
  return tags[type] || 'info'
}

const getTypeLabel = (type) => {
  const labels = {
    agent: 'Agent',
    nl2sql: 'NL2SQL',
    rag: 'RAG'
  }
  return labels[type] || type
}

const formatNumber = (num) => {
  return (num || 0).toLocaleString()
}

const formatResponseTime = (ms) => {
  if (!ms) return '-'
  if (ms < 1000) return `${ms}ms`
  return `${(ms / 1000).toFixed(1)}s`
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  const second = String(date.getSeconds()).padStart(2, '0')
  return `${year}.${month}.${day} ${hour}:${minute}:${second}`
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

// URL 쿼리 파라미터 감시 (session_id 직접 감시)
watch(() => route.query.session_id, (newSessionId) => {
  filters.session_id = newSessionId || ''
  loadData()
}, { immediate: true })

// 초기 로드
onMounted(() => {
  loadStatistics()
})
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.history-view {
  .page-header {
    @include mx.page-header;
  }

  .stats-row {
    @include mx.stats-row;
  }

  .stat-card {
    @include mx.stat-card;

    // HistoryView 고유: 타입별 현황 아이콘
    .stat-icon {
      &.request-type-stats {
        flex-direction: column;
        gap: 4px;
        background: transparent;
        width: auto;

        .type-item {
          display: flex;
          align-items: center;
          gap: 4px;
          font-size: 12px;
        }

        .type-badge {
          width: 18px;
          height: 18px;
          border-radius: 4px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 10px;
          font-weight: bold;
          color: white;

          &.agent { background-color: #409eff; }
          &.nl2sql { background-color: #67c23a; }
          &.rag { background-color: #e6a23c; }
        }
      }
    }
  }

  .content-card {
    @include mx.content-card;
  }

  .filter-section {
    .filter-row {
      @include mx.filter-row;

      .flex-1 {
        flex: 1;
      }
    }
  }

  .request-id {
    font-family: monospace;
    font-size: 12px;
  }

  .title-link {
    @include mx.title-link;
  }

  .text-muted {
    color: var(--text-color-secondary);
  }

  .pagination-wrapper {
    @include mx.pagination-wrapper;
  }
}
</style>
