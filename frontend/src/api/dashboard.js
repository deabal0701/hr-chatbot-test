/**
 * 대시보드 API 클라이언트
 *
 * 백엔드: app/api/routes/dashboard.py (prefix: /api/v1/dashboard)
 */
import apiClient from './index'

const dashboardApi = {
  /**
   * 대시보드 요약 데이터 조회 (KPI + 차트 + 최근 활동 + 시스템 현황)
   * @param {Object} params - { period: 'today'|'week'|'month', tenant_id? }
   */
  getSummary(params = {}) {
    return apiClient.get('/api/v1/dashboard/summary', { params })
  },
}

export default dashboardApi
