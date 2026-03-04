/**
 * 인증/권한 Composable
 * Vuex auth 모듈 접근을 캡슐화
 */
import { computed } from 'vue'
import { useStore } from 'vuex'

export function useAuth() {
  const store = useStore()

  const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])
  const currentUser = computed(() => store.getters['auth/currentUser'])
  const displayName = computed(() => store.getters['auth/displayName'])
  const roleCode = computed(() => store.getters['auth/roleCode'])
  const roleName = computed(() => store.getters['auth/roleName'] || store.getters['auth/roleCode'] || '-')
  const landingPage = computed(() => store.getters['auth/landingPage'])

  const hasMenuPermission = (menuCode, action) => store.getters['auth/hasMenuPermission'](menuCode, action)
  const login = (loginId, password) => store.dispatch('auth/login', { loginId, password })
  const logout = () => store.dispatch('auth/logout')

  return {
    isAuthenticated,
    currentUser,
    displayName,
    roleCode,
    roleName,
    landingPage,
    hasMenuPermission,
    login,
    logout
  }
}
