<template>
  <el-container class="admin-layout">
    <!-- 사이드바 -->
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="admin-sidebar">
      <AppSidebar />
    </el-aside>

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
import { computed } from 'vue'
import { useStore } from 'vuex'
import AppSidebar from '@/components/layout/AppSidebar.vue'
import AppHeader from '@/components/layout/AppHeader.vue'

const store = useStore()
const sidebarCollapsed = computed(() => store.state.app.sidebarCollapsed)
</script>

<style lang="scss" scoped>
.admin-layout {
  height: 100vh;
  overflow: hidden;
}

.admin-sidebar {
  background-color: #304156;
  transition: width 0.3s ease;
  overflow: hidden;
}

.admin-main {
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.admin-header {
  background-color: #fff;
  border-bottom: 1px solid #ebeef5;
  padding: 0 20px;
  display: flex;
  align-items: center;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  z-index: 10;
}

.admin-content {
  background-color: #f5f7fa;
  padding: 20px;
  overflow-y: auto;
}
</style>
