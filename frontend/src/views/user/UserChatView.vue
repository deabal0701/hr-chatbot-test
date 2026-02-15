<template>
  <div class="user-chat-view" :class="{ 'no-header': hideHeader }">
    <!-- 헤더 (hideHeader가 false일 때만 표시) -->
    <header v-if="!hideHeader" class="chat-header">
      <div class="header-left">
        <div class="header-logo">
          <div class="logo-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 1 1-7.6-11.7 8.5 8.5 0 0 1 5.3 1.9"></path>
              <polyline points="16 5 12 9 8 5"></polyline>
            </svg>
          </div>
          <h1 class="logo-text">MUREUM</h1>
        </div>
      </div>
      <div class="header-right">
        <el-tooltip :content="isDarkMode ? '라이트 모드로 전환' : '다크 모드로 전환'" placement="bottom">
          <button class="theme-toggle-btn" @click="toggleDarkMode">
            <el-icon v-if="isDarkMode"><Sunny /></el-icon>
            <el-icon v-else><Moon /></el-icon>
          </button>
        </el-tooltip>
        <!-- 사용자 정보 / 로그인 버튼 -->
        <span v-if="isAuthenticated" class="user-label">{{ displayName }}</span>
        <el-button v-else type="primary" size="small" @click="goToLogin">로그인</el-button>
      </div>
    </header>

    <!-- 메인 콘텐츠 -->
    <main class="chat-main" ref="chatMainRef">
      <div class="chat-content">
        <!-- 환영 메시지 (대화 시작 전) -->
        <div v-if="messages.length === 0" class="welcome-section">
          <div class="welcome-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="48" height="48">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              <path d="M8 10h.01"></path>
              <path d="M12 10h.01"></path>
              <path d="M16 10h.01"></path>
            </svg>
          </div>
          <h2 class="welcome-title">무엇을 도와드릴까요?</h2>
          <p class="welcome-subtitle">문서 기반 검색과 데이터 조회를 한 번에 해결하세요.</p>

          <!-- 예시 질문 -->
          <div class="example-queries">
            <button
              v-for="example in exampleQueries"
              :key="example"
              class="example-btn"
              @click="sendExample(example)"
            >
              <el-icon class="btn-icon"><ChatLineRound /></el-icon>
              {{ example }}
            </button>
          </div>
        </div>

        <!-- 메시지 목록 -->
        <div v-else class="messages-container">
          <UserChatMessage
            v-for="message in messages"
            :key="message.id"
            :message="message"
          />

          <!-- 로딩 인디케이터 -->
          <div v-if="isLoading && !isStreaming" class="loading-indicator">
            <div class="assistant-avatar-small">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 8V4m0 0L9 7m3-3l3 3M9 15v4m0 0l-3-3m3 3l3-3M5 12H1m0 0l3-3m-3 3l3 3M23 12h-4m0 0l-3-3m3 3l3 3" />
              </svg>
            </div>
            <div class="loading-content">
              <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
              <span class="loading-text">답변을 준비하고 있습니다...</span>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- 입력 영역 -->
    <footer class="chat-footer">
      <div class="input-container">
        <div class="input-wrapper">
          <!-- 프롬프트 가이드 버튼 - 추후 사용 예정
          <el-tooltip content="프롬프트 작성 가이드" placement="top">
            <button class="guide-btn" @click="showGuideModal = true">
              <el-icon><QuestionFilled /></el-icon>
            </button>
          </el-tooltip>
          -->

          <!-- 모드 선택 드롭다운 -->
          <el-dropdown trigger="click" popper-class="dark-dropdown-popper" @command="handleModeChange">
            <button class="mode-btn">
              <el-icon><Operation /></el-icon>
              <span>{{ modeLabel }}</span>
              <el-icon class="arrow"><ArrowDown /></el-icon>
            </button>
            <template #dropdown>
              <el-dropdown-menu>
                <!-- AUTO 모드 주석처리 (추후 기능 완료되면 Open)
                <el-dropdown-item command="auto" :class="{ active: searchMode === 'auto' }">
                  <div class="mode-option">
                    <span class="mode-name">
                      <el-icon class="mode-icon"><MagicStick /></el-icon>
                      Auto
                    </span>
                    <span class="mode-desc">질문을 분석하여 자동으로 최적의 검색 방식을 선택합니다</span>
                  </div>
                </el-dropdown-item>
                -->
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
            placeholder="궁금한 내용을 입력하세요..."
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
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" width="18" height="18">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>

        <p class="footer-note">
          본 AI 어시스턴트가 생성한 답변은 참고용입니다. 정확한 정보는 관련 부서에 확인 바랍니다.
        </p>
      </div>
    </footer>

    <!-- 프롬프트 가이드 모달 - 추후 사용 예정
    <PromptGuideModal
      v-model="showGuideModal"
      :mode="searchMode"
      @use-example="handleUseExample"
    />
    -->
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { Operation, ArrowDown, MagicStick, Document, DataLine, CoffeeCup, ChatLineRound, Sunny, Moon, QuestionFilled } from '@element-plus/icons-vue'
import UserChatMessage from '@/components/user/UserChatMessage.vue'
import PromptGuideModal from '@/components/chat/PromptGuideModal.vue'

// Props
defineProps({
  hideHeader: {
    type: Boolean,
    default: false
  }
})

const store = useStore()
const router = useRouter()

// ===== 인증 상태 =====
const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])
const displayName = computed(() => store.getters['auth/displayName'])

const goToLogin = () => {
  router.push({ path: '/login', query: { redirect: '/chat' } })
}

// 테마 관련
const isDarkMode = computed(() => store.getters['app/isDarkMode'])

const toggleDarkMode = () => {
  store.dispatch('app/toggleDarkMode')
}

// 사용자 화면 진입 시 currentView 설정 + 채팅 이력 로드
onMounted(() => {
  store.dispatch('app/setCurrentView', 'user')
  store.dispatch('chat/fetchChatHistory')
})

// 사용자 화면 이탈 시 관리자로 복원 (선택적)
onUnmounted(() => {
  store.dispatch('app/setCurrentView', 'admin')
})

const inputRef = ref(null)
const chatMainRef = ref(null)
const inputText = ref('')
const showGuideModal = ref(false)

const messages = computed(() => store.state.chat.messages)
const isLoading = computed(() => store.state.chat.isLoading)
const isStreaming = computed(() => store.state.chat.isStreaming)
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

// 검색 모드별 예시 질문
const ragExampleQueries = [
  '재택근무 정책의 적용 조건과 제한 사항은?',
  '연차 휴가 신청 절차와 승인 기준은?',
  '성과평가 제도는 어떻게 운영되나요?',
  '출장비 정산 절차와 기준은?'
]

const nl2sqlExampleQueries = [
  '2017년 입사자 현황을 상세하게 알려줘!',
  '우리회사의 부서별 직원 수는?',
  '2000년 이후 재직자와 퇴직자 현황은?',
  '가장 최근에 입사한 직원 5명은?'
]

const agentExampleQueries = [
  '연차휴가 규정과 부서별 연차 사용일수를 알려줘',
  '인사평가 등급별 직원 분포와 성과평가 운영 방식은?',
  '2024년 신규 입사자 명단과 온보딩 절차를 알려줘',
  '자격증 보유 현황과 자격증 취득 지원 제도는?'
]

const exampleQueries = computed(() => {
  if (searchMode.value === 'nl2sql') {
    return nl2sqlExampleQueries
  }
  if (searchMode.value === 'agent') {
    return agentExampleQueries
  }
  return ragExampleQueries
})

// 관리자 페이지로 이동 (주석처리 - 로그인 기능 없음)
// const goToAdmin = () => {
//   router.push('/admin')
// }

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

// 가이드에서 예시 사용
const handleUseExample = (example) => {
  inputText.value = example
  if (inputRef.value) {
    inputRef.value.focus()
  }
}

// 입력창 자동 크기 조절
const autoResize = () => {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
    inputRef.value.style.height = Math.min(inputRef.value.scrollHeight, 200) + 'px'
  }
}

// 메시지 추가 시 스크롤 (chat-main 요소 기준)
watch(messages, async () => {
  await nextTick()
  if (chatMainRef.value) {
    chatMainRef.value.scrollTop = chatMainRef.value.scrollHeight
  }
}, { deep: true })
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.user-chat-view {
  display: flex;
  flex-direction: column;
  height: 100%;
  max-height: 100%;
  overflow: hidden;
  background-color: var(--user-sidebar-bg);
  color: var(--user-sidebar-text);
  transition: var(--theme-transition);

  &.no-header {
    .chat-main {
      height: 100%;
    }
  }
}

// 헤더
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 24px;
  border-bottom: 1px solid var(--user-sidebar-border);
  background-color: var(--user-sidebar-bg);
  z-index: 10;
  transition: var(--theme-transition);

  .header-logo {
    display: flex;
    align-items: center;
    gap: 12px;

    .logo-icon {
      width: 32px;
      height: 32px;
      background-color: var(--icon-bg, #333333);
      border: 1px solid var(--icon-bg-border, #555555);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--icon-color, #ffffff);

      svg {
        width: 18px;
        height: 18px;
      }
    }

    .logo-text {
      font-size: 19px;
      font-weight: 700;
      color: var(--text-color-primary);
      margin: 0;
      letter-spacing: -0.01em;
    }
  }

  .header-btn {
    color: var(--user-sidebar-text-muted);
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 6px;

    &:hover {
      color: var(--text-color-primary);
      background-color: transparent;
    }

    .btn-text {
      margin-top: 1px;
    }
  }

  .user-label {
    color: var(--user-sidebar-text-muted);
    font-size: 14px;
    font-weight: 500;
  }

  .theme-toggle-btn {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    border: 1px solid var(--border-color);
    background-color: var(--bg-color-input);
    color: var(--text-color-primary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
    margin-right: 12px;

    &:hover {
      background-color: var(--bg-color-hover);
      border-color: var(--color-primary);
    }

    .el-icon {
      font-size: 18px;
    }
  }
}

// 메인 콘텐츠
.chat-main {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  display: flex;
  justify-content: center;

  // 스크롤바 스타일링 (화면 오른쪽 끝에 위치)
  &::-webkit-scrollbar {
    width: 8px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background-color: var(--scrollbar-thumb);
    border-radius: 4px;

    &:hover {
      background-color: var(--border-color);
    }
  }
}

.chat-content {
  width: 100%;
  max-width: 1200px;
  padding: 0 32px;
}

// 환영 섹션
.welcome-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100%;
  text-align: center;
  padding-bottom: 80px;

  .welcome-icon {
    width: 84px;
    height: 84px;
    border-radius: 24px;
    background-color: var(--icon-bg, #333333);
    border: 2px solid var(--icon-bg-border, #555555);
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 28px;
    color: var(--icon-color, #ffffff);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    transform: rotate(-5deg);
  }

  .welcome-title {
    font-size: 36px;
    font-weight: 700;
    margin: 0 0 16px;
    color: var(--text-color-primary);
    letter-spacing: -0.02em;
  }

  .welcome-subtitle {
    font-size: 17px;
    color: var(--text-color-secondary);
    margin: 0 0 40px;
    max-width: 480px;
    line-height: 1.6;
  }
}

// 예시 질문
.example-queries {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  justify-content: center;
  max-width: 720px;

  .example-btn {
    padding: 14px 22px;
    background-color: var(--icon-bg);
    border: 1px solid var(--icon-bg-border);
    border-radius: 16px;
    color: var(--text-color-primary);
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    align-items: center;
    gap: 10px;

    .btn-icon {
      font-size: 16px;
      color: var(--icon-color-secondary);
    }

    &:hover {
      background-color: var(--bg-color-hover);
      border-color: var(--border-color);
      transform: translateY(-2px);
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }
  }
}

// 메시지 컨테이너
.messages-container {
  padding: 40px 0;
}

// 로딩 인디케이터
.loading-indicator {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 24px 0;
  
  .assistant-avatar-small {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background-color: var(--icon-bg, #333333);
    border: 1px solid var(--icon-bg-border, #555555);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--icon-color, #ffffff);
    flex-shrink: 0;

    svg {
      width: 18px;
      height: 18px;
    }
  }

  .loading-content {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .typing-dots {
    display: flex;
    gap: 5px;

    span {
      width: 6px;
      height: 6px;
      background-color: var(--icon-color-secondary, #cccccc);
      border-radius: 50%;
      animation: typing 1.4s infinite ease-in-out both;

      &:nth-child(1) { animation-delay: -0.32s; }
      &:nth-child(2) { animation-delay: -0.16s; }
    }
  }

  .loading-text {
    font-size: 14px;
    color: var(--text-color-secondary);
    font-weight: 500;
  }
}

@include mx.typing-animation;

// 푸터 (입력 영역)
.chat-footer {
  padding: 12px 32px 16px;
  background-color: var(--user-sidebar-bg);
  transition: var(--theme-transition);
}

.input-container {
  max-width: 1200px;
  margin: 0 auto;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 12px;
  padding: 14px 18px;
  background-color: var(--bg-color-input);
  border-radius: 20px;
  border: 1px solid var(--border-color);
  box-shadow: var(--box-shadow-light);
  transition: border-color 0.2s, box-shadow 0.2s, background-color 0.3s;

  &:focus-within {
    border-color: var(--color-primary);
    box-shadow: var(--box-shadow);
  }
}

// 프롬프트 가이드 버튼
.guide-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 38px;
  height: 38px;
  background-color: var(--icon-bg);
  border: none;
  border-radius: 12px;
  color: var(--text-color-secondary);
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;

  &:hover {
    background-color: var(--bg-color-hover);
    color: var(--color-primary);
  }

  .el-icon {
    font-size: 18px;
  }
}

// 모드 선택 버튼
.mode-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background-color: var(--icon-bg);
  border: none;
  border-radius: 12px;
  color: var(--text-color-primary);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: background-color 0.2s;

  &:hover {
    background-color: var(--bg-color-hover);
  }

  .arrow {
    font-size: 12px;
    color: var(--text-color-secondary);
  }
}

// 텍스트 입력
.chat-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-color-primary);
  font-size: 16px;
  line-height: 1.6;
  resize: none;
  max-height: 200px;
  padding: 4px 0;

  &::placeholder {
    color: var(--text-color-placeholder);
  }
}

// 전송 버튼
.send-btn {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  border: none;
  background-color: var(--icon-bg);
  color: var(--text-color-placeholder);
  cursor: not-allowed;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;

  &.active {
    background-color: var(--color-primary);
    color: #ffffff;
    cursor: pointer;
    box-shadow: var(--box-shadow);

    &:hover {
      transform: scale(1.05);
      box-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
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
  color: var(--text-color-secondary);
  margin: 8px 0 0;
}

// 드롭다운 메뉴 스타일 (전역 스타일 필요)
:deep(.mode-dropdown) {
  background-color: var(--bg-color-card) !important;
  border: 1px solid var(--border-color) !important;

  .el-dropdown-menu__item {
    color: var(--text-color-primary) !important;

    &:hover {
      background-color: var(--bg-color-hover) !important;
    }

    &.active {
      background-color: var(--bg-color-hover) !important;
      color: var(--color-primary) !important;
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
    color: var(--text-color-secondary);
  }
}

// ===========================================
// 모바일 반응형 스타일
// ===========================================
@media (max-width: 768px) {
  .chat-header {
    padding: 12px 16px;

    .header-logo {
      gap: 8px;

      .logo-icon {
        width: 28px;
        height: 28px;

        svg {
          width: 16px;
          height: 16px;
        }
      }

      .logo-text {
        font-size: 17px;
      }
    }

    .theme-toggle-btn {
      width: 32px;
      height: 32px;
      margin-right: 8px;

      .el-icon {
        font-size: 16px;
      }
    }

    .user-label {
      font-size: 13px;
    }
  }

  .chat-content {
    padding: 0 16px;
  }

  .welcome-section {
    padding-bottom: 40px;

    .welcome-icon {
      width: 64px;
      height: 64px;
      border-radius: 18px;
      margin-bottom: 20px;

      svg {
        width: 36px;
        height: 36px;
      }
    }

    .welcome-title {
      font-size: 24px;
      margin-bottom: 12px;
    }

    .welcome-subtitle {
      font-size: 15px;
      margin-bottom: 28px;
      padding: 0 8px;
    }
  }

  .example-queries {
    flex-direction: column;
    gap: 10px;
    width: 100%;
    max-width: 100%;
    padding: 0 8px;

    .example-btn {
      width: 100%;
      padding: 12px 16px;
      border-radius: 12px;
      font-size: 13px;
      justify-content: flex-start;

      .btn-icon {
        font-size: 14px;
      }
    }
  }

  .messages-container {
    padding: 24px 0;
  }

  .chat-footer {
    padding: 8px 16px 12px;
  }

  .input-wrapper {
    padding: 10px 12px;
    border-radius: 16px;
    gap: 8px;
  }

  .guide-btn {
    width: 34px;
    height: 34px;
    border-radius: 10px;

    .el-icon {
      font-size: 16px;
    }
  }

  .mode-btn {
    padding: 8px 10px;
    font-size: 12px;
    border-radius: 10px;
    gap: 6px;

    span {
      display: none; // 모바일에서 텍스트 숨김
    }

    .arrow {
      display: none;
    }
  }

  .chat-input {
    font-size: 15px;
  }

  .send-btn {
    width: 34px;
    height: 34px;
    border-radius: 10px;

    svg {
      width: 16px;
      height: 16px;
    }
  }

  .footer-note {
    font-size: 11px;
    margin-top: 8px;
  }

  .loading-indicator {
    gap: 12px;
    padding: 16px 0;

    .assistant-avatar-small {
      width: 28px;
      height: 28px;

      svg {
        width: 16px;
        height: 16px;
      }
    }

    .loading-text {
      font-size: 13px;
    }
  }
}

// 매우 작은 화면 (375px 이하)
@media (max-width: 375px) {
  .chat-content {
    padding: 0 12px;
  }

  .chat-footer {
    padding: 8px 12px 10px;
  }

  .welcome-section {
    .welcome-title {
      font-size: 22px;
    }

    .welcome-subtitle {
      font-size: 14px;
    }
  }

  .example-queries .example-btn {
    padding: 10px 14px;
    font-size: 12px;
  }
}
</style>
