<template>
  <div class="dashboard-view">
    <!-- 페이지 헤더 + 기간 필터 -->
    <div class="page-header">
      <div>
        <h2>대시보드</h2>
        <p class="subtitle">MUREUM AI 지식기반 관리 현황</p>
      </div>
      <div class="header-actions">
        <el-button-group>
          <el-button :type="period === 'today' ? 'primary' : ''"
                     size="small" @click="changePeriod('today')">오늘</el-button>
          <el-button :type="period === 'week' ? 'primary' : ''"
                     size="small" @click="changePeriod('week')">최근 7일</el-button>
          <el-button :type="period === 'month' ? 'primary' : ''"
                     size="small" @click="changePeriod('month')">최근 1달</el-button>
        </el-button-group>
        <el-button :icon="Refresh" circle size="small"
                   @click="loadDashboardData" :loading="isLoading" />
      </div>
    </div>

    <!-- ① KPI 카드 (1줄 4개) -->
    <KpiCards :kpi="summaryData.kpi" :system="summaryData.system"
              :loading="isLoading" />

    <!-- ② 차트 영역 (2개) -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <DailyTrendChart :data="summaryData.daily_trend"
                         :loading="isLoading" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <RequestTypeChart :kpi="summaryData.kpi"
                          :loading="isLoading" />
      </el-col>
    </el-row>

    <!-- ③ 최근 활동 + 시스템 현황 -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <RecentActivity :data="summaryData.recent_requests"
                        :loading="isLoading" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <SystemStatus :system="summaryData.system"
                      :settings="settingsData"
                      :loading="isLoading" />
      </el-col>
    </el-row>

    <!-- ④ 빠른 액션 -->
    <div class="content-card">
      <h3 class="card-title">빠른 시작</h3>
      <div class="quick-actions">
        <router-link to="/admin/chat" class="action-item">
          <el-icon :size="32" class="icon-primary"><ChatDotRound /></el-icon>
          <span>자연어 검색</span>
          <p>AI 기반 문서 검색, 데이터 조회</p>
        </router-link>

        <router-link to="/admin/documents" class="action-item">
          <el-icon :size="32" class="icon-success"><FolderAdd /></el-icon>
          <span>문서 등록</span>
          <p>새로운 지식 문서 추가</p>
        </router-link>

        <div class="action-item" @click="goTo('/admin/documents?indexed=false')">
          <el-icon :size="32" class="icon-warning"><Upload /></el-icon>
          <span>임베딩 실행</span>
          <p>대기 중인 문서 처리</p>
        </div>

        <router-link to="/admin/users" class="action-item">
          <el-icon :size="32" class="icon-primary"><UserFilled /></el-icon>
          <span>사용자 관리</span>
          <p>사용자 생성/수정</p>
        </router-link>

        <router-link to="/admin/settings" class="action-item">
          <el-icon :size="32" class="icon-info"><Setting /></el-icon>
          <span>설정 관리</span>
          <p>시스템 설정</p>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import {
  Refresh,
  ChatDotRound,
  FolderAdd,
  Upload,
  UserFilled,
  Setting
} from '@element-plus/icons-vue'
import dashboardApi from '@/api/dashboard'
import settingsApi from '@/api/settings'
import KpiCards from '@/components/dashboard/KpiCards.vue'
import DailyTrendChart from '@/components/dashboard/DailyTrendChart.vue'
import RequestTypeChart from '@/components/dashboard/RequestTypeChart.vue'
import RecentActivity from '@/components/dashboard/RecentActivity.vue'
import SystemStatus from '@/components/dashboard/SystemStatus.vue'

const router = useRouter()

const isLoading = ref(false)
const period = ref('today')

const summaryData = ref({
  kpi: { total_requests: 0, success_rate: 0, error_count: 0, nl2sql_count: 0, rag_count: 0 },
  daily_trend: [],
  recent_requests: [],
  system: { active_users: 0, active_tenants: 0, total_documents: 0, indexed_documents: 0, pending_documents: 0 },
})
const settingsData = ref({})

// 자동 새로고침 타이머
let refreshTimer = null
const REFRESH_INTERVAL = 60000

const loadDashboardData = async () => {
  isLoading.value = true
  try {
    const [summary, llmSettings, embeddingSettings, nl2sqlSettings] = await Promise.all([
      dashboardApi.getSummary({ period: period.value }),
      settingsApi.getCategory('llm').catch(() => ({})),
      settingsApi.getCategory('embedding').catch(() => ({})),
      settingsApi.getCategory('nl2sql').catch(() => ({})),
    ])
    summaryData.value = summary || summaryData.value
    settingsData.value = {
      llm: llmSettings?.settings || llmSettings?.items || [],
      embedding: embeddingSettings?.settings || embeddingSettings?.items || [],
      nl2sql: nl2sqlSettings?.settings || nl2sqlSettings?.items || [],
    }
  } catch (error) {
    console.error('Dashboard data load error:', error)
  } finally {
    isLoading.value = false
  }
}

const changePeriod = (newPeriod) => {
  period.value = newPeriod
  loadDashboardData()
}

const goTo = (path) => {
  router.push(path)
}

// 자동 새로고침 (화면 비활성 시 중지)
const startAutoRefresh = () => {
  stopAutoRefresh()
  refreshTimer = setInterval(() => {
    if (!document.hidden) {
      loadDashboardData()
    }
  }, REFRESH_INTERVAL)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}

const handleVisibilityChange = () => {
  if (!document.hidden) {
    loadDashboardData()
  }
}

onMounted(() => {
  loadDashboardData()
  startAutoRefresh()
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onBeforeUnmount(() => {
  stopAutoRefresh()
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
</script>

<style lang="scss" scoped>
.dashboard-view {
  .page-header {
    align-items: center;

    .subtitle {
      margin: 4px 0 0;
      font-size: 14px;
      color: var(--text-color-secondary);
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .el-row {
    margin-bottom: 12px;
    display: flex;
    flex-wrap: wrap;
    align-items: stretch;

    :deep(.el-col) {
      display: flex;
      flex-direction: column;

      > * {
        flex: 1;
      }
    }
  }

  .card-title {
    margin: 0 0 16px;
    font-size: 16px;
    font-weight: 500;
    color: var(--text-color-primary);
  }

  .icon-primary { color: var(--color-primary); }
  .icon-success { color: var(--color-success); }
  .icon-warning { color: var(--color-warning); }
  .icon-info { color: var(--color-info); }

  .quick-actions {
    display: flex;
    gap: 16px;

    .action-item {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 12px;
      background-color: var(--bg-color-hover);
      border-radius: 8px;
      text-decoration: none;
      color: inherit;
      cursor: pointer;
      transition: var(--theme-transition);

      &:hover {
        background-color: var(--bg-color-code);
        transform: translateY(-2px);
      }

      span {
        margin-top: 12px;
        font-size: 14px;
        font-weight: 500;
        color: var(--text-color-primary);
      }

      p {
        margin: 6px 0 0;
        font-size: 12px;
        color: var(--text-color-secondary);
        text-align: center;
      }
    }
  }

}

@media (max-width: 768px) {
  .quick-actions {
    flex-wrap: wrap;

    .action-item {
      min-width: calc(50% - 8px);
    }
  }
}
</style>
