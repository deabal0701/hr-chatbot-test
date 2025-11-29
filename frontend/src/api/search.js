import apiClient from './index'

// 검색 API
export default {
  /**
   * 통합 검색
   * @param {Object} params - 검색 파라미터
   * @param {string} params.query - 검색 질의
   * @param {string} params.mode - 검색 모드 ('auto' | 'rag' | 'nl2sql')
   * @param {Object} params.filters - 검색 필터
   * @param {number} params.top_k - 상위 K개 결과
   */
  search(params) {
    const payload = {
      query: params.query,
      mode: params.mode || 'auto',
      filters: params.filters || {}
    }
    // top_k가 지정된 경우에만 전송 (미지정 시 서버에서 DB 설정값 사용)
    if (params.top_k) {
      payload.top_k = params.top_k
    }
    return apiClient.post('/api/v1/search', payload)
  },

  /**
   * RAG 검색
   * @param {Object} params - 검색 파라미터
   */
  searchRag(params) {
    const payload = {
      query: params.query,
      filters: params.filters || {}
    }
    // top_k가 지정된 경우에만 전송 (미지정 시 서버에서 DB 설정값 사용)
    if (params.top_k) {
      payload.top_k = params.top_k
    }
    return apiClient.post('/api/v1/rag', payload)
  },

  /**
   * NL2SQL 검색
   * @param {Object} params - 검색 파라미터
   */
  searchNl2sql(params) {
    return apiClient.post('/api/v1/nl2sql', {
      query: params.query,
      filters: params.filters || {}
    })
  }
}
