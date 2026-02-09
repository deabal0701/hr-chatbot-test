/**
 * Agent API 클라이언트
 *
 * apiClient 사용으로 success_response 래퍼 자동 처리
 * - 성공: data 필드만 반환
 * - 실패: 에러 throw (code, message 포함)
 */

import apiClient from './index'
import { streamSSE } from './sse'

/**
 * Agent 검색
 * @param {Object} params
 * @param {string} params.question - 질문
 * @param {string} params.sessionId - 세션 ID (멀티턴 대화용, 첫 요청시 null)
 * @returns {Promise}
 *
 * Note: Agent 설정(max_iterations, timeout 등)은 서버 DB에서 관리됩니다.
 * 첫 요청 시 sessionId를 생략하면 서버가 생성하여 응답에 포함합니다.
 */
export const agentSearch = async ({ question, sessionId = null }) => {
  const requestBody = {
    question,
    session_id: sessionId
  }

  const response = await apiClient.post('/api/v1/agent/search', requestBody)

  if (import.meta.env.DEV) {
    console.log('[Agent API Response]', response)
  }
  return response
}

/**
 * 세션 목록 조회
 * @returns {Promise<string[]>}
 */
export const listSessions = async () => {
  return apiClient.get('/api/v1/agent/sessions')
}

/**
 * 세션 메모리 조회
 * @param {string} sessionId
 * @returns {Promise}
 */
export const getSessionMemory = async (sessionId) => {
  return apiClient.get(`/api/v1/agent/sessions/${sessionId}/memory`)
}

/**
 * 세션 삭제
 * @param {string} sessionId
 * @returns {Promise}
 */
export const deleteSession = async (sessionId) => {
  return apiClient.delete(`/api/v1/agent/sessions/${sessionId}`)
}

/**
 * 세션 메트릭 조회
 * @param {string} sessionId
 * @returns {Promise}
 */
export const getSessionMetrics = async (sessionId) => {
  return apiClient.get(`/api/v1/agent/sessions/${sessionId}/metrics`)
}

/**
 * 사용 가능한 도구 목록 조회
 * @returns {Promise}
 */
export const listTools = async () => {
  return apiClient.get('/api/v1/agent/tools')
}

/**
 * Agent SSE 스트리밍 검색
 * @param {Object} params
 * @param {string} params.question - 질문
 * @param {string} params.sessionId - 세션 ID
 * @param {Object} callbacks - SSE 이벤트 콜백
 * @returns {AbortController} - 스트림 취소용 컨트롤러
 */
export const agentSearchStream = ({ question, sessionId = null }, callbacks) => {
  return streamSSE(
    '/api/v1/agent/search/stream',
    { question, session_id: sessionId },
    callbacks
  )
}

export default {
  agentSearch,
  agentSearchStream,
  listSessions,
  getSessionMemory,
  deleteSession,
  getSessionMetrics,
  listTools
}
