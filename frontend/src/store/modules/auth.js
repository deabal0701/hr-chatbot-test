/**
 * 인증 상태 관리 (Vuex Module) — v2.0 메뉴 기반
 *
 * State:
 *   user        — UserInfo (user_id, login_id, display_name, role_code, scope_type, landing_page, menus[])
 *   accessToken — JWT Access Token
 *   refreshToken — JWT Refresh Token
 *
 * 토큰 저장: localStorage
 *   - mureum_access_token
 *   - mureum_refresh_token
 *   - mureum_user (JSON)
 */
import authApi from '@/api/auth'

const TOKEN_KEYS = {
  ACCESS: 'mureum_access_token',
  REFRESH: 'mureum_refresh_token',
  USER: 'mureum_user'
}

const getStoredToken = (key) => {
  try { return localStorage.getItem(key) } catch { return null }
}

const getStoredUser = () => {
  try {
    const json = localStorage.getItem(TOKEN_KEYS.USER)
    return json ? JSON.parse(json) : null
  } catch { return null }
}

const saveTokens = (accessToken, refreshToken, user) => {
  try {
    localStorage.setItem(TOKEN_KEYS.ACCESS, accessToken)
    localStorage.setItem(TOKEN_KEYS.REFRESH, refreshToken)
    localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(user))
  } catch { /* ignore */ }
}

const clearTokens = () => {
  try {
    localStorage.removeItem(TOKEN_KEYS.ACCESS)
    localStorage.removeItem(TOKEN_KEYS.REFRESH)
    localStorage.removeItem(TOKEN_KEYS.USER)
  } catch { /* ignore */ }
}

export default {
  namespaced: true,

  state: () => ({
    user: getStoredUser(),
    accessToken: getStoredToken(TOKEN_KEYS.ACCESS),
    refreshToken: getStoredToken(TOKEN_KEYS.REFRESH),
    loginLoading: false,
    loginError: null
  }),

  mutations: {
    SET_AUTH(state, { accessToken, refreshToken, user }) {
      state.accessToken = accessToken
      state.refreshToken = refreshToken
      state.user = user
      state.loginError = null
      saveTokens(accessToken, refreshToken, user)
    },
    CLEAR_AUTH(state) {
      state.accessToken = null
      state.refreshToken = null
      state.user = null
      state.loginError = null
      clearTokens()
    },
    SET_USER(state, user) {
      state.user = user
      try { localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(user)) } catch { /* ignore */ }
    },
    SET_LOGIN_LOADING(state, loading) {
      state.loginLoading = loading
    },
    SET_LOGIN_ERROR(state, error) {
      state.loginError = error
    }
  },

  getters: {
    isAuthenticated: (state) => !!state.accessToken && !!state.user,
    currentUser: (state) => state.user,
    accessToken: (state) => state.accessToken,
    refreshToken: (state) => state.refreshToken,
    displayName: (state) => state.user?.display_name || state.user?.login_id || '',

    // v2.0 메뉴 기반 권한 헬퍼
    menus: (state) => state.user?.menus || [],
    roleCode: (state) => state.user?.role_code || 'USER',
    scopeType: (state) => state.user?.scope_type || 'USER',
    landingPage: (state) => state.user?.landing_page || '/chat',

    /**
     * 메뉴 CRUD 권한 체크
     * @param {string} menuCode - 메뉴 코드 (예: 'DASHBOARD', 'USER_MGMT')
     * @param {string} action - 액션 (create, read, update, delete, export)
     * @returns {boolean}
     */
    hasMenuPermission: (state) => (menuCode, action = 'read') => {
      if (!state.user?.menus) return false
      const menu = state.user.menus.find(m => m.menu_code === menuCode)
      if (!menu) return false
      return !!menu[`can_${action}`]
    },

    // 관리 메뉴 접근 여부 (메뉴가 1개라도 할당되면 관리자 영역 접근 가능)
    canAccessAdmin: (state) => {
      if (!state.user) return false
      return (state.user.menus?.length || 0) > 0
    }
  },

  actions: {
    /**
     * 로그인
     * - 성공: TokenResponse → SET_AUTH → user 반환
     * - 실패: 에러 메시지 SET_LOGIN_ERROR (계정잠금, 비활성화, 인증실패 구분)
     */
    async login({ commit }, { loginId, password }) {
      commit('SET_LOGIN_LOADING', true)
      commit('SET_LOGIN_ERROR', null)
      try {
        const data = await authApi.login(loginId, password)
        commit('SET_AUTH', {
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          user: data.user
        })
        return data.user
      } catch (err) {
        // 백엔드 에러 코드에 따른 메시지 분기
        const code = err.code || ''
        let message = err.message || '로그인에 실패했습니다'

        if (code === 'ACCOUNT_LOCKED') {
          message = '계정이 잠겼습니다. 잠시 후 다시 시도해주세요.'
        } else if (code === 'ACCOUNT_DISABLED' || code === 'ACCOUNT_INACTIVE') {
          message = '비활성화된 계정입니다. 관리자에게 문의해주세요.'
        } else if (code === 'UNAUTHORIZED' || code === 'INVALID_CREDENTIALS') {
          message = '아이디 또는 비밀번호가 올바르지 않습니다.'
        }

        commit('SET_LOGIN_ERROR', message)
        throw err
      } finally {
        commit('SET_LOGIN_LOADING', false)
      }
    },

    /**
     * 로그아웃
     * - 서버에 로그아웃 요청 (세션 삭제)
     * - 로컬 토큰 및 상태 초기화
     */
    async logout({ commit, state }) {
      try {
        if (state.accessToken) {
          await authApi.logout()
        }
      } catch {
        // 서버 에러 무시 (이미 만료 등)
      } finally {
        commit('CLEAR_AUTH')
      }
    },

    /**
     * 토큰 갱신
     * @returns {Promise<string>} 새 Access Token
     */
    async refresh({ commit, state }) {
      if (!state.refreshToken) throw new Error('No refresh token')
      const data = await authApi.refreshToken(state.refreshToken)
      commit('SET_AUTH', {
        accessToken: data.access_token,
        refreshToken: data.refresh_token || state.refreshToken,
        user: data.user || state.user
      })
      return data.access_token
    },

    /**
     * 사용자 정보 갱신 (GET /me)
     */
    async fetchMe({ commit }) {
      const user = await authApi.getMe()
      commit('SET_USER', user)
      return user
    },

    /**
     * 비밀번호 변경
     */
    async changePassword(_, { currentPassword, newPassword }) {
      return authApi.changePassword(currentPassword, newPassword)
    },

    /**
     * 앱 초기화 시 토큰 유효성 확인
     * localStorage에 토큰이 있으면 /me 호출하여 검증
     */
    async initAuth({ commit, state, dispatch }) {
      if (!state.accessToken) return false
      try {
        await dispatch('fetchMe')
        return true
      } catch {
        commit('CLEAR_AUTH')
        return false
      }
    }
  }
}
