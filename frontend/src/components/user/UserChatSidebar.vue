<template>
  <aside class="user-chat-sidebar">
    <!-- Header with Logo and Toggle -->
    <div class="sidebar-header">
      <div class="logo-section">
        <div class="logo-icon">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <span class="logo-text">{{ appTitle }}</span>
      </div>
      <!-- Desktop collapse button -->
      <button v-if="!isMobile" class="collapse-btn" @click="$emit('toggle')" title="사이드바 접기">
        <el-icon><Fold /></el-icon>
      </button>
      <!-- Mobile close button -->
      <button class="close-btn" @click="$emit('close')" v-if="isMobile">
        <el-icon><Close /></el-icon>
      </button>
    </div>

    <!-- New Chat & Dashboard Buttons -->
    <div class="new-chat-section">
      <button class="new-chat-btn" @click="handleNewChat">
        <el-icon><RefreshRight /></el-icon>
        <span>새 채팅</span>
      </button>
      <button class="new-chat-btn dashboard-btn" @click="goToDashboard" :class="{ active: isDashboardRoute }">
        <el-icon><DataAnalysis /></el-icon>
        <span>나의 대시보드</span>
      </button>
      <button v-if="canAccessAdmin" class="new-chat-btn admin-btn" @click="goToAdmin">
        <el-icon><Setting /></el-icon>
        <span>관리자 페이지</span>
      </button>
    </div>

    <!-- Search Input -->
    <div class="search-section">
      <div class="search-input-wrapper">
        <el-icon class="search-icon"><Search /></el-icon>
        <input
          v-model="searchQuery"
          type="text"
          class="search-input"
          placeholder="이력 검색..."
          @input="handleSearchInput"
        />
        <button v-if="searchQuery" class="search-clear-btn" @click="clearSearch">
          <el-icon><Close /></el-icon>
        </button>
      </div>
    </div>

    <!-- Chat History -->
    <div class="chat-history-section">
      <!-- Loading State -->
      <div v-if="historyLoading && chatHistory.length === 0" class="history-loading">
        <div v-for="i in 5" :key="i" class="skeleton-item">
          <div class="skeleton-line"></div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="chatHistory.length === 0" class="history-empty">
        <el-icon class="empty-icon"><ChatLineRound /></el-icon>
        <p>{{ searchQuery ? '검색 결과가 없습니다' : '검색 이력이 없습니다' }}</p>
      </div>

      <!-- Grouped Chat List -->
      <template v-else>
        <div v-for="group in groupedHistory" :key="group.label" class="history-group">
          <div class="group-label">{{ group.label }}</div>
          <div class="chat-list">
            <div
              v-for="chat in group.items"
              :key="chat.session_key"
              class="chat-item"
              :class="{ active: activeChatId === chat.session_key }"
              @click="handleSelectChat(chat.session_key)"
            >
              <span class="chat-title">{{ chat.title }}</span>
              <button
                class="chat-delete-btn"
                @click.stop="handleDeleteChat(chat.session_key)"
                title="삭제"
              >
                <el-icon><Delete /></el-icon>
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>

    <!-- Footer with User Info / Login -->
    <div class="sidebar-footer">
      <!-- 인증됨: 사용자 드롭다운 -->
      <el-dropdown v-if="isAuthenticated" @command="handleUserCommand" trigger="click" placement="top-start">
        <div class="user-info-btn">
          <el-avatar :size="28" class="user-avatar">
            <el-icon :size="14"><UserFilled /></el-icon>
          </el-avatar>
          <div class="user-info-text">
            <span class="user-name">{{ displayName }}</span>
          </div>
          <el-icon class="user-more"><MoreFilled /></el-icon>
        </div>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item disabled>
              <span class="user-role-label">권한 : {{ roleName }}</span>
            </el-dropdown-item>
            <el-dropdown-item command="password" divided>
              <el-icon><Lock /></el-icon> 비밀번호 변경
            </el-dropdown-item>
            <el-dropdown-item command="logout">
              <el-icon><SwitchButton /></el-icon> 로그아웃
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- 미인증: 로그인 버튼 -->
      <button v-else class="login-btn" @click="goToLogin">
        <el-icon><User /></el-icon>
        <span>로그인</span>
      </button>
    </div>

    <!-- 비밀번호 변경 다이얼로그 -->
    <el-dialog
      v-model="passwordDialogVisible"
      title="비밀번호 변경"
      width="420px"
      :close-on-click-modal="false"
      append-to-body
    >
      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-position="top"
      >
        <el-form-item label="현재 비밀번호" prop="currentPassword">
          <el-input v-model="passwordForm.currentPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="새 비밀번호" prop="newPassword">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="비밀번호 확인" prop="confirmPassword">
          <el-input v-model="passwordForm.confirmPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="passwordDialogVisible = false">취소</el-button>
        <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">변경</el-button>
      </template>
    </el-dialog>
  </aside>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { useAuth } from '@/composables/useAuth'
import { ElMessage } from 'element-plus'
import { Close, RefreshRight, ChatLineRound, Fold, User, Search, Delete, UserFilled, MoreFilled, Lock, SwitchButton, DataAnalysis, Setting } from '@element-plus/icons-vue'

const appTitle = import.meta.env.VITE_APP_TITLE || 'win-AI'

const props = defineProps({
  isMobile: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['new-chat', 'select-chat', 'close', 'toggle'])

const store = useStore()
const router = useRouter()

// ===== 인증 상태 =====
const { isAuthenticated, displayName, roleName, canAccessAdmin, logout } = useAuth()

// 사용자 메뉴 커맨드 처리
const handleUserCommand = async (command) => {
  if (command === 'logout') {
    await logout()
    router.push('/login')
  } else if (command === 'password') {
    passwordDialogVisible.value = true
  }
}

// 로그인 페이지로 이동
const goToLogin = () => {
  router.push({ path: '/login', query: { redirect: '/chat' } })
}

// ===== 대시보드/관리자 네비게이션 =====
const isDashboardRoute = computed(() => router.currentRoute.value.path === '/dashboard')
const goToDashboard = () => {
  router.push('/dashboard')
  if (props.isMobile) emit('close')
}
const goToAdmin = () => {
  // 사용자가 접근 가능한 첫 번째 관리 메뉴로 이동 (menu_path는 /admin/... 전체 경로)
  const menus = store.getters['auth/menus'] || []
  const adminPage = menus.find(m => m.menu_path && m.menu_type === 'PAGE' && m.menu_path.startsWith('/admin'))
  router.push(adminPage ? adminPage.menu_path : '/admin/dashboard')
  if (props.isMobile) emit('close')
}

// ===== 비밀번호 변경 =====
const passwordDialogVisible = ref(false)
const passwordLoading = ref(false)
const passwordFormRef = ref(null)
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  currentPassword: [
    { required: true, message: '현재 비밀번호를 입력해주세요', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '새 비밀번호를 입력해주세요', trigger: 'blur' },
    { min: 8, message: '8자 이상 입력해주세요', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '비밀번호를 다시 입력해주세요', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('비밀번호가 일치하지 않습니다'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

const handleChangePassword = async () => {
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) return

  passwordLoading.value = true
  try {
    await store.dispatch('auth/changePassword', {
      currentPassword: passwordForm.currentPassword,
      newPassword: passwordForm.newPassword
    })
    ElMessage.success('비밀번호가 변경되었습니다')
    passwordDialogVisible.value = false
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (err) {
    ElMessage.error(err.message || '비밀번호 변경에 실패했습니다')
  } finally {
    passwordLoading.value = false
  }
}

const searchQuery = ref('')
let searchTimer = null

const chatHistory = computed(() => store.getters['chat/getChatHistory'])
const activeChatId = computed(() => store.getters['chat/getActiveChatId'])
const historyLoading = computed(() => store.getters['chat/isHistoryLoading'])

// 날짜 그룹핑 (ChatGPT 스타일)
const groupedHistory = computed(() => {
  const groups = []
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)
  const weekAgo = new Date(today)
  weekAgo.setDate(weekAgo.getDate() - 7)
  const monthAgo = new Date(today)
  monthAgo.setDate(monthAgo.getDate() - 30)

  const buckets = {
    today: { label: '오늘', items: [] },
    yesterday: { label: '어제', items: [] },
    week: { label: '지난 7일', items: [] },
    month: { label: '지난 30일', items: [] },
    older: { label: '이전', items: [] }
  }

  for (const chat of chatHistory.value) {
    const date = new Date(chat.last_activity || chat.created_at)
    if (date >= today) {
      buckets.today.items.push(chat)
    } else if (date >= yesterday) {
      buckets.yesterday.items.push(chat)
    } else if (date >= weekAgo) {
      buckets.week.items.push(chat)
    } else if (date >= monthAgo) {
      buckets.month.items.push(chat)
    } else {
      buckets.older.items.push(chat)
    }
  }

  for (const bucket of Object.values(buckets)) {
    if (bucket.items.length > 0) {
      groups.push(bucket)
    }
  }

  return groups
})

const handleNewChat = () => {
  store.dispatch('chat/newChat')
  emit('new-chat')
  if (props.isMobile) {
    emit('close')
  }
}

const handleSelectChat = (sessionKey) => {
  store.dispatch('chat/selectChat', sessionKey)
  emit('select-chat', sessionKey)
  if (props.isMobile) {
    emit('close')
  }
}

const handleDeleteChat = (sessionKey) => {
  store.dispatch('chat/deleteChatHistory', sessionKey)
}

const handleSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    store.dispatch('chat/fetchChatHistory', searchQuery.value || null)
  }, 300)
}

const clearSearch = () => {
  searchQuery.value = ''
  store.dispatch('chat/fetchChatHistory')
}
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.user-chat-sidebar {
  width: var(--user-sidebar-width);
  height: 100%;
  background-color: var(--user-sidebar-bg);
  border-right: 1px solid var(--user-sidebar-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--user-sidebar-border);
  flex-shrink: 0;

  .logo-section {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .logo-icon {
    width: 36px;
    height: 36px;
    background-color: var(--icon-bg);
    border: 1px solid var(--icon-bg-border);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--icon-color);
  }

  .logo-text {
    font-size: 18px;
    font-weight: 700;
    color: var(--user-sidebar-text);
  }

  .close-btn,
  .collapse-btn {
    background: none;
    border: none;
    padding: 8px;
    cursor: pointer;
    color: var(--user-sidebar-text-muted);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s;

    &:hover {
      background-color: var(--user-sidebar-hover-bg);
      color: var(--user-sidebar-text);
    }
  }
}

.new-chat-section {
  padding: 12px 16px 0;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;

  .new-chat-btn {
    width: 100%;
    height: 42px;
    background-color: transparent;
    border: 1px dashed var(--user-sidebar-border);
    border-radius: 10px;
    color: var(--user-sidebar-text);
    font-size: 14px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    padding-left: 12px;
    gap: 8px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background-color: var(--user-sidebar-hover-bg);
      border-style: solid;
      border-color: var(--user-sidebar-text-muted);
    }

    &.dashboard-btn {
      font-weight: 500;
      font-size: 13px;
      height: 38px;

      &.active {
        background-color: rgba(var(--color-primary-rgb), 0.08);
        border: 1px solid var(--el-color-primary);
        color: var(--el-color-primary);
      }
    }

    &.admin-btn {
      font-weight: 500;
      font-size: 13px;
      height: 38px;
    }
  }
}

.search-section {
  padding: 12px 16px;
  flex-shrink: 0;

  .search-input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-icon {
    position: absolute;
    left: 10px;
    color: var(--user-sidebar-text-muted);
    font-size: 14px;
    pointer-events: none;
  }

  .search-input {
    width: 100%;
    height: 36px;
    padding: 0 32px 0 32px;
    border: 1px solid var(--user-sidebar-border);
    border-radius: 8px;
    background-color: transparent;
    color: var(--user-sidebar-text);
    font-size: 13px;
    outline: none;
    transition: border-color 0.2s;

    &::placeholder {
      color: var(--user-sidebar-text-muted);
    }

    &:focus {
      border-color: var(--user-sidebar-text-muted);
    }
  }

  .search-clear-btn {
    position: absolute;
    right: 6px;
    background: none;
    border: none;
    padding: 4px;
    cursor: pointer;
    color: var(--user-sidebar-text-muted);
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 12px;

    &:hover {
      color: var(--user-sidebar-text);
    }
  }
}

.chat-history-section {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;

  .history-group {
    margin-bottom: 4px;
  }

  .group-label {
    font-size: 11px;
    font-weight: 600;
    color: var(--user-sidebar-text-muted);
    padding: 10px 8px 6px;
    letter-spacing: 0.02em;
  }

  .chat-list {
    display: flex;
    flex-direction: column;
    gap: 1px;
  }

  .chat-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 10px;
    border-radius: 8px;
    color: var(--user-sidebar-text);
    font-size: 13px;
    cursor: pointer;
    transition: background-color 0.15s;
    position: relative;

    &:hover {
      background-color: var(--user-sidebar-hover-bg);

      .chat-delete-btn {
        opacity: 1;
      }
    }

    &.active {
      background-color: var(--user-sidebar-active-bg);
    }

    .chat-title {
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      min-width: 0;
    }

    .chat-delete-btn {
      flex-shrink: 0;
      opacity: 0;
      background: none;
      border: none;
      padding: 2px;
      cursor: pointer;
      color: var(--user-sidebar-text-muted);
      border-radius: 4px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 13px;
      transition: opacity 0.15s, color 0.15s;

      &:hover {
        color: var(--color-danger);
      }
    }
  }

  // Loading skeleton
  .history-loading {
    padding: 8px 0;

    .skeleton-item {
      padding: 10px 12px;

      .skeleton-line {
        height: 14px;
        border-radius: 4px;
        background: linear-gradient(
          90deg,
          var(--user-sidebar-border) 25%,
          var(--user-sidebar-hover-bg) 50%,
          var(--user-sidebar-border) 75%
        );
        background-size: 200% 100%;
        animation: skeleton-shimmer 1.5s infinite;
      }

      &:nth-child(1) .skeleton-line { width: 85%; }
      &:nth-child(2) .skeleton-line { width: 70%; }
      &:nth-child(3) .skeleton-line { width: 90%; }
      &:nth-child(4) .skeleton-line { width: 60%; }
      &:nth-child(5) .skeleton-line { width: 75%; }
    }
  }

  // Empty state
  .history-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 20px;
    color: var(--user-sidebar-text-muted);

    .empty-icon {
      font-size: 32px;
      margin-bottom: 12px;
      opacity: 0.4;
    }

    p {
      font-size: 13px;
      margin: 0;
    }
  }
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--user-sidebar-border);
  flex-shrink: 0;

  .user-info-btn {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border-radius: 8px;
    cursor: pointer;
    transition: background-color 0.2s;
    width: 100%;

    &:hover {
      background-color: var(--user-sidebar-hover-bg);
    }

    .user-avatar {
      flex-shrink: 0;
      background-color: var(--avatar-bg);
      color: var(--avatar-text);
    }

    .user-info-text {
      flex: 1;
      min-width: 0;
    }

    .user-name {
      font-size: 14px;
      font-weight: 500;
      color: var(--user-sidebar-text);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
      display: block;
    }

    .user-more {
      flex-shrink: 0;
      color: var(--user-sidebar-text-muted);
      font-size: 16px;
    }
  }

  .login-btn {
    width: 100%;
    height: 40px;
    background-color: transparent;
    border: 1px dashed var(--user-sidebar-border);
    border-radius: 8px;
    color: var(--user-sidebar-text-muted);
    font-size: 14px;
    display: flex;
    align-items: center;
    justify-content: flex-start;
    padding-left: 12px;
    gap: 10px;
    cursor: pointer;
    transition: all 0.2s;

    &:hover {
      background-color: var(--user-sidebar-hover-bg);
      border-style: solid;
      color: var(--user-sidebar-text);
    }
  }
}

.user-role-label {
  font-size: 13px;
  color: var(--text-color-primary);
  font-weight: 500;
}

// Scrollbar styling
.chat-history-section {
  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: transparent;
  }

  &::-webkit-scrollbar-thumb {
    background-color: var(--user-sidebar-border);
    border-radius: 3px;

    &:hover {
      background-color: var(--user-sidebar-text-muted);
    }
  }
}

// ===========================================
// 모바일 반응형 스타일
// ===========================================
@include mx.mobile {
  .user-chat-sidebar {
    width: 280px;
    max-width: 85vw;
  }

  .sidebar-header {
    padding: 14px;

    .logo-icon {
      width: 32px;
      height: 32px;
      border-radius: 8px;

      svg {
        width: 20px;
        height: 20px;
      }
    }

    .logo-text {
      font-size: 16px;
    }

    .close-btn {
      width: 36px;
      height: 36px;
    }
  }

  .new-chat-section {
    padding: 10px 12px 0;

    .new-chat-btn {
      height: 40px;
      font-size: 13px;
    }
  }

  .search-section {
    padding: 10px 12px;
  }

  .chat-history-section {
    padding: 0 10px;

    .group-label {
      font-size: 10px;
      padding: 8px 6px 4px;
    }

    .chat-item {
      padding: 9px 8px;
      font-size: 12px;
      gap: 8px;
    }
  }

  .sidebar-footer {
    padding: 12px;

    .user-info-btn {
      padding: 6px 8px;

      .user-name {
        font-size: 13px;
      }
    }

    .login-btn {
      height: 36px;
      font-size: 13px;
    }
  }
}
</style>
