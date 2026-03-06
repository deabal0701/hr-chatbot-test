# 2. API 모듈 패턴 - 16개 모듈이 같은 구조인 이유

## 이 문서에서 배우는 것

`frontend/src/api/` 폴더에는 16개의 API 모듈 파일이 있습니다. 놀라운 것은, **거의 모든 파일이 같은 패턴**으로 작성되어 있다는 것입니다.

대표 파일 3개를 통해 패턴을 이해하면, 나머지 13개도 바로 읽을 수 있습니다.

```
api/
├── index.js        ← 공통 기반 (이전 문서에서 학습)
├── auth.js         ← 패턴 ①: 인증 (특수한 기능)
├── users.js        ← 패턴 ②: CRUD + 옵션 (가장 일반적)
└── search.js       ← 패턴 ③: 검색 + SSE 스트리밍 + 파일 다운로드
```

---

## 공통 패턴: API 모듈의 기본 구조

모든 API 모듈은 이 구조를 따릅니다:

```javascript
// 1. apiClient 가져오기
import apiClient from './index'

// 2. 기본 URL 상수 정의
const BASE_URL = '/api/v1/리소스명'

// 3. API 함수들을 객체로 묶기
const 모듈Api = {
  list: (params) => apiClient.get(BASE_URL, { params }),
  get: (id) => apiClient.get(`${BASE_URL}/${id}`),
  create: (data) => apiClient.post(BASE_URL, data),
  update: (id, data) => apiClient.put(`${BASE_URL}/${id}`, data),
  delete: (id) => apiClient.delete(`${BASE_URL}/${id}`)
}

// 4. 기본 내보내기
export default 모듈Api
```

**이 패턴이 반복되는 이유:**

```
프론트엔드 API 모듈은 "얇은 계층(Thin Layer)"입니다.

비즈니스 로직 ❌ → 그건 Store(Vuex)가 담당
에러 처리 ❌    → 그건 index.js 인터셉터가 담당
토큰 관리 ❌    → 그건 index.js 인터셉터가 담당

API 모듈은 오직:
  ✅ "어떤 URL로"
  ✅ "어떤 HTTP 메서드로"
  ✅ "어떤 데이터를 보낼지"만 정의
```

---

## 패턴 ①: auth.js — 인증 API

> **파일 위치**: `frontend/src/api/auth.js` (45줄)

```javascript
import apiClient from './index'

const AUTH_BASE = '/api/v1/auth'

const authApi = {
  // 로그인
  login(loginId, password) {
    return apiClient.post(`${AUTH_BASE}/login`, {
      login_id: loginId,       // 프론트엔드 변수명 → 서버 필드명 변환
      password
    })
  },

  // 로그아웃
  logout() {
    return apiClient.post(`${AUTH_BASE}/logout`)
  },

  // 토큰 갱신
  refreshToken(refreshToken) {
    return apiClient.post(`${AUTH_BASE}/refresh`, {
      refresh_token: refreshToken
    })
  },

  // 현재 사용자 정보 조회
  getMe() {
    return apiClient.get(`${AUTH_BASE}/me`)
  },

  // 비밀번호 변경
  changePassword(currentPassword, newPassword) {
    return apiClient.put(`${AUTH_BASE}/me/password`, {
      current_password: currentPassword,
      new_password: newPassword
    })
  }
}

export default authApi
```

**auth.js의 특징:**

```
일반 CRUD 모듈과 다른 점:

일반 CRUD:  GET /users     → list
            GET /users/1   → get(1)
            POST /users    → create
            PUT /users/1   → update(1)
            DELETE /users/1 → delete(1)

인증 API:   POST /auth/login    → 로그인
            POST /auth/logout   → 로그아웃
            POST /auth/refresh  → 토큰 갱신
            GET  /auth/me       → 내 정보
            PUT  /auth/me/password → 비밀번호 변경

→ 리소스 CRUD가 아니라 "동작(Action)" 중심이라 이름이 다름
```

**변수명 변환 패턴:**

```javascript
login(loginId, password) {        // ← 프론트엔드: camelCase
  return apiClient.post('...', {
    login_id: loginId,             // → 서버: snake_case
    password
  })
}

// 왜? JavaScript는 camelCase가 관례, Python은 snake_case가 관례
// API 모듈이 이 변환을 담당합니다
```

**Store에서 호출하는 방식** (Phase 3 복습):

```javascript
// store/modules/auth.js
import authApi from '@/api/auth'

async login({ commit }, { loginId, password }) {
  const data = await authApi.login(loginId, password)
  // data = { access_token, refresh_token, user }
  // → 인터셉터가 이미 success_response에서 data만 추출해줬음!
  commit('SET_AUTH', data)
}
```

---

## 패턴 ②: users.js — CRUD + 옵션 API

> **파일 위치**: `frontend/src/api/users.js` (53줄)

```javascript
import apiClient from './index'

const BASE_URL = '/api/admin/v1/users'

const usersApi = {
  /** 사용자 목록 조회 */
  list: (params = {}) => apiClient.get(BASE_URL, { params }),

  /** 사용자 상세 조회 */
  get: (userId) => apiClient.get(`${BASE_URL}/${userId}`),

  /** 사용자 생성 */
  create: (data) => apiClient.post(BASE_URL, data),

  /** 사용자 수정 */
  update: (userId, data) => apiClient.put(`${BASE_URL}/${userId}`, data),

  /** 사용자 삭제 */
  delete: (userId) => apiClient.delete(`${BASE_URL}/${userId}`),

  /** 사용자 메뉴 권한 조회 */
  getUserMenus: (userId) => apiClient.get(`${BASE_URL}/${userId}/menus`),

  /** 사용자 메뉴 권한 할당 */
  assignMenus: (userId, menus) =>
    apiClient.put(`${BASE_URL}/${userId}/menus`, { menus }),

  /** 역할 선택 옵션 */
  getRoleOptions: () => apiClient.get(`${BASE_URL}/options/roles`),

  /** 테넌트 선택 옵션 */
  getTenantOptions: () => apiClient.get(`${BASE_URL}/options/tenants`),

  /** 메뉴 선택 옵션 */
  getMenuOptions: () => apiClient.get(`${BASE_URL}/options/menus`),

  /** 부서 선택 옵션 */
  getDeptOptions: (tenantId) => apiClient.get(`${BASE_URL}/options/departments`, {
    params: tenantId ? { tenant_id: tenantId } : {}
  }),
}

export default usersApi
```

**users.js의 특징:**

```
기본 CRUD (5개) + 확장 API (6개):

기본 CRUD:
  list()           GET    /api/admin/v1/users          → 목록
  get(id)          GET    /api/admin/v1/users/3         → 상세
  create(data)     POST   /api/admin/v1/users          → 생성
  update(id, data) PUT    /api/admin/v1/users/3         → 수정
  delete(id)       DELETE /api/admin/v1/users/3         → 삭제

하위 리소스 (메뉴 권한):
  getUserMenus(id)   GET  /api/admin/v1/users/3/menus   → 권한 조회
  assignMenus(id, m) PUT  /api/admin/v1/users/3/menus   → 권한 할당

옵션 API (셀렉트박스용):
  getRoleOptions()   GET  /api/admin/v1/users/options/roles
  getTenantOptions() GET  /api/admin/v1/users/options/tenants
  getMenuOptions()   GET  /api/admin/v1/users/options/menus
  getDeptOptions(t)  GET  /api/admin/v1/users/options/departments
```

**`params`를 사용하는 방법:**

```javascript
// list() 호출 시 검색 조건 전달
usersApi.list({ page: 1, page_size: 20, keyword: '홍길동' })

// Axios가 자동으로 쿼리 스트링 변환:
// GET /api/admin/v1/users?page=1&page_size=20&keyword=홍길동

// 조건이 없으면 기본값 사용
usersApi.list()
// GET /api/admin/v1/users (params 없음)
```

**화살표 함수(=>)와 일반 함수의 차이:**

```javascript
// users.js 스타일: 화살표 함수
list: (params) => apiClient.get(BASE_URL, { params })

// auth.js 스타일: 일반 함수
login(loginId, password) {
  return apiClient.post(...)
}

// 둘 다 같은 결과! 차이는 코드 길이뿐
// 한 줄이면 화살표 함수, 여러 줄이면 일반 함수를 쓰는 경향
```

---

## 패턴 ③: search.js — 검색 + SSE + 파일 다운로드

> **파일 위치**: `frontend/src/api/search.js` (118줄)

```javascript
import axios from 'axios'        // 직접 axios도 사용 (Excel용)
import apiClient from './index'
import { streamSSE } from './sse' // SSE 스트리밍 사용

const searchApi = {
  // 통합 검색 (일반 HTTP)
  search(params) {
    const payload = {
      query: params.query,
      mode: params.mode || 'auto',
      filters: params.filters || {}
    }
    if (params.top_k) payload.top_k = params.top_k
    if (params.sessionId) payload.session_id = params.sessionId
    return apiClient.post('/api/v1/search', payload)
  },

  // NL2SQL SSE 스트리밍 검색
  searchStream(params, callbacks) {
    const payload = {
      query: params.query,
      mode: params.mode || 'nl2sql',
    }
    if (params.sessionId) payload.session_id = params.sessionId
    return streamSSE('/api/v1/search/stream', payload, callbacks)
  },

  // Excel 내보내기 (Blob 다운로드)
  async exportExcel(data) {
    const response = await axios.post('/api/v1/export/excel', data, {
      responseType: 'blob',     // ← 파일 다운로드는 JSON이 아닌 Blob!
      headers: { 'Content-Type': 'application/json' }
    })
    // Blob → 다운로드 처리 (브라우저 파일 저장)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'report.xlsx')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }
}
```

**search.js의 특징:**

```
3가지 다른 통신 방식을 사용:

① 일반 HTTP (apiClient)
   search()     → POST /api/v1/search
   searchRag()  → POST /api/v1/rag
   searchNl2sql() → POST /api/v1/nl2sql
   → 요청 보내고 한번에 응답 받음

② SSE 스트리밍 (streamSSE)
   searchStream() → POST /api/v1/search/stream
   → 실시간으로 진행 상태를 받으며 화면 갱신

③ Blob 다운로드 (axios 직접 사용)
   exportExcel() → POST /api/v1/export/excel
   → JSON이 아닌 파일(Excel)을 다운로드
```

**왜 exportExcel은 apiClient를 안 쓰는가?**

```
apiClient의 응답 인터셉터:
  → response.data에서 { success, data } 구조를 기대
  → Blob(파일 데이터)은 이 구조가 아님!

그래서 직접 axios를 사용:
  → responseType: 'blob'으로 바이너리 데이터 수신
  → 인터셉터를 거치지 않고 직접 처리
```

**Blob → 파일 다운로드 과정:**

```
① 서버 → Blob (바이너리 데이터) 수신
② Blob → URL 생성 (임시 브라우저 URL)
③ <a> 태그 생성 → href = 임시 URL, download = 'report.xlsx'
④ 프로그래밍으로 클릭 → 파일 다운로드 시작!
⑤ <a> 태그 제거, URL 해제 (메모리 정리)
```

---

## 16개 API 모듈 분류

```
┌──────────── API 모듈 분류 ────────────┐
│                                        │
│  [인증] 특수                           │
│  ├─ auth.js         인증/로그아웃       │
│                                        │
│  [관리 CRUD] /api/admin/v1/...         │
│  ├─ users.js        사용자 관리         │
│  ├─ roles.js        역할 관리           │
│  ├─ menus.js        메뉴 관리           │
│  ├─ tenants.js      테넌트 관리         │
│  ├─ documents.js    문서 관리           │
│  ├─ settings.js     시스템 설정         │
│  ├─ codes.js        코드 관리           │
│  └─ departments.js  부서 조회           │
│                                        │
│  [AI 검색] /api/v1/...                 │
│  ├─ search.js       통합 검색           │
│  ├─ agent.js        AI Agent            │
│  └─ sse.js          SSE 스트리밍 유틸    │
│                                        │
│  [조회] 이력/대시보드                    │
│  ├─ history.js      검색 이력           │
│  ├─ dashboard.js    관리자 대시보드      │
│  └─ personalDashboard.js 개인 대시보드  │
│                                        │
└────────────────────────────────────────┘
```

---

## agent.js — 두 가지 export 스타일

> **파일 위치**: `frontend/src/api/agent.js` (105줄)

agent.js는 두 가지 내보내기 방식을 모두 사용합니다:

```javascript
// Named export (개별 가져오기 가능)
export const agentSearch = async ({ question, sessionId }) => { ... }
export const agentSearchStream = ({ question, sessionId }, callbacks) => { ... }
export const listSessions = async () => { ... }

// Default export (한번에 가져오기)
const agentApi = {
  agentSearch,
  agentSearchStream,
  listSessions,
  // ...
}
export default agentApi
```

**사용 시 차이:**

```javascript
// ① default export 사용 (대부분의 다른 모듈 방식)
import agentApi from '@/api/agent'
agentApi.agentSearch({ question: '...' })

// ② named export 사용 (필요한 함수만 가져오기)
import { agentSearch } from '@/api/agent'
agentSearch({ question: '...' })
```

---

## HTTP 메서드와 CRUD 매핑

모든 CRUD 모듈은 **같은 HTTP 메서드 규칙**을 따릅니다:

```
┌─────────┬─────────┬───────────────────────┬──────────────┐
│ 작업    │ 메서드  │ URL 예시              │ 응답 상태코드 │
├─────────┼─────────┼───────────────────────┼──────────────┤
│ 목록    │ GET     │ /api/admin/v1/users   │ 200          │
│ 상세    │ GET     │ /api/admin/v1/users/3 │ 200          │
│ 생성    │ POST    │ /api/admin/v1/users   │ 201          │
│ 수정    │ PUT     │ /api/admin/v1/users/3 │ 200          │
│ 삭제    │ DELETE  │ /api/admin/v1/users/3 │ 200          │
└─────────┴─────────┴───────────────────────┴──────────────┘

기억법:
  GET    = "가져와"   (데이터 읽기)
  POST   = "새로 만들어" (데이터 생성)
  PUT    = "바꿔"      (데이터 수정)
  DELETE = "지워"      (데이터 삭제)
```

---

## 리뷰 체크리스트

- [x] 모든 모듈이 `apiClient`를 가져오는가? → import from './index' ✅
- [x] BASE_URL이 상수로 정의되어 있는가? → 모든 모듈에 정의됨 ✅
- [x] CRUD 함수명이 일관적인가? → list/get/create/update/delete ✅
- [x] 에러 처리를 모듈에서 직접 하지 않는가? → index.js에 위임 ✅
- [x] camelCase ↔ snake_case 변환이 되는가? → API 모듈에서 처리 ✅
- [x] SSE 스트리밍은 별도 함수로 분리되어 있는가? → searchStream, agentSearchStream ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **얇은 계층** | API 모듈은 URL, 메서드, 데이터만 정의. 로직은 없음 |
| **BASE_URL** | 각 모듈의 기본 엔드포인트. 반복 타이핑 방지 |
| **CRUD 패턴** | list/get/create/update/delete — 모든 관리 모듈에 동일 |
| **params** | GET 요청의 쿼리 스트링. Axios가 `?key=value` 형태로 자동 변환 |
| **camelCase → snake_case** | JS 관례 → Python 관례 변환을 API 모듈이 담당 |
| **Blob 다운로드** | Excel 등 파일은 `responseType: 'blob'`으로 수신 |

---
> **이전**: [01_axios_basics.md](01_axios_basics.md) - Axios 기초
> **다음**: [03_sse_streaming.md](03_sse_streaming.md) - SSE 스트리밍
