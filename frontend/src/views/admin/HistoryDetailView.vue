<template>
  <div class="history-detail-view">
    <!-- 헤더 -->
    <div class="page-header">
      <div class="header-left">
        <el-button :icon="ArrowLeft" @click="goBack">
          목록으로
        </el-button>
        <h2>요청 상세</h2>
      </div>
      <el-button type="danger" plain :icon="Delete" @click="handleDelete" :loading="isDeleting">
        이력 삭제
      </el-button>
    </div>

    <!-- 내용 -->
    <div class="content-card detail-container" v-loading="isLoading">
      <template v-if="historyItem">
        <el-row :gutter="24">
          <!-- 왼쪽: 메타 정보 -->
          <el-col :span="8">
            <div class="meta-section">
              <h3>기본 정보</h3>

              <el-descriptions :column="1" border size="small" :label-width="200">
                <el-descriptions-item label="ID">{{ historyItem.id }}</el-descriptions-item>
                <el-descriptions-item label="Request ID">
                  <code>{{ historyItem.request_id }}</code>
                </el-descriptions-item>
                <el-descriptions-item label="요청 타입">
                  <el-tag :type="getTypeTag(historyItem.request_type)" size="small">
                    {{ getTypeLabel(historyItem.request_type) }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="세션 ID">
                  <code v-if="historyItem.session_id">{{ historyItem.session_id }}</code>
                  <span v-else class="text-muted">-</span>
                </el-descriptions-item>
                <el-descriptions-item label="성공 여부">
                  <el-tag :type="historyItem.success ? 'success' : 'danger'" size="small">
                    {{ historyItem.success ? '성공' : '실패' }} ({{ historyItem.response_code }})
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="응답 시간">
                  {{ formatResponseTime(historyItem.response_time_ms) }}
                  <span class="text-muted">({{ historyItem.response_time_ms?.toLocaleString() }}ms)</span>
                </el-descriptions-item>
                <el-descriptions-item label="엔드포인트">
                  <code>{{ historyItem.endpoint }}</code>
                </el-descriptions-item>
              </el-descriptions>

              <!-- 사용자 정보 -->
              <h3 style="margin-top: 24px;">사용자 정보</h3>

              <el-descriptions :column="1" border size="small" :label-width="200">
                <el-descriptions-item label="사용자 ID">
                  {{ historyItem.user_id || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="사용자명">
                  {{ historyItem.user_name || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="테넌트 ID">
                  {{ historyItem.tenant_id || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="Client IP">
                  {{ historyItem.client_ip || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="User Agent">
                  <el-tooltip :content="historyItem.user_agent" placement="top" v-if="historyItem.user_agent">
                    <span class="truncate-text">{{ truncateText(historyItem.user_agent, 40) }}</span>
                  </el-tooltip>
                  <span v-else>-</span>
                </el-descriptions-item>
              </el-descriptions>

              <!-- 타임스탬프 -->
              <h3 style="margin-top: 24px;">타임스탬프</h3>

              <el-descriptions :column="1" border size="small" :label-width="200">
                <el-descriptions-item label="요청 시작">
                  {{ formatDateTime(historyItem.requested_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="응답 완료">
                  {{ formatDateTime(historyItem.completed_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="DB 저장">
                  {{ formatDateTime(historyItem.created_at) }}
                </el-descriptions-item>
              </el-descriptions>

              <!-- 세션 히스토리 바로가기 (세션 ID가 있을 경우) -->
              <div class="action-section" v-if="historyItem.session_id">
                <el-button
                  type="primary"
                  plain
                  style="width: 100%"
                  @click="viewSessionHistory"
                >
                  이 세션의 전체 이력 보기
                </el-button>
              </div>
            </div>
          </el-col>

          <!-- 오른쪽: 내용 -->
          <el-col :span="16">
            <div class="content-section">
              <!-- 질문 -->
              <div class="content-block">
                <div class="content-header">
                  <h3>질문</h3>
                  <el-button text :icon="CopyDocument" @click="copyText(historyItem.question)">
                    복사
                  </el-button>
                </div>
                <div class="content-body">
                  {{ historyItem.question || '(질문 없음)' }}
                </div>
              </div>

              <!-- 답변 -->
              <div class="content-block">
                <div class="content-header">
                  <h3>답변</h3>
                  <el-button text :icon="CopyDocument" @click="copyText(historyItem.answer)">
                    복사
                  </el-button>
                </div>
                <div class="content-body answer-body">
                  {{ historyItem.answer || '(답변 없음)' }}
                </div>
              </div>

              <!-- 에러 메시지 (실패 시) -->
              <div class="content-block" v-if="!historyItem.success && historyItem.error_message">
                <div class="content-header">
                  <h3>에러 메시지</h3>
                </div>
                <div class="content-body error-body">
                  {{ historyItem.error_message }}
                </div>
              </div>

              <!-- 실행 추적 (토글 방식) -->
              <div class="trace-section" v-if="historyItem.trace_data">
                <button class="trace-toggle" @click="showTrace = !showTrace">
                  <div class="toggle-left">
                    <el-icon><DataLine /></el-icon>
                    <span>실행 추적 (Tracing)</span>
                  </div>
                  <el-icon class="toggle-icon" :class="{ expanded: showTrace }">
                    <ArrowDown />
                  </el-icon>
                </button>

                <div v-show="showTrace" class="trace-content">
                  <!-- 토글: 포맷팅/JSON -->
                  <div class="trace-view-toggle">
                    <el-button-group size="small">
                      <el-button :type="!showRawJson ? 'primary' : 'default'" @click="showRawJson = false">
                        포맷팅 보기
                      </el-button>
                      <el-button :type="showRawJson ? 'primary' : 'default'" @click="showRawJson = true">
                        JSON 보기
                      </el-button>
                    </el-button-group>
                  </div>

                  <!-- JSON 보기 -->
                  <div v-if="showRawJson" class="json-body">
                    <pre>{{ formatJson(historyItem.trace_data) }}</pre>
                  </div>

                  <!-- 포맷팅 보기 -->
                  <div v-else class="trace-body">
                    <!-- Agent -->
                    <template v-if="historyItem.request_type === 'agent' && historyItem.trace_data">
                      <div class="trace-item">
                        <strong>사용된 도구:</strong>
                        <div class="tools-list">
                          <el-tag
                            v-for="tool in historyItem.trace_data.tools_used || []"
                            :key="tool"
                            size="small"
                            type="info"
                          >
                            {{ tool }}
                          </el-tag>
                          <span v-if="!historyItem.trace_data.tools_used?.length" class="text-muted">없음</span>
                        </div>
                      </div>
                      <div class="trace-item">
                        <strong>반복 횟수:</strong> {{ historyItem.trace_data.iteration_count || 0 }}회
                      </div>
                      <div class="trace-item" v-if="historyItem.trace_data.steps?.length">
                        <strong>실행 단계:</strong>
                        <div class="steps-list">
                          <div v-for="(step, index) in historyItem.trace_data.steps" :key="index" class="step-item">
                            <span class="step-number">{{ index + 1 }}</span>
                            <span class="step-action">{{ step.action || step.tool || '-' }}</span>
                            <span class="step-thought" v-if="step.thought">{{ truncateText(step.thought, 100) }}</span>
                          </div>
                        </div>
                      </div>
                    </template>

                    <!-- NL2SQL -->
                    <template v-else-if="historyItem.request_type === 'nl2sql' && historyItem.trace_data">
                      <div class="trace-item">
                        <strong>생성된 SQL:</strong>
                        <pre class="sql-code">{{ historyItem.trace_data.sql || '-' }}</pre>
                      </div>
                      <div class="trace-item">
                        <strong>턴 수:</strong> {{ historyItem.trace_data.current_turn || 1 }}
                      </div>
                      <div class="trace-item">
                        <strong>검증 통과:</strong>
                        <el-tag :type="historyItem.trace_data.validation_passed ? 'success' : 'danger'" size="small">
                          {{ historyItem.trace_data.validation_passed ? '통과' : '실패' }}
                        </el-tag>
                      </div>
                      <div class="trace-item" v-if="historyItem.trace_data.sql_result">
                        <strong>SQL 결과:</strong>
                        <pre class="sql-result">{{ formatJson(historyItem.trace_data.sql_result) }}</pre>
                      </div>
                    </template>

                    <!-- RAG -->
                    <template v-else-if="historyItem.request_type === 'rag' && historyItem.trace_data">
                      <div class="trace-item">
                        <strong>검색된 문서:</strong> {{ historyItem.trace_data.sources_count || 0 }}개
                      </div>
                      <div class="trace-item">
                        <strong>최고 유사도:</strong>
                        {{ historyItem.trace_data.top_similarity
                          ? (historyItem.trace_data.top_similarity * 100).toFixed(1) + '%'
                          : '-' }}
                      </div>
                      <div class="trace-item" v-if="historyItem.trace_data.sources?.length">
                        <strong>소스 문서:</strong>
                        <div class="sources-list">
                          <div v-for="(source, index) in historyItem.trace_data.sources" :key="index" class="source-item">
                            <span class="source-title">{{ source.title || source.id || `문서 ${index + 1}` }}</span>
                            <el-tag type="info" size="small" v-if="source.similarity || source.similarity_score">
                              {{ ((source.similarity || source.similarity_score) * 100).toFixed(1) }}%
                            </el-tag>
                          </div>
                        </div>
                      </div>
                    </template>

                    <!-- 기타 -->
                    <template v-else>
                      <span class="text-muted">추적 데이터 없음</span>
                    </template>
                  </div>
                </div>
              </div>
            </div>
          </el-col>
        </el-row>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ArrowLeft, ArrowDown, CopyDocument, DataLine, Delete } from '@element-plus/icons-vue'
import historyApi from '@/api/history'
import { formatDateTime, formatResponseTime, truncateText } from '@/utils/format'

const router = useRouter()
const route = useRoute()

const historyItem = ref(null)
const isLoading = ref(false)
const isDeleting = ref(false)
const showRawJson = ref(false)
const showTrace = ref(false)

const requestId = computed(() => route.params.requestId)

// 데이터 로드
onMounted(async () => {
  if (requestId.value) {
    isLoading.value = true
    try {
      historyItem.value = await historyApi.get(requestId.value)
    } catch (error) {
      console.error('Failed to load history detail:', error)
      ElMessage.error('이력 정보를 불러올 수 없습니다.')
      router.push({ name: 'AdminHistory' })
    } finally {
      isLoading.value = false
    }
  }
})

// 목록으로 돌아가기
const goBack = () => {
  router.push({ name: 'AdminHistory' })
}

// 이력 삭제
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(
      '이 검색 이력을 삭제하시겠습니까? 삭제된 이력은 복구할 수 없습니다.',
      '이력 삭제 확인',
      { type: 'warning', confirmButtonText: '삭제', cancelButtonText: '취소' }
    )

    isDeleting.value = true
    await historyApi.delete(requestId.value)
    ElMessage.success('이력이 삭제되었습니다.')
    router.push({ name: 'AdminHistory' })
  } catch (error) {
    if (error !== 'cancel') {
      console.error('Failed to delete history:', error)
      ElMessage.error('이력 삭제에 실패했습니다.')
    }
  } finally {
    isDeleting.value = false
  }
}

// 세션 히스토리 보기
const viewSessionHistory = () => {
  router.push({
    name: 'AdminHistory',
    query: { session_id: historyItem.value.session_id }
  })
}

// 텍스트 복사
const copyText = async (text) => {
  if (!text) {
    ElMessage.warning('복사할 내용이 없습니다.')
    return
  }
  try {
    await navigator.clipboard.writeText(text)
    ElMessage.success('클립보드에 복사되었습니다.')
  } catch (error) {
    ElMessage.error('복사에 실패했습니다.')
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


const formatJson = (data) => {
  if (!data) return '-'
  try {
    return JSON.stringify(data, null, 2)
  } catch {
    return String(data)
  }
}
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.history-detail-view {
  height: 100%;
  display: flex;
  flex-direction: column;

  .page-header {
    align-items: center;

    .header-left {
      @include mx.page-header-left;

      h2 {
        font-size: 24px;
        font-weight: 600;
        color: var(--text-color-primary);
      }
    }
  }

  .content-card {
    padding: 24px;
  }

  .detail-container {
    flex: 1;
    overflow: auto;
  }

  .meta-section {
    flex: 1;
    display: flex;
    flex-direction: column;

    h3 {
      margin: 0 0 16px;
      font-size: 15px;
      font-weight: 600;
      color: var(--text-color-primary);
    }

    .action-section {
      margin-top: 12px;
    }

    code {
      padding: 2px 6px;
      background-color: var(--bg-color-code);
      border-radius: 4px;
      font-family: monospace;
      font-size: 12px;
    }

    .text-muted {
      color: var(--text-color-secondary);
    }

    .truncate-text {
      display: inline-block;
      max-width: 200px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      vertical-align: middle;
    }
  }

  .content-section {
    display: flex;
    flex-direction: column;
    height: 100%;

    .content-block {
      margin-bottom: 24px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    .content-header {
      @include mx.content-header;
      margin-bottom: 12px;

      h3 {
        font-size: 15px;
      }
    }

    .content-body {
      padding: 16px;
      background-color: var(--bg-color-hover);
      border-radius: 8px;
      font-size: 14px;
      line-height: 1.7;
      color: var(--text-color-primary);
      white-space: pre-wrap;
      word-break: break-word;
      transition: var(--theme-transition);

      &.answer-body {
        min-height: 420px;
        max-height: 420px;
        overflow-y: auto;
      }

      &.error-body {
        background-color: #fef0f0;
        color: #f56c6c;
      }
    }

    // 실행 추적 토글 섹션 (mixin)
    .trace-section {
      @include mx.toggle-section-container($margin-top: 24px, $border-radius: 8px);

      .trace-toggle {
        @include mx.toggle-button($padding: 14px 16px);

        .toggle-left .el-icon {
          color: var(--color-primary);
        }
      }

      .trace-content {
        padding: 16px;
        border-top: 1px solid var(--border-color-light);
        background-color: var(--bg-color-overlay);

        .trace-view-toggle {
          margin-bottom: 16px;
        }

        .json-body {
          padding: 16px;
          background-color: var(--bg-color-code);
          border-radius: 6px;
          max-height: 400px;
          overflow: auto;

          pre {
            margin: 0;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            color: var(--text-color-primary);
          }
        }

        .trace-body {
          .trace-item {
            margin-bottom: 16px;

            &:last-child {
              margin-bottom: 0;
            }

            strong {
              display: block;
              margin-bottom: 8px;
              color: var(--text-color-primary);
              font-size: 13px;
            }

            .tools-list {
              display: flex;
              flex-wrap: wrap;
              gap: 6px;
            }

            .sql-code, .sql-result {
              margin-top: 8px;
              padding: 12px;
              background-color: var(--bg-color-code);
              border-radius: 4px;
              font-family: 'Consolas', 'Monaco', monospace;
              font-size: 12px;
              overflow-x: auto;
              white-space: pre;
              max-height: 300px;
              overflow-y: auto;
            }

            .steps-list {
              margin-top: 8px;

              .step-item {
                display: flex;
                align-items: flex-start;
                gap: 8px;
                padding: 8px;
                margin-bottom: 4px;
                background-color: var(--bg-color-code);
                border-radius: 4px;

                .step-number {
                  flex-shrink: 0;
                  width: 20px;
                  height: 20px;
                  border-radius: 50%;
                  background-color: var(--color-primary);
                  color: white;
                  font-size: 12px;
                  font-weight: bold;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                }

                .step-action {
                  font-weight: 500;
                  color: var(--text-color-primary);
                }

                .step-thought {
                  color: var(--text-color-secondary);
                  font-size: 13px;
                }
              }
            }

            .sources-list {
              margin-top: 8px;

              .source-item {
                display: flex;
                align-items: center;
                justify-content: space-between;
                padding: 8px 12px;
                margin-bottom: 4px;
                background-color: var(--bg-color-code);
                border-radius: 4px;

                .source-title {
                  font-size: 13px;
                  color: var(--text-color-primary);
                }
              }
            }
          }

          .text-muted {
            color: var(--text-color-secondary);
          }
        }
      }
    }
  }
}
</style>
