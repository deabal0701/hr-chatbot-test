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
      <div class="avatar-container">
        <div class="avatar assistant">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 8V4m0 0L9 7m3-3l3 3M9 15v4m0 0l-3-3m3 3l3-3M5 12H1m0 0l3-3m-3 3l3 3M23 12h-4m0 0l-3-3m3 3l3 3" />
          </svg>
        </div>
      </div>
      <div class="message-content assistant-message">
        <div class="answer-text" v-html="formattedContent" />

        <!-- 소스 정보 -->
        <div v-if="message.sources && message.sources.length > 0" class="sources-section">
          <button class="sources-toggle" @click="showSources = !showSources">
            <div class="toggle-left">
              <el-icon><Document /></el-icon>
              <span>{{ message.sources.length }}개의 출처 확인</span>
            </div>
            <el-icon class="toggle-icon" :class="{ expanded: showSources }">
              <ArrowDown />
            </el-icon>
          </button>

          <div v-show="showSources" class="sources-list-container">
            <div class="sources-list">
              <div
                v-for="(source, index) in message.sources"
                :key="index"
                class="source-card"
              >
                <div class="source-header">
                  <span class="source-index">{{ index + 1 }}</span>
                  <span class="source-title">{{ source.title || '관련 문서' }}</span>
                  <span class="source-score" v-if="source.score">
                    {{ Math.round(source.score * 100) }}% 일치
                  </span>
                </div>
                <p class="source-text">{{ truncateText(source.content, 180) }}</p>
              </div>
            </div>
          </div>
        </div>

        <!-- SQL 정보 (NL2SQL 모드) -->
        <div v-if="message.sql" class="sql-section">
          <button class="sql-toggle" @click="showSql = !showSql">
            <div class="toggle-left">
              <el-icon><DataLine /></el-icon>
              <span>데이터 조회 쿼리</span>
            </div>
            <el-icon class="toggle-icon" :class="{ expanded: showSql }">
              <ArrowDown />
            </el-icon>
          </button>

          <div v-show="showSql" class="sql-content">
            <div class="sql-header">PostgreSQL Query</div>
            <pre><code>{{ message.sql }}</code></pre>
          </div>
        </div>

        <!-- Agent 실행 단계 (Agent 모드) -->
        <div v-if="message.agentResult && message.agentResult.steps" class="agent-section">
          <button class="agent-toggle" @click="showAgentSteps = !showAgentSteps">
            <div class="toggle-left">
              <el-icon><CoffeeCup /></el-icon>
              <span>에이전트 사고 과정 ({{ message.agentResult.totalIterations }}단계)</span>
            </div>
            <el-icon class="toggle-icon" :class="{ expanded: showAgentSteps }">
              <ArrowDown />
            </el-icon>
          </button>

          <div v-show="showAgentSteps" class="agent-steps-container">
            <div class="agent-steps">
              <div
                v-for="(step, index) in message.agentResult.steps"
                :key="index"
                class="agent-step-item"
              >
                <div class="step-marker">
                  <div class="step-dot"></div>
                  <div v-if="index < message.agentResult.steps.length - 1" class="step-line"></div>
                </div>
                <div class="step-body">
                  <div class="step-header">
                    <span class="step-tool" v-if="step.action">
                      <el-icon>{{ getToolIcon(step.action) }}</el-icon>
                      {{ getToolLabel(step.action) }}
                    </span>
                    <span class="step-name">단계 {{ index + 1 }}</span>
                  </div>
                  <div class="step-main">
                    <div v-if="step.thought" class="step-thought">
                      {{ step.thought }}
                    </div>
                    <div v-if="step.observation" class="step-observation">
                      <div class="obs-label">결과값</div>
                      <div class="obs-content">{{ truncateText(step.observation, 300) }}</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="agent-summary">
              <div class="summary-item">
                <span class="label">상태</span>
                <span class="value" :class="message.agentResult.success ? 'success' : 'error'">
                  {{ message.agentResult.success ? '해결됨' : '실패' }}
                </span>
              </div>
              <div class="summary-item" v-if="message.agentResult.toolsUsed">
                <span class="label">도구</span>
                <span class="value">{{ message.agentResult.toolsUsed.join(', ') }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 메타 정보 -->
        <div class="message-footer">
          <div class="meta-left">
            <span class="mode-badge" v-if="message.mode">
              {{ getModeLabel(message.mode) }}
            </span>
            <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="meta-right">
            <button class="action-btn" title="복사">
              <el-icon><CopyDocument /></el-icon>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Document, ArrowDown, DataLine, CoffeeCup, CopyDocument } from '@element-plus/icons-vue'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const showSources = ref(false)
const showSql = ref(false)
const showAgentSteps = ref(false)

// 디버깅: 메시지 내용 확인 (개발 환경에서만)
onMounted(() => {
  if (import.meta.env.DEV && props.message.role === 'assistant') {
    console.log('[UserChatMessage Mounted]', props.message)
    console.log('[UserChatMessage Content]', props.message.content)
    console.log('[UserChatMessage QueryType]', props.message.queryType)
    console.log('[UserChatMessage AgentResult]', props.message.agentResult)
  }
})

watch(() => props.message.content, (newVal) => {
  if (import.meta.env.DEV) {
    console.log('[UserChatMessage Content Changed]', newVal)
    console.log('[UserChatMessage Content Length]', newVal?.length)
  }
}, { immediate: true })

// 마크다운 간단 처리
const formattedContent = computed(() => {
  // 디버깅 로그 (개발 환경에서만)
  if (import.meta.env.DEV) {
    console.log('[UserChatMessage formattedContent] Computing...', props.message.content)
    console.log('[UserChatMessage formattedContent] Content type:', typeof props.message.content)
    console.log('[UserChatMessage formattedContent] Content length:', props.message.content?.length)
  }
  
  if (!props.message.content) {
    if (import.meta.env.DEV) {
      console.warn('[UserChatMessage formattedContent] Content is empty!')
    }
    return '<span style="color: #999;">내용이 없습니다.</span>'
  }
  
  // 빈 문자열 체크
  if (props.message.content.trim() === '') {
    if (import.meta.env.DEV) {
      console.warn('[UserChatMessage formattedContent] Content is empty string!')
    }
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
  
  if (import.meta.env.DEV) {
    console.log('[UserChatMessage formattedContent] Formatted text:', text.substring(0, 100))
  }
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
  margin-bottom: 32px;
  animation: fadeIn 0.4s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.message-row {
  display: flex;
  gap: 20px;
  width: 100%;

  &.user {
    flex-direction: row-reverse;
  }

  &.assistant {
    justify-content: flex-start;
  }
}

// 아바타
.avatar-container {
  flex-shrink: 0;
  padding-top: 4px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  
  &.assistant {
    background: linear-gradient(135deg, #10a37f 0%, #0d8a6c 100%);
    box-shadow: 0 4px 12px rgba(16, 163, 127, 0.2);
  }

  svg {
    width: 22px;
    height: 22px;
  }
}

// 메시지 내용
.message-content {
  flex: 1;
  max-width: calc(100% - 100px);
}

// 사용자 메시지
.user-message {
  background-color: #2f2f2f;
  padding: 12px 20px;
  border-radius: 18px;
  color: #ffffff;
  font-size: 16px;
  line-height: 1.6;
  width: fit-content;
  margin-left: auto;
  border: 1px solid #424242;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

// AI 메시지
.assistant-message {
  color: #ececec;
  font-size: 16px;
  line-height: 1.8;
  padding-top: 6px;

  .answer-text {
    word-break: break-word;

    :deep(p) {
      margin: 0 0 12px;
      &:last-child { margin-bottom: 0; }
    }

    :deep(pre) {
      background-color: #1a1a1a;
      padding: 20px;
      border-radius: 12px;
      overflow-x: auto;
      margin: 16px 0;
      border: 1px solid #333;

      code {
        font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
        font-size: 14px;
        color: #e6e6e6;
        line-height: 1.5;
      }
    }

    :deep(code) {
      background-color: #383838;
      padding: 2px 6px;
      border-radius: 6px;
      font-family: 'Fira Code', monospace;
      font-size: 14px;
      color: #10a37f;
      font-weight: 500;
    }

    :deep(strong) {
      font-weight: 700;
      color: #ffffff;
    }

    :deep(ul), :deep(ol) {
      margin: 12px 0;
      padding-left: 24px;
      li { margin-bottom: 8px; }
    }
  }
}

// 공통 토글 섹션 (Sources, SQL, Agent)
.sources-section, .sql-section, .agent-section {
  margin-top: 24px;
  border: 1px solid #383838;
  border-radius: 12px;
  overflow: hidden;
  background-color: #262626;
}

.sources-toggle, .sql-toggle, .agent-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: none;
  border: none;
  color: #b4b4b4;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background-color: #2f2f2f;
    color: #ffffff;
  }

  .toggle-left {
    display: flex;
    align-items: center;
    gap: 10px;
    
    .el-icon {
      font-size: 18px;
      color: #10a37f;
    }
  }

  .toggle-icon {
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    &.expanded {
      transform: rotate(180deg);
    }
  }
}

// 소스 리스트
.sources-list-container {
  padding: 0 16px 16px;
  background-color: #262626;
}

.sources-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 4px;
}

.source-card {
  flex: 1;
  min-width: 260px;
  background-color: #1e1e1e;
  border: 1px solid #333;
  border-radius: 10px;
  padding: 14px;
  transition: border-color 0.2s;

  &:hover {
    border-color: #10a37f;
  }

  .source-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;

    .source-index {
      background-color: #333;
      color: #8e8e8e;
      width: 20px;
      height: 20px;
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 11px;
      font-weight: 700;
    }

    .source-title {
      font-weight: 600;
      color: #e0e0e0;
      font-size: 13px;
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .source-score {
      font-size: 11px;
      color: #10a37f;
      font-weight: 600;
      background-color: rgba(16, 163, 127, 0.1);
      padding: 2px 6px;
      border-radius: 4px;
    }
  }

  .source-text {
    font-size: 13px;
    color: #9a9a9a;
    line-height: 1.6;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
}

// SQL 섹션
.sql-content {
  padding: 16px;
  background-color: #1a1a1a;
  border-top: 1px solid #333;

  .sql-header {
    font-size: 11px;
    font-weight: 700;
    color: #666;
    text-transform: uppercase;
    margin-bottom: 12px;
    letter-spacing: 0.1em;
  }

  pre {
    margin: 0;
    code {
      font-family: 'Fira Code', monospace;
      font-size: 13px;
      color: #e0e0e0;
      line-height: 1.5;
    }
  }
}

// Agent 섹션
.agent-steps-container {
  padding: 20px 16px;
  background-color: #1e1e1e;
  border-top: 1px solid #333;
}

.agent-steps {
  display: flex;
  flex-direction: column;
}

.agent-step-item {
  display: flex;
  gap: 16px;

  .step-marker {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 12px;

    .step-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background-color: #10a37f;
      margin-top: 6px;
    }

    .step-line {
      width: 2px;
      flex: 1;
      background-color: #333;
      margin: 4px 0;
    }
  }

  .step-body {
    flex: 1;
    padding-bottom: 24px;

    .step-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 8px;

      .step-tool {
        display: flex;
        align-items: center;
        gap: 6px;
        font-size: 12px;
        font-weight: 700;
        color: #10a37f;
        background-color: rgba(16, 163, 127, 0.1);
        padding: 2px 8px;
        border-radius: 6px;

        .el-icon { font-size: 14px; }
      }

      .step-name {
        font-size: 12px;
        font-weight: 600;
        color: #666;
      }
    }

    .step-main {
      .step-thought {
        font-size: 14px;
        color: #e0e0e0;
        line-height: 1.6;
        margin-bottom: 12px;
      }

      .step-observation {
        background-color: #141414;
        border: 1px solid #2a2a2a;
        border-radius: 8px;
        padding: 12px;

        .obs-label {
          font-size: 11px;
          font-weight: 700;
          color: #555;
          margin-bottom: 6px;
          text-transform: uppercase;
        }

        .obs-content {
          font-size: 13px;
          color: #888;
          line-height: 1.5;
        }
      }
    }
  }
}

.agent-summary {
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid #333;
  display: flex;
  gap: 24px;

  .summary-item {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .label {
      font-size: 11px;
      color: #666;
      font-weight: 700;
      text-transform: uppercase;
    }

    .value {
      font-size: 13px;
      font-weight: 600;
      color: #b4b4b4;

      &.success { color: #10a37f; }
      &.error { color: #ff6b6b; }
    }
  }
}

// 메시지 푸터 (메타 정보)
.message-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16px;
  padding-top: 12px;
  
  .meta-left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .mode-badge {
    background-color: #333;
    color: #999;
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .timestamp {
    font-size: 12px;
    color: #666;
  }

  .action-btn {
    background: none;
    border: none;
    color: #555;
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;

    &:hover {
      color: #b4b4b4;
      background-color: #333;
    }
  }
}
</style>