<template>
  <div class="sidebar-container">
    <!-- 로고 -->
    <div class="sidebar-logo" :class="{ collapsed: isCollapsed }">
      <el-icon :size="28" color="#409eff">
        <ChatDotRound />
      </el-icon>
      <span v-if="!isCollapsed" class="logo-text">DocuRAG</span>
    </div>

    <!-- 메뉴 -->
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapsed"
      :collapse-transition="false"
      :background-color="menuBgColor"
      :text-color="menuTextColor"
      :active-text-color="menuActiveColor"
      router
    >
      <el-menu-item index="/admin">
        <el-icon><DataAnalysis /></el-icon>
        <template #title>대시보드</template>
      </el-menu-item>

      <el-menu-item index="/admin/documents">
        <el-icon><Document /></el-icon>
        <template #title>RAG 문서관리</template>
      </el-menu-item>

      <el-menu-item index="/admin/chat">
        <el-icon><ChatDotSquare /></el-icon>
        <template #title>자연어 검색</template>
      </el-menu-item>

      <el-menu-item index="/admin/settings">
        <el-icon><Setting /></el-icon>
        <template #title>시스템 설정</template>
      </el-menu-item>
    </el-menu>

    <!-- 하단 정보 -->
    <div v-if="!isCollapsed" class="sidebar-footer">
      <div class="version">v1.0.0</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from 'vuex'
import {
  ChatDotRound,
  DataAnalysis,
  ChatDotSquare,
  Document,
  Setting
} from '@element-plus/icons-vue'

const route = useRoute()
const store = useStore()

const isCollapsed = computed(() => store.state.app.sidebarCollapsed)
const activeMenu = computed(() => route.path)
const isDarkMode = computed(() => store.state.app.darkMode)

// 다크모드에 따른 메뉴 색상
const menuBgColor = computed(() => isDarkMode.value ? '#1f1f1f' : '#304156')
const menuTextColor = computed(() => isDarkMode.value ? '#a3a3a3' : '#bfcbd9')
const menuActiveColor = computed(() => '#409eff')
</script>

<style lang="scss" scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.sidebar-logo {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  background-color: var(--sidebar-hover-bg);
  border-bottom: 1px solid var(--border-color-lighter);
  transition: var(--theme-transition);

  &.collapsed {
    padding: 0;
  }

  .logo-text {
    margin-left: 12px;
    font-size: 18px;
    font-weight: 600;
    color: #fff;
    white-space: nowrap;
  }
}

.el-menu {
  border-right: none;
  flex: 1;

  .el-menu-item {
    &:hover {
      background-color: var(--sidebar-hover-bg) !important;
    }

    &.is-active {
      background-color: var(--sidebar-hover-bg) !important;
    }
  }
}

.sidebar-footer {
  padding: 16px;
  text-align: center;
  border-top: 1px solid var(--border-color-lighter);

  .version {
    font-size: 12px;
    color: var(--text-color-secondary);
  }
}
</style>
