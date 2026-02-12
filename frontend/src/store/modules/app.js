// 앱 전역 상태 모듈 (테마, 사이드바, API 상태 관리)
// 인증 관련은 store/modules/auth.js로 이전됨

// localStorage 키 정의
const STORAGE_KEYS = {
  USER_THEME: 'user_theme',    // 사용자 화면 테마
  ADMIN_THEME: 'admin_theme',  // 관리자 화면 테마
  USER_SIDEBAR: 'user_sidebar_visible'  // 사용자 사이드바 표시 상태
}

// 기본 테마 설정
const DEFAULT_THEMES = {
  user: true,    // 사용자 화면: 다크모드 기본
  admin: true   // 관리자 화면: 다크모드 기본(라이트모드 기본시 -> false로 변경)
}

// localStorage에서 테마 설정 로드
const getStoredTheme = (type = 'admin') => {
  try {
    const key = type === 'user' ? STORAGE_KEYS.USER_THEME : STORAGE_KEYS.ADMIN_THEME
    const theme = localStorage.getItem(key)
    // 저장된 값이 없으면 기본값 사용
    if (theme === null) {
      return DEFAULT_THEMES[type]
    }
    return theme === 'dark'
  } catch {
    return DEFAULT_THEMES[type]
  }
}

// 테마를 DOM에 적용
const applyTheme = (isDark) => {
  if (isDark) {
    document.documentElement.setAttribute('data-theme', 'dark')
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.removeAttribute('data-theme')
    document.documentElement.classList.remove('dark')
  }
}

// localStorage에 테마 저장
const saveTheme = (type, isDark) => {
  try {
    const key = type === 'user' ? STORAGE_KEYS.USER_THEME : STORAGE_KEYS.ADMIN_THEME
    localStorage.setItem(key, isDark ? 'dark' : 'light')
  } catch {
    // localStorage 사용 불가시 무시
  }
}

// localStorage에서 사이드바 상태 로드
const getStoredSidebarVisible = () => {
  try {
    const value = localStorage.getItem(STORAGE_KEYS.USER_SIDEBAR)
    if (value === null) return true  // 기본값: 표시
    return value === 'true'
  } catch {
    return true
  }
}

// localStorage에 사이드바 상태 저장
const saveSidebarVisible = (visible) => {
  try {
    localStorage.setItem(STORAGE_KEYS.USER_SIDEBAR, String(visible))
  } catch {
    // localStorage 사용 불가시 무시
  }
}

export default {
  namespaced: true,

  state: () => ({
    sidebarCollapsed: false,

    // 사용자 채팅 사이드바 상태 (localStorage에서 복원)
    userSidebarVisible: getStoredSidebarVisible(),

    // 앱 설정
    apiHealthy: true,

    // 테마 설정 (사용자/관리자 분리)
    userDarkMode: getStoredTheme('user'),    // 사용자 화면 테마 (기본: 다크)
    adminDarkMode: getStoredTheme('admin'),  // 관리자 화면 테마 (기본: 라이트)
    currentView: 'admin'                      // 현재 화면 타입 ('user' | 'admin')
  }),

  mutations: {
    TOGGLE_SIDEBAR(state) {
      state.sidebarCollapsed = !state.sidebarCollapsed
    },
    SET_SIDEBAR_COLLAPSED(state, collapsed) {
      state.sidebarCollapsed = collapsed
    },
    SET_API_HEALTH(state, healthy) {
      state.apiHealthy = healthy
    },
    // 현재 화면 타입 설정
    SET_CURRENT_VIEW(state, view) {
      state.currentView = view
      // 화면 전환 시 해당 화면의 테마 적용
      const isDark = view === 'user' ? state.userDarkMode : state.adminDarkMode
      applyTheme(isDark)
    },
    // 사용자 화면 테마 설정
    SET_USER_DARK_MODE(state, isDark) {
      state.userDarkMode = isDark
      saveTheme('user', isDark)
      // 현재 사용자 화면이면 즉시 적용
      if (state.currentView === 'user') {
        applyTheme(isDark)
      }
    },
    // 관리자 화면 테마 설정
    SET_ADMIN_DARK_MODE(state, isDark) {
      state.adminDarkMode = isDark
      saveTheme('admin', isDark)
      // 현재 관리자 화면이면 즉시 적용
      if (state.currentView === 'admin') {
        applyTheme(isDark)
      }
    },
    // 현재 화면의 테마 토글
    TOGGLE_CURRENT_DARK_MODE(state) {
      if (state.currentView === 'user') {
        state.userDarkMode = !state.userDarkMode
        saveTheme('user', state.userDarkMode)
        applyTheme(state.userDarkMode)
      } else {
        state.adminDarkMode = !state.adminDarkMode
        saveTheme('admin', state.adminDarkMode)
        applyTheme(state.adminDarkMode)
      }
    },
    TOGGLE_USER_SIDEBAR(state) {
      state.userSidebarVisible = !state.userSidebarVisible
      saveSidebarVisible(state.userSidebarVisible)
    },
    SET_USER_SIDEBAR_VISIBLE(state, visible) {
      state.userSidebarVisible = visible
      saveSidebarVisible(visible)
    }
  },

  getters: {
    // 인증 관련 getter는 auth 모듈로 이전됨
    // auth/isAuthenticated, auth/canAccessAdmin 사용
    // 현재 화면의 다크모드 상태
    isDarkMode: (state) => state.currentView === 'user' ? state.userDarkMode : state.adminDarkMode,
    // 개별 화면 다크모드 상태
    isUserDarkMode: (state) => state.userDarkMode,
    isAdminDarkMode: (state) => state.adminDarkMode,
    currentView: (state) => state.currentView,
    isUserSidebarVisible: (state) => state.userSidebarVisible
  },

  actions: {
    // 로그인/로그아웃은 auth 모듈로 이전됨
    // auth/login, auth/logout 사용
    toggleSidebar({ commit }) {
      commit('TOGGLE_SIDEBAR')
    },
    // 현재 화면의 테마 토글
    toggleDarkMode({ commit }) {
      commit('TOGGLE_CURRENT_DARK_MODE')
    },
    // 현재 화면 타입 설정 (user/admin)
    setCurrentView({ commit }, view) {
      commit('SET_CURRENT_VIEW', view)
    },
    // 사용자 화면 테마 설정
    setUserDarkMode({ commit }, isDark) {
      commit('SET_USER_DARK_MODE', isDark)
    },
    // 관리자 화면 테마 설정
    setAdminDarkMode({ commit }, isDark) {
      commit('SET_ADMIN_DARK_MODE', isDark)
    },
    // 앱 초기화 시 저장된 테마 적용 (관리자 기본)
    initTheme({ state }) {
      const isDark = state.currentView === 'user' ? state.userDarkMode : state.adminDarkMode
      applyTheme(isDark)
    },
    toggleUserSidebar({ commit }) {
      commit('TOGGLE_USER_SIDEBAR')
    },
    setUserSidebarVisible({ commit }, visible) {
      commit('SET_USER_SIDEBAR_VISIBLE', visible)
    }
  }
}
