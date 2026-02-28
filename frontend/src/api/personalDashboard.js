import apiClient from './index'

// 개인 대시보드 API
const personalDashboardApi = {
  /**
   * 위젯 목록 조회
   * @returns {Promise} { items: [...], total: N }
   */
  getWidgets() {
    return apiClient.get('/api/v1/dashboard/widgets')
  },

  /**
   * 위젯 생성
   * @param {Object} data - { title, widget_type, query, sql, chart_config, cached_data, grid_position }
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
   */
  saveLayout(layout) {
    return apiClient.put('/api/v1/dashboard/layout', { layout })
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
