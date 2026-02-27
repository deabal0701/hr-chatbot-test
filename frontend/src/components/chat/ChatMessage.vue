<template>
  <div class="chat-message" :class="message.role">
    <!-- 사용자 메시지 -->
    <div v-if="message.role === 'user'" class="message-bubble user">
      <div class="message-content">{{ message.content }}</div>
    </div>

    <!-- AI 응답 -->
    <div v-else class="message-bubble assistant" :class="{ error: message.isError }">
      <!-- SSE 스트리밍 진행 상태 -->
      <template v-if="message.isStreaming">
        <div class="streaming-indicator">
          <div class="stream-steps" v-if="message.streamProgress && message.streamProgress.length > 0">
            <div class="stream-step" v-for="(p, idx) in message.streamProgress" :key="idx">
              <span class="step-check-icon">&#10003;</span>
              <span class="step-label">{{ p.message }}</span>
            </div>
          </div>
          <div class="streaming-current">
            <div class="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span class="streaming-text">{{ message.currentStep || '처리 중...' }}</span>
          </div>
        </div>
      </template>
      <!-- 최종 응답 -->
      <template v-else>
        <div class="message-content" v-html="formattedContent"></div>
      </template>

      <!-- 메타 정보 -->
      <div v-if="!message.isError" class="message-meta">
        <el-tag size="small" :type="queryTypeTag.type" effect="plain">
          {{ queryTypeTag.label }}
        </el-tag>
        <!-- 멀티턴 인디케이터 -->
        <span v-if="turnInfo" class="turn-indicator">
          {{ turnInfo }}
        </span>
        <span v-if="message.responseTimeMs" class="response-time">
          {{ message.responseTimeMs }}ms
        </span>
      </div>

      <!-- NL2SQL 결과 (통합 SearchResponse 구조) -->
      <div v-if="message.sql" class="nl2sql-result">
        <el-collapse>
          <el-collapse-item title="실행된 SQL 쿼리" name="sql">
            <pre class="sql-code">{{ message.sql }}</pre>
          </el-collapse-item>
          <el-collapse-item v-if="message.sqlResult" title="조회 결과" name="result">
            <div class="result-summary">
              총 {{ message.sqlResult.row_count }}개 행 조회됨
            </div>
            <el-table
              v-if="message.sqlResult.rows.length > 0"
              :data="message.sqlResult.rows.slice(0, 1000)"
              size="small"
              border
              max-height="500"
            >
              <el-table-column
                v-for="col in message.sqlResult.columns"
                :key="col"
                :prop="col"
                :label="col"
                min-width="100"
              />
            </el-table>
            <div v-if="message.sqlResult.row_count > 1000" class="more-rows">
              ... 외 {{ message.sqlResult.row_count - 1000 }}개 행
            </div>
            <!-- 차트 생성 -->
            <ChartBuilder
              ref="chartBuilderRef"
              v-if="message.sqlResult.rows.length > 0"
              :columns="message.sqlResult.columns"
              :rows="message.sqlResult.rows"
            />
            <div class="export-bar">
              <el-button size="small" :icon="Download" :loading="exporting" @click="exportToExcel">
                Excel 다운로드
              </el-button>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- RAG 출처 (통합 SearchResponse 구조) -->
      <div v-if="message.sources?.length > 0" class="rag-sources">
        <div class="sources-title">
          <el-icon><Document /></el-icon>
          참고 문서 ({{ message.sources.length }}개)
        </div>
        <div class="sources-list">
          <SourceCard
            v-for="source in message.sources"
            :key="source.id"
            :source="source"
          />
        </div>
      </div>

      <!-- Agent 결과 -->
      <div v-if="message.agentResult" class="agent-result">
        <el-collapse>
          <el-collapse-item title="실행 단계 보기" name="steps">
            <div class="agent-summary">
              <el-tag size="small" type="success">
                총 {{ message.agentResult.totalIterations }}번 반복
              </el-tag>
              <el-tag size="small" type="info" v-if="message.agentResult.toolsUsed">
                사용 도구: {{ message.agentResult.toolsUsed.join(', ') }}
              </el-tag>
              <el-tag size="small" :type="message.agentResult.success ? 'success' : 'danger'">
                {{ message.agentResult.success ? '성공' : '실패' }}
              </el-tag>
            </div>

            <div v-if="message.agentResult.steps?.length > 0" class="steps-list">
              <div
                v-for="(step, index) in message.agentResult.steps"
                :key="index"
                class="step-item"
              >
                <div class="step-header">
                  <span class="step-number">Step {{ step.step_number || (index + 1) }}</span>
                  <el-tag size="small" type="primary">{{ step.action }}</el-tag>
                </div>
                <div class="step-content">
                  <div v-if="step.thought" class="step-thought">
                    <strong>생각:</strong> {{ step.thought }}
                  </div>
                  <div v-if="step.observation" class="step-observation">
                    <strong>관찰:</strong> {{ step.observation }}
                  </div>

                  <div v-if="step.sql_result" class="step-sql-result">
                    <el-collapse>
                      <el-collapse-item title="SQL 쿼리 및 결과 보기" name="sql">
                        <div class="sql-section">
                          <div class="sql-label">실행된 SQL:</div>
                          <pre class="sql-code">{{ step.sql_result.sql }}</pre>
                        </div>
                        <div v-if="step.sql_result.rows?.length > 0" class="result-section">
                          <div class="result-summary">
                            총 {{ step.sql_result.row_count }}개 행 조회됨
                            <span v-if="step.sql_result.execution_time_ms">
                              ({{ step.sql_result.execution_time_ms }}ms)
                            </span>
                          </div>
                          <el-table
                            :data="step.sql_result.rows.slice(0, 1000)"
                            size="small"
                            border
                            max-height="500"
                          >
                            <el-table-column
                              v-for="col in step.sql_result.columns"
                              :key="col"
                              :prop="col"
                              :label="col"
                              min-width="100"
                            />
                          </el-table>
                          <div v-if="step.sql_result.row_count > 1000" class="more-rows">
                            ... 외 {{ step.sql_result.row_count - 1000 }}개 행
                          </div>
                          <ChartBuilder
                            :columns="step.sql_result.columns"
                            :rows="step.sql_result.rows"
                          />
                        </div>
                        <div v-else class="no-results">
                          조회 결과가 없습니다.
                        </div>
                      </el-collapse-item>
                    </el-collapse>
                  </div>
                </div>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </div>

    <!-- 타임스탬프 -->
    <div class="message-time">
      {{ formatTime(message.timestamp) }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Document, Download } from '@element-plus/icons-vue'
import SourceCard from './SourceCard.vue'
import ChartBuilder from '../chart/ChartBuilder.vue'
import searchApi from '@/api/search'
import { ElMessage } from 'element-plus'
import { formatMarkdownToHtml, registerTableCopyFunction } from '@/utils/markdownParser'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

// 전역 테이블 복사 함수 등록
onMounted(() => {
  registerTableCopyFunction()

  if (import.meta.env.DEV && props.message.role === 'assistant') {
    console.log('[ChatMessage Mounted]', props.message)
    console.log('[ChatMessage Content]', props.message.content)
    console.log('[ChatMessage Content Type]', typeof props.message.content)
    console.log('[ChatMessage Content Length]', props.message.content?.length)
  }
})

watch(() => props.message.content, (newVal) => {
  if (import.meta.env.DEV) {
    console.log('[ChatMessage Content Changed]', newVal)
  }
}, { immediate: true })

// 마크다운 처리 (모듈 사용)
const formattedContent = computed(() => {
  return formatMarkdownToHtml(props.message.content)
})

const queryTypeTag = computed(() => {
  switch (props.message.queryType) {
    case 'rag':
      return { label: 'RAG', type: 'success' }
    case 'nl2sql':
      return { label: 'NL2SQL', type: 'warning' }
    case 'agent':
      return { label: 'Agent', type: 'primary' }
    default:
      return { label: 'Auto', type: 'info' }
  }
})

// 멀티턴 인디케이터 (NL2SQL 모드에서만 표시)
const turnInfo = computed(() => {
  const metadata = props.message.metadata
  if (!metadata) return null

  const currentTurn = metadata.current_turn
  const maxTurns = metadata.max_turns

  // NL2SQL 모드이고 멀티턴 정보가 있을 때만 표시
  if (currentTurn && maxTurns && props.message.queryType === 'nl2sql') {
    return `턴 ${currentTurn}/${maxTurns}`
  }
  return null
})

const chartBuilderRef = ref(null)
const exporting = ref(false)

// Excel 내보내기
const exportToExcel = async () => {
  exporting.value = true
  try {
    const msg = props.message
    const cb = chartBuilderRef.value
    const includeChart = cb?.chartGenerated || false
    await searchApi.exportExcel({
      columns: msg.sqlResult.columns,
      rows: msg.sqlResult.rows,
      question: msg.content || '',
      sql: msg.sql || '',
      answer: msg.content || '',
      execution_time_ms: msg.sqlResult.execution_time_ms || 0,
      include_chart: includeChart,
      chart_config: includeChart ? {
        chart_type: cb.chartType,
        x_column: cb.xAxisColumn,
        y_columns: cb.yAxisColumns,
        pie_top_n: cb.pieTopN
      } : null
    })
    ElMessage.success('Excel 파일이 다운로드되었습니다.')
  } catch {
    ElMessage.error('Excel 다운로드에 실패했습니다.')
  } finally {
    exporting.value = false
  }
}

const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.chat-message {
  margin-bottom: 20px;

  &.user {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }

  &.assistant {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }
}

.message-bubble {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 12px;

  &.user {
    background-color: var(--chat-bubble-user-bg);
    color: var(--chat-bubble-user-text);
    border-bottom-right-radius: 4px;
  }

  &.assistant {
    background-color: var(--chat-bubble-assistant-bg);
    color: var(--chat-bubble-assistant-text);
    border: 1px solid var(--chat-bubble-assistant-border);
    border-bottom-left-radius: 4px;
    box-shadow: var(--box-shadow-light);
    transition: var(--theme-transition);
    min-width: 720px;

    &.error {
      background-color: #fef0f0;
      border-color: #fbc4c4;
      color: #f56c6c;
    }
  }
}

.message-content {
  word-break: break-word;
  line-height: 1.6;

  // 마크다운 테이블/코드/헤더/리스트/수평선/기울임 (mixin)
  @include mx.md-table-styles;
  @include mx.copy-table-btn;
  @include mx.md-header-styles;
  @include mx.md-list-styles;
  @include mx.inline-code-styles;
  @include mx.code-block-styles;
  @include mx.strong-styles;
  @include mx.md-hr-styles;
  @include mx.md-em-styles;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color-lighter);

  .turn-indicator {
    font-size: 12px;
    color: var(--color-primary);
    font-weight: 500;
    padding: 2px 8px;
    background-color: rgba(var(--color-primary-rgb), 0.1);
    border-radius: 4px;
  }

  .response-time {
    font-size: 12px;
    color: var(--text-color-secondary);
  }
}

.message-time {
  font-size: 11px;
  color: var(--text-color-placeholder);
  margin-top: 4px;
}

.nl2sql-result {
  margin-top: 12px;

  .sql-code {
    background-color: var(--bg-color-code);
    padding: 12px;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    overflow-x: auto;
    margin: 0;
    color: var(--text-color-primary);
    transition: var(--theme-transition);
  }

  .result-summary {
    margin-bottom: 8px;
    font-size: 12px;
    color: var(--text-color-secondary);
  }

  .more-rows {
    margin-top: 8px;
    font-size: 12px;
    color: var(--text-color-secondary);
    text-align: center;
  }

  .export-bar {
    margin-top: 12px;
    display: flex;
    justify-content: flex-end;
  }
}

.rag-sources {
  margin-top: 12px;

  .sources-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-color-regular);
    margin-bottom: 8px;
  }

  .sources-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
}

.agent-result {
  margin-top: 12px;

  .agent-summary {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 12px;
  }

  .steps-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .step-item {
    padding: 12px;
    background-color: var(--bg-color-page);
    border-radius: 6px;
    border: 1px solid var(--border-color-light);

    .step-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 8px;

      .step-number {
        font-size: 12px;
        font-weight: 600;
        color: var(--color-primary);
      }
    }

    .step-content {
      font-size: 13px;
      
      > div {
        margin-bottom: 6px;

        &:last-child {
          margin-bottom: 0;
        }
      }

      .step-thought {
        color: var(--text-color-regular);
        font-style: italic;
      }

      .step-observation {
        color: var(--text-color-secondary);
        padding: 8px;
        background-color: var(--bg-color-code);
        border-radius: 4px;
        font-family: monospace;
        font-size: 12px;
      }

      .step-sql-result {
        margin-top: 12px;

        .sql-section {
          margin-bottom: 12px;

          .sql-label {
            font-size: 12px;
            font-weight: 500;
            color: var(--text-color-regular);
            margin-bottom: 4px;
          }

          .sql-code {
            background-color: var(--bg-color-code);
            padding: 12px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            overflow-x: auto;
            margin: 0;
            color: var(--text-color-primary);
            transition: var(--theme-transition);
          }
        }

        .result-section {
          .result-summary {
            margin-bottom: 8px;
            font-size: 12px;
            color: var(--text-color-secondary);
          }

          .more-rows {
            margin-top: 8px;
            font-size: 12px;
            color: var(--text-color-secondary);
            text-align: center;
          }
        }

        .no-results {
          font-size: 12px;
          color: var(--text-color-placeholder);
          text-align: center;
          padding: 12px;
        }
      }
    }
  }
}

// SSE 스트리밍 진행 상태
.streaming-indicator {
  padding: 4px 0;

  .stream-steps {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 10px;
  }

  .stream-step {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-color-regular);

    .step-check-icon {
      color: var(--el-color-success);
      font-size: 14px;
      font-weight: bold;
    }

    .step-label {
      color: var(--text-color-secondary);
    }
  }

  .streaming-current {
    display: flex;
    align-items: center;
    gap: 8px;

    .streaming-text {
      font-size: 13px;
      color: var(--color-primary);
      font-weight: 500;
    }
  }

  .typing-dots {
    display: flex;
    gap: 3px;
    align-items: center;

    span {
      display: inline-block;
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background-color: var(--color-primary);
      animation: streaming-typing 1.4s infinite ease-in-out both;

      &:nth-child(1) { animation-delay: 0s; }
      &:nth-child(2) { animation-delay: 0.2s; }
      &:nth-child(3) { animation-delay: 0.4s; }
    }
  }
}

@keyframes streaming-typing {
  0%, 80%, 100% {
    transform: scale(0.4);
    opacity: 0.4;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
