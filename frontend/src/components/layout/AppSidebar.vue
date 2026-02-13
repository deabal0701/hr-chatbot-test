<template>
  <div class="sidebar-container">
    <!-- 로고 -->
    <div class="sidebar-logo" :class="{ collapsed: isCollapsed }">
      <el-icon :size="28" color="#409eff">
        <ChatDotRound />
      </el-icon>
      <span v-if="!isCollapsed" class="logo-text">MUREUM</span>
    </div>

    <!-- 메뉴 (v2.0 — user.menus[]에서 동적 렌더링) -->
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapsed"
      :collapse-transition="false"
      :background-color="menuBgColor"
      :text-color="menuTextColor"
      :active-text-color="menuActiveColor"
      router
    >
      <el-menu-item
        v-for="item in visibleMenuItems"
        :key="item.menu_code"
        :index="item.menu_path"
      >
        <el-icon><component :is="resolveIcon(item.icon)" /></el-icon>
        <template #title>{{ item.menu_name }}</template>
      </el-menu-item>
    </el-menu>

    <!-- 하단 정보 -->
    <div v-if="!isCollapsed" class="sidebar-footer">
      <div class="version">v2.0.0</div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useStore } from 'vuex'
import {
  ChatDotRound,
  ChatDotSquare,
  Document,
  Setting,
  Grid,
  Histogram,
  User,
  Key,
  OfficeBuilding,
  Odometer,
  Menu as MenuIcon,
  List,
  Folder,
  DataLine
} from '@element-plus/icons-vue'

const route = useRoute()
const store = useStore()

const isCollapsed = computed(() => store.state.app.sidebarCollapsed)
const activeMenu = computed(() => route.path)
const isDarkMode = computed(() => store.getters['app/isDarkMode'])
const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])

// DB 아이콘명 → Element Plus 아이콘 컴포넌트 매핑
// DB에 소문자 약어로 저장됨 (예: 'dashboard', 'chat', 'document')
const ICON_MAP = {
  // DB 소문자 아이콘명
  dashboard: Odometer,
  chat: ChatDotSquare,
  document: Document,
  users: User,
  menu: MenuIcon,
  role: Key,
  tenant: OfficeBuilding,
  settings: Setting,
  code: Grid,
  history: Histogram,
  search: DataLine,
  folder: Folder,
  // PascalCase (Element Plus 원본명)
  Odometer, ChatDotSquare, Document, Setting, Grid,
  Histogram, User, Key, OfficeBuilding, Menu: MenuIcon,
  List, Folder, DataLine, ChatDotRound
}

const resolveIcon = (iconName) => {
  return ICON_MAP[iconName] || Document
}

// 사용자 메뉴에서 PAGE 타입만 필터링 + sort_order 정렬
const visibleMenuItems = computed(() => {
  if (!isAuthenticated.value) return []
  const menus = store.getters['auth/menus'] || []
  return menus
    .filter(m => m.menu_type === 'PAGE' && m.menu_path)
    .sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
})

// 다크모드에 따른 메뉴 색상 (_variables.scss 와 동기화)
const menuBgColor = computed(() => isDarkMode.value ? '#1f1f1f' : '#304156')
const menuTextColor = computed(() => isDarkMode.value ? '#a3a3a3' : '#bfcbd9')
const menuActiveColor = '#409eff'
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
