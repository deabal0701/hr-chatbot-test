<template>
  <div class="chat-view">
    <!-- 채팅 영역 -->
    <div class="chat-container content-card">
      <!-- 메시지 목록 -->
      <div ref="messagesContainer" class="chat-messages">
        <!-- 환영 메시지 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <el-icon :size="48" color="#409eff">
            <ChatDotRound />
          </el-icon>
          <h3>MUREUM에 오신 것을 환영합니다</h3>
          <p>문서 기반 질문을 자유롭게 해주세요.</p>
          <div class="example-queries">
            <p class="example-title">예시 질문:</p>
            <el-button
              v-for="example in exampleQueries"
              :key="example"
              size="small"
              round
              @click="sendExample(example)"
            >
              {{ example }}
            </el-button>
          </div>
        </div>

        <!-- 메시지 목록 -->
        <ChatMessage
          v-for="message in messages"
          :key="message.id"
          :message="message"
        />

        <!-- 로딩 인디케이터 -->
        <div v-if="isLoading" class="loading-message">
          <el-icon class="is-loading" :size="20">
            <Loading />
          </el-icon>
          <span>답변을 생성하고 있습니다...</span>
        </div>
      </div>

      <!-- 입력 영역 -->
      <div class="chat-input-area">
        <ChatInput @send="handleSend" :disabled="isLoading" />
      </div>
    </div>

    <!-- 우측: 설정 및 정보 -->
    <div class="chat-sidebar">
      <!-- 검색 모드 선택 -->
      <div class="sidebar-section content-card">
        <h4>검색 모드</h4>
        <div class="mode-selector-wrapper">
          <el-radio-group v-model="searchMode" @change="handleModeChange" class="mode-row-primary">
            <el-radio-button value="auto">Auto</el-radio-button>
          </el-radio-group>
          <el-radio-group v-model="searchMode" @change="handleModeChange" class="mode-row-secondary">
            <el-radio-button value="rag">RAG</el-radio-button>
            <el-radio-button value="nl2sql">NL2SQL</el-radio-button>
            <el-radio-button value="agent">Agent</el-radio-button>
          </el-radio-group>
        </div>
        <p class="mode-description">
          <template v-if="searchMode === 'auto'">
            질문을 분석하여 자동으로 적합한 검색 방식을 선택합니다.
          </template>
          <template v-else-if="searchMode === 'rag'">
            문서 기반 검색 (정책, 가이드, 규정 등)
          </template>
          <template v-else-if="searchMode === 'nl2sql'">
            데이터베이스 조회 (통계, 수치 데이터 등)
          </template>
          <template v-else-if="searchMode === 'agent'">
            AI Agent가 도구를 자율 선택하여 복합 질문 처리<br>
            <small>(컨텍스트 검색 → DB 조회 → 문서 검색 → 계산)</small>
          </template>
        </p>
      </div>

      <!-- 대화 관리 -->
      <div class="sidebar-section content-card">
        <h4>대화 관리</h4>
        <el-button
          type="danger"
          plain
          :icon="Delete"
          :disabled="messages.length === 0"
          @click="clearChat"
        >
          대화 초기화
        </el-button>
      </div>

      <!-- 사용자 화면 -->
      <div class="sidebar-section content-card">
        <h4>사용자 화면</h4>
        <el-button
          type="primary"
          plain
          :icon="Monitor"
          @click="openUserChat"
        >
          새 창으로 열기
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useStore } from 'vuex'
import { ChatDotRound, Loading, Delete, Monitor } from '@element-plus/icons-vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatInput from '@/components/chat/ChatInput.vue'

const store = useStore()
const messagesContainer = ref(null)

const messages = computed(() => store.state.chat.messages)
const isLoading = computed(() => store.state.chat.isLoading)
const searchMode = computed({
  get: () => store.state.chat.searchMode,
  set: (value) => store.dispatch('chat/setMode', value)
})

const exampleQueries = [
  '2024년 입사자 현황을 알려줘',
  '재택근무 정책의 적용 조건과 제한 사항은?',
  '부서별 직원 수는?',
  '연차 휴가 신청 절차와 승인 기준은?'
]

// 메시지 전송
const handleSend = (query) => {
  store.dispatch('chat/sendMessage', query)
}

// 예시 질문 전송
const sendExample = (query) => {
  handleSend(query)
}

// 모드 변경
const handleModeChange = (mode) => {
  store.dispatch('chat/setMode', mode)
}

// 대화 초기화
const clearChat = () => {
  store.dispatch('chat/clearChat')
}

// 사용자 화면 새 창으로 열기
const openUserChat = () => {
  window.open('/chat', '_blank', 'width=800,height=900')
}

// 메시지 추가 시 스크롤
watch(messages, async () => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}, { deep: true })
</script>

<style lang="scss" scoped>
.chat-view {
  display: flex;
  gap: 20px;
  height: calc(100vh - 120px);
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-color-regular);

  h3 {
    margin: 20px 0 10px;
    font-size: 20px;
    color: var(--text-color-primary);
  }

  p {
    margin: 0 0 20px;
  }

  .example-title {
    font-size: 14px;
    color: var(--text-color-secondary);
    margin-bottom: 12px;
  }

  .el-button {
    margin: 4px;
  }
}

.loading-message {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px;
  color: var(--text-color-secondary);

  .is-loading {
    animation: rotating 1s linear infinite;
  }
}

@keyframes rotating {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.chat-input-area {
  padding: 20px;
  border-top: 1px solid var(--chat-input-border);
  background-color: var(--chat-input-bg);
  transition: var(--theme-transition);
}

.chat-sidebar {
  width: 280px;
  flex-shrink: 0;
}

.sidebar-section {
  margin-bottom: 20px;
  padding: 16px;

  h4 {
    margin: 0 0 12px;
    font-size: 14px;
    font-weight: 600;
    color: var(--text-color-primary);
  }

  .mode-selector-wrapper {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .mode-row-primary,
  .mode-row-secondary {
    display: flex;
    width: 100%;

    .el-radio-button {
      flex: 1;

      :deep(.el-radio-button__inner) {
        width: 100%;
      }
    }
  }

  .mode-description {
    margin: 12px 0 0;
    font-size: 12px;
    color: var(--text-color-secondary);
    line-height: 1.5;
  }
}
</style>
