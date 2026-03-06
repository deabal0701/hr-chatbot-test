import axios from 'axios'

// API 클라이언트 인스턴스 생성
// 환경별 설정:
//   - 로컬 개발 (npm run dev)  : .env.development → VITE_API_URL=http://localhost:8000
//   - Docker 배포 (nginx proxy): .env.docker      → VITE_API_URL= (빈 문자열, 상대경로 사용)
//   - 프로덕션 빌드            : .env.production  → VITE_API_URL=https://api.yourcompany.com
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 120000, // 120초 (Agent/NL2SQL 처리 시간 고려)
  headers: {
    'Content-Type': 'application/json'
  }
})

// ===== 401 자동 갱신 관련 =====
let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token)
  })
  failedQueue = []
}

// 요청 인터셉터 — Bearer 토큰 자동 첨부
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('mureum_access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 응답 인터셉터
// 통일된 응답 형식: { success, data, error }
apiClient.interceptors.response.use(
  (response) => {
    const result = response.data

    // 응답 형식: { success, data, error }
    if (result && typeof result.success === 'boolean') {
      if (result.success) {
        // 성공: data 필드만 반환
        return result.data
      }
      // 실패: 에러 throw
      const error = new Error(result.error?.message || '오류가 발생했습니다')
      error.code = result.error?.code || 'UNKNOWN_ERROR'
      error.detail = result.error?.detail
      error.response = response
      return Promise.reject(error)
    }

    // 예상치 못한 응답 형식
    console.warn('Unexpected response format:', result)
    return result
  },
  (error) => {
    // HTTP 에러 처리 (4xx, 5xx, 네트워크 오류 등)

    // 네트워크 오류 (response 없음)
    if (!error.response) {
      const networkError = new Error('네트워크 연결을 확인해주세요')
      networkError.code = 'NETWORK_ERROR'
      networkError.detail = error.message
      console.error('API Network Error:', error.message)
      return Promise.reject(networkError)
    }

    const originalRequest = error.config

    // 401 Unauthorized → 토큰 자동 갱신 시도 (refresh 토큰으로 자동 갱신 시도, 성공하며 원래의 요청 재전송)
    if (error.response.status === 401 && !originalRequest._retry) {
      // 로그인/refresh 요청 자체의 401은 갱신 시도하지 않고 오류 처리함.
      if (originalRequest.url?.includes('/auth/login') || originalRequest.url?.includes('/auth/refresh')) {
        return handleApiError(error)
      }

      if (isRefreshing) {
        // 이미 갱신 중이면 큐에 대기
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return apiClient(originalRequest)
        }).catch(err => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      const refreshToken = localStorage.getItem('mureum_refresh_token')
      if (!refreshToken) {
        isRefreshing = false
        clearAuthAndRedirect()
        return Promise.reject(error)
      }

      //  토큰 갱신 요청
      return apiClient.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken
      }).then(data => {
        const newToken = data.access_token
        localStorage.setItem('mureum_access_token', newToken)
        if (data.refresh_token) {
          localStorage.setItem('mureum_refresh_token', data.refresh_token)
        }
        if (data.user) {
          localStorage.setItem('mureum_user', JSON.stringify(data.user))
        }
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        processQueue(null, newToken)
        return apiClient(originalRequest)
      }).catch(err => {
        processQueue(err, null)
        clearAuthAndRedirect()
        return Promise.reject(err)
      }).finally(() => {
        isRefreshing = false
      })
    }

    return handleApiError(error)
  }
)

/**
 * 표준 API 에러 처리
 * - 서버의 표준 응답({ success, error })에서 code/message/detail 추출
 * - 403 FORBIDDEN은 서버 메시지를 그대로 전달 (권한 관련 구체적 안내)
 */
function handleApiError(error) {
  const errorData = error.response?.data
  const status = error.response?.status

  // 표준 에러 응답: { success: false, error: { code, message, detail } }
  if (errorData?.error && typeof errorData.success === 'boolean') {
    const serverError = errorData.error
    const customError = new Error(serverError.message || '오류가 발생했습니다')    
    customError.code = serverError.code || 'UNKNOWN_ERROR'                          // 에러 유형 (FORBIDDEN, NOT_FOUND 등)
    customError.detail = serverError.detail                                         // 디버깅용 상세 정보
    customError.status = status                                                     // HTTP 상태 코드
    customError.response = error.response                                           // 원본 응답
    console.error('API Error:', customError.code, customError.message)
    return Promise.reject(customError)
  }

  // 비표준 응답이지만 HTTP status가 있는 경우 — status 기반 기본 메시지
  const statusMessages = {
    403: '권한이 없어 작업을 수행할 수 없습니다',
    404: '요청한 데이터를 찾을 수 없습니다',
    409: '이미 존재하는 데이터입니다',
    500: '서버 내부 오류가 발생했습니다',
  }
  if (status && statusMessages[status]) {
    const fallbackError = new Error(statusMessages[status])
    fallbackError.code = status === 403 ? 'FORBIDDEN' : 'HTTP_ERROR'
    fallbackError.status = status
    fallbackError.response = error.response
    console.error('API Error (non-standard):', status, fallbackError.message)
    return Promise.reject(fallbackError)
  }

  // 예상치 못한 에러 형식 (로깅 후 그대로 전달)
  console.error('Unexpected error format:', status, errorData || error.message)
  return Promise.reject(error)
}

/**
 * 토큰 전부 삭제 + 로그인 페이지 리다이렉트
 */
function clearAuthAndRedirect() {
  localStorage.removeItem('mureum_access_token')
  localStorage.removeItem('mureum_refresh_token')
  localStorage.removeItem('mureum_user')
  // 이미 로그인 페이지면 리다이렉트하지 않음
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

export default apiClient
