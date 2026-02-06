import apiClient from './index'

// API 이력 관리 API
export default {
  /**
   * 이력 목록 조회
   * @param {Object} params - 조회 파라미터
   */
  list(params = {}) {
    return apiClient.get('/api/v1/history', { params })
  },

  /**
   * 단일 이력 상세 조회
   * @param {string} requestId - 요청 ID
   */
  get(requestId) {
    return apiClient.get(`/api/v1/history/${requestId}`)
  },

  /**
   * 통계 조회
   * @param {Object} params - 조회 파라미터
   */
  getStatistics(params = {}) {
    return apiClient.get('/api/v1/history/statistics', { params })
  },

  /**
   * 사용자별 요약 조회
   * @param {string} userId - 사용자 ID
   * @param {string} tenantId - 테넌트 ID (선택)
   */
  getUserSummary(userId, tenantId = null) {
    const params = tenantId ? { tenant_id: tenantId } : {}
    return apiClient.get(`/api/v1/history/users/${userId}`, { params })
  },

  /**
   * 사용자별 이력 상세 조회
   * @param {string} userId - 사용자 ID
   * @param {Object} params - 조회 파라미터
   */
  getUserHistory(userId, params = {}) {
    return apiClient.get(`/api/v1/history/users/${userId}/history`, { params })
  },

  /**
   * 세션별 이력 조회
   * @param {string} sessionId - 세션 ID
   */
  getSessionHistory(sessionId) {
    return apiClient.get(`/api/v1/history/sessions/${sessionId}`)
  },

  /**
   * 오래된 이력 정리 (관리자용)
   * @param {number} days - 보관 기간 (일)
   * @param {string} tenantId - 테넌트 ID (선택)
   */
  cleanup(days = 90, tenantId = null) {
    const params = { days }
    if (tenantId) params.tenant_id = tenantId
    return apiClient.delete('/api/v1/history/cleanup', { params })
  }
}
