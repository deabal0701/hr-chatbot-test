# 1. Axios 인스턴스와 인터셉터 - API 통신의 핵심

> **파일 위치**: `frontend/src/api/index.js` (168줄)

## 이 파일이 하는 일

모든 API 호출의 **공통 기반**입니다. 16개의 API 모듈(auth, users, search 등)이 전부 이 파일이 만든 `apiClient`를 사용합니다.

```
이 파일이 자동으로 해주는 것:
├── 모든 요청에 JWT 토큰 자동 첨부
├── 서버 응답에서 data만 자동 추출
├── 토큰 만료 시 자동 갱신 (사용자 모르게!)
└── 에러를 표준 형식으로 통일
```

---

## 비유로 이해하기

Axios 인스턴스는 **회사 전용 택배 서비스**와 같습니다:

```
[일반 택배]                         [회사 전용 택배 (apiClient)]

매번 주소 직접 적기                 → 기본 주소가 이미 설정됨
매번 보내는 사람 정보 적기           → 사원증(토큰)이 자동으로 붙음
상자 열어서 내용물 직접 꺼내기       → 포장 뜯고 내용물만 전달
배송 실패하면 직접 처리              → 자동으로 재시도하거나 안내
```

---

## Axios 인스턴스 생성

```javascript
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 120000,  // 120초
  headers: {
    'Content-Type': 'application/json'
  }
})
```

**각 설정의 의미:**

| 설정 | 값 | 설명 |
|------|----|------|
| `baseURL` | 환경별 다름 | 모든 URL 앞에 자동으로 붙는 주소 |
| `timeout` | 120000 (120초) | AI 처리(Agent/NL2SQL)가 오래 걸릴 수 있어서 넉넉하게 |
| `Content-Type` | `application/json` | "보내는 데이터는 JSON 형식이에요" |

**`baseURL`이 환경별로 다른 이유:**

```
로컬 개발 (.env.development):
  VITE_API_URL = http://localhost:8000
  → apiClient.get('/api/v1/users')
  → http://localhost:8000/api/v1/users

Docker 배포 (.env.docker):
  VITE_API_URL = (빈 문자열)
  → apiClient.get('/api/v1/users')
  → /api/v1/users (상대경로 → nginx가 프록시)

프로덕션 (.env.production):
  VITE_API_URL = https://api.yourcompany.com
  → apiClient.get('/api/v1/users')
  → https://api.yourcompany.com/api/v1/users
```

→ 코드는 동일하지만, **환경 변수만 바꾸면** 개발/운영 서버를 자유롭게 전환!

---

## 요청 인터셉터 — 토큰 자동 첨부 ⭐

```javascript
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
```

**인터셉터(Interceptor)**란 "가로채기"라는 뜻입니다. 요청이 서버로 나가기 **직전에** 자동으로 실행됩니다.

```
모든 API 호출:
  apiClient.get('/api/v1/users')
      │
      ▼
  [요청 인터셉터가 가로챔]
      │
      ├─ localStorage에서 토큰 꺼냄
      ├─ 토큰이 있으면 → headers에 'Bearer eyJ...' 추가
      └─ 토큰이 없으면 → 그냥 통과 (로그인 전)
      │
      ▼
  서버로 전송: GET /api/v1/users
               Authorization: Bearer eyJhbGci...
```

**이 방식의 장점:**
```
❌ 인터셉터 없이:
  // 매번 토큰을 직접 넣어야 함
  apiClient.get('/users', { headers: { Authorization: `Bearer ${token}` } })
  apiClient.get('/menus', { headers: { Authorization: `Bearer ${token}` } })
  apiClient.get('/roles', { headers: { Authorization: `Bearer ${token}` } })
  // 16개 파일, 50개 이상의 API 호출에 전부...

✅ 인터셉터 사용:
  // 한 번만 설정하면 자동!
  apiClient.get('/users')   // 토큰이 자동으로 붙음
  apiClient.get('/menus')   // 토큰이 자동으로 붙음
  apiClient.get('/roles')   // 토큰이 자동으로 붙음
```

---

## 응답 인터셉터 — 성공 처리 ⭐

```javascript
apiClient.interceptors.response.use(
  (response) => {
    const result = response.data

    if (result && typeof result.success === 'boolean') {
      if (result.success) {
        return result.data     // ← 핵심! data만 반환
      }
      // 실패 응답
      const error = new Error(result.error?.message || '오류가 발생했습니다')
      error.code = result.error?.code
      return Promise.reject(error)
    }

    return result  // 예상치 못한 형식
  },
  // ... 에러 핸들러
)
```

**서버 응답 형식과 자동 언래핑:**

```
서버가 보내는 응답 (success_response 래퍼):
{
  "success": true,
  "data": {                    ← 이 부분만 필요!
    "items": [...],
    "total": 25
  },
  "error": null
}

인터셉터 없이:
  const response = await apiClient.get('/users')
  const users = response.data.data.items  // response → data → data → items 😵

인터셉터 사용:
  const data = await apiClient.get('/users')
  const users = data.items                // data → items 👍
```

**비유:**
```
[택배 상자]
┌─────────────────────────────┐
│  택배 상자 (HTTP 응답)        │
│  ┌─────────────────────────┐ │
│  │  포장재 (success, error) │ │
│  │  ┌────────────────────┐ │ │
│  │  │  실제 상품 (data)   │ │ │   ← 인터셉터가 여기만 꺼내줌!
│  │  └────────────────────┘ │ │
│  └─────────────────────────┘ │
└─────────────────────────────┘
```

---

## 응답 인터셉터 — 401 자동 갱신 ⭐⭐ (가장 복잡!)

JWT 토큰은 **30분 후 만료**됩니다. 만료되면 서버가 `401 Unauthorized`를 보냅니다.
사용자가 30분마다 다시 로그인해야 한다면 매우 불편하겠죠?

**해결책**: 401이 오면 **자동으로 토큰을 갱신**합니다.

### 기본 흐름

```
[평소]
apiClient.get('/users') → 200 OK → data 반환 ✅

[토큰 만료 시]
apiClient.get('/users') → 401 Unauthorized!
    │
    ▼
인터셉터가 감지: "401이네?"
    │
    ├─ refreshToken으로 새 토큰 요청
    │   POST /api/v1/auth/refresh
    │
    ├─ 성공 → 새 토큰을 localStorage에 저장
    │         → 원래 요청(/users)을 새 토큰으로 재시도!
    │         → 사용자는 에러를 전혀 모름 😊
    │
    └─ 실패 → 로그인 페이지로 이동
              (refreshToken도 만료된 경우)
```

### 동시 요청 문제와 큐 패턴

**문제 상황**: 토큰이 만료된 순간에 API 요청이 3개 동시에 발생하면?

```
❌ 큐 없이:
  요청A → 401 → 토큰 갱신 시도 (1번째)
  요청B → 401 → 토큰 갱신 시도 (2번째)  ← 불필요!
  요청C → 401 → 토큰 갱신 시도 (3번째)  ← 불필요!
  → 갱신 API를 3번이나 호출! 비효율적

✅ 큐 사용:
  요청A → 401 → 토큰 갱신 시도 (1번만!)
  요청B → 401 → 큐에 대기 ⏳
  요청C → 401 → 큐에 대기 ⏳

  갱신 완료! →
    요청A → 새 토큰으로 재시도 → 성공 ✅
    요청B → 큐에서 나와서 새 토큰으로 재시도 → 성공 ✅
    요청C → 큐에서 나와서 새 토큰으로 재시도 → 성공 ✅
```

### 코드 상세 설명

```javascript
// ===== 상태 변수 =====
let isRefreshing = false    // 현재 갱신 중인가?
let failedQueue = []        // 대기 중인 요청들

// 대기 큐 처리 함수
const processQueue = (error, token = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)    // 갱신 실패 → 모두 실패
    else resolve(token)          // 갱신 성공 → 모두에게 새 토큰 전달
  })
  failedQueue = []               // 큐 비우기
}
```

```javascript
// 401 처리 로직 (응답 인터셉터의 에러 핸들러 내부)
if (error.response.status === 401 && !originalRequest._retry) {

  // ① 로그인/refresh 요청 자체의 401은 갱신하지 않음
  if (originalRequest.url?.includes('/auth/login') ||
      originalRequest.url?.includes('/auth/refresh')) {
    return handleApiError(error)
  }

  // ② 이미 갱신 중이면 큐에 대기
  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve, reject })
    }).then(token => {
      originalRequest.headers.Authorization = `Bearer ${token}`
      return apiClient(originalRequest)  // 새 토큰으로 재시도
    })
  }

  // ③ 갱신 시작
  originalRequest._retry = true
  isRefreshing = true

  const refreshToken = localStorage.getItem('mureum_refresh_token')
  if (!refreshToken) {
    isRefreshing = false
    clearAuthAndRedirect()   // 로그인 페이지로
    return Promise.reject(error)
  }

  // ④ 갱신 API 호출
  return apiClient.post('/api/v1/auth/refresh', {
    refresh_token: refreshToken
  }).then(data => {
    // 성공: 새 토큰 저장
    localStorage.setItem('mureum_access_token', data.access_token)
    if (data.refresh_token) {
      localStorage.setItem('mureum_refresh_token', data.refresh_token)
    }

    // 원래 요청 재시도 + 큐의 요청들도 처리
    originalRequest.headers.Authorization = `Bearer ${data.access_token}`
    processQueue(null, data.access_token)
    return apiClient(originalRequest)
  }).catch(err => {
    // 실패: 큐의 요청들도 모두 실패 처리 + 로그인 페이지로
    processQueue(err, null)
    clearAuthAndRedirect()
    return Promise.reject(err)
  }).finally(() => {
    isRefreshing = false
  })
}
```

**`_retry` 플래그의 역할:**
```
originalRequest._retry = true

이것이 없으면:
  요청 → 401 → 갱신 → 재시도 → 또 401 → 갱신 → 재시도 → ...
  → 무한 루프! 😱

_retry = true로 설정하면:
  요청 → 401 → 갱신 → 재시도 → 또 401이지만 _retry가 true
  → 이미 재시도한 요청이므로 → 에러 처리 (루프 방지!)
```

---

## 에러 표준화 (handleApiError)

```javascript
function handleApiError(error) {
  const errorData = error.response?.data

  // 서버의 표준 에러: { success: false, error: { code, message, detail } }
  if (errorData?.error && typeof errorData.success === 'boolean') {
    const customError = new Error(errorData.error.message || '오류가 발생했습니다')
    customError.code = errorData.error.code || 'UNKNOWN_ERROR'
    customError.detail = errorData.error.detail
    return Promise.reject(customError)
  }

  // 예상치 못한 에러 형식
  return Promise.reject(error)
}
```

**에러 객체의 통일된 형태:**
```javascript
// API 모듈에서 에러를 catch할 때 항상 같은 형태
try {
  const data = await apiClient.get('/users')
} catch (error) {
  console.log(error.message)  // "권한이 없습니다"
  console.log(error.code)     // "FORBIDDEN"
  console.log(error.detail)   // "USER_MGMT 메뉴 read 권한이 필요합니다"
}
```

---

## 로그아웃 처리 (clearAuthAndRedirect)

```javascript
function clearAuthAndRedirect() {
  // 저장된 인증 정보 모두 삭제
  localStorage.removeItem('mureum_access_token')
  localStorage.removeItem('mureum_refresh_token')
  localStorage.removeItem('mureum_user')

  // 이미 로그인 페이지면 리다이렉트하지 않음
  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}
```

```
이 함수가 호출되는 경우:
├── refreshToken이 없을 때
├── refreshToken으로 갱신 실패했을 때 (refresh도 만료)
└── 결과: localStorage 정리 + 로그인 페이지 이동
```

**`window.location.href`를 쓰는 이유:**
```
router.push('/login')  → Vue 내부 이동 (상태 유지될 수 있음)
window.location.href   → 브라우저 전체 새로고침 (모든 상태 초기화!)

→ 보안상 window.location.href가 더 안전
   (메모리에 남은 민감한 데이터까지 깨끗하게 정리)
```

---

## 전체 요청/응답 흐름 한눈에

```
apiClient.post('/api/v1/auth/login', { login_id, password })
    │
    ▼
[1. 요청 인터셉터]
    ├─ localStorage에서 토큰 확인
    ├─ 토큰 있으면 → Authorization 헤더 추가
    └─ config 반환
    │
    ▼
[2. Axios가 HTTP 요청 전송]
    POST http://localhost:8000/api/v1/auth/login
    Headers: { Authorization: 'Bearer eyJ...' }
    Body: { login_id: 'admin', password: '...' }
    │
    ▼
[3. 서버 응답 수신]
    200 OK
    { success: true, data: { access_token, user }, error: null }
    │
    ▼
[4. 응답 인터셉터]
    ├─ success === true?
    │   └─ YES → return result.data  ← { access_token, user } 만 반환!
    │
    └─ 401 에러?
        └─ YES → 토큰 갱신 시도 → 재시도 또는 로그인 이동
    │
    ▼
[5. 호출한 곳에서 결과 수신]
    const data = await apiClient.post('/api/v1/auth/login', ...)
    // data = { access_token: 'eyJ...', user: { login_id: 'admin', ... } }
```

---

## 리뷰 체크리스트

- [x] baseURL이 환경별로 설정 가능한가? → `import.meta.env.VITE_API_URL` ✅
- [x] 모든 요청에 토큰이 자동 첨부되는가? → 요청 인터셉터 ✅
- [x] 서버 응답의 data가 자동 추출되는가? → 응답 인터셉터 ✅
- [x] 401 시 자동 갱신이 동작하는가? → refresh + 재시도 ✅
- [x] 동시 401 시 갱신이 1번만 되는가? → isRefreshing + failedQueue ✅
- [x] 무한 루프가 방지되는가? → `_retry` 플래그 ✅
- [x] 갱신 실패 시 로그아웃 되는가? → clearAuthAndRedirect ✅
- [x] 에러 형식이 통일되어 있는가? → handleApiError ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **Axios 인스턴스** | 공통 설정(baseURL, timeout)이 적용된 HTTP 클라이언트 |
| **요청 인터셉터** | 요청 직전에 JWT 토큰을 자동으로 헤더에 첨부 |
| **응답 인터셉터** | 성공 시 `data`만 추출, 실패 시 에러 표준화 |
| **자동 토큰 갱신** | 401 발생 시 refresh_token으로 자동 갱신 후 재시도 |
| **failedQueue** | 동시 401을 모아서 갱신 1회로 처리하는 대기열 |
| **clearAuthAndRedirect** | 토큰 삭제 + 로그인 페이지 전체 새로고침 이동 |

---
> **다음**: [02_api_modules.md](02_api_modules.md) - API 모듈 패턴
