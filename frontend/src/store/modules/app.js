// 앱 전역 상태 모듈 (향후 인증 확장용)

// localStorage 키 정의
const STORAGE_KEYS = {
  USER_THEME: 'user_theme',    // 사용자 화면 테마
  ADMIN_THEME: 'admin_theme'   // 관리자 화면 테마
}

// 기본 테마 설정
const DEFAULT_THEMES = {
  user: true,    // 사용자 화면: 다크모드 기본
  admin: false   // 관리자 화면: 라이트모드 기본
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

export default {
  namespaced: true,

  state: () => ({
    // 향후 확장용
    user: null,           // 로그인 사용자 정보
    userRole: 'admin',    // 'admin' | 'user'
    sidebarCollapsed: false,

    // 사용자 채팅 사이드바 상태
    userSidebarVisible: true,

    // 앱 설정
    apiHealthy: true,

    // 테마 설정 (사용자/관리자 분리)
    userDarkMode: getStoredTheme('user'),    // 사용자 화면 테마 (기본: 다크)
    adminDarkMode: getStoredTheme('admin'),  // 관리자 화면 테마 (기본: 라이트)
    currentView: 'admin'                      // 현재 화면 타입 ('user' | 'admin')
  }),

  mutations: {
    SET_USER(state, user) {
      state.user = user
    },
    SET_ROLE(state, role) {
      state.userRole = role
    },
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
    },
    SET_USER_SIDEBAR_VISIBLE(state, visible) {
      state.userSidebarVisible = visible
    }
  },

  getters: {
    isAdmin: (state) => state.userRole === 'admin',
    isAuthenticated: (state) => state.user !== null,
    // 현재 화면의 다크모드 상태
    isDarkMode: (state) => state.currentView === 'user' ? state.userDarkMode : state.adminDarkMode,
    // 개별 화면 다크모드 상태
    isUserDarkMode: (state) => state.userDarkMode,
    isAdminDarkMode: (state) => state.adminDarkMode,
    currentView: (state) => state.currentView,
    isUserSidebarVisible: (state) => state.userSidebarVisible
  },

  actions: {
    // 향후 로그인/로그아웃 구현
    async login({ commit }, credentials) {
      // const user = await authApi.login(credentials)
      // commit('SET_USER', user)
      console.log('Login action - to be implemented', credentials)
    },
    logout({ commit }) {
      commit('SET_USER', null)
    },
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
