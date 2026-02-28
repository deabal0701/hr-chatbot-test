import apiClient from './index'

// 개인 대시보드 API
const personalDashboardApi = {
  // ============================================
  // 대시보드 CRUD
  // ============================================

  /**
   * 대시보드 목록 조회 (내 대시보드 + 공유 대시보드)
   * @returns {Promise} { my_dashboards: [...], shared_dashboards: [...] }
   */
  getDashboards() {
    return apiClient.get('/api/v1/dashboard/dashboards')
  },

  /**
   * 대시보드 생성
   * @param {Object} data - { name, description? }
   */
  createDashboard(data) {
    return apiClient.post('/api/v1/dashboard/dashboards', data)
  },

  /**
   * 대시보드 수정
   * @param {number} dashboardId - 대시보드 ID
   * @param {Object} data - { name?, description? }
   */
  updateDashboard(dashboardId, data) {
    return apiClient.put(`/api/v1/dashboard/dashboards/${dashboardId}`, data)
  },

  /**
   * 대시보드 삭제
   * @param {number} dashboardId - 대시보드 ID
   */
  deleteDashboard(dashboardId) {
    return apiClient.delete(`/api/v1/dashboard/dashboards/${dashboardId}`)
  },

  /**
   * 기본 대시보드 설정
   * @param {number} dashboardId - 대시보드 ID
   */
  setDefaultDashboard(dashboardId) {
    return apiClient.put(`/api/v1/dashboard/dashboards/${dashboardId}/default`)
  },

  /**
   * 대시보드 공유 설정
   * @param {number} dashboardId - 대시보드 ID
   * @param {Object} data - { is_shared, share_scope? }
   */
  shareDashboard(dashboardId, data) {
    return apiClient.put(`/api/v1/dashboard/dashboards/${dashboardId}/share`, data)
  },

  // ============================================
  // 위젯 CRUD
  // ============================================

  /**
   * 위젯 목록 조회
   * @param {number|null} dashboardId - 대시보드 ID (미지정시 기본 대시보드)
   * @returns {Promise} { items: [...], total: N, dashboard_id, is_read_only }
   */
  getWidgets(dashboardId = null) {
    const params = dashboardId ? { dashboard_id: dashboardId } : {}
    return apiClient.get('/api/v1/dashboard/widgets', { params })
  },

  /**
   * 위젯 생성
   * @param {Object} data - { dashboard_id?, title, widget_type, query, sql, chart_config, cached_data, grid_position }
   */
  createWidget(data) {
    return apiClient.post('/api/v1/dashboard/widgets', data)
  },

  /**
   * 위젯 수정
   * @param {number} widgetId - 위젯 ID
   * @param {Object} data - 변경 필드만 포함
   */
  updateWidget(widgetId, data) {
    return apiClient.put(`/api/v1/dashboard/widgets/${widgetId}`, data)
  },

  /**
   * 위젯 삭제
   * @param {number} widgetId - 위젯 ID
   */
  deleteWidget(widgetId) {
    return apiClient.delete(`/api/v1/dashboard/widgets/${widgetId}`)
  },

  /**
   * 레이아웃 일괄 저장
   * @param {Array} layout - [{ widget_id, x, y, w, h }, ...]
   * @param {number|null} dashboardId - 대시보드 ID
   */
  saveLayout(layout, dashboardId = null) {
    return apiClient.put('/api/v1/dashboard/layout', {
      dashboard_id: dashboardId,
      layout
    })
  },

  /**
   * 위젯 데이터 새로고침 (저장된 SQL 재실행)
   * @param {number} widgetId - 위젯 ID
   */
  refreshWidget(widgetId) {
    return apiClient.post(`/api/v1/dashboard/widgets/${widgetId}/refresh`)
  },

  /**
   * SQL 테스트 실행 (미리보기용, 저장 안함)
   * @param {string} sql - 실행할 SQL
   */
  executeSql(sql) {
    return apiClient.post('/api/v1/dashboard/execute-sql', { sql })
  }
}

export default personalDashboardApi
