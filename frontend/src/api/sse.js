/**
 * SSE 스트리밍 클라이언트
 *
 * POST 요청으로 SSE 스트림을 소비하는 유틸리티.
 * EventSource는 GET만 지원하므로 fetch + ReadableStream 사용.
 */

const BASE_URL = import.meta.env.VITE_API_URL || ''

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
export function streamSSE(url, body, callbacks) {
  const controller = new AbortController()
  const fullUrl = `${BASE_URL}${url}`

  fetch(fullUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
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

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

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
    })
    .catch((err) => {
      if (err.name === 'AbortError') {
        if (import.meta.env.DEV) {
          console.log('[SSE] Stream aborted by user')
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
