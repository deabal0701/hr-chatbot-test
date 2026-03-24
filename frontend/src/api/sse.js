/**
 * SSE 스트리밍 클라이언트
 *
 * POST 요청으로 SSE 스트림을 소비하는 유틸리티.
 * EventSource는 GET만 지원하므로 fetch + ReadableStream 사용.
 * 401 응답 시 refresh token으로 자동 갱신 후 재시도.
 */

import apiClient from './index'

const BASE_URL = import.meta.env.VITE_API_URL || ''

/**
 * 401 응답 시 refresh token으로 access token 갱신
 * @returns {string|null} 새 access token 또는 null (실패 시)
 */
async function refreshAccessToken() {
  const refreshToken = localStorage.getItem('mureum_refresh_token')
  if (!refreshToken) return null

  try {
    // apiClient를 사용하여 refresh 요청 (axios 인터셉터의 갱신 로직과 동일 경로)
    const data = await apiClient.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken
    })
    const newToken = data.access_token
    localStorage.setItem('mureum_access_token', newToken)
    if (data.refresh_token) {
      localStorage.setItem('mureum_refresh_token', data.refresh_token)
    }
    if (data.user) {
      localStorage.setItem('mureum_user', JSON.stringify(data.user))
    }
    return newToken
  } catch {
    return null
  }
}

/**
 * SSE 스트리밍 요청
 *
 * @param {string} url - API 엔드포인트 URL
 * @param {Object} body - POST 요청 바디
 * @param {Object} callbacks - 이벤트 콜백
 * @param {Function} callbacks.onNodeStart - 노드 시작 이벤트 (event) => void
 * @param {Function} callbacks.onNodeComplete - 노드 완료 이벤트 (event) => void
 * @param {Function} callbacks.onComplete - 최종 완료 이벤트 (data) => void
 * @param {Function} callbacks.onError - 오류 이벤트 (error) => void
 * @returns {AbortController} - 스트림 취소용 컨트롤러
 */
export function streamSSE(url, body, callbacks, { idleTimeoutMs = 60000 } = {}) {
  const controller = new AbortController()
  const fullUrl = `${BASE_URL}${url}`

  // Idle timeout: 마지막 이벤트 수신 후 일정 시간 무응답 시 자동 abort
  let idleTimer = null
  const resetIdleTimer = () => {
    if (idleTimer) clearTimeout(idleTimer)
    idleTimer = setTimeout(() => {
      if (!controller.signal.aborted) {
        controller.abort()
        callbacks.onError?.({ code: 'IDLE_TIMEOUT', message: '서버 응답이 지연되어 연결을 종료합니다' })
      }
    }, idleTimeoutMs)
  }
  const clearIdleTimer = () => { if (idleTimer) { clearTimeout(idleTimer); idleTimer = null } }

  /**
   * SSE fetch 실행 (토큰 갱신 후 재시도 지원)
   * @param {string} accessToken - 현재 access token
   * @param {boolean} isRetry - 재시도 여부 (true면 갱신 실패 시 에러 반환)
   */
  async function executeFetch(accessToken, isRetry = false) {
    const headers = { 'Content-Type': 'application/json' }
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`
    }

    const response = await fetch(fullUrl, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal: controller.signal,
    })

    // 401 → 토큰 갱신 후 1회 재시도
    if (response.status === 401 && !isRetry) {
      const newToken = await refreshAccessToken()
      if (newToken) {
        return executeFetch(newToken, true)
      }
      // refresh 실패 → 로그인 페이지로 이동
      localStorage.removeItem('mureum_access_token')
      localStorage.removeItem('mureum_refresh_token')
      localStorage.removeItem('mureum_user')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
      return
    }

    if (!response.ok) {
      clearIdleTimer()
      let errorData
      try {
        errorData = await response.json()
      } catch {
        errorData = { message: `HTTP ${response.status}` }
      }
      const error = new Error(errorData?.error?.message || `서버 오류 (${response.status})`)
      error.code = errorData?.error?.code || 'HTTP_ERROR'
      callbacks.onError?.(error)
      return
    }

    // 정상 응답 → SSE 스트림 소비
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    resetIdleTimer()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      resetIdleTimer()
      buffer += decoder.decode(value, { stream: true })

      // SSE 이벤트 파싱 (이중 줄바꿈으로 구분)
      const events = buffer.split('\n\n')
      buffer = events.pop() // 마지막 불완전한 이벤트는 버퍼에 유지

      for (const eventStr of events) {
        if (!eventStr.trim()) continue

        const parsed = parseSSEEvent(eventStr)
        if (!parsed) continue

        switch (parsed.type) {
          case 'node_start':
            callbacks.onNodeStart?.(parsed.data)
            // 브라우저 렌더링 양보: "~중..." 레이블이 화면에 반영되도록 대기
            await new Promise(resolve => requestAnimationFrame(resolve))
            break
          case 'node_complete':
            callbacks.onNodeComplete?.(parsed.data)
            await new Promise(resolve => requestAnimationFrame(resolve))
            break
          case 'complete':
            callbacks.onComplete?.(parsed.data)
            break
          case 'error':
            callbacks.onError?.(parsed.data)
            break
          default:
            if (import.meta.env.DEV) {
              console.warn('[SSE] Unknown event type:', parsed.type)
            }
        }
      }
    }

    clearIdleTimer()
  }

  // 실행
  const token = localStorage.getItem('mureum_access_token')
  executeFetch(token).catch((err) => {
    clearIdleTimer()
    if (err.name === 'AbortError') {
      if (import.meta.env.DEV) {
        console.log('[SSE] Stream aborted')
      }
      return
    }
    callbacks.onError?.({
      code: 'NETWORK_ERROR',
      message: '네트워크 연결을 확인해주세요',
      detail: err.message,
    })
  })

  return controller
}

/**
 * SSE 이벤트 문자열 파싱
 * @param {string} eventStr - "event: type\ndata: {...}" 형식
 * @returns {{ type: string, data: Object } | null}
 */
function parseSSEEvent(eventStr) {
  const lines = eventStr.split('\n')
  let eventType = null
  let dataStr = null

  for (const line of lines) {
    if (line.startsWith('event: ')) {
      eventType = line.slice(7).trim()
    } else if (line.startsWith('data: ')) {
      dataStr = line.slice(6)
    }
  }

  if (!dataStr) return null

  try {
    const data = JSON.parse(dataStr)
    return { type: eventType || data.type, data }
  } catch {
    if (import.meta.env.DEV) {
      console.warn('[SSE] Failed to parse event data:', dataStr)
    }
    return null
  }
}

export default { streamSSE }
