<template>
  <div class="chat-message" :class="message.role">
    <!-- 사용자 메시지 -->
    <div v-if="message.role === 'user'" class="message-row user">
      <div class="message-content user-message">
        {{ message.content }}
      </div>
    </div>

    <!-- AI 응답 -->
    <div v-else class="message-row assistant">
      <div class="avatar">
        <svg viewBox="0 0 24 24" fill="currentColor" width="20" height="20">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
        </svg>
      </div>
      <div class="message-content assistant-message">
        <div class="answer-text" v-html="formattedContent" />

        <!-- 소스 정보 -->
        <div v-if="message.sources && message.sources.length > 0" class="sources-section">
          <button class="sources-toggle" @click="showSources = !showSources">
            <el-icon><Document /></el-icon>
            <span>{{ message.sources.length }}개 출처</span>
            <el-icon class="toggle-icon" :class="{ expanded: showSources }">
              <ArrowDown />
            </el-icon>
          </button>

          <div v-show="showSources" class="sources-list">
            <div
              v-for="(source, index) in message.sources"
              :key="index"
              class="source-item"
            >
              <div class="source-header">
                <span class="source-title">{{ source.title || `문서 ${index + 1}` }}</span>
                <span class="source-score" v-if="source.score">
                  {{ Math.round(source.score * 100) }}%
                </span>
              </div>
              <p class="source-content">{{ truncateText(source.content, 150) }}</p>
            </div>
          </div>
        </div>

        <!-- SQL 정보 (NL2SQL 모드) -->
        <div v-if="message.sql" class="sql-section">
          <button class="sql-toggle" @click="showSql = !showSql">
            <el-icon><DataLine /></el-icon>
            <span>SQL 쿼리</span>
            <el-icon class="toggle-icon" :class="{ expanded: showSql }">
              <ArrowDown />
            </el-icon>
          </button>

          <div v-show="showSql" class="sql-content">
            <pre><code>{{ message.sql }}</code></pre>
          </div>
        </div>

        <!-- Agent 실행 단계 (Agent 모드) -->
        <div v-if="message.agentResult && message.agentResult.steps" class="agent-section">
          <button class="agent-toggle" @click="showAgentSteps = !showAgentSteps">
            <el-icon><CoffeeCup /></el-icon>
            <span>실행 단계 ({{ message.agentResult.totalIterations }}회 반복)</span>
            <el-icon class="toggle-icon" :class="{ expanded: showAgentSteps }">
              <ArrowDown />
            </el-icon>
          </button>

          <div v-show="showAgentSteps" class="agent-steps">
            <div
              v-for="(step, index) in message.agentResult.steps"
              :key="index"
              class="agent-step"
            >
              <div class="step-header">
                <span class="step-number">{{ index + 1 }}</span>
                <span class="step-tool" v-if="step.action">
                  <el-icon>{{ getToolIcon(step.action) }}</el-icon>
                  {{ getToolLabel(step.action) }}
                </span>
              </div>
              <div class="step-content">
                <div v-if="step.thought" class="step-thought">
                  <strong>생각:</strong> {{ step.thought }}
                </div>
                <div v-if="step.action" class="step-action">
                  <strong>동작:</strong> {{ step.action }}
                </div>
                <div v-if="step.observation" class="step-observation">
                  <strong>결과:</strong> {{ truncateText(step.observation, 200) }}
                </div>
              </div>
            </div>

            <!-- Agent 메트릭 -->
            <div class="agent-metrics">
              <span v-if="message.agentResult.toolsUsed">
                사용된 도구: {{ message.agentResult.toolsUsed.join(', ') }}
              </span>
              <span :class="message.agentResult.success ? 'success' : 'error'">
                {{ message.agentResult.success ? '성공' : '실패' }}
              </span>
            </div>
          </div>
        </div>

        <!-- 메타 정보 -->
        <div class="message-meta">
          <span class="mode-tag" v-if="message.mode">
            {{ getModeLabel(message.mode) }}
          </span>
          <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Document, ArrowDown, DataLine, CoffeeCup } from '@element-plus/icons-vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const showSources = ref(false)
const showSql = ref(false)
const showAgentSteps = ref(false)

// 디버깅: 메시지 내용 확인
onMounted(() => {
  if (props.message.role === 'assistant') {
    console.log('[UserChatMessage Mounted]', props.message)
    console.log('[UserChatMessage Content]', props.message.content)
    console.log('[UserChatMessage QueryType]', props.message.queryType)
    console.log('[UserChatMessage AgentResult]', props.message.agentResult)
  }
})

watch(() => props.message.content, (newVal) => {
  console.log('[UserChatMessage Content Changed]', newVal)
  console.log('[UserChatMessage Content Length]', newVal?.length)
}, { immediate: true })

// 마크다운 간단 처리
const formattedContent = computed(() => {
  console.log('[UserChatMessage formattedContent] Computing...', props.message.content)
  console.log('[UserChatMessage formattedContent] Content type:', typeof props.message.content)
  console.log('[UserChatMessage formattedContent] Content length:', props.message.content?.length)
  
  if (!props.message.content) {
    console.warn('[UserChatMessage formattedContent] Content is empty!')
    return '<span style="color: #999;">내용이 없습니다.</span>'
  }
  
  // 빈 문자열 체크
  if (props.message.content.trim() === '') {
    console.warn('[UserChatMessage formattedContent] Content is empty string!')
    return '<span style="color: #999;">답변이 비어있습니다.</span>'
  }

  let text = props.message.content
    // 코드 블록
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="$1">$2</code></pre>')
    // 인라인 코드
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // 볼드
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // 이탤릭
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // 줄바꿈
    .replace(/\n/g, '<br>')
  
  console.log('[UserChatMessage formattedContent] Formatted text:', text.substring(0, 100))
  return text
})

const truncateText = (text, length) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

const getModeLabel = (mode) => {
  const labels = {
    auto: 'Auto',
    rag: 'RAG',
    nl2sql: 'NL2SQL',
    agent: 'Agent'
  }
  return labels[mode] || mode
}

const getToolLabel = (toolName) => {
  const labels = {
    query_database: 'DB 조회',
    search_documents: '문서 검색',
    calculate: '계산'
  }
  return labels[toolName] || toolName
}

const getToolIcon = (toolName) => {
  // Element Plus 아이콘 컴포넌트는 템플릿에서 직접 사용해야 하므로
  // 여기서는 아이콘 이름만 반환
  const icons = {
    query_database: 'DataLine',
    search_documents: 'Document',
    calculate: 'Calculator'
  }
  return icons[toolName] || 'Tools'
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
.chat-message {
  margin-bottom: 24px;
}

.message-row {
  display: flex;
  gap: 12px;

  &.user {
    justify-content: flex-end;
  }

  &.assistant {
    justify-content: flex-start;
  }
}

// 아바타
.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #10a37f;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  flex-shrink: 0;
}

// 메시지 내용
.message-content {
  max-width: 85%;
}

// 사용자 메시지
.user-message {
  background-color: #303030;
  padding: 12px 16px;
  border-radius: 18px 18px 4px 18px;
  color: #ececec;
  font-size: 15px;
  line-height: 1.6;
}

// AI 메시지
.assistant-message {
  color: #ececec;
  font-size: 15px;
  line-height: 1.7;

  .answer-text {
    :deep(pre) {
      background-color: #1a1a1a;
      padding: 16px;
      border-radius: 8px;
      overflow-x: auto;
      margin: 12px 0;

      code {
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 14px;
        color: #e6e6e6;
      }
    }

    :deep(code) {
      background-color: #303030;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 14px;
    }

    :deep(strong) {
      font-weight: 600;
      color: #fff;
    }
  }
}

// 소스 섹션
.sources-section {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #303030;
}

.sources-toggle,
.sql-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: #8e8e8e;
  font-size: 13px;
  cursor: pointer;
  padding: 0;

  &:hover {
    color: #ececec;
  }

  .toggle-icon {
    transition: transform 0.2s;
    &.expanded {
      transform: rotate(180deg);
    }
  }
}

.sources-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.source-item {
  background-color: #303030;
  border-radius: 8px;
  padding: 12px;

  .source-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .source-title {
    font-weight: 500;
    color: #ececec;
    font-size: 13px;
  }

  .source-score {
    font-size: 12px;
    color: #10a37f;
    background-color: rgba(16, 163, 127, 0.1);
    padding: 2px 8px;
    border-radius: 4px;
  }

  .source-content {
    font-size: 13px;
    color: #8e8e8e;
    line-height: 1.5;
    margin: 0;
  }
}

// SQL 섹션
.sql-section {
  margin-top: 12px;
}

.sql-content {
  margin-top: 8px;

  pre {
    background-color: #1a1a1a;
    padding: 12px;
    border-radius: 8px;
    overflow-x: auto;
    margin: 0;

    code {
      font-family: 'Consolas', 'Monaco', monospace;
      font-size: 13px;
      color: #e6e6e6;
    }
  }
}

// Agent 섹션
.agent-section {
  margin-top: 12px;
}

.agent-toggle {
  display: flex;
  align-items: center;
  gap: 8px;
  background: none;
  border: none;
  color: #8e8e8e;
  font-size: 13px;
  cursor: pointer;
  padding: 0;

  &:hover {
    color: #ececec;
  }

  .toggle-icon {
    transition: transform 0.2s;
    &.expanded {
      transform: rotate(180deg);
    }
  }
}

.agent-steps {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.agent-step {
  background-color: #2a2a2a;
  border-left: 3px solid #10a37f;
  border-radius: 8px;
  padding: 12px;

  .step-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;

    .step-number {
      background-color: #10a37f;
      color: #fff;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      font-weight: 600;
    }

    .step-tool {
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 13px;
      color: #10a37f;
      font-weight: 500;
    }
  }

  .step-content {
    padding-left: 32px;
    font-size: 13px;

    > div {
      margin-bottom: 6px;

      &:last-child {
        margin-bottom: 0;
      }

      strong {
        color: #ececec;
        margin-right: 6px;
      }
    }

    .step-thought {
      color: #b8b8b8;
    }

    .step-action {
      color: #10a37f;
    }

    .step-observation {
      color: #8e8e8e;
      background-color: #1a1a1a;
      padding: 8px;
      border-radius: 4px;
      margin-top: 4px;
    }
  }
}

.agent-metrics {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #303030;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #8e8e8e;

  .success {
    color: #10a37f;
    font-weight: 500;
  }

  .error {
    color: #ff6b6b;
    font-weight: 500;
  }
}

// 메타 정보
.message-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-size: 12px;
  color: #6e6e6e;

  .mode-tag {
    background-color: #303030;
    padding: 2px 8px;
    border-radius: 4px;
  }
}
</style>
