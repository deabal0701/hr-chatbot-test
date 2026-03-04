<template>
  <div class="sidebar-container">
    <!-- 로고 -->
    <div class="sidebar-logo" :class="{ collapsed: isCollapsed }">
      <div class="logo-icon">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
          <path d="M8 10h.01"></path>
          <path d="M12 10h.01"></path>
          <path d="M16 10h.01"></path>
        </svg>
      </div>
      <span v-if="!isCollapsed" class="logo-text">{{ appTitle }}</span>
    </div>

    <!-- 메뉴 (v2.2 — 트리 기반 계층 구조: 최상위 DIRECTORY 펼침 + 중간 DIRECTORY → sub-menu) -->
    <el-menu
      :default-active="activeMenu"
      :collapse="isCollapsed"
      :collapse-transition="false"
      :background-color="menuBgColor"
      :text-color="menuTextColor"
      :active-text-color="menuActiveColor"
      router
    >
      <template v-for="item in sidebarMenuItems">
        <!-- DIRECTORY with children → el-sub-menu -->
        <el-sub-menu
          v-if="item.children && item.children.length"
          :key="'dir-' + item.menu_code"
          :index="item.menu_code"
        >
          <template #title>
            <el-icon><component :is="resolveIcon(item.icon)" /></el-icon>
            <span>{{ item.menu_name }}</span>
          </template>
          <el-menu-item
            v-for="child in item.children"
            :key="child.menu_code"
            :index="child.menu_path"
          >
            <el-icon><component :is="resolveIcon(child.icon)" /></el-icon>
            <template #title>{{ child.menu_name }}</template>
          </el-menu-item>
        </el-sub-menu>
        <!-- PAGE without parent DIRECTORY → flat el-menu-item -->
        <el-menu-item
          v-else
          :key="'page-' + item.menu_code"
          :index="item.menu_path"
        >
          <el-icon><component :is="resolveIcon(item.icon)" /></el-icon>
          <template #title>{{ item.menu_name }}</template>
        </el-menu-item>
      </template>
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
const appTitle = import.meta.env.VITE_APP_TITLE || 'MUREUM'
const route = useRoute()
const store = useStore()

const isCollapsed = computed(() => store.state.app.sidebarCollapsed)
const activeMenu = computed(() => route.path)
const isDarkMode = computed(() => store.getters['app/isDarkMode'])
const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])

// DB 아이콘명 → Element Plus 전역 등록 아이콘명 매핑
// main.js에서 모든 아이콘이 전역 등록되므로 문자열 이름 사용
// (컴포넌트 객체 참조 시 Vue Proxy 이슈로 el-sub-menu 접힘 상태에서 아이콘 미표시 방지)
const ICON_MAP = {
  dashboard: 'Odometer',
  chat: 'ChatDotSquare',
  document: 'Document',
  users: 'User',
  menu: 'Menu',
  role: 'Key',
  tenant: 'OfficeBuilding',
  settings: 'Setting',
  setup: 'SetUp',
  tools: 'Tools',
  code: 'Grid',
  history: 'Histogram',
  search: 'DataLine',
  folder: 'Folder',
  department: 'Management',
}

const resolveIcon = (iconName) => {
  return ICON_MAP[iconName] || 'Document'
}

// 트리 기반 계층 메뉴 구성
// 1) flat 메뉴 리스트 → parent_menu_code 기반 트리 빌드
// 2) 최상위 DIRECTORY(depth=0)는 자식을 루트 레벨로 승격 (폴더 자체는 숨김)
// 3) 중간 DIRECTORY(depth>0)는 el-sub-menu로 렌더링
const sidebarMenuItems = computed(() => {
  if (!isAuthenticated.value) return []
  const menus = store.getters['auth/menus'] || []
  if (!menus.length) return []

  // 1. 맵 생성: menu_code → { ...menu, children: [] }
  const menuMap = new Map()
  menus.forEach(m => {
    menuMap.set(m.menu_code, { ...m, children: [] })
  })

  // 2. 트리 빌드: parent_menu_code로 자식 할당
  const roots = []
  menuMap.forEach(m => {
    if (m.parent_menu_code && menuMap.has(m.parent_menu_code)) {
      menuMap.get(m.parent_menu_code).children.push(m)
    } else {
      roots.push(m)
    }
  })

  // 3. 재귀 정렬
  const sortItems = (items) => {
    items.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
    items.forEach(item => { if (item.children.length) sortItems(item.children) })
  }
  sortItems(roots)

  // 4. 관리자 메뉴(DIR_ROOT)의 자식만 루트 레벨로 승격
  //    DIR_PUBLIC(사용자 메뉴) 등 다른 최상위 DIRECTORY는 사이드바에 표시하지 않음
  const result = []
  for (const root of roots) {
    if (root.menu_type === 'DIRECTORY' && root.menu_code === 'DIR_ROOT') {
      result.push(...root.children)
    }
  }

  // 5. children 없는 DIRECTORY 제외 (빈 폴더 숨김)
  return result.filter(m => {
    if (m.menu_type === 'DIRECTORY' && m.children.length === 0) return false
    return true
  })
})

// 다크모드에 따른 메뉴 색상 (_variables.scss CSS 변수에서 읽기)
const getVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim()
const menuBgColor = computed(() => getVar('--sidebar-bg') || (isDarkMode.value ? '#1f1f1f' : '#304156'))
const menuTextColor = computed(() => getVar('--sidebar-text') || (isDarkMode.value ? '#a3a3a3' : '#bfcbd9'))
const menuActiveColor = computed(() => getVar('--sidebar-active-text') || '#409eff')
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

    .logo-icon {
      margin: 0;
    }
  }

  .logo-icon {
    width: 32px;
    height: 32px;
    background-color: var(--icon-bg, #333333);
    border: 1px solid var(--icon-bg-border, #555555);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    color: var(--icon-color, #ffffff);

    svg {
      width: 18px;
      height: 18px;
    }
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

  .el-sub-menu {
    :deep(.el-sub-menu__title) {
      &:hover {
        background-color: var(--sidebar-hover-bg) !important;
      }

    }

    .el-menu-item {
      &:hover {
        background-color: var(--sidebar-hover-bg) !important;
      }

      &.is-active {
        background-color: var(--sidebar-hover-bg) !important;
      }
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
