<template>
  <div class="sidebar-container">
    <!-- 로고 -->
    <div class="sidebar-logo" :class="{ collapsed: isCollapsed }">
      <el-icon :size="28" color="#409eff">
        <ChatDotRound />
      </el-icon>
      <span v-if="!isCollapsed" class="logo-text">HR Chatbot</span>
    </div>

    <!-- 메뉴 -->
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapsed"
      :collapse-transition="false"
      background-color="#304156"
      text-color="#bfcbd9"
      active-text-color="#409eff"
      router
    >
      <el-menu-item index="/admin">
        <el-icon><DataAnalysis /></el-icon>
        <template #title>대시보드</template>
      </el-menu-item>

      <el-menu-item index="/admin/chat">
        <el-icon><ChatDotSquare /></el-icon>
        <template #title>HR 챗봇</template>
      </el-menu-item>

      <el-menu-item index="/admin/documents">
        <el-icon><Document /></el-icon>
        <template #title>문서 관리</template>
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
  Document
} from '@element-plus/icons-vue'

const route = useRoute()
const store = useStore()

const isCollapsed = computed(() => store.state.app.sidebarCollapsed)
const activeMenu = computed(() => route.path)
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
  background-color: #263445;
  border-bottom: 1px solid #1f2d3d;

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
      background-color: #263445 !important;
    }

    &.is-active {
      background-color: #263445 !important;
    }
  }
}

.sidebar-footer {
  padding: 16px;
  text-align: center;
  border-top: 1px solid #1f2d3d;

  .version {
    font-size: 12px;
    color: #6b7a8f;
  }
}
</style>
