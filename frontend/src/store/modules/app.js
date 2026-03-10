// 앱 전역 상태 모듈 (테마, 사이드바, API 상태 관리)
// 인증 관련은 store/modules/auth.js로 이전됨

// localStorage 키 정의
const STORAGE_KEYS = {
  THEME: 'app_theme',                       // 통합 테마 (dark | light)
  USER_SIDEBAR: 'user_sidebar_visible'       // 사용자 사이드바 표시 상태
}

// localStorage에서 테마 설정 로드
const getStoredTheme = () => {
  try {
    const theme = localStorage.getItem(STORAGE_KEYS.THEME)
    if (theme === null) return true  // 기본: 다크모드
    return theme === 'dark'
  } catch {
    return true
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
const saveTheme = (isDark) => {
  try {
    localStorage.setItem(STORAGE_KEYS.THEME, isDark ? 'dark' : 'light')
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

    // 통합 테마 (관리자/사용자 동일)
    darkMode: getStoredTheme()
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
    // 테마 설정
    SET_DARK_MODE(state, isDark) {
      state.darkMode = isDark
      saveTheme(isDark)
      applyTheme(isDark)
    },
    // 테마 토글
    TOGGLE_DARK_MODE(state) {
      state.darkMode = !state.darkMode
      saveTheme(state.darkMode)
      applyTheme(state.darkMode)
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
    isDarkMode: (state) => state.darkMode,
    isUserSidebarVisible: (state) => state.userSidebarVisible
  },

  actions: {
    toggleSidebar({ commit }) {
      commit('TOGGLE_SIDEBAR')
    },
    toggleDarkMode({ commit }) {
      commit('TOGGLE_DARK_MODE')
    },
    setDarkMode({ commit }, isDark) {
      commit('SET_DARK_MODE', isDark)
    },
    // 앱 초기화 시 저장된 테마 적용
    initTheme({ state }) {
      applyTheme(state.darkMode)
    },
    toggleUserSidebar({ commit }) {
      commit('TOGGLE_USER_SIDEBAR')
    },
    setUserSidebarVisible({ commit }, visible) {
      commit('SET_USER_SIDEBAR_VISIBLE', visible)
    }
  }
}
