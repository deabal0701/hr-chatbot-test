<template>
  <el-row :gutter="20" class="kpi-cards" v-loading="loading">
    <!-- 총 요청 수 -->
    <el-col :xs="12" :sm="12" :lg="6">
      <div class="stat-card">
        <div class="stat-icon is-primary">
          <el-icon :size="24" color="var(--color-primary)"><DataAnalysis /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ formatNumber(kpi.total_requests) }}</div>
          <div class="stat-label">총 요청 수</div>
          <div class="stat-sub">
            NL2SQL {{ formatNumber(kpi.nl2sql_count) }} / RAG {{ formatNumber(kpi.rag_count) }}
          </div>
        </div>
      </div>
    </el-col>

    <!-- 성공률 -->
    <el-col :xs="12" :sm="12" :lg="6">
      <div class="stat-card">
        <div class="stat-icon is-success">
          <el-icon :size="24" color="var(--color-success)"><CircleCheck /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ kpi.success_rate }}%</div>
          <div class="stat-label">성공률</div>
          <div class="stat-sub" :class="{ 'is-error': kpi.error_count > 0 }">
            에러 {{ formatNumber(kpi.error_count) }}건
          </div>
        </div>
      </div>
    </el-col>

    <!-- 활성 사용자 -->
    <el-col :xs="12" :sm="12" :lg="6">
      <div class="stat-card">
        <div class="stat-icon is-warning">
          <el-icon :size="24" color="var(--color-warning)"><User /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ formatNumber(system.active_users) }}</div>
          <div class="stat-label">활성 사용자</div>
          <div class="stat-sub">{{ formatNumber(system.active_tenants) }}개 테넌트</div>
        </div>
      </div>
    </el-col>

    <!-- 전체 문서 -->
    <el-col :xs="12" :sm="12" :lg="6">
      <div class="stat-card">
        <div class="stat-icon is-info">
          <el-icon :size="24" color="var(--color-info)"><Document /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ formatNumber(system.total_documents) }}</div>
          <div class="stat-label">전체 문서</div>
          <div class="stat-sub">
            완료 {{ formatNumber(system.indexed_documents) }} / 대기 {{ formatNumber(system.pending_documents) }}
          </div>
        </div>
      </div>
    </el-col>
  </el-row>
</template>

<script setup>
import { DataAnalysis, CircleCheck, User, Document } from '@element-plus/icons-vue'
import { formatNumber } from '@/utils/format'

defineProps({
  kpi: {
    type: Object,
    default: () => ({ total_requests: 0, success_rate: 0, error_count: 0, nl2sql_count: 0, rag_count: 0 })
  },
  system: {
    type: Object,
    default: () => ({ active_users: 0, active_tenants: 0, total_documents: 0, indexed_documents: 0, pending_documents: 0 })
  },
  loading: { type: Boolean, default: false }
})
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.kpi-cards {
  @include mx.stats-row;

  .stat-card {
    @include mx.stat-card;

    .stat-sub {
      font-size: 12px;
      color: var(--text-color-secondary);
      margin-top: 2px;

      &.is-error {
        color: var(--el-color-danger);
      }
    }
  }
}
</style>
