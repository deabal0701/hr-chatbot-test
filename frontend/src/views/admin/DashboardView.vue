<template>
  <div class="dashboard-view">
    <!-- 페이지 헤더 -->
    <div class="page-header">
      <h2>대시보드</h2>
      <p class="subtitle">HR Chatbot 관리 현황을 확인하세요.</p>
    </div>

    <!-- 통계 카드 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon is-primary">
            <el-icon :size="24" color="#409eff"><Document /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.totalDocuments }}</div>
            <div class="stat-label">전체 문서</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon is-success">
            <el-icon :size="24" color="#67c23a"><CircleCheck /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.indexedDocuments }}</div>
            <div class="stat-label">임베딩 완료</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon is-warning">
            <el-icon :size="24" color="#e6a23c"><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.pendingDocuments }}</div>
            <div class="stat-label">임베딩 대기</div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :sm="12" :lg="6">
        <div class="stat-card">
          <div class="stat-icon is-info">
            <el-icon :size="24" color="#909399"><ChatDotSquare /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.todayChats }}</div>
            <div class="stat-label">오늘 대화</div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- 빠른 액션 및 정보 -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <div class="content-card">
          <h3 class="card-title">빠른 시작</h3>
          <div class="quick-actions">
            <router-link to="/admin/chat" class="action-item">
              <el-icon :size="32" color="#409eff"><ChatDotRound /></el-icon>
              <span>HR 챗봇</span>
              <p>직원 정보 조회, 정책 검색</p>
            </router-link>

            <router-link to="/admin/documents" class="action-item">
              <el-icon :size="32" color="#67c23a"><FolderAdd /></el-icon>
              <span>문서 등록</span>
              <p>새로운 HR 문서 추가</p>
            </router-link>

            <div class="action-item" @click="goToPendingDocuments">
              <el-icon :size="32" color="#e6a23c"><Upload /></el-icon>
              <span>임베딩 실행</span>
              <p>대기 중인 문서 처리</p>
            </div>
          </div>
        </div>
      </el-col>

      <el-col :xs="24" :lg="12">
        <div class="content-card">
          <h3 class="card-title">시스템 정보</h3>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="API 상태">
              <el-tag :type="apiHealthy ? 'success' : 'danger'" size="small">
                {{ apiHealthy ? '정상' : '연결 안됨' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="API 서버">
              {{ apiUrl }}
            </el-descriptions-item>
            <el-descriptions-item label="검색 모드">
              Auto / RAG / NL2SQL
            </el-descriptions-item>
            <el-descriptions-item label="임베딩 모델">
              text-embedding-3-small
            </el-descriptions-item>
            <el-descriptions-item label="LLM 모델">
              GPT-3.5/4
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </el-col>
    </el-row>

    <!-- 최근 문서 -->
    <div class="content-card">
      <div class="card-header">
        <h3 class="card-title">최근 등록 문서</h3>
        <router-link to="/admin/documents">
          <el-button text type="primary">전체보기</el-button>
        </router-link>
      </div>

      <el-table
        :data="recentDocuments"
        v-loading="isLoading"
        size="small"
        style="width: 100%"
      >
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="title" label="제목" min-width="200">
          <template #default="{ row }">
            <router-link :to="`/admin/documents?id=${row.id}`" class="doc-link">
              {{ row.title }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="doc_type" label="유형" width="100">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.doc_type }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="indexed" label="상태" width="100" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.indexed" type="success" size="small">완료</el-tag>
            <el-tag v-else type="warning" size="small">대기</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="등록일" width="120">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import {
  Document,
  CircleCheck,
  Clock,
  ChatDotSquare,
  ChatDotRound,
  FolderAdd,
  Upload
} from '@element-plus/icons-vue'
import documentApi from '@/api/documents'
import { formatDate } from '@/utils/format'

const router = useRouter()
const store = useStore()

const isLoading = ref(false)
const recentDocuments = ref([])
const stats = ref({
  totalDocuments: 0,
  indexedDocuments: 0,
  pendingDocuments: 0,
  todayChats: 0
})

const apiHealthy = computed(() => store.state.app.apiHealthy)
const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// 통계 및 최근 문서 로드
const loadDashboardData = async () => {
  isLoading.value = true

  try {
    // 병렬로 API 호출 (total은 limit과 관계없이 전체 카운트 반환)
    const [allDocs, indexedDocs, pendingDocs, recent] = await Promise.all([
      documentApi.list({ limit: 1 }),           // 전체 문서 카운트
      documentApi.list({ indexed: true, limit: 1 }),   // 임베딩 완료 카운트
      documentApi.list({ indexed: false, limit: 1 }),  // 임베딩 대기 카운트
      documentApi.list({ limit: 5 })            // 최근 문서 5개
    ])

    stats.value.totalDocuments = allDocs.total
    stats.value.indexedDocuments = indexedDocs.total
    stats.value.pendingDocuments = pendingDocs.total
    recentDocuments.value = recent.items || []

    // 오늘 대화 수 (현재는 로컬 상태에서)
    stats.value.todayChats = store.state.chat.messages.filter(
      m => m.role === 'user'
    ).length

  } catch (error) {
    console.error('Dashboard data load error:', error)
  } finally {
    isLoading.value = false
  }
}

// 임베딩 대기 문서로 이동
const goToPendingDocuments = () => {
  router.push('/admin/documents?indexed=false')
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.dashboard-view {
  .stats-row {
    @include mx.stats-row;

    .el-col {
      margin-bottom: 20px;
    }
  }

  .stat-card {
    @include mx.stat-card;
  }

  .card-title {
    margin: 0 0 16px;
    font-size: 16px;
    font-weight: 500;
    color: var(--text-color-primary);
  }

  .card-header {
    @include mx.content-header;
  }

  .quick-actions {
    display: flex;
    gap: 16px;

    .action-item {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 20px;
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

  .doc-link {
    color: var(--color-primary);
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}

@media (max-width: 768px) {
  .quick-actions {
    flex-direction: column;
  }
}
</style>
