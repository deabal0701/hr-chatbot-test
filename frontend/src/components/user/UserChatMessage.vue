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

        <!-- 소스 정보 :  임시로 주석처리함.-->
        <!-- <div v-if="message.sources && message.sources.length > 0" class="sources-section">
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
        </div> -->

        <!-- SQL 정보 (NL2SQL 모드)  :  임시로 주석처리함-->
        <!-- <div v-if="message.sql" class="sql-section">
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
        </div> -->

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
            <span class="mode-badge" v-if="message.queryType">
              {{ getModeLabel(message.queryType) }}
            </span>
            <!-- 멀티턴 인디케이터 (NL2SQL 모드) -->
            <span class="turn-badge" v-if="turnInfo">
              {{ turnInfo }}
            </span>
            <span class="timestamp">{{ formatTime(message.timestamp) }}</span>
          </div>
          <div class="meta-right">
            <button class="action-btn" title="복사" @click="copyContent">
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
import { ElMessage } from 'element-plus'
import { formatMarkdownToHtml, registerTableCopyFunction } from '@/utils/markdownParser'

const props = defineProps({
  message: {
    type: Object,
    required: true
  }
})

const showSources = ref(false)
const showSql = ref(false)
const showAgentSteps = ref(false)

// 전역 테이블 복사 함수 등록
onMounted(() => {
  registerTableCopyFunction()

  // 디버깅: 메시지 내용 확인 (개발 환경에서만)
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

// 마크다운 처리 (모듈 사용)
const formattedContent = computed(() => {
  return formatMarkdownToHtml(props.message.content)
})

// 멀티턴 인디케이터 (NL2SQL 모드에서만 표시)
const turnInfo = computed(() => {
  const metadata = props.message.metadata
  if (!metadata) return null

  const currentTurn = metadata.current_turn
  const maxTurns = metadata.max_turns

  // NL2SQL 모드이고 멀티턴 정보가 있을 때만 표시
  if (currentTurn && maxTurns && props.message.queryType === 'nl2sql') {
    return `${currentTurn}/${maxTurns}`
  }
  return null
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
    query_database_tool: 'DB 조회',
    search_documents_tool: '문서 검색',
    calculate_tool: '계산'
  }
  return labels[toolName] || toolName
}

const getToolIcon = (toolName) => {
  // Element Plus 아이콘 컴포넌트는 템플릿에서 직접 사용해야 하므로
  // 여기서는 아이콘 이름만 반환
  const icons = {
    query_database_tool: 'DataLine',
    search_documents_tool: 'Document',
    calculate_tool: 'Calculator'
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

// 현재 메시지 내용만 복사
const copyContent = async () => {
  // HTTPS 또는 localhost가 아닌 경우 클립보드 API 사용 불가
  if (!window.isSecureContext) {
    ElMessage.warning('복사 기능은 https:// 주소에서만 지원됩니다. 관리자에게 문의해 주세요.')
    return
  }

  try {
    const content = props.message.content || ''
    await navigator.clipboard.writeText(content)
    ElMessage.success('답변이 클립보드에 복사되었습니다.')
  } catch {
    ElMessage.error('클립보드 복사에 실패했습니다.')
  }
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
  color: var(--icon-color, #ffffff);

  &.assistant {
    background-color: var(--icon-bg, #333333);
    border: 1px solid var(--icon-bg-border, #555555);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
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
  background-color: var(--chat-bubble-user-bg);
  padding: 12px 20px;
  border-radius: 18px;
  color: var(--chat-bubble-user-text);
  font-size: 16px;
  line-height: 1.6;
  width: fit-content;
  margin-left: auto;
  border: 1px solid var(--border-color);
  box-shadow: var(--box-shadow-light);
}

// AI 메시지
.assistant-message {
  color: var(--chat-bubble-assistant-text);
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
      background-color: var(--bg-color-code);
      padding: 20px;
      border-radius: 12px;
      overflow-x: auto;
      margin: 16px 0;
      border: 1px solid var(--border-color);

      code {
        font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
        font-size: 14px;
        color: var(--text-color-primary);
        line-height: 1.5;
      }
    }

    :deep(code) {
      background-color: var(--bg-color-hover);
      padding: 2px 6px;
      border-radius: 6px;
      font-family: 'Fira Code', monospace;
      font-size: 14px;
      color: var(--text-color-regular);
      font-weight: 500;
    }

    // 마크다운 테이블 스타일
    :deep(.md-table-wrapper) {
      position: relative;
      margin: 20px 0;
      border-radius: 12px;
      border: 1px solid var(--border-color);
      background-color: var(--bg-color-card);
    }

    :deep(.md-table-scroll) {
      overflow-x: auto;
    }

    :deep(.copy-table-btn) {
      position: absolute;
      top: 8px;
      right: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      width: 32px;
      height: 32px;
      padding: 0;
      background-color: var(--bg-color-card);
      border: 1px solid var(--border-color);
      border-radius: 6px;
      color: var(--text-color-secondary);
      cursor: pointer;
      transition: all 0.2s;
      z-index: 1;

      &:hover {
        background-color: var(--bg-color-hover);
        color: var(--text-color-primary);
        border-color: var(--color-primary);
      }

      svg {
        width: 16px;
        height: 16px;
      }
    }

    :deep(.md-table) {
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;

      th, td {
        padding: 12px 16px;
        text-align: left;
        border-bottom: 1px solid var(--border-color);
        white-space: nowrap;
      }

      th {
        background-color: var(--bg-color-hover);
        font-weight: 600;
        color: var(--text-color-primary);
      }

      td {
        color: var(--text-color-regular);
      }

      tbody tr:hover {
        background-color: var(--bg-color-hover);
      }

      tbody tr:last-child td {
        border-bottom: none;
      }
    }

    // 마크다운 헤더 스타일
    :deep(.md-h2), :deep(.md-h3) {
      display: block;
      margin: 20px 0 12px;
      font-size: 16px;
    }

    // 마크다운 리스트 스타일
    :deep(.md-list-item) {
      display: block;
      padding-left: 8px;
      margin: 4px 0;
    }

    :deep(strong) {
      font-weight: 700;
      color: var(--text-color-primary);
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
  border: 1px solid var(--border-color);
  border-radius: 12px;
  overflow: hidden;
  background-color: var(--bg-color-card);
}

.sources-toggle, .sql-toggle, .agent-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: none;
  border: none;
  color: var(--text-color-secondary);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background-color: var(--bg-color-hover);
    color: var(--text-color-primary);
  }

  .toggle-left {
    display: flex;
    align-items: center;
    gap: 10px;

    .el-icon {
      font-size: 18px;
      color: var(--text-color-secondary);
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
  background-color: var(--bg-color-card);
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
  background-color: var(--bg-color-overlay);
  border: 1px solid var(--border-color-light);
  border-radius: 10px;
  padding: 14px;
  transition: border-color 0.2s;

  &:hover {
    border-color: var(--border-color);
  }

  .source-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;

    .source-index {
      background-color: var(--bg-color-hover);
      color: var(--text-color-secondary);
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
      color: var(--text-color-primary);
      font-size: 13px;
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .source-score {
      font-size: 11px;
      color: var(--text-color-secondary);
      font-weight: 600;
      background-color: var(--bg-color-hover);
      padding: 2px 6px;
      border-radius: 4px;
    }
  }

  .source-text {
    font-size: 13px;
    color: var(--text-color-secondary);
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
  background-color: var(--bg-color-code);
  border-top: 1px solid var(--border-color-light);

  .sql-header {
    font-size: 11px;
    font-weight: 700;
    color: var(--text-color-secondary);
    text-transform: uppercase;
    margin-bottom: 12px;
    letter-spacing: 0.1em;
  }

  pre {
    margin: 0;
    code {
      font-family: 'Fira Code', monospace;
      font-size: 13px;
      color: var(--text-color-primary);
      line-height: 1.5;
    }
  }
}

// Agent 섹션
.agent-steps-container {
  padding: 20px 16px;
  background-color: var(--bg-color-overlay);
  border-top: 1px solid var(--border-color-light);
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
      background-color: var(--color-primary);
      margin-top: 6px;
    }

    .step-line {
      width: 2px;
      flex: 1;
      background-color: var(--border-color-light);
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
        color: var(--color-primary);
        background-color: var(--bg-color-hover);
        padding: 2px 8px;
        border-radius: 6px;

        .el-icon { font-size: 14px; }
      }

      .step-name {
        font-size: 12px;
        font-weight: 600;
        color: var(--text-color-secondary);
      }
    }

    .step-main {
      .step-thought {
        font-size: 14px;
        color: var(--text-color-primary);
        line-height: 1.6;
        margin-bottom: 12px;
      }

      .step-observation {
        background-color: var(--bg-color-code);
        border: 1px solid var(--border-color-light);
        border-radius: 8px;
        padding: 12px;

        .obs-label {
          font-size: 11px;
          font-weight: 700;
          color: var(--text-color-secondary);
          margin-bottom: 6px;
          text-transform: uppercase;
        }

        .obs-content {
          font-size: 13px;
          color: var(--text-color-regular);
          line-height: 1.5;
        }
      }
    }
  }
}

.agent-summary {
  margin-top: 8px;
  padding-top: 16px;
  border-top: 1px solid var(--border-color-light);
  display: flex;
  gap: 24px;

  .summary-item {
    display: flex;
    flex-direction: column;
    gap: 4px;

    .label {
      font-size: 11px;
      color: var(--text-color-secondary);
      font-weight: 700;
      text-transform: uppercase;
    }

    .value {
      font-size: 13px;
      font-weight: 600;
      color: var(--text-color-regular);

      &.success { color: var(--color-success); }
      &.error { color: var(--color-danger); }
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
    background-color: var(--bg-color-hover);
    color: var(--text-color-secondary);
    font-size: 11px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .turn-badge {
    background-color: transparent;
    color: var(--text-color-secondary);
    font-size: 11px;
    font-weight: 500;
    opacity: 0.7;

    &::before {
      content: '•';
      margin-right: 6px;
      opacity: 0.5;
    }
  }

  .timestamp {
    font-size: 12px;
    color: var(--text-color-secondary);
  }

  .action-btn {
    background: none;
    border: none;
    color: var(--text-color-secondary);
    cursor: pointer;
    padding: 4px;
    border-radius: 4px;
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;

    &:hover {
      color: var(--text-color-primary);
      background-color: var(--bg-color-hover);
    }
  }
}

// ===========================================
// 모바일 반응형 스타일
// ===========================================
@media (max-width: 768px) {
  .chat-message {
    margin-bottom: 24px;
  }

  .message-row {
    gap: 12px;
  }

  .avatar {
    width: 30px;
    height: 30px;
    border-radius: 8px;

    svg {
      width: 18px;
      height: 18px;
    }
  }

  .message-content {
    max-width: calc(100% - 50px);
  }

  .user-message {
    padding: 10px 16px;
    border-radius: 16px;
    font-size: 15px;
  }

  .assistant-message {
    font-size: 15px;
    line-height: 1.7;

    .answer-text {
      :deep(pre) {
        padding: 14px;
        border-radius: 10px;
        margin: 12px 0;

        code {
          font-size: 12px;
        }
      }

      :deep(code) {
        font-size: 13px;
        padding: 1px 4px;
      }

      :deep(ul), :deep(ol) {
        padding-left: 20px;
        li { margin-bottom: 6px; }
      }
    }
  }

  // 토글 섹션들
  .sources-section, .sql-section, .agent-section {
    margin-top: 16px;
    border-radius: 10px;
  }

  .sources-toggle, .sql-toggle, .agent-toggle {
    padding: 10px 12px;
    font-size: 13px;

    .toggle-left {
      gap: 8px;

      .el-icon {
        font-size: 16px;
      }
    }
  }

  // 소스 리스트
  .sources-list-container {
    padding: 0 12px 12px;
  }

  .sources-list {
    flex-direction: column;
    gap: 10px;
  }

  .source-card {
    min-width: 100%;
    padding: 12px;

    .source-header {
      flex-wrap: wrap;
      gap: 6px;
      margin-bottom: 8px;

      .source-index {
        width: 18px;
        height: 18px;
        font-size: 10px;
      }

      .source-title {
        font-size: 12px;
        max-width: 150px;
      }

      .source-score {
        font-size: 10px;
      }
    }

    .source-text {
      font-size: 12px;
      -webkit-line-clamp: 2;
    }
  }

  // SQL 섹션
  .sql-content {
    padding: 12px;

    .sql-header {
      font-size: 10px;
      margin-bottom: 10px;
    }

    pre code {
      font-size: 11px;
    }
  }

  // Agent 섹션
  .agent-steps-container {
    padding: 14px 12px;
  }

  .agent-step-item {
    gap: 12px;

    .step-marker {
      width: 10px;

      .step-dot {
        width: 6px;
        height: 6px;
      }
    }

    .step-body {
      padding-bottom: 18px;

      .step-header {
        flex-wrap: wrap;
        gap: 6px;
        margin-bottom: 6px;

        .step-tool {
          font-size: 11px;
          padding: 2px 6px;

          .el-icon { font-size: 12px; }
        }

        .step-name {
          font-size: 11px;
        }
      }

      .step-main {
        .step-thought {
          font-size: 13px;
          margin-bottom: 10px;
        }

        .step-observation {
          padding: 10px;

          .obs-label {
            font-size: 10px;
            margin-bottom: 4px;
          }

          .obs-content {
            font-size: 12px;
          }
        }
      }
    }
  }

  .agent-summary {
    padding-top: 12px;
    gap: 16px;
    flex-wrap: wrap;

    .summary-item {
      gap: 2px;

      .label {
        font-size: 10px;
      }

      .value {
        font-size: 12px;
      }
    }
  }

  // 메시지 푸터
  .message-footer {
    margin-top: 12px;
    padding-top: 10px;

    .meta-left {
      gap: 8px;
    }

    .mode-badge {
      font-size: 10px;
      padding: 2px 6px;
    }

    .turn-badge {
      font-size: 10px;
    }

    .timestamp {
      font-size: 11px;
    }
  }
}

// 매우 작은 화면 (375px 이하)
@media (max-width: 375px) {
  .message-row {
    gap: 10px;
  }

  .avatar {
    width: 26px;
    height: 26px;

    svg {
      width: 16px;
      height: 16px;
    }
  }

  .user-message {
    padding: 8px 14px;
    font-size: 14px;
  }

  .assistant-message {
    font-size: 14px;
  }

  .source-card .source-header .source-title {
    max-width: 120px;
  }
}
</style>