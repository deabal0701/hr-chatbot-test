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
        <span class="logo-text">MUREUM</span>
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

    <!-- New Chat Button -->
    <div class="new-chat-section">
      <button class="new-chat-btn" @click="handleNewChat">
        <el-icon><EditPen /></el-icon>
        <span>새 채팅</span>
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

    <!-- Footer with User Label -->
    <div class="sidebar-footer">
      <div class="user-link">
        <el-icon><User /></el-icon>
        <span>User</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useStore } from 'vuex'
import { Close, EditPen, ChatLineRound, Fold, User, Search, Delete } from '@element-plus/icons-vue'

const props = defineProps({
  isMobile: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['new-chat', 'select-chat', 'close', 'toggle'])

const store = useStore()

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

  .new-chat-btn {
    width: 100%;
    height: 44px;
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
        color: #f56c6c;
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

  .user-link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 8px;
    color: var(--user-sidebar-text-muted);
    font-size: 14px;
  }
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
@media (max-width: 768px) {
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

    .user-link {
      padding: 8px 10px;
      font-size: 13px;
    }
  }
}
</style>
