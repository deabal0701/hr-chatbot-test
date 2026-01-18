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

    <!-- Chat History -->
    <div class="chat-history-section">
      <div class="section-title"><!-- 내 채팅 (일단 주석처리함. ) --> </div>
      <div class="chat-list">
        <div
          v-for="chat in chatHistory"
          :key="chat.id"
          class="chat-item"
          :class="{ active: activeChatId === chat.id }"
          @click="handleSelectChat(chat.id)"
        >
          <el-icon><ChatLineRound /></el-icon>
          <span class="chat-title">{{ chat.title }}</span>
        </div>
      </div>
    </div>

    <!-- Footer with User Label (관리자 링크 주석처리 - 로그인 기능 없음) -->
    <div class="sidebar-footer">
      <!-- <router-link to="/admin" class="admin-link">
        <el-icon><Setting /></el-icon>
        <span>Admin</span>
      </router-link> -->
      <div class="user-link">
        <el-icon><User /></el-icon>
        <span>User</span>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { Close, EditPen, ChatLineRound, Fold, User } from '@element-plus/icons-vue'

const props = defineProps({
  isMobile: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['new-chat', 'select-chat', 'close', 'toggle'])

const store = useStore()

const chatHistory = computed(() => store.getters['chat/getChatHistory'])
const activeChatId = computed(() => store.getters['chat/getActiveChatId'])

const handleNewChat = () => {
  store.dispatch('chat/newChat')
  emit('new-chat')
  if (props.isMobile) {
    emit('close')
  }
}

const handleSelectChat = (chatId) => {
  store.dispatch('chat/selectChat', chatId)
  emit('select-chat', chatId)
  if (props.isMobile) {
    emit('close')
  }
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
  padding: 16px;
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

.chat-history-section {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;

  .section-title {
    font-size: 12px;
    font-weight: 600;
    color: var(--user-sidebar-text-muted);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 12px 8px 8px;
  }

  .chat-list {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .chat-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    border-radius: 8px;
    color: var(--user-sidebar-text);
    font-size: 14px;
    cursor: pointer;
    transition: background-color 0.2s;

    &:hover {
      background-color: var(--user-sidebar-hover-bg);
    }

    &.active {
      background-color: var(--user-sidebar-active-bg);
    }

    .chat-title {
      flex: 1;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  }
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--user-sidebar-border);
  flex-shrink: 0;

  .admin-link {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 8px;
    color: var(--user-sidebar-text-muted);
    font-size: 14px;
    text-decoration: none;
    transition: all 0.2s;

    &:hover {
      background-color: var(--user-sidebar-hover-bg);
      color: var(--user-sidebar-text);
    }
  }

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
    padding: 12px;

    .new-chat-btn {
      height: 40px;
      font-size: 13px;
    }
  }

  .chat-history-section {
    padding: 0 10px;

    .section-title {
      font-size: 11px;
      padding: 10px 6px 6px;
    }

    .chat-item {
      padding: 10px;
      font-size: 13px;
      gap: 10px;
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
