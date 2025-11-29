import apiClient from './index'

const BASE_URL = '/api/admin/v1/settings'

export default {
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
  }
}
