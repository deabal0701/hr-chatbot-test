<template>
  <div class="chat-view">
    <!-- 채팅 영역 -->
    <div class="chat-container content-card">
      <!-- 메시지 목록 -->
      <div ref="messagesContainer" class="chat-messages">
        <!-- 환영 메시지 -->
        <div v-if="messages.length === 0" class="welcome-message">
          <div class="welcome-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" width="48" height="48">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              <path d="M8 10h.01"></path>
              <path d="M12 10h.01"></path>
              <path d="M16 10h.01"></path>
            </svg>
          </div>
          <h3>{{ appTitle }}에 오신 것을 환영합니다</h3>
          <p>{{ welcomeDescription }}</p>
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
        <ChatInput @send="handleSend" :disabled="isLoading" :placeholder="modePlaceholder" />
      </div>
    </div>

    <!-- 우측: 오버레이 사이드바 -->
    <div
      class="sidebar-overlay-wrapper"
      :class="{ visible: isSidebarVisible }"
      @mouseenter="showSidebar"
      @mouseleave="hideSidebar"
    >
      <!-- 트리거 탭 (항상 보임, 클릭으로 토글) -->
      <div class="sidebar-trigger" @click.stop="toggleSidebar">
        <span class="trigger-arrow">{{ isSidebarVisible ? '»' : '«' }}</span>
      </div>

      <!-- 사이드바 패널 -->
      <div class="chat-sidebar">
        <!-- 프롬프트 가이드 - 추후 사용 예정
        <div class="sidebar-section content-card">
          <h4>프롬프트 가이드</h4>
          <el-button
            type="info"
            plain
            :icon="QuestionFilled"
            @click="showGuideModal = true"
          >
            작성 가이드 보기
          </el-button>
        </div>
        -->

        <!-- 검색 모드 선택 -->
        <div class="sidebar-section content-card">
          <h4>검색 모드</h4>
          <div class="mode-selector-wrapper">
            <!-- Auto 모드 - 추후 사용 예정
            <el-radio-group v-model="searchMode" @change="handleModeChange" class="mode-row-primary">
              <el-radio-button value="auto">Auto</el-radio-button>
            </el-radio-group>
            -->
            <el-radio-group v-model="searchMode" @change="handleModeChange" class="mode-row-secondary">
              <el-radio-button value="rag">RAG</el-radio-button>
              <el-radio-button value="nl2sql">NL2SQL</el-radio-button>
              <!-- Agent 모드 - 추후 복원 예정
              <el-radio-button value="agent">Agent</el-radio-button>
              -->
            </el-radio-group>
          </div>
          <p class="mode-description">
            <!-- Auto 모드 설명 - 추후 사용 예정
            <template v-if="searchMode === 'auto'">
              질문을 분석하여 자동으로 적합한 검색 방식을 선택합니다.
            </template>
            -->
            <template v-if="searchMode === 'rag'">
              문서 기반 검색 (정책, 가이드, 규정 등)
            </template>
            <template v-else-if="searchMode === 'nl2sql'">
              데이터베이스 조회 (통계, 수치 데이터 등)
            </template>
            <!-- Agent 모드 설명 - 추후 복원 예정
            <template v-else-if="searchMode === 'agent'">
              AI Agent가 도구를 자율 선택하여 복합 질문 처리<br>
              <small>(DB 조회 → 문서 검색 → 계산)</small>
            </template>
            -->
          </p>
        </div>

        <!-- 대화 관리 -->
        <div class="sidebar-section content-card">
          <h4>대화 관리</h4>
          <el-button
            type="danger"
            plain
            size="small"
            :icon="Delete"
            :disabled="messages.length === 0"
            style="width: 100%"
            @click="clearChat"
          >
            대화 초기화
          </el-button>
        </div>
      </div>
    </div>

    <!-- 프롬프트 가이드 모달 -->
    <PromptGuideModal
      v-model="showGuideModal"
      :mode="searchMode"
      @use-example="handleUseExample"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { useStore } from 'vuex'
import { Loading, Delete } from '@element-plus/icons-vue'
import ChatMessage from '@/components/chat/ChatMessage.vue'
import ChatInput from '@/components/chat/ChatInput.vue'
import PromptGuideModal from '@/components/chat/PromptGuideModal.vue'

const appTitle = import.meta.env.VITE_APP_TITLE || 'MUREUM'
const store = useStore()
const messagesContainer = ref(null)
const showGuideModal = ref(false)

// 사이드바 호버 슬라이드 (진입/이탈 모두 1초 대기 후 트랜지션)
const isSidebarVisible = ref(false)
let sidebarShowTimer = null
let sidebarHideTimer = null

const showSidebar = () => {
  if (sidebarHideTimer) {
    clearTimeout(sidebarHideTimer)
    sidebarHideTimer = null
  }
  if (!isSidebarVisible.value && !sidebarShowTimer) {
    sidebarShowTimer = setTimeout(() => {
      isSidebarVisible.value = true
      sidebarShowTimer = null
    }, 500)
  }
}

const hideSidebar = () => {
  if (sidebarShowTimer) {
    clearTimeout(sidebarShowTimer)
    sidebarShowTimer = null
  }
  if (isSidebarVisible.value) {
    sidebarHideTimer = setTimeout(() => {
      isSidebarVisible.value = false
      sidebarHideTimer = null
    }, 500)
  }
}

// 트리거 클릭으로 즉시 토글
const toggleSidebar = () => {
  if (sidebarShowTimer) { clearTimeout(sidebarShowTimer); sidebarShowTimer = null }
  if (sidebarHideTimer) { clearTimeout(sidebarHideTimer); sidebarHideTimer = null }
  isSidebarVisible.value = !isSidebarVisible.value
}

const messages = computed(() => store.state.chat.messages)
const isLoading = computed(() => store.state.chat.isLoading)
const searchMode = computed({
  get: () => store.state.chat.searchMode,
  set: (value) => store.dispatch('chat/setMode', value)
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

// 검색 모드별 환영 메시지 설명
const welcomeDescription = computed(() => {
  if (searchMode.value === 'nl2sql') return '데이터베이스 기반 질문을 자유롭게 해주세요.'
  if (searchMode.value === 'agent') return 'AI Agent에게 복합 질문을 자유롭게 해주세요.'
  return '문서 기반 질문을 자유롭게 해주세요.'
})

// 검색 모드별 입력 플레이스홀더
const modePlaceholder = computed(() => {
  const modeLabels = { rag: 'RAG', nl2sql: 'NL2SQL', agent: 'Agent' }
  const label = modeLabels[searchMode.value] || searchMode.value
  return `[${label}] 질문을 입력하세요...`
})

const exampleQueries = computed(() => {
  if (searchMode.value === 'nl2sql') {
    return nl2sqlExampleQueries
  }
  if (searchMode.value === 'agent') {
    return agentExampleQueries
  }
  return ragExampleQueries
})

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

// 가이드에서 예시 사용
const handleUseExample = (example) => {
  handleSend(example)
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
@use '../../assets/styles/mixins' as mx;

.chat-view {
  display: flex;
  position: relative;
  height: calc(100vh - 84px);
  overflow: hidden;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 0;
  margin-bottom: 0;
  overflow: hidden;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;

  // 관리자 화면: 어시스턴트 응답 폭 확장
  :deep(.message-bubble.assistant) {
    max-width: 90%;
  }
}

.welcome-message {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-color-regular);

  .welcome-icon {
    width: 84px;
    height: 84px;
    border-radius: 24px;
    background-color: var(--icon-bg, #333333);
    border: 2px solid var(--icon-bg-border, #555555);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 28px;
    color: var(--icon-color, #ffffff);
    box-shadow: var(--box-shadow);
    transform: rotate(-5deg);
  }

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

  @include mx.rotating-animation;
}

.chat-input-area {
  padding: 12px 20px;
  border-top: 1px solid var(--chat-input-border);
  background-color: var(--chat-input-bg);
  transition: var(--theme-transition);
}

// 우측 오버레이 사이드바 래퍼 (트리거 + 사이드바를 flex로 묶어 한 덩어리로 슬라이딩)
.sidebar-overlay-wrapper {
  position: absolute;
  right: 0;
  top: 0;
  height: 100%;
  display: flex;
  z-index: 10;
  transform: translateX(280px);
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);

  &.visible {
    transform: translateX(0);

    .chat-sidebar {
      box-shadow: var(--box-shadow);
    }

    .sidebar-trigger .trigger-arrow {
      opacity: 0.8;
      color: var(--color-primary, #409eff);
      background-color: var(--bg-color-card);
    }
  }
}

// 트리거 영역 (투명 flex 아이템, 중앙에 작은 탭만 표시)
.sidebar-trigger {
  width: 24px;
  flex-shrink: 0;
  position: relative;
  cursor: pointer;

  .trigger-arrow {
    position: absolute;
    top: 50%;
    left: 0;
    transform: translateY(-50%);
    width: 24px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--bg-color-card);
    border: 1px solid var(--border-color);
    border-right: none;
    border-radius: 6px 0 0 6px;
    font-size: 13px;
    font-weight: 700;
    color: var(--text-color-secondary);
    opacity: 0.5;
    user-select: none;
    transition: opacity 0.2s ease, color 0.2s ease, background-color 0.2s ease;
  }

  &:hover .trigger-arrow {
    opacity: 1;
    color: var(--color-primary, #409eff);
  }
}

// 사이드바 패널 (flex 아이템)
.chat-sidebar {
  width: 280px;
  flex-shrink: 0;
  height: 100%;
  overflow-y: auto;
  padding-top: 0;
  background-color: var(--bg-color-page);
  border-left: 1px solid var(--border-color);
  transition: box-shadow 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.sidebar-section {
  margin-bottom: 12px;
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

.sidebar-row {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.sidebar-half-card {
  flex: 1;
  margin-bottom: 0;

  .el-button {
    width: 100%;
    padding: 8px 4px;
    font-size: 12px;
  }
}
</style>
