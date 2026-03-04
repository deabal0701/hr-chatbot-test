<template>
  <div class="user-chat-layout" :class="{ 'sidebar-collapsed': !sidebarVisible }">
    <!-- Mobile overlay -->
    <div
      v-if="sidebarVisible && isMobile"
      class="sidebar-overlay"
      @click="closeSidebar"
    />

    <!-- Desktop sidebar toggle button (when collapsed) -->
    <button
      v-if="!sidebarVisible && !isMobile"
      class="sidebar-expand-btn"
      @click="toggleSidebar"
      title="사이드바 열기"
    >
      <el-icon :size="20"><Expand /></el-icon>
    </button>

    <!-- Sidebar -->
    <transition name="sidebar-slide">
      <UserChatSidebar
        v-show="sidebarVisible"
        :class="{ 'mobile-visible': sidebarVisible && isMobile }"
        :is-mobile="isMobile"
        @close="closeSidebar"
        @toggle="toggleSidebar"
      />
    </transition>

    <!-- Main Chat Area -->
    <div class="chat-area">
      <!-- Desktop header with actions -->
      <header v-if="!isMobile" class="desktop-header">
        <div class="header-left"></div>
        <div class="header-actions">
          <!-- [임시 비활성화] 테마 토글 - 이 코드를 삭제하지 마시오. 추후 복구 예정입니다.
          <el-tooltip :content="isDarkMode ? '라이트 모드로 전환' : '다크 모드로 전환'" placement="bottom">
            <el-button
              circle
              :icon="isDarkMode ? Sunny : Moon"
              @click="toggleDarkMode"
              class="theme-toggle-btn"
            />
          </el-tooltip>
          -->
          <button class="action-btn" @click="handleShare" title="공유하기">
            <el-icon :size="18"><Share /></el-icon>
            <span>공유하기</span>
          </button>
          <button class="action-btn" @click="handleSave" title="저장하기">
            <el-icon :size="18"><Download /></el-icon>
            <span>저장하기</span>
          </button>
        </div>
      </header>

      <!-- Mobile header with toggle -->
      <header v-if="isMobile" class="mobile-header">
        <button class="sidebar-toggle-btn" @click="toggleSidebar">
          <el-icon :size="20"><Menu /></el-icon>
        </button>
        <h1 class="logo-text">{{ appTitle }}</h1>
        <div class="header-actions-mobile">
          <!-- [임시 비활성화] 테마 토글 - 이 코드를 삭제하지 마시오. 추후 복구 예정입니다.
          <button class="action-btn-icon" @click="toggleDarkMode" :title="isDarkMode ? '라이트 모드' : '다크 모드'">
            <el-icon :size="18"><Sunny v-if="isDarkMode" /><Moon v-else /></el-icon>
          </button>
          -->
          <button class="action-btn-icon" @click="handleShare" title="공유하기">
            <el-icon :size="18"><Share /></el-icon>
          </button>
          <button class="action-btn-icon" @click="handleSave" title="저장하기">
            <el-icon :size="18"><Download /></el-icon>
          </button>
          <!-- 모바일: 사용자 아바타 / 로그인 아이콘 -->
          <el-avatar v-if="isAuthenticated" :size="24" class="mobile-user-avatar">
            <el-icon :size="12"><UserFilled /></el-icon>
          </el-avatar>
          <button v-else class="action-btn-icon" @click="goToLogin" title="로그인">
            <el-icon :size="18"><User /></el-icon>
          </button>
        </div>
      </header>

      <!-- Chat View -->
      <UserChatView :hide-header="true" />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { useTheme } from '@/composables/useTheme'
import { Menu, Expand, Share, Download, Sunny, Moon, User, UserFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import UserChatSidebar from '@/components/user/UserChatSidebar.vue'
import UserChatView from '@/views/user/UserChatView.vue'

const appTitle = import.meta.env.VITE_APP_TITLE || 'MUREUM'
const store = useStore()
const router = useRouter()

// ===== 인증 상태 =====
const { isAuthenticated } = useAuth()

const goToLogin = () => {
  router.push({ path: '/login', query: { redirect: '/chat' } })
}

const windowWidth = ref(window.innerWidth)
const MOBILE_BREAKPOINT = 768

const isMobile = computed(() => windowWidth.value <= MOBILE_BREAKPOINT)
const sidebarVisible = computed(() => store.state.app.userSidebarVisible)

// 테마 관련
const { isDarkMode, toggleDarkMode } = useTheme()

const toggleSidebar = () => {
  store.dispatch('app/toggleUserSidebar')
}

const closeSidebar = () => {
  if (isMobile.value) {
    store.dispatch('app/setUserSidebarVisible', false)
  }
}

// 공유하기 기능
const handleShare = async () => {
  // HTTPS 또는 localhost가 아닌 경우 클립보드 API 사용 불가
  if (!window.isSecureContext) {
    ElMessage.warning('공유 기능은 https:// 주소에서만 지원됩니다. 관리자에게 문의해 주세요.')
    return
  }

  const messages = store.state.chat.messages
  if (messages.length === 0) {
    ElMessage.warning('공유할 대화 내용이 없습니다.')
    return
  }

  // 대화 내용을 텍스트로 변환
  const chatText = messages.map(msg => {
    const role = msg.role === 'user' ? '사용자' : 'AI'
    return `[${role}]\n${msg.content}`
  }).join('\n\n---\n\n')

  try {
    await navigator.clipboard.writeText(chatText)
    ElMessage.success('대화 내용이 클립보드에 복사되었습니다.')
  } catch {
    ElMessage.error('클립보드 복사에 실패했습니다.')
  }
}

// 저장하기 기능
const handleSave = () => {
  const messages = store.state.chat.messages
  if (messages.length === 0) {
    ElMessage.warning('저장할 대화 내용이 없습니다.')
    return
  }

  // 대화 내용을 마크다운으로 변환
  const now = new Date()
  const dateStr = now.toLocaleDateString('ko-KR')
  const timeStr = now.toLocaleTimeString('ko-KR')

  let markdown = `# ${appTitle} 대화 기록\n\n`
  markdown += `- 저장 일시: ${dateStr} ${timeStr}\n`
  markdown += `- 메시지 수: ${messages.length}개\n\n---\n\n`

  messages.forEach(msg => {
    const role = msg.role === 'user' ? '👤 사용자' : '🤖 AI'
    markdown += `## ${role}\n\n${msg.content}\n\n`

    // RAG 소스가 있으면 추가
    if (msg.ragResult?.sources?.length > 0) {
      markdown += `<details>\n<summary>📚 참조 문서</summary>\n\n`
      msg.ragResult.sources.forEach((src, idx) => {
        markdown += `${idx + 1}. **${src.title}** (유사도: ${(src.score * 100).toFixed(1)}%)\n`
      })
      markdown += `\n</details>\n\n`
    }

    // SQL 결과가 있으면 추가
    if (msg.nl2sqlResult?.sql) {
      markdown += `<details>\n<summary>🔍 SQL 쿼리</summary>\n\n\`\`\`sql\n${msg.nl2sqlResult.sql}\n\`\`\`\n\n</details>\n\n`
    }

    markdown += `---\n\n`
  })

  // 파일 다운로드
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `mureum-chat-${now.toISOString().slice(0, 10)}.md`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)

  ElMessage.success('대화 내용이 저장되었습니다.')
}

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  // 모바일에서는 항상 사이드바 숨김, 데스크탑에서는 localStorage 저장값 유지
  if (isMobile.value) {
    store.dispatch('app/setUserSidebarVisible', false)
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
@use '../../assets/styles/mixins' as mx;

.user-chat-layout {
  display: flex;
  height: 100vh;
  width: 100vw;
  overflow: hidden;
  background-color: var(--user-sidebar-bg);
  transition: var(--theme-transition);
}

.chat-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0; // Prevent flex item from overflowing
}

// Desktop header
.desktop-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background-color: var(--user-sidebar-bg);
  flex-shrink: 0;
  transition: var(--theme-transition);

  .header-left {
    flex: 1;
  }

  .header-actions {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

// 테마 토글 버튼 (el-button circle 스타일)
.theme-toggle-btn {
  border: 1px solid var(--border-color);
  background-color: var(--bg-color-overlay);
  color: var(--text-color-regular);
  transition: var(--theme-transition);

  &:hover {
    color: var(--color-primary);
    border-color: var(--color-primary);
    background-color: var(--bg-color-hover);
  }
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background-color: transparent;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-color-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background-color: var(--bg-color-hover);
    border-color: var(--color-primary);
    color: var(--text-color-primary);
  }
}

.action-btn-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  background-color: transparent;
  border: none;
  border-radius: 8px;
  color: var(--text-color-secondary);
  cursor: pointer;
  transition: all 0.2s;

  &:hover {
    background-color: var(--bg-color-hover);
    color: var(--text-color-primary);
  }
}

.mobile-header {
  display: none;
  align-items: center;
  padding: 12px 16px;
  gap: 12px;
  border-bottom: 1px solid var(--user-sidebar-border);
  background-color: var(--user-sidebar-bg);
  flex-shrink: 0;
  transition: var(--theme-transition);

  .sidebar-toggle-btn {
    background: none;
    border: none;
    padding: 8px;
    cursor: pointer;
    color: var(--text-color-primary);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;

    &:hover {
      background-color: var(--bg-color-hover);
    }
  }

  .logo-text {
    flex: 1;
    font-size: 18px;
    font-weight: 700;
    color: var(--text-color-primary);
    margin: 0;
    text-align: center;
  }

  .header-actions-mobile {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .mobile-user-avatar {
    background-color: var(--avatar-bg);
    color: var(--avatar-text);
    flex-shrink: 0;
  }
}

.sidebar-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

// Sidebar transition
@include mx.sidebar-slide-transition;

// Mobile responsive
@media (max-width: 768px) {
  .user-chat-layout {
    position: relative;
  }

  .mobile-header {
    display: flex;
  }

  :deep(.user-chat-sidebar) {
    position: fixed;
    top: 0;
    left: 0;
    height: 100%;
    z-index: 1000;
    transform: translateX(-100%);
    transition: transform 0.3s ease;

    &.mobile-visible {
      transform: translateX(0);
    }
  }
}

@media (min-width: 769px) {
  .sidebar-overlay {
    display: none;
  }
}

// Desktop sidebar expand button (when collapsed)
.sidebar-expand-btn {
  position: fixed;
  top: 16px;
  left: 16px;
  z-index: 100;
  width: 40px;
  height: 40px;
  background-color: var(--user-sidebar-bg, #171717);
  border: 1px solid var(--user-sidebar-border, #2a2a2a);
  border-radius: 8px;
  color: var(--user-sidebar-text, #ececec);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;

  &:hover {
    background-color: var(--user-sidebar-hover-bg, #212121);
  }
}
</style>
