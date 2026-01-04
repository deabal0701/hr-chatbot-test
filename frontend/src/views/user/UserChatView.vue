<template>
  <div class="user-chat-view">
    <!-- 헤더 -->
    <header class="chat-header">
      <div class="header-left">
        <h1 class="logo">RAG 자연어 검색</h1>
      </div>
      <div class="header-right">
        <el-button text class="header-btn" @click="goToAdmin">
          <el-icon><Setting /></el-icon>
        </el-button>
      </div>
    </header>

    <!-- 메인 콘텐츠 -->
    <main class="chat-main">
      <div class="chat-content">
        <!-- 환영 메시지 (대화 시작 전) -->
        <div v-if="messages.length === 0" class="welcome-section">
          <div class="welcome-icon">
            <svg viewBox="0 0 24 24" fill="currentColor" width="48" height="48">
              <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
            </svg>
          </div>
          <h2 class="welcome-title">무엇을 도와드릴까요?</h2>
          <p class="welcome-subtitle">문서 기반 질문을 자유롭게 입력해 주세요</p>

          <!-- 예시 질문 -->
          <div class="example-queries">
            <button
              v-for="example in exampleQueries"
              :key="example"
              class="example-btn"
              @click="sendExample(example)"
            >
              {{ example }}
            </button>
          </div>
        </div>

        <!-- 메시지 목록 -->
        <div v-else class="messages-container" ref="messagesContainer">
          <UserChatMessage
            v-for="message in messages"
            :key="message.id"
            :message="message"
          />

          <!-- 로딩 인디케이터 -->
          <div v-if="isLoading" class="loading-indicator">
            <div class="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <span class="loading-text">답변을 생성하고 있습니다...</span>
          </div>
        </div>
      </div>
    </main>

    <!-- 입력 영역 -->
    <footer class="chat-footer">
      <div class="input-container">
        <div class="input-wrapper">
          <!-- 모드 선택 드롭다운 -->
          <el-dropdown trigger="click" popper-class="dark-dropdown-popper" @command="handleModeChange">
            <button class="mode-btn">
              <el-icon><Operation /></el-icon>
              <span>{{ modeLabel }}</span>
              <el-icon class="arrow"><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="auto" :class="{ active: searchMode === 'auto' }">
                  <div class="mode-option">
                    <span class="mode-name">
                      <el-icon class="mode-icon"><MagicStick /></el-icon>
                      Auto
                    </span>
                    <span class="mode-desc">질문을 분석하여 자동으로 최적의 검색 방식을 선택합니다</span>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item command="rag" :class="{ active: searchMode === 'rag' }">
                  <div class="mode-option">
                    <span class="mode-name">
                      <el-icon class="mode-icon"><Document /></el-icon>
                      RAG
                    </span>
                    <span class="mode-desc">정책, 가이드, FAQ 등 문서 기반 검색</span>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item command="nl2sql" :class="{ active: searchMode === 'nl2sql' }">
                  <div class="mode-option">
                    <span class="mode-name">
                      <el-icon class="mode-icon"><DataLine /></el-icon>
                      NL2SQL
                    </span>
                    <span class="mode-desc">통계, 수치 등 데이터베이스 조회</span>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item command="agent" :class="{ active: searchMode === 'agent' }">
                  <div class="mode-option">
                    <span class="mode-name">
                      <el-icon class="mode-icon"><CoffeeCup /></el-icon>
                      Agent
                    </span>
                    <span class="mode-desc">복잡한 멀티스텝 질문 자동 처리 (SQL + 문서 + 계산)</span>
                  </div>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>

          <!-- 텍스트 입력 -->
          <textarea
            ref="inputRef"
            v-model="inputText"
            class="chat-input"
            placeholder="메시지를 입력하세요..."
            rows="1"
            @keydown.enter.exact.prevent="handleSend"
            @input="autoResize"
          />

          <!-- 전송 버튼 -->
          <button
            class="send-btn"
            :class="{ active: inputText.trim() }"
            :disabled="!inputText.trim() || isLoading"
            @click="handleSend"
          >
            <el-icon><Promotion /></el-icon>
          </button>
        </div>

        <p class="footer-note">
          AI가 생성한 답변은 부정확할 수 있습니다. 중요한 정보는 담당자에게 확인하세요.
        </p>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { Setting, Operation, ArrowDown, Promotion, MagicStick, Document, DataLine, CoffeeCup } from '@element-plus/icons-vue'
import UserChatMessage from '@/components/user/UserChatMessage.vue'

const router = useRouter()
const store = useStore()

const inputRef = ref(null)
const messagesContainer = ref(null)
const inputText = ref('')

const messages = computed(() => store.state.chat.messages)
const isLoading = computed(() => store.state.chat.isLoading)
const searchMode = computed(() => store.state.chat.searchMode)

const modeLabel = computed(() => {
  const labels = {
    auto: 'Auto',
    rag: 'RAG',
    nl2sql: 'NL2SQL',
    agent: 'Agent'
  }
  return labels[searchMode.value] || 'Auto'
})

const exampleQueries = [
  '재택근무 정책에 대해 알려줘',
  '연차 신청 방법이 뭐야?',
  '2024년 입사자 현황을 알려줘',
  '부서별 직원 수는?'
]

// 관리자 페이지로 이동
const goToAdmin = () => {
  router.push('/admin')
}

// 모드 변경
const handleModeChange = (mode) => {
  store.dispatch('chat/setMode', mode)
}

// 메시지 전송
const handleSend = () => {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  store.dispatch('chat/sendMessage', text)
  inputText.value = ''

  // 입력창 높이 초기화
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
}

// 예시 질문 전송
const sendExample = (query) => {
  store.dispatch('chat/sendMessage', query)
}

// 입력창 자동 크기 조절
const autoResize = () => {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 200) + 'px'
  }
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
.user-chat-view {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background-color: #212121;
  color: #ececec;
}

// 헤더
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  border-bottom: 1px solid #303030;
  background-color: #212121;

  .logo {
    font-size: 18px;
    font-weight: 600;
    color: #ececec;
    margin: 0;
  }

  .header-btn {
    color: #8e8e8e;
    &:hover {
      color: #ececec;
    }
  }
}

// 메인 콘텐츠
.chat-main {
  flex: 1;
  overflow: hidden;
  display: flex;
  justify-content: center;
}

.chat-content {
  width: 100%;
  max-width: 800px;
  height: 100%;
  overflow-y: auto;
  padding: 0 24px;
}

// 환영 섹션
.welcome-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding-bottom: 100px;

  .welcome-icon {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background-color: #303030;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 24px;
    color: #10a37f;
  }

  .welcome-title {
    font-size: 32px;
    font-weight: 600;
    margin: 0 0 12px;
    color: #ececec;
  }

  .welcome-subtitle {
    font-size: 16px;
    color: #8e8e8e;
    margin: 0 0 32px;
  }
}

// 예시 질문
.example-queries {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
  max-width: 600px;

  .example-btn {
    padding: 12px 20px;
    background-color: #303030;
    border: 1px solid #424242;
    border-radius: 12px;
    color: #ececec;
    font-size: 14px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background-color: #3d3d3d;
      border-color: #525252;
    }
  }
}

// 메시지 컨테이너
.messages-container {
  padding: 24px 0;
  overflow-y: auto;
  height: 100%;
}

// 로딩 인디케이터
.loading-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 0;
  color: #8e8e8e;

  .typing-dots {
    display: flex;
    gap: 4px;

    span {
      width: 8px;
      height: 8px;
      background-color: #8e8e8e;
      border-radius: 50%;
      animation: typing 1.4s infinite ease-in-out both;

      &:nth-child(1) { animation-delay: -0.32s; }
      &:nth-child(2) { animation-delay: -0.16s; }
    }
  }

  .loading-text {
    font-size: 14px;
  }
}

@keyframes typing {
  0%, 80%, 100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

// 푸터 (입력 영역)
.chat-footer {
  padding: 16px 24px 24px;
  background-color: #212121;
}

.input-container {
  max-width: 800px;
  margin: 0 auto;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  padding: 12px 16px;
  background-color: #303030;
  border-radius: 24px;
  border: 1px solid #424242;

  &:focus-within {
    border-color: #525252;
  }
}

// 모드 선택 버튼
.mode-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  background-color: #424242;
  border: none;
  border-radius: 8px;
  color: #ececec;
  font-size: 13px;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.2s;

  &:hover {
    background-color: #525252;
  }

  .arrow {
    font-size: 12px;
    color: #8e8e8e;
  }
}

// 텍스트 입력
.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #ececec;
  font-size: 16px;
  line-height: 1.5;
  resize: none;
  max-height: 200px;

  &::placeholder {
    color: #6e6e6e;
  }
}

// 전송 버튼
.send-btn {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: none;
  background-color: #424242;
  color: #6e6e6e;
  cursor: not-allowed;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  &.active {
    background-color: #10a37f;
    color: #fff;
    cursor: pointer;

    &:hover {
      background-color: #0d8a6c;
    }
  }

  &:disabled {
    cursor: not-allowed;
  }
}

// 푸터 노트
.footer-note {
  text-align: center;
  font-size: 12px;
  color: #6e6e6e;
  margin: 12px 0 0;
}

// 드롭다운 메뉴 스타일 (전역 스타일 필요)
:deep(.mode-dropdown) {
  background-color: #303030 !important;
  border: 1px solid #424242 !important;

  .el-dropdown-menu__item {
    color: #ececec !important;

    &:hover {
      background-color: #424242 !important;
    }

    &.active {
      background-color: #424242 !important;
      color: #10a37f !important;
    }
  }
}

.mode-option {
  display: flex;
  flex-direction: column;
  gap: 2px;

  .mode-name {
    font-weight: 500;
  }

  .mode-desc {
    font-size: 12px;
    color: #8e8e8e;
  }
}
</style>
