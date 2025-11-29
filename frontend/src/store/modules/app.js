// 앱 전역 상태 모듈 (향후 인증 확장용)
export default {
  namespaced: true,

  state: () => ({
    // 향후 확장용
    user: null,           // 로그인 사용자 정보
    userRole: 'admin',    // 'admin' | 'user'
    sidebarCollapsed: false,

    // 앱 설정
    apiHealthy: true
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
    }
  },

  getters: {
    isAdmin: (state) => state.userRole === 'admin',
    isAuthenticated: (state) => state.user !== null
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
    }
  }
}
