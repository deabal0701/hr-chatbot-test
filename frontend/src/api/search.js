import axios from 'axios'
import apiClient from './index'
import { streamSSE } from './sse'

// 검색 API
const searchApi = {
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
    // session_id 전달 (멀티턴 대화 지원)
    if (params.sessionId) {
      payload.session_id = params.sessionId
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
  },

  /**
   * NL2SQL SSE 스트리밍 검색
   * @param {Object} params - 검색 파라미터
   * @param {Object} callbacks - SSE 이벤트 콜백
   * @returns {AbortController} - 스트림 취소용 컨트롤러
   */
  searchStream(params, callbacks) {
    const payload = {
      query: params.query,
      mode: params.mode || 'nl2sql',
    }
    if (params.sessionId) {
      payload.session_id = params.sessionId
    }
    return streamSSE('/api/v1/search/stream', payload, callbacks)
  },

  /**
   * NL2SQL 결과를 Excel 파일로 내보내기
   * @param {Object} data - 내보내기 데이터
   * @param {string[]} data.columns - 컬럼 목록
   * @param {Object[]} data.rows - 데이터 행 목록
   * @param {string} data.question - 사용자 질문
   * @param {string} data.sql - 실행된 SQL
   * @param {string} data.answer - AI 답변
   * @param {number} data.execution_time_ms - 실행 시간
   */
  async exportExcel(data) {
    const baseURL = import.meta.env.VITE_API_URL || ''
    const response = await axios.post(`${baseURL}/api/v1/export/excel`, data, {
      responseType: 'blob',
      headers: { 'Content-Type': 'application/json' }
    })

    // Content-Disposition에서 파일명 추출 또는 기본값 사용
    const disposition = response.headers['content-disposition']
    let filename = 'report.xlsx'
    if (disposition) {
      const match = disposition.match(/filename\*?=(?:UTF-8'')?([^;\s]+)/)
      if (match) filename = decodeURIComponent(match[1])
    }

    // Blob → 다운로드
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)

    return filename
  }
}

export default searchApi
