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

// 요청 인터셉터
apiClient.interceptors.request.use(
  (config) => {
    // 향후 인증 토큰 추가 위치
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }
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

    const errorData = error.response?.data

    // 표준 에러 응답: { success: false, error: { code, message, detail } }
    if (errorData?.error && typeof errorData.success === 'boolean') {
      const customError = new Error(errorData.error.message || '오류가 발생했습니다')
      customError.code = errorData.error.code || 'UNKNOWN_ERROR'
      customError.detail = errorData.error.detail
      customError.response = error.response
      console.error('API Error:', customError.code, customError.message)
      return Promise.reject(customError)
    }

    // 예상치 못한 에러 형식 (로깅 후 그대로 전달)
    console.error('Unexpected error format:', error.response?.status, errorData || error.message)
    return Promise.reject(error)
  }
)

export default apiClient
