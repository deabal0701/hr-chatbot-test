<template>
  <el-container class="admin-layout">
    <!-- 사이드바 래퍼 (토글 버튼 포함) -->
    <div class="sidebar-wrapper" :class="{ collapsed: sidebarCollapsed }">
      <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="admin-sidebar">
        <AppSidebar />
      </el-aside>

      <!-- 사이드바 토글 버튼 -->
      <button class="sidebar-toggle" @click="toggleSidebar">
        <el-icon :size="10">
          <ArrowLeft v-if="!sidebarCollapsed" />
          <ArrowRight v-else />
        </el-icon>
      </button>
    </div>

    <!-- 메인 영역 -->
    <el-container class="admin-main">
      <!-- 헤더 -->
      <el-header class="admin-header" height="60px">
        <AppHeader />
      </el-header>

      <!-- 콘텐츠 -->
      <el-main class="admin-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'

const store = useStore()
const sidebarCollapsed = computed(() => store.state.app.sidebarCollapsed)

const toggleSidebar = () => {
  store.dispatch('app/toggleSidebar')
}

// 관리자 화면 진입 시 currentView 설정
onMounted(() => {
  store.dispatch('app/setCurrentView', 'admin')
})
</script>

<style lang="scss" scoped>
.admin-layout {
  height: 100vh;
  overflow: hidden;
}

.sidebar-wrapper {
  position: relative;
  display: flex;
  flex-shrink: 0;

  &.collapsed {
    .sidebar-toggle {
      right: -6px;
    }
  }
}

.admin-sidebar {
  background-color: var(--sidebar-bg);
  transition: width 0.3s ease, background-color 0.3s ease;
  overflow: hidden;
}

// 사이드바 토글 버튼
.sidebar-toggle {
  position: absolute;
  top: 50%;
  right: -6px;
  transform: translateY(-50%);
  z-index: 100;

  width: 12px;
  height: 48px;
  border-radius: 0 6px 6px 0;
  border: none;
  background-color: var(--sidebar-toggle-bg);

  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s ease;

  color: var(--sidebar-toggle-color);

  &:hover {
    background-color: var(--sidebar-toggle-hover-bg);
    width: 14px;
  }
}

.admin-main {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.admin-header {
  background-color: var(--header-bg);
  border-bottom: 1px solid var(--header-border);
  padding: 0 20px;
  display: flex;
  align-items: center;
  box-shadow: var(--box-shadow-light);
  z-index: 10;
  transition: var(--theme-transition);
}

.admin-content {
  background-color: var(--bg-color-page);
  padding: 12px;
  overflow-y: auto;
  transition: var(--theme-transition);
}
</style>
