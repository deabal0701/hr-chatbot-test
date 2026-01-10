// 앱 전역 상태 모듈 (향후 인증 확장용)

// localStorage에서 테마 설정 로드
const getStoredTheme = () => {
  try {
    const theme = localStorage.getItem('theme')
    return theme === 'dark'
  } catch {
    return false
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
    darkMode: getStoredTheme()  // 다크모드 상태
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
    SET_DARK_MODE(state, isDark) {
      state.darkMode = isDark
      // localStorage에 저장
      try {
        localStorage.setItem('theme', isDark ? 'dark' : 'light')
      } catch {
        // localStorage 사용 불가시 무시
      }
      // DOM에 테마 적용
      applyTheme(isDark)
    },
    TOGGLE_DARK_MODE(state) {
      state.darkMode = !state.darkMode
      try {
        localStorage.setItem('theme', state.darkMode ? 'dark' : 'light')
      } catch {
        // localStorage 사용 불가시 무시
      }
      applyTheme(state.darkMode)
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
    isDarkMode: (state) => state.darkMode,
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
