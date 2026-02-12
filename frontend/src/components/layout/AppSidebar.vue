<template>
  <div class="sidebar-container">
    <!-- 로고 -->
    <div class="sidebar-logo" :class="{ collapsed: isCollapsed }">
      <el-icon :size="28" color="#409eff">
        <ChatDotRound />
      </el-icon>
      <span v-if="!isCollapsed" class="logo-text">MUREUM</span>
    </div>

    <!-- 메뉴 (권한 기반 동적 필터링) -->
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
        :key="item.index"
        :index="item.index"
      >
        <el-icon><component :is="item.icon" /></el-icon>
        <template #title>{{ item.title }}</template>
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
  ChatDotSquare,
  Document,
  Setting,
  Grid,
  Histogram,
  User,
  Key,
  OfficeBuilding
} from '@element-plus/icons-vue'

const route = useRoute()
const store = useStore()

const isCollapsed = computed(() => store.state.app.sidebarCollapsed)
const activeMenu = computed(() => route.path)
const isDarkMode = computed(() => store.getters['app/isDarkMode'])
const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])

// 권한 체크 헬퍼
const hasPermission = (code) => store.getters['auth/hasPermission'](code)

// 전체 메뉴 정의 (permission 조건 포함)
const allMenuItems = [
  { index: '/admin/documents', icon: Document, title: '지식문서 관리', permission: 'document:read' },
  { index: '/admin/chat', icon: ChatDotSquare, title: '자연어 검색', permission: null },
  { index: '/admin/settings', icon: Setting, title: '시스템 설정', permission: 'admin:settings' },
  { index: '/admin/codes', icon: Grid, title: '코드 관리', permission: 'admin:settings' },
  { index: '/admin/history', icon: Histogram, title: '검색 이력(Tracing)', permission: null },
  { index: '/admin/users', icon: User, title: '사용자 관리', permission: 'admin:users' },
  { index: '/admin/roles', icon: Key, title: '역할 관리', permission: 'admin:users' },
  { index: '/admin/tenants', icon: OfficeBuilding, title: '테넌트 관리', permission: 'admin:tenants' }
]

// 권한에 따라 보이는 메뉴만 필터링
const visibleMenuItems = computed(() => {
  // 미인증 상태에서는 전체 메뉴 표시 (Phase 3a 하위호환)
  if (!isAuthenticated.value) {
    return allMenuItems.filter(item => !item.permission || item.permission === 'document:read')
  }
  // 인증된 상태: 권한 기반 필터링
  return allMenuItems.filter(item => {
    if (!item.permission) return true
    return hasPermission(item.permission)
  })
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
