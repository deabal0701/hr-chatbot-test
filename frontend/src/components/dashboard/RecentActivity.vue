<template>
  <div class="content-card recent-activity" v-loading="loading">
    <div class="card-header">
      <h3>최근 검색 요청</h3>
      <router-link to="/admin/history">
        <el-button text type="primary" size="small">전체보기</el-button>
      </router-link>
    </div>

    <ul class="activity-list" v-if="data && data.length">
      <li v-for="item in data" :key="item.request_id" class="activity-item"
          @click="goToDetail(item.request_id)">
        <span class="activity-time">{{ formatTime(item.created_at) }}</span>
        <el-tag :type="typeTag(item.request_type)" size="small" effect="plain">
          {{ item.request_type?.toUpperCase() }}
        </el-tag>
        <span class="activity-question">{{ item.question }}</span>
        <span class="activity-meta">
          <el-icon v-if="!item.success" color="var(--color-danger)"><CircleCloseFilled /></el-icon>
          <span class="activity-time-ms">{{ formatResponseTime(item.response_time_ms) }}</span>
        </span>
      </li>
    </ul>
    <div v-else class="empty-text">검색 이력이 없습니다</div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { CircleCloseFilled } from '@element-plus/icons-vue'
import { formatResponseTime } from '@/utils/format'

const router = useRouter()

defineProps({
  data: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false }
})

const typeTag = (type) => {
  if (type === 'nl2sql') return 'success'
  if (type === 'rag') return 'warning'
  return 'info'
}

const formatTime = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '-'
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

const goToDetail = (requestId) => {
  router.push({ name: 'AdminHistoryDetail', params: { requestId } })
}
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.recent-activity {
  display: flex;
  flex-direction: column;

  .activity-list {
    @include mx.activity-list;
  }

  .activity-item {
    cursor: pointer;
    transition: background-color 0.15s;
    padding: 6px 8px;
    border-radius: 4px;

    &:hover {
      background-color: var(--bg-color-hover);
    }
  }

  .activity-time {
    font-size: 12px;
    color: var(--text-color-secondary);
    min-width: 42px;
    flex-shrink: 0;
  }

  .activity-question {
    flex: 1;
    font-size: 13px;
    color: var(--text-color-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .activity-meta {
    display: flex;
    align-items: center;
    gap: 4px;
    flex-shrink: 0;
  }

  .activity-time-ms {
    font-size: 12px;
    color: var(--text-color-secondary);
  }

  .empty-text {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    color: var(--text-color-secondary);
  }
}
</style>
