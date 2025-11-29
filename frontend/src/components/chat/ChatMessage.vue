<template>
  <div class="chat-message" :class="message.role">
    <!-- 사용자 메시지 -->
    <div v-if="message.role === 'user'" class="message-bubble user">
      <div class="message-content">{{ message.content }}</div>
    </div>

    <!-- AI 응답 -->
    <div v-else class="message-bubble assistant" :class="{ error: message.isError }">
      <div class="message-content">{{ message.content }}</div>

      <!-- 메타 정보 -->
      <div v-if="!message.isError" class="message-meta">
        <el-tag size="small" :type="queryTypeTag.type" effect="plain">
          {{ queryTypeTag.label }}
        </el-tag>
        <span v-if="message.responseTimeMs" class="response-time">
          {{ message.responseTimeMs }}ms
        </span>
      </div>

      <!-- NL2SQL 결과 -->
      <div v-if="message.nl2sqlResult" class="nl2sql-result">
        <el-collapse>
          <el-collapse-item title="실행된 SQL 쿼리" name="sql">
            <pre class="sql-code">{{ message.nl2sqlResult.sql }}</pre>
          </el-collapse-item>
          <el-collapse-item v-if="message.nl2sqlResult.result" title="조회 결과" name="result">
            <div class="result-summary">
              총 {{ message.nl2sqlResult.result.row_count }}개 행 조회됨
            </div>
            <el-table
              v-if="message.nl2sqlResult.result.rows.length > 0"
              :data="message.nl2sqlResult.result.rows.slice(0, 10)"
              size="small"
              border
              max-height="300"
            >
              <el-table-column
                v-for="col in message.nl2sqlResult.result.columns"
                :key="col"
                :prop="col"
                :label="col"
                min-width="100"
              />
            </el-table>
            <div v-if="message.nl2sqlResult.result.row_count > 10" class="more-rows">
              ... 외 {{ message.nl2sqlResult.result.row_count - 10 }}개 행
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>

      <!-- RAG 출처 -->
      <div v-if="message.ragResult?.sources?.length > 0" class="rag-sources">
        <div class="sources-title">
          <el-icon><Document /></el-icon>
          참고 문서 ({{ message.ragResult.sources.length }}개)
        </div>
        <div class="sources-list">
          <SourceCard
            v-for="source in message.ragResult.sources"
            :key="source.id"
            :source="source"
          />
        </div>
      </div>
    </div>

    <!-- 타임스탬프 -->
    <div class="message-time">
      {{ formatTime(message.timestamp) }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Document } from '@element-plus/icons-vue'
import SourceCard from './SourceCard.vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const queryTypeTag = computed(() => {
  switch (props.message.queryType) {
    case 'rag':
      return { label: 'RAG', type: 'success' }
    case 'nl2sql':
      return { label: 'NL2SQL', type: 'warning' }
    default:
      return { label: 'Auto', type: 'info' }
  }
})

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

    &.error {
      background-color: #fef0f0;
      border-color: #fbc4c4;
      color: #f56c6c;
    }
  }
}

.message-content {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;
}

.message-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid var(--border-color-lighter);

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
</style>
