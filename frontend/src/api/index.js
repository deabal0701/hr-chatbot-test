import axios from 'axios'

// API 클라이언트 인스턴스 생성
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  timeout: 60000, // NL2SQL은 시간이 걸릴 수 있음
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
apiClient.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    // 향후 인증 추가 시 401 처리
    // if (error.response?.status === 401) {
    //   localStorage.removeItem('token')
    //   window.location.href = '/login'
    // }

    // 에러 로깅
    console.error('API Error:', error.response?.data || error.message)

    return Promise.reject(error)
  }
)

export default apiClient
