import apiClient from './index'

const BASE_URL = '/api/admin/v1/settings'

const settingsApi = {
  /**
   * 전체 설정 조회
   */
  getAll() {
    return apiClient.get(BASE_URL)
  },

  /**
   * 카테고리별 설정 조회
   * @param {string} category - 카테고리명 (openai, embedding, llm, rag, nl2sql, chunking)
   */
  getCategory(category) {
    return apiClient.get(`${BASE_URL}/${category}`)
  },

  /**
   * 단일 설정 조회
   * @param {string} category - 카테고리명
   * @param {string} key - 설정 키
   */
  getSetting(category, key) {
    return apiClient.get(`${BASE_URL}/${category}/${key}`)
  },

  /**
   * 단일 설정 조회 (마스킹 없이)
   * @param {string} category - 카테고리명
   * @param {string} key - 설정 키
   */
  revealSetting(category, key) {
    return apiClient.get(`${BASE_URL}/${category}/${key}/reveal`)
  },

  /**
   * 단일 설정 수정
   * @param {string} category - 카테고리명
   * @param {string} key - 설정 키
   * @param {string} value - 설정 값
   */
  updateSetting(category, key, value) {
    return apiClient.put(`${BASE_URL}/${category}/${key}`, { value })
  },

  /**
   * 카테고리별 설정 일괄 수정
   * @param {string} category - 카테고리명
   * @param {Object} settings - key-value 쌍 객체
   */
  updateCategory(category, settings) {
    return apiClient.put(`${BASE_URL}/${category}`, { settings })
  },

  /**
   * 카테고리 설정 초기화
   * @param {string} category - 카테고리명
   */
  resetCategory(category) {
    return apiClient.post(`${BASE_URL}/${category}/reset`)
  },

  /**
   * OpenAI API 키 검증
   * @param {string} apiKey - API 키
   */
  validateApiKey(apiKey) {
    return apiClient.post(`${BASE_URL}/validate-api-key`, { api_key: apiKey })
  },

  /**
   * 설정 캐시 새로고침
   */
  refreshCache() {
    return apiClient.post(`${BASE_URL}/refresh-cache`)
  },

  /**
   * 외부 데이터베이스 연결 테스트
   * @param {Object} connection - 연결 정보
   * @param {string} connection.db_type - DB 타입 (postgresql, oracle, mysql)
   * @param {string} connection.host - 호스트
   * @param {number} connection.port - 포트
   * @param {string} connection.database - DB 이름
   * @param {string} connection.username - 사용자명
   * @param {string} connection.password - 비밀번호
   * @param {string} connection.schema - 스키마
   */
  testExternalConnection(connection) {
    return apiClient.post(`${BASE_URL}/external-database/test`, connection)
  },

  /**
   * 프롬프트 변경 이력 조회
   * @param {number} limit - 조회할 최대 개수 (기본: 100)
   */
  getPromptHistory(limit = 100) {
    return apiClient.get(`${BASE_URL}/prompt/history`, { params: { limit } })
  },

  /**
   * 특정 프롬프트의 변경 이력 조회
   * @param {string} category - 카테고리
   * @param {string} key - 프롬프트 키
   * @param {number} limit - 조회할 최대 개수 (기본: 50)
   */
  getPromptHistoryByKey(category, key, limit = 50) {
    return apiClient.get(`${BASE_URL}/prompt/history/${category}/${key}`, { params: { limit } })
  },

  /**
   * 프롬프트 복원
   * @param {number} historyId - 복원할 이력 ID
   */
  restorePromptFromHistory(historyId) {
    return apiClient.post(`${BASE_URL}/prompt/restore/${historyId}`)
  }
}

export default settingsApi
