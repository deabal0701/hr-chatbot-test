<template>
  <el-container class="admin-layout">
    <!-- 사이드바 래퍼 -->
    <div class="sidebar-wrapper" :class="{ collapsed: sidebarCollapsed }">
      <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="admin-sidebar">
        <AppSidebar />
      </el-aside>
    </div>

    <!-- 모바일 사이드바 오버레이 -->
    <div v-if="isMobile && !sidebarCollapsed" class="sidebar-overlay" @click="toggleSidebar"></div>

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
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useStore } from 'vuex'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'

const store = useStore()
const sidebarCollapsed = computed(() => store.state.app.sidebarCollapsed)
const isMobile = ref(window.innerWidth < 768)

const toggleSidebar = () => {
  store.dispatch('app/toggleSidebar')
}

const handleResize = () => {
  const wasMobile = isMobile.value
  isMobile.value = window.innerWidth < 768
  // 모바일 진입 시 사이드바 자동 접기
  if (isMobile.value && !wasMobile && !sidebarCollapsed.value) {
    store.dispatch('app/toggleSidebar')
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  // 모바일로 처음 진입 시 사이드바 접기
  if (isMobile.value && !sidebarCollapsed.value) {
    store.dispatch('app/toggleSidebar')
  }
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style lang="scss" scoped>
@use '@/assets/styles/mixins' as mx;

.admin-layout {
  height: 100vh;
  overflow: hidden;
}

.sidebar-wrapper {
  position: relative;
  display: flex;
  flex-shrink: 0;

  // 모바일: 사이드바 오버레이 모드
  @include mx.mobile {
    position: fixed;
    top: 0;
    left: 0;
    z-index: 200;
    height: 100vh;

    &.collapsed {
      left: -220px;
    }
  }
}

// 모바일 사이드바 배경 오버레이
.sidebar-overlay {
  display: none;

  @include mx.mobile {
    display: block;
    position: fixed;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.5);
    z-index: 199;
  }
}

.admin-sidebar {
  background-color: var(--sidebar-bg);
  border-right: 1px solid var(--sidebar-border);
  transition: width 0.3s ease, background-color 0.3s ease, border-color 0.3s ease;
  overflow: hidden;
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

  @include mx.mobile {
    padding: 0 12px;
  }
}

.admin-content {
  background-color: var(--bg-color-page);
  padding: 12px;
  overflow-y: auto;
  transition: var(--theme-transition);

  @include mx.mobile {
    padding: 8px;
  }
}
</style>
