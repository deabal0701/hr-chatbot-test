<template>
  <div class="content-card system-status" v-loading="loading">
    <div class="card-header">
      <h3>시스템 현황</h3>
    </div>

    <el-descriptions :column="1" border size="small">
      <el-descriptions-item label="서버 상태">
        <el-tag :type="apiHealthy ? 'success' : 'danger'" size="small">
          {{ apiHealthy ? '정상' : '연결 안됨' }}
        </el-tag>
      </el-descriptions-item>

      <el-descriptions-item label="LLM 프로바이더">
        {{ llmProvider }}
      </el-descriptions-item>

      <el-descriptions-item label="LLM 모델">
        {{ llmModel }}
      </el-descriptions-item>

      <el-descriptions-item label="임베딩 모델">
        {{ embeddingModel }}
      </el-descriptions-item>

      <el-descriptions-item label="활성 테넌트">
        {{ system.active_tenants }}개
      </el-descriptions-item>

      <el-descriptions-item label="활성 사용자">
        {{ system.active_users }}명
      </el-descriptions-item>

      <el-descriptions-item label="마지막 요청">
        {{ formatLastRequest(system.last_request_at) }}
      </el-descriptions-item>

      <el-descriptions-item label="문서 상태">
        <div class="doc-progress">
          <el-progress
            :percentage="docPercentage"
            :stroke-width="14"
            :format="() => `${system.indexed_documents} / ${system.total_documents}`"
          />
        </div>
      </el-descriptions-item>
    </el-descriptions>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'

const store = useStore()

const props = defineProps({
  system: {
    type: Object,
    default: () => ({ active_users: 0, active_tenants: 0, total_documents: 0, indexed_documents: 0, pending_documents: 0 })
  },
  settings: { type: Object, default: () => ({}) },
  loading: { type: Boolean, default: false }
})

const apiHealthy = computed(() => store.state.app?.apiHealthy ?? true)

const llmProvider = computed(() => {
  const s = props.settings
  return s?.llm?.provider || s?.llm?.find?.(i => i.key === 'provider')?.value || 'OpenAI'
})

const llmModel = computed(() => {
  const s = props.settings
  return s?.llm?.model || s?.llm?.find?.(i => i.key === 'model')?.value || '-'
})

const embeddingModel = computed(() => {
  const s = props.settings
  return s?.embedding?.model || s?.embedding?.find?.(i => i.key === 'model')?.value || '-'
})

const docPercentage = computed(() => {
  const total = props.system.total_documents || 0
  const indexed = props.system.indexed_documents || 0
  return total > 0 ? Math.round((indexed / total) * 100) : 0
})

const formatLastRequest = (dateStr) => {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '-'
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  const ss = String(d.getSeconds()).padStart(2, '0')
  return `${yyyy}년 ${mm}월 ${dd}일 ${hh}:${mi}:${ss}`
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.system-status {
  .doc-progress {
    width: 100%;

    :deep(.el-progress__text) {
      font-size: 12px !important;
      min-width: 80px;
    }
  }
}
</style>
