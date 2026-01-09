/**
 * Agent API 클라이언트
 */

import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

/**
 * Agent 검색
 * @param {Object} params
 * @param {string} params.question - 질문
 * @param {string} params.sessionId - 세션 ID (멀티턴 대화용)
 * @param {Object} params.config - Agent 설정
 * @returns {Promise}
 */
export const agentSearch = async ({ question, sessionId = null, config = {} }) => {
  try {
    // config 객체를 전달하지 않으면 서버가 DB 설정을 사용함
    // config를 명시적으로 전달하면 해당 값이 우선됨
    const requestBody = {
      question,
      session_id: sessionId,
      verbose: config.verbose || false
    }

    // config가 명시적으로 제공된 경우만 전달 (빈 객체는 전달하지 않음)
    if (config && Object.keys(config).length > 0 && config.maxIterations) {
      requestBody.config = {
        max_iterations: config.maxIterations,
        enable_memory: config.enableMemory !== false,
        llm_temperature: config.llmTemperature || 0.0,
        timeout_seconds: config.timeoutSeconds || 60,
        // llm_model은 서버 DB 설정 사용 (하드코딩 제거)
        ...config
      }
    }

    const response = await axios.post(`${API_BASE_URL}/api/v1/agent/search`, requestBody)
    // 디버깅 로그 (개발 환경에서만)
    if (import.meta.env.DEV) {
      console.log('[Agent API Raw Response]', response)
      console.log('[Agent API Data]', response.data)
      console.log('[Agent API Answer Field]', response.data.answer)
    }
    return response.data
  } catch (error) {
    console.error('Agent search error:', error)
    throw error
  }
}

/**
 * 세션 목록 조회
 * @returns {Promise<string[]>}
 */
export const listSessions = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/v1/agent/sessions`)
    return response.data
  } catch (error) {
    console.error('List sessions error:', error)
    throw error
  }
}

/**
 * 세션 메모리 조회
 * @param {string} sessionId
 * @returns {Promise}
 */
export const getSessionMemory = async (sessionId) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/agent/sessions/${sessionId}/memory`
    )
    return response.data
  } catch (error) {
    console.error('Get session memory error:', error)
    throw error
  }
}

/**
 * 세션 삭제
 * @param {string} sessionId
 * @returns {Promise}
 */
export const deleteSession = async (sessionId) => {
  try {
    const response = await axios.delete(
      `${API_BASE_URL}/api/v1/agent/sessions/${sessionId}`
    )
    return response.data
  } catch (error) {
    console.error('Delete session error:', error)
    throw error
  }
}

/**
 * 세션 메트릭 조회
 * @param {string} sessionId
 * @returns {Promise}
 */
export const getSessionMetrics = async (sessionId) => {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/v1/agent/sessions/${sessionId}/metrics`
    )
    return response.data
  } catch (error) {
    console.error('Get session metrics error:', error)
    throw error
  }
}

/**
 * 사용 가능한 도구 목록 조회
 * @returns {Promise}
 */
export const listTools = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/v1/agent/tools`)
    return response.data
  } catch (error) {
    console.error('List tools error:', error)
    throw error
  }
}

export default {
  agentSearch,
  listSessions,
  getSessionMemory,
  deleteSession,
  getSessionMetrics,
  listTools
}
