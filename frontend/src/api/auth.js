/**
 * 인증 API 클라이언트
 *
 * Backend endpoints:
 *   POST /api/v1/auth/login    → login(loginId, password)
 *   POST /api/v1/auth/logout   → logout()
 *   POST /api/v1/auth/refresh  → refreshToken(refreshToken)
 *   GET  /api/v1/auth/me       → getMe()
 *   PUT  /api/v1/auth/me/password → changePassword(current, new)
 *   POST /api/v1/auth/sso-redirect → (외부 시스템 Hidden Form POST, 프론트에서 직접 호출 안 함)
 */
import apiClient from './index'

const AUTH_BASE = '/api/v1/auth'

const authApi = {
  login(loginId, password) {
    return apiClient.post(`${AUTH_BASE}/login`, {
      login_id: loginId,
      password
    })
  },

  logout() {
    return apiClient.post(`${AUTH_BASE}/logout`)
  },

  refreshToken(refreshToken) {
    return apiClient.post(`${AUTH_BASE}/refresh`, {
      refresh_token: refreshToken
    })
  },

  getMe() {
    return apiClient.get(`${AUTH_BASE}/me`)
  },

  changePassword(currentPassword, newPassword) {
    return apiClient.put(`${AUTH_BASE}/me/password`, {
      current_password: currentPassword,
      new_password: newPassword
    })
  }
}

export default authApi