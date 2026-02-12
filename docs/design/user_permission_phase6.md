# Phase 6: 프론트엔드 인증 및 권한 UI 구현 설계서

> **문서 버전**: 1.0
> **작성일**: 2026-02-12
> **상태**: Draft
> **선행 조건**: Phase 2 (Core Security), Phase 3 (인증 API + 미들웨어) 완료
> **참조**: `docs/design/user_permission_system.md`

---

## 목차

1. [개요](#1-개요)
2. [현재 상태 분석](#2-현재-상태-분석)
3. [단계별 구현 계획 (Step 1~7)](#3-단계별-구현-계획)
4. [Step 1: 인증 인프라](#4-step-1-인증-인프라)
5. [Step 2: 로그인 화면](#5-step-2-로그인-화면)
6. [Step 3: 라우터 가드 + 레이아웃 UI](#6-step-3-라우터-가드--레이아웃-ui)
7. [Step 4: 사용자 관리 API + 화면](#7-step-4-사용자-관리-api--화면)
8. [Step 5: 역할 관리 API + 화면](#8-step-5-역할-관리-api--화면)
9. [Step 6: 테넌트 관리 API + 화면](#9-step-6-테넌트-관리-api--화면)
10. [Step 7: 인증 필수 모드 전환](#10-step-7-인증-필수-모드-전환)
11. [산출물 총괄](#11-산출물-총괄)
12. [검증 계획](#12-검증-계획)

---

## 1. 개요

### 1.1 목적

Phase 3에서 구현한 백엔드 인증 API(login, logout, refresh, me, password)를 프론트엔드에 통합하고, 역할(Role) 기반 메뉴 제어, 관리 화면(사용자/역할/테넌트)을 구현합니다.

### 1.2 핵심 원칙

```
┌──────────────────────────────────────────────────────────────────┐
│  1. 점진적 적용 — 각 Step 완료 후 기존 기능이 정상 동작해야 함     │
│  2. 권한 코드 기반 — 역할 이름이 아닌 permission 코드로 UI 제어    │
│  3. 백엔드 의존 최소화 — 이미 구현된 API만 활용                    │
│  4. 하위 호환 — Step 7 전까지 토큰 없이도 기존 API 사용 가능       │
└──────────────────────────────────────────────────────────────────┘
```

### 1.3 전체 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Vue 3 + Vuex + Vue Router + Element Plus)            │
│                                                                  │
│  ┌─────────┐    ┌──────────┐    ┌──────────────┐               │
│  │LoginView│───►│auth store│───►│api/auth.js   │               │
│  └─────────┘    │(Vuex)    │    │(Axios client)│               │
│       │         └─────┬────┘    └──────┬───────┘               │
│       │               │               │                         │
│       ▼               ▼               ▼                         │
│  ┌─────────┐    ┌──────────┐    ┌──────────────┐               │
│  │Router   │    │AppSidebar│    │api/index.js  │               │
│  │Guard    │    │(메뉴필터)│    │(interceptors)│               │
│  │beforeEach│   │AppHeader │    │401→refresh   │               │
│  └─────────┘    │(사용자)  │    │403→logout    │               │
│                 └──────────┘    └──────┬───────┘               │
│                                        │                        │
├────────────────────────────────────────┼────────────────────────┤
│  Backend (FastAPI — Phase 3 완료)       │                        │
│                                        ▼                        │
│  ┌──────────────────────────────────────────┐                   │
│  │  POST /api/v1/auth/login                 │                   │
│  │  POST /api/v1/auth/logout                │                   │
│  │  POST /api/v1/auth/refresh               │                   │
│  │  GET  /api/v1/auth/me                    │                   │
│  │  PUT  /api/v1/auth/me/password           │                   │
│  └──────────────────────────────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 현재 상태 분석

### 2.1 프론트엔드 현황 (변경 필요 항목)

| 파일 | 현재 상태 | 변경 필요 |
|------|----------|----------|
| `router/index.js` | `beforeEach` 가드 주석 처리, `/login` 라우트 없음 | 가드 활성화, 로그인 라우트 추가 |
| `store/modules/app.js` | `userRole: 'admin'` 하드코딩, `login()` 플레이스홀더 | auth 모듈로 분리 |
| `api/index.js` | 토큰 인터셉터 주석 처리, 401/403 미처리 | 인터셉터 활성화 |
| `api/auth.js` | **미존재** | 신규 생성 |
| `components/layout/AppSidebar.vue` | 정적 메뉴, 권한 필터 없음 | 권한 기반 메뉴 필터링 |
| `components/layout/AppHeader.vue` | 사용자 드롭다운 주석 처리 | 로그인 사용자 표시 + 로그아웃 |
| `views/LoginView.vue` | **미존재** | 신규 생성 |
| `views/admin/UsersView.vue` | **미존재** | Step 4에서 생성 |
| `views/admin/RolesView.vue` | **미존재** | Step 5에서 생성 |
| `views/admin/TenantsView.vue` | **미존재** | Step 6에서 생성 |

### 2.2 백엔드 현황 (이미 완료)

| 구분 | 파일 | 상태 |
|------|------|------|
| 인증 API | `app/api/routes/auth.py` | 5개 엔드포인트 완료 |
| 인증 서비스 | `app/api/services/auth_service.py` | authenticate, create_session 등 완료 |
| JWT | `app/core/security/jwt.py` | HS256, Access 30분, Refresh 7일 |
| 비밀번호 | `app/core/security/password.py` | bcrypt 해싱 완료 |
| 의존성 | `app/core/security/dependencies.py` | get_current_user, require_permission 완료 |
| 미들웨어 | `app/middleware/auth.py` | Phase 3a 선택적 모드 |
| 모델 | `app/models/auth.py` | UserContext, TokenResponse 등 완료 |

### 2.3 백엔드 미구현 (Step 4~6에서 함께 구현)

| 구분 | 파일 | 상태 |
|------|------|------|
| 사용자 관리 API | `app/api/routes/users.py` | **미구현** |
| 사용자 서비스 | `app/api/services/user_service.py` | **미구현** |
| 역할 관리 API | `app/api/routes/roles.py` | **미구현** |
| 역할 서비스 | `app/api/services/role_service.py` | **미구현** |
| 테넌트 관리 API | `app/api/routes/tenants.py` | **미구현** |
| 테넌트 서비스 | `app/api/services/tenant_service.py` | **미구현** |
| 사용자 모델 | `app/models/user.py` | **미구현** |
| 테넌트 모델 | `app/models/tenant.py` | **미구현** |

---

## 3. 단계별 구현 계획

### 3.1 Step 의존성 다이어그램

```
Step 1 ─────► Step 2 ─────► Step 3 ─────► Step 7
(인증 인프라)  (로그인 화면)  (라우터가드+UI)  (필수모드)
                                │
                                ├──► Step 4 (사용자 관리)
                                ├──► Step 5 (역할 관리)
                                └──► Step 6 (테넌트 관리)
                                       │
                                       └──► Step 7 (필수모드)
```

### 3.2 Step 요약

| Step | 이름 | 범위 | 신규 파일 | 수정 파일 |
|------|------|------|----------|----------|
| **1** | 인증 인프라 | FE | 2개 | 1개 |
| **2** | 로그인 화면 | FE | 1개 | 1개 |
| **3** | 라우터 가드 + 레이아웃 UI | FE | 0개 | 3개 |
| **4** | 사용자 관리 | BE + FE | 5~6개 | 1~2개 |
| **5** | 역할 관리 | BE + FE | 4~5개 | 1~2개 |
| **6** | 테넌트 관리 | BE + FE | 4~5개 | 1~2개 |
| **7** | 인증 필수 모드 전환 | BE + FE | 0개 | 2개 |

### 3.3 Step별 독립 실행 가능 여부

| Step | 독립 실행 | 설명 |
|------|:---------:|------|
| 1 | ✗ | Step 2와 함께 검증 |
| 2 | ✓ | 로그인 → 토큰 저장 → API 호출 확인 가능 |
| 3 | ✓ | 메뉴 필터링, 라우터 가드 동작 확인 |
| 4 | ✓ | 사용자 CRUD 독립 동작 |
| 5 | ✓ | 역할 CRUD 독립 동작 |
| 6 | ✓ | 테넌트 CRUD 독립 동작 |
| 7 | ✓ | 토큰 없으면 차단 확인 |

---

## 4. Step 1: 인증 인프라

### 4.1 목표

프론트엔드 인증의 핵심 인프라 3개를 구축합니다:
- **auth API 클라이언트** (`api/auth.js`) — 백엔드 인증 API 호출
- **auth Vuex 모듈** (`store/modules/auth.js`) — 인증 상태 관리
- **Axios 인터셉터** (`api/index.js` 수정) — 자동 토큰 첨부 + 401 자동 갱신

### 4.2 산출물

```
신규:
  frontend/src/api/auth.js              # 인증 API 클라이언트
  frontend/src/store/modules/auth.js    # 인증 상태 관리 (Vuex)

수정:
  frontend/src/api/index.js             # Axios 인터셉터 활성화
```

### 4.3 `frontend/src/api/auth.js`

```javascript
/**
 * 인증 API 클라이언트
 *
 * Backend endpoints:
 *   POST /api/v1/auth/login    → login(loginId, password)
 *   POST /api/v1/auth/logout   → logout()
 *   POST /api/v1/auth/refresh  → refreshToken(refreshToken)
 *   GET  /api/v1/auth/me       → getMe()
 *   PUT  /api/v1/auth/me/password → changePassword(current, new)
 */
import apiClient from './index'

const AUTH_BASE = '/api/v1/auth'

export default {
  login(loginId, password) {
    return apiClient.post(`${AUTH_BASE}/login`, {
      login_id: loginId,
      password
    })
  },

  logout() {
    return apiClient.post(`${AUTH_BASE}/logout`)
  },

  refreshToken(refreshToken) {
    return apiClient.post(`${AUTH_BASE}/refresh`, {
      refresh_token: refreshToken
    })
  },

  getMe() {
    return apiClient.get(`${AUTH_BASE}/me`)
  },

  changePassword(currentPassword, newPassword) {
    return apiClient.put(`${AUTH_BASE}/me/password`, {
      current_password: currentPassword,
      new_password: newPassword
    })
  }
}
```

### 4.4 `frontend/src/store/modules/auth.js`

```javascript
/**
 * 인증 상태 관리 (Vuex Module)
 *
 * State:
 *   user        — UserInfo (user_id, login_id, display_name, scope_type, roles, permissions)
 *   accessToken — JWT Access Token
 *   refreshToken — JWT Refresh Token
 *
 * 토큰 저장: localStorage
 *   - mureum_access_token
 *   - mureum_refresh_token
 *   - mureum_user (JSON)
 */
import authApi from '@/api/auth'

const TOKEN_KEYS = {
  ACCESS: 'mureum_access_token',
  REFRESH: 'mureum_refresh_token',
  USER: 'mureum_user'
}

// localStorage에서 초기값 복원
const getStoredToken = (key) => {
  try { return localStorage.getItem(key) } catch { return null }
}

const getStoredUser = () => {
  try {
    const json = localStorage.getItem(TOKEN_KEYS.USER)
    return json ? JSON.parse(json) : null
  } catch { return null }
}

const saveTokens = (accessToken, refreshToken, user) => {
  try {
    localStorage.setItem(TOKEN_KEYS.ACCESS, accessToken)
    localStorage.setItem(TOKEN_KEYS.REFRESH, refreshToken)
    localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(user))
  } catch { /* ignore */ }
}

const clearTokens = () => {
  try {
    localStorage.removeItem(TOKEN_KEYS.ACCESS)
    localStorage.removeItem(TOKEN_KEYS.REFRESH)
    localStorage.removeItem(TOKEN_KEYS.USER)
  } catch { /* ignore */ }
}

export default {
  namespaced: true,

  state: () => ({
    user: getStoredUser(),
    accessToken: getStoredToken(TOKEN_KEYS.ACCESS),
    refreshToken: getStoredToken(TOKEN_KEYS.REFRESH),
    loginLoading: false,
    loginError: null
  }),

  mutations: {
    SET_AUTH(state, { accessToken, refreshToken, user }) {
      state.accessToken = accessToken
      state.refreshToken = refreshToken
      state.user = user
      saveTokens(accessToken, refreshToken, user)
    },
    CLEAR_AUTH(state) {
      state.accessToken = null
      state.refreshToken = null
      state.user = null
      clearTokens()
    },
    SET_USER(state, user) {
      state.user = user
      try { localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(user)) } catch { /* ignore */ }
    },
    SET_LOGIN_LOADING(state, loading) {
      state.loginLoading = loading
    },
    SET_LOGIN_ERROR(state, error) {
      state.loginError = error
    }
  },

  getters: {
    isAuthenticated: (state) => !!state.accessToken && !!state.user,
    currentUser: (state) => state.user,
    accessToken: (state) => state.accessToken,
    refreshToken: (state) => state.refreshToken,

    // 권한 헬퍼
    permissions: (state) => state.user?.permissions || [],
    roles: (state) => state.user?.roles || [],
    scopeType: (state) => state.user?.scope_type || 'USER',

    hasPermission: (state) => (code) => {
      if (!state.user) return false
      return state.user.permissions?.includes(code) || false
    },
    hasAnyPermission: (state) => (...codes) => {
      if (!state.user) return false
      return codes.some(c => state.user.permissions?.includes(c))
    },

    // 관리 메뉴 접근 여부
    canAccessAdmin: (state) => {
      if (!state.user) return false
      const adminPerms = ['admin:settings', 'admin:users', 'admin:tenants',
                          'document:write', 'document:delete']
      return adminPerms.some(p => state.user.permissions?.includes(p))
    }
  },

  actions: {
    /**
     * 로그인
     * @returns {Promise<object>} TokenResponse.user
     */
    async login({ commit }, { loginId, password }) {
      commit('SET_LOGIN_LOADING', true)
      commit('SET_LOGIN_ERROR', null)
      try {
        // apiClient 인터셉터가 data를 추출하므로 바로 TokenResponse 수신
        const data = await authApi.login(loginId, password)
        commit('SET_AUTH', {
          accessToken: data.access_token,
          refreshToken: data.refresh_token,
          user: data.user
        })
        return data.user
      } catch (err) {
        commit('SET_LOGIN_ERROR', err.message || '로그인에 실패했습니다')
        throw err
      } finally {
        commit('SET_LOGIN_LOADING', false)
      }
    },

    /**
     * 로그아웃
     */
    async logout({ commit, state }) {
      try {
        if (state.accessToken) {
          await authApi.logout()
        }
      } catch { /* 서버 에러 무시 */ } finally {
        commit('CLEAR_AUTH')
      }
    },

    /**
     * 토큰 갱신
     * @returns {Promise<string>} 새 Access Token
     */
    async refresh({ commit, state }) {
      if (!state.refreshToken) throw new Error('No refresh token')
      const data = await authApi.refreshToken(state.refreshToken)
      commit('SET_AUTH', {
        accessToken: data.access_token,
        refreshToken: data.refresh_token || state.refreshToken,
        user: data.user || state.user
      })
      return data.access_token
    },

    /**
     * 사용자 정보 갱신 (GET /me)
     */
    async fetchMe({ commit }) {
      const user = await authApi.getMe()
      commit('SET_USER', user)
      return user
    },

    /**
     * 비밀번호 변경
     */
    async changePassword(_, { currentPassword, newPassword }) {
      return authApi.changePassword(currentPassword, newPassword)
    },

    /**
     * 앱 초기화 시 토큰 검증
     * localStorage에 토큰이 있으면 /me 호출하여 유효성 확인
     */
    async initAuth({ commit, state, dispatch }) {
      if (!state.accessToken) return false
      try {
        await dispatch('fetchMe')
        return true
      } catch {
        commit('CLEAR_AUTH')
        return false
      }
    }
  }
}
```

### 4.5 `frontend/src/api/index.js` 수정

주석 처리된 인터셉터를 활성화하고, 401 → 자동 갱신 로직을 추가합니다.

**변경 사항**:

```javascript
// ===== 요청 인터셉터 변경 =====
// 기존 (주석):
//   const token = localStorage.getItem('token')
//   if (token) { config.headers.Authorization = `Bearer ${token}` }

// 변경:
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('mureum_access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// ===== 응답 인터셉터 — 401 자동 갱신 추가 =====
// 기존 에러 핸들러 앞에 401 처리 로직 삽입:

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error)
    else resolve(token)
  })
  failedQueue = []
}

// 에러 인터셉터에 추가:
(error) => {
  const originalRequest = error.config

  // 401 Unauthorized → 토큰 갱신 시도
  if (error.response?.status === 401 && !originalRequest._retry) {
    if (isRefreshing) {
      return new Promise((resolve, reject) => {
        failedQueue.push({ resolve, reject })
      }).then(token => {
        originalRequest.headers.Authorization = `Bearer ${token}`
        return apiClient(originalRequest)
      })
    }

    originalRequest._retry = true
    isRefreshing = true

    const refreshToken = localStorage.getItem('mureum_refresh_token')
    if (!refreshToken) {
      // Refresh Token 없음 → 로그인 페이지로
      window.location.href = '/login'
      return Promise.reject(error)
    }

    return apiClient.post('/api/v1/auth/refresh', {
      refresh_token: refreshToken
    }).then(data => {
      const newToken = data.access_token
      localStorage.setItem('mureum_access_token', newToken)
      if (data.refresh_token) {
        localStorage.setItem('mureum_refresh_token', data.refresh_token)
      }
      originalRequest.headers.Authorization = `Bearer ${newToken}`
      processQueue(null, newToken)
      return apiClient(originalRequest)
    }).catch(err => {
      processQueue(err, null)
      // Refresh 실패 → 토큰 전부 삭제 + 로그인 페이지
      localStorage.removeItem('mureum_access_token')
      localStorage.removeItem('mureum_refresh_token')
      localStorage.removeItem('mureum_user')
      window.location.href = '/login'
      return Promise.reject(err)
    }).finally(() => {
      isRefreshing = false
    })
  }

  // 403 Forbidden → 권한 부족 (기존 에러 핸들러에 위임)
  // ... 기존 에러 처리 로직 유지
}
```

### 4.6 Vuex Store 등록

`frontend/src/store/index.js`에 auth 모듈 추가:

```javascript
import auth from './modules/auth'

// modules에 추가:
modules: {
  app,
  chat,
  document,
  auth  // ← 추가
}
```

### 4.7 검증 항목

- [ ] `authApi.login('admin', 'admin123!')` 호출 → TokenResponse 수신
- [ ] localStorage에 `mureum_access_token`, `mureum_refresh_token`, `mureum_user` 저장됨
- [ ] 후속 API 요청에 `Authorization: Bearer <token>` 헤더 자동 첨부
- [ ] 401 응답 시 자동 refresh → 재요청 성공

---

## 5. Step 2: 로그인 화면

### 5.1 목표

로그인 페이지(`LoginView.vue`)를 구현하고 라우터에 등록합니다.

### 5.2 산출물

```
신규:
  frontend/src/views/LoginView.vue      # 로그인 페이지

수정:
  frontend/src/router/index.js          # /login 라우트 추가
```

### 5.3 `frontend/src/views/LoginView.vue`

**UI 설계**:

```
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│                     ┌────────────────────┐                   │
│                     │   🤖 MUREUM         │                   │
│                     │   AI 지식 도우미     │                   │
│                     │                     │                   │
│                     │  ┌───────────────┐  │                   │
│                     │  │ 아이디         │  │                   │
│                     │  └───────────────┘  │                   │
│                     │  ┌───────────────┐  │                   │
│                     │  │ 비밀번호       │  │                   │
│                     │  └───────────────┘  │                   │
│                     │                     │                   │
│                     │  [    로그인     ]   │                   │
│                     │                     │                   │
│                     └────────────────────┘                   │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

**컴포넌트 설계**:

```vue
<template>
  <div class="login-container">
    <div class="login-card">
      <!-- 로고 + 타이틀 -->
      <div class="login-header">
        <el-icon :size="48" color="#409eff"><ChatDotRound /></el-icon>
        <h1 class="login-title">MUREUM</h1>
        <p class="login-subtitle">AI 지식 도우미</p>
      </div>

      <!-- 로그인 폼 -->
      <el-form ref="formRef" :model="form" :rules="rules" @submit.prevent="handleLogin">
        <el-form-item prop="loginId">
          <el-input v-model="form.loginId" placeholder="아이디" prefix-icon="User" size="large" />
        </el-form-item>
        <el-form-item prop="password">
          <el-input v-model="form.password" type="password" placeholder="비밀번호"
                    prefix-icon="Lock" size="large" show-password
                    @keyup.enter="handleLogin" />
        </el-form-item>

        <!-- 에러 메시지 -->
        <el-alert v-if="loginError" :title="loginError" type="error"
                  show-icon :closable="false" class="login-error" />

        <!-- 로그인 버튼 -->
        <el-button type="primary" size="large" :loading="loginLoading"
                   @click="handleLogin" class="login-btn">
          로그인
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ChatDotRound } from '@element-plus/icons-vue'

const store = useStore()
const router = useRouter()
const formRef = ref(null)

const form = reactive({ loginId: '', password: '' })
const rules = {
  loginId: [{ required: true, message: '아이디를 입력해주세요', trigger: 'blur' }],
  password: [{ required: true, message: '비밀번호를 입력해주세요', trigger: 'blur' }]
}

const loginLoading = computed(() => store.state.auth.loginLoading)
const loginError = computed(() => store.state.auth.loginError)

const handleLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    const user = await store.dispatch('auth/login', {
      loginId: form.loginId,
      password: form.password
    })
    // 권한에 따라 리다이렉트
    const canAdmin = store.getters['auth/canAccessAdmin']
    router.push(canAdmin ? '/admin' : '/chat')
  } catch {
    // loginError가 store에 설정됨
  }
}
</script>
```

**스타일**: 다크 테마 기본, 중앙 카드 레이아웃, mixins의 `_forms.scss` 참조

### 5.4 `router/index.js` 수정

```javascript
// 라우트 추가 (최상위, /chat 위에)
{
  path: '/login',
  name: 'Login',
  component: () => import('@/views/LoginView.vue'),
  meta: { title: '로그인', public: true }
},
```

### 5.5 검증 항목

- [ ] `/login` 페이지 렌더링 확인
- [ ] 올바른 계정 입력 → 로그인 성공 → `/admin` 또는 `/chat`으로 이동
- [ ] 잘못된 계정 입력 → 에러 메시지 표시
- [ ] Enter 키로 로그인 가능
- [ ] 이미 로그인된 상태에서 `/login` 접근 시 리다이렉트 (Step 3에서 구현)

---

## 6. Step 3: 라우터 가드 + 레이아웃 UI

### 6.1 목표

- Router `beforeEach` 가드 활성화 — 관리 페이지 접근 시 인증 확인
- AppSidebar 메뉴를 권한 기반으로 필터링
- AppHeader에 로그인 사용자 정보 + 로그아웃 버튼 표시

### 6.2 산출물

```
수정:
  frontend/src/router/index.js                    # beforeEach 가드 구현
  frontend/src/components/layout/AppSidebar.vue   # 권한 기반 메뉴 필터링
  frontend/src/components/layout/AppHeader.vue    # 사용자 드롭다운 활성화
```

### 6.3 `router/index.js` — 라우터 가드

기존 주석 처리된 `beforeEach`를 교체합니다:

```javascript
import store from '@/store'

router.beforeEach(async (to, from, next) => {
  const isAuthenticated = store.getters['auth/isAuthenticated']

  // 1. 로그인 페이지: 이미 인증됐으면 리다이렉트
  if (to.path === '/login') {
    if (isAuthenticated) {
      const canAdmin = store.getters['auth/canAccessAdmin']
      return next(canAdmin ? '/admin' : '/chat')
    }
    return next()
  }

  // 2. 공개 페이지: 인증 불필요
  if (to.meta.public) return next()

  // 3. 관리자 페이지: 인증 + 관리 권한 필요
  if (to.meta.requiresAdmin) {
    if (!isAuthenticated) return next('/login')
    const canAdmin = store.getters['auth/canAccessAdmin']
    if (!canAdmin) return next('/chat')
    return next()
  }

  // 4. 일반 페이지 (/chat): 통과 (Phase 3a 선택적 모드)
  next()
})
```

> **주의**: Step 7에서 인증 필수 모드 전환 시, 일반 페이지도 인증을 요구하도록 변경합니다.

### 6.4 `AppSidebar.vue` — 권한 기반 메뉴 필터링

**메뉴 아이템을 동적으로 구성**합니다:

```javascript
// <script setup> 내부
const hasPermission = (code) => store.getters['auth/hasPermission'](code)

const menuItems = computed(() => {
  const items = []

  // 지식문서 관리: document:read 이상
  if (hasPermission('document:read')) {
    items.push({ index: '/admin/documents', icon: 'Document', title: '지식문서 관리' })
  }

  // 자연어 검색: 관리 권한이 하나라도 있으면
  items.push({ index: '/admin/chat', icon: 'ChatDotSquare', title: '자연어 검색' })

  // 시스템 설정: admin:settings
  if (hasPermission('admin:settings')) {
    items.push({ index: '/admin/settings', icon: 'Setting', title: '시스템 설정' })
  }

  // 코드 관리: admin:settings
  if (hasPermission('admin:settings')) {
    items.push({ index: '/admin/codes', icon: 'Grid', title: '코드 관리' })
  }

  // 검색 이력: 모든 관리자
  items.push({ index: '/admin/history', icon: 'Histogram', title: '검색 이력(Tracing)' })

  // 사용자 관리: admin:users (Step 4 이후)
  if (hasPermission('admin:users')) {
    items.push({ index: '/admin/users', icon: 'User', title: '사용자 관리' })
  }

  // 역할 관리: admin:users (Step 5 이후)
  if (hasPermission('admin:users')) {
    items.push({ index: '/admin/roles', icon: 'Key', title: '역할 관리' })
  }

  // 테넌트 관리: admin:tenants (Step 6 이후)
  if (hasPermission('admin:tenants')) {
    items.push({ index: '/admin/tenants', icon: 'OfficeBuilding', title: '테넌트 관리' })
  }

  return items
})
```

**template 변경**:

```html
<!-- 기존 정적 el-menu-item들을 동적으로 교체 -->
<el-menu-item v-for="item in menuItems" :key="item.index" :index="item.index">
  <el-icon><component :is="item.icon" /></el-icon>
  <template #title>{{ item.title }}</template>
</el-menu-item>
```

### 6.5 `AppHeader.vue` — 사용자 드롭다운

주석 처리된 사용자 드롭다운을 활성화합니다:

```html
<!-- 기존 주석 제거 → 활성화 -->
<el-dropdown v-if="currentUser" @command="handleUserCommand">
  <div class="user-info">
    <el-avatar :size="28" icon="UserFilled" />
    <span class="user-name">{{ currentUser.display_name || currentUser.login_id }}</span>
  </div>
  <template #dropdown>
    <el-dropdown-menu>
      <el-dropdown-item disabled>
        <el-tag size="small" type="info">{{ currentUser.scope_type }}</el-tag>
        {{ currentUser.roles?.join(', ') }}
      </el-dropdown-item>
      <el-dropdown-item command="password" divided>비밀번호 변경</el-dropdown-item>
      <el-dropdown-item command="logout">로그아웃</el-dropdown-item>
    </el-dropdown-menu>
  </template>
</el-dropdown>
```

```javascript
// <script setup> 추가
const currentUser = computed(() => store.getters['auth/currentUser'])

const handleUserCommand = async (command) => {
  if (command === 'logout') {
    await store.dispatch('auth/logout')
    router.push('/login')
  } else if (command === 'password') {
    // 비밀번호 변경 다이얼로그 (간단한 ElMessageBox 활용)
    // ... 또는 별도 컴포넌트
  }
}
```

### 6.6 역할별 메뉴 가시성 매트릭스

| 메뉴 | 필요 권한 | SYSTEM_ADMIN | TENANT_ADMIN | USER |
|------|----------|:---:|:---:|:---:|
| 지식문서 관리 | `document:read` | O | O | O |
| 자연어 검색 | (기본 표시) | O | O | O |
| 시스템 설정 | `admin:settings` | O | | |
| 코드 관리 | `admin:settings` | O | | |
| 검색 이력 | (기본 표시) | O | O | O |
| 사용자 관리 | `admin:users` | O | O | |
| 역할 관리 | `admin:users` | O | O | |
| 테넌트 관리 | `admin:tenants` | O | | |

### 6.7 검증 항목

- [ ] 미인증 상태에서 `/admin` 접근 → `/login`으로 리다이렉트
- [ ] SYSTEM_ADMIN 로그인 → 모든 메뉴 표시
- [ ] TENANT_ADMIN 로그인 → 시스템 설정, 코드 관리, 테넌트 관리 숨김
- [ ] USER 로그인 → `/admin` 접근 불가, `/chat`으로 리다이렉트
- [ ] AppHeader에 로그인 사용자명 표시
- [ ] 로그아웃 → `/login` 이동 + localStorage 정리

---

## 7. Step 4: 사용자 관리 API + 화면

### 7.1 목표

백엔드 사용자 관리 API와 프론트엔드 사용자 관리 화면을 구현합니다.

### 7.2 산출물

```
Backend 신규:
  app/models/user.py                    # 사용자 Pydantic 모델
  app/api/services/user_service.py      # 사용자 CRUD 서비스
  app/api/routes/users.py               # 사용자 관리 API 엔드포인트

Frontend 신규:
  frontend/src/api/users.js             # 사용자 관리 API 클라이언트
  frontend/src/views/admin/UsersView.vue # 사용자 관리 화면

Backend 수정:
  app/main.py                           # users 라우터 등록
```

### 7.3 Backend API 설계

**`app/api/routes/users.py`** — `prefix="/api/v1/users"`, `tags=["users"]`

| Method | Endpoint | Description | 필요 권한 |
|--------|----------|-------------|-----------|
| GET | `/` | 사용자 목록 (scope 기반 필터) | `admin:users` |
| POST | `/` | 사용자 생성 | `admin:users` |
| GET | `/{user_id}` | 사용자 상세 | `admin:users` 또는 본인 |
| PUT | `/{user_id}` | 사용자 수정 | `admin:users` |
| DELETE | `/{user_id}` | 사용자 비활성화 (soft delete) | `admin:users` |
| PUT | `/{user_id}/roles` | 역할 할당/변경 | `admin:users` |
| PUT | `/{user_id}/reset-password` | 비밀번호 초기화 | `admin:users` |

**scope_type 기반 데이터 범위**:
- `GLOBAL`: 전체 사용자 조회/관리
- `TENANT`: 자기 테넌트 사용자만 조회/관리
- `USER`: 본인 정보만 조회

### 7.4 `app/models/user.py`

```python
"""사용자 관리 스키마"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class UserListItem(BaseModel):
    """사용자 목록 아이템"""
    user_id: int
    login_id: str
    display_name: Optional[str] = None
    email: str
    tenant_id: Optional[int] = None
    tenant_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False
    roles: List[str] = Field(default_factory=list)
    last_login_at: Optional[str] = None
    created_at: Optional[str] = None


class UserCreate(BaseModel):
    """사용자 생성 요청"""
    login_id: str = Field(..., min_length=3, max_length=100)
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = Field(None, max_length=100)
    tenant_id: Optional[int] = None
    role_ids: List[int] = Field(default_factory=list)


class UserUpdate(BaseModel):
    """사용자 수정 요청"""
    display_name: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    tenant_id: Optional[int] = None


class UserRoleAssign(BaseModel):
    """역할 할당 요청"""
    role_ids: List[int] = Field(..., min_length=1)


class ResetPasswordRequest(BaseModel):
    """비밀번호 초기화 요청"""
    new_password: str = Field(..., min_length=8)
```

### 7.5 `app/api/services/user_service.py` 핵심 로직

```python
class UserService:
    """사용자 CRUD 서비스 (scope_type 기반 데이터 범위 제한)"""

    def list_users(self, current_user: UserContext, page=1, size=20, keyword=None):
        """scope_type에 따라 조회 범위 자동 제한"""
        # GLOBAL → 전체, TENANT → 자기 테넌트, USER → 본인만
        ...

    def create_user(self, current_user: UserContext, data: UserCreate):
        """사용자 생성 — TENANT scope는 자기 테넌트에만"""
        # TENANT_ADMIN: data.tenant_id = current_user.tenant_id (강제)
        ...

    def update_user(self, current_user: UserContext, user_id: int, data: UserUpdate):
        """사용자 수정 — scope 검증 후 업데이트"""
        ...

    def delete_user(self, current_user: UserContext, user_id: int):
        """soft delete (is_active = false)"""
        ...

    def assign_roles(self, current_user: UserContext, user_id: int, role_ids: list):
        """역할 할당 — TENANT scope는 TENANT/USER 역할만 부여 가능"""
        ...
```

### 7.6 Frontend `UsersView.vue`

**UI 구성**:

```
┌─────────────────────────────────────────────────────────────┐
│  사용자 관리                                    [+ 사용자 추가] │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ 검색: [_______________] [검색]   상태: [전체 ▼]          │ │
│ └─────────────────────────────────────────────────────────┘ │
│ ┌─────┬────────┬────────┬────────┬────────┬────────┬─────┐ │
│ │ ID  │ 아이디  │ 이름   │ 테넌트  │ 역할   │ 상태   │ 액션 │ │
│ ├─────┼────────┼────────┼────────┼────────┼────────┼─────┤ │
│ │ 1   │ admin  │ 관리자 │ -      │ SYS..  │ 활성   │ ✏ 🗑 │ │
│ │ 2   │ user1  │ 김철수 │ A사    │ TENA.. │ 활성   │ ✏ 🗑 │ │
│ └─────┴────────┴────────┴────────┴────────┴────────┴─────┘ │
│                    [< 1 2 3 >]                               │
└─────────────────────────────────────────────────────────────┘
```

**핵심 기능**:
- 테이블 형태 사용자 목록 (페이징)
- 검색/필터 (키워드, 상태, 테넌트)
- 사용자 추가 다이얼로그 (ElDialog)
- 사용자 수정 다이얼로그
- 역할 할당 (ElSelect multi)
- 비밀번호 초기화
- 비활성화 (soft delete)

### 7.7 검증 항목

- [ ] SYSTEM_ADMIN: 전체 사용자 목록 조회 가능
- [ ] TENANT_ADMIN: 자기 테넌트 사용자만 표시
- [ ] 사용자 생성 → 목록에 반영
- [ ] 사용자 수정 → 변경사항 반영
- [ ] 역할 할당 → 사용자의 역할 변경
- [ ] 비밀번호 초기화 → 성공 메시지
- [ ] 비활성화 → 상태 변경 (삭제 아님)

---

## 8. Step 5: 역할 관리 API + 화면

### 8.1 목표

역할(Role) CRUD와 역할에 대한 권한(Permission) 할당 기능을 구현합니다.

### 8.2 산출물

```
Backend 신규:
  app/models/role.py                    # 역할/권한 Pydantic 모델
  app/api/services/role_service.py      # 역할/권한 CRUD 서비스
  app/api/routes/roles.py              # 역할 관리 API

Frontend 신규:
  frontend/src/api/roles.js             # 역할 관리 API 클라이언트
  frontend/src/views/admin/RolesView.vue # 역할 관리 화면

Backend 수정:
  app/main.py                           # roles 라우터 등록
```

### 8.3 Backend API 설계

**`app/api/routes/roles.py`** — `prefix="/api/v1/roles"`, `tags=["roles"]`

| Method | Endpoint | Description | 필요 권한 |
|--------|----------|-------------|-----------|
| GET | `/` | 역할 목록 | `admin:users` |
| POST | `/` | 역할 생성 | `admin:users` (GLOBAL만) |
| GET | `/{role_id}` | 역할 상세 (권한 포함) | `admin:users` |
| PUT | `/{role_id}` | 역할 수정 | `admin:users` (GLOBAL만) |
| DELETE | `/{role_id}` | 역할 삭제 (`is_system=false`만) | `admin:users` (GLOBAL만) |
| PUT | `/{role_id}/permissions` | 역할에 권한 할당 | `admin:users` (GLOBAL만) |
| GET | `/permissions` | 전체 권한 목록 | `admin:users` |

> **TENANT_ADMIN**은 역할 목록 조회만 가능합니다 (역할 생성/수정/삭제는 SYSTEM_ADMIN만).

### 8.4 `app/models/role.py`

```python
"""역할/권한 관리 스키마"""
from typing import List, Optional
from pydantic import BaseModel, Field


class PermissionItem(BaseModel):
    """권한 아이템"""
    permission_id: int
    permission_code: str
    permission_name: str
    category: str


class RoleListItem(BaseModel):
    """역할 목록 아이템"""
    role_id: int
    role_code: str
    role_name: str
    scope_type: str
    is_system: bool = False
    user_count: int = 0
    permission_count: int = 0


class RoleDetail(RoleListItem):
    """역할 상세 (권한 포함)"""
    description: Optional[str] = None
    permissions: List[PermissionItem] = Field(default_factory=list)


class RoleCreate(BaseModel):
    """역할 생성 요청"""
    role_code: str = Field(..., min_length=2, max_length=50)
    role_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    scope_type: str = Field(..., pattern="^(GLOBAL|TENANT|USER)$")
    permission_ids: List[int] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    """역할 수정 요청"""
    role_name: Optional[str] = None
    description: Optional[str] = None
    scope_type: Optional[str] = None


class RolePermissionAssign(BaseModel):
    """역할 권한 할당 요청"""
    permission_ids: List[int] = Field(..., min_length=0)
```

### 8.5 Frontend `RolesView.vue`

**UI 구성**:

```
┌──────────────────────────────────────────────────────────────┐
│  역할 관리                                      [+ 역할 추가]  │
│ ┌────────┬───────┬─────────┬──────┬──────┬──────┬──────────┐ │
│ │역할 코드│역할명 │ 범위    │시스템│사용자│권한수│ 액션     │ │
│ ├────────┼───────┼─────────┼──────┼──────┼──────┼──────────┤ │
│ │SYS_ADM │시스템…│ GLOBAL  │ ✓   │  1   │  9   │ 👁       │ │
│ │TEN_ADM │테넌트…│ TENANT  │ ✓   │  3   │  6   │ 👁       │ │
│ │USER    │일반…  │ USER    │ ✓   │ 10   │  3   │ 👁       │ │
│ │CUSTOM  │감사자 │ TENANT  │     │  2   │  4   │ ✏ 🗑     │ │
│ └────────┴───────┴─────────┴──────┴──────┴──────┴──────────┘ │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │  역할 상세: CUSTOM (감사자)                              │   │
│  │  ┌──────────────────────────────────────────────────┐  │   │
│  │  │  권한 할당                                        │  │   │
│  │  │  ☑ nl2sql:execute    ☑ rag:search                │  │   │
│  │  │  ☑ document:read     ☐ document:write            │  │   │
│  │  │  ☐ document:delete   ☐ admin:settings            │  │   │
│  │  │  ☐ admin:users       ☐ admin:tenants             │  │   │
│  │  │  ☑ nl2sql:view_all                               │  │   │
│  │  └──────────────────────────────────────────────────┘  │   │
│  │  [저장]  [취소]                                          │   │
│  └────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

**핵심 기능**:
- 역할 목록 테이블 (사용자 수, 권한 수 표시)
- 시스템 역할(`is_system=true`)은 수정/삭제 불가 (읽기 전용)
- 역할 상세 패널 — 권한 체크박스 할당
- 카테고리별 권한 그룹핑 (nl2sql, rag, document, admin)

### 8.6 검증 항목

- [ ] 역할 목록 조회 (사용자 수, 권한 수 포함)
- [ ] 커스텀 역할 생성 → 목록 반영
- [ ] 역할에 권한 할당 → 저장 후 확인
- [ ] 시스템 역할 수정/삭제 시 에러 메시지
- [ ] TENANT_ADMIN은 조회만 가능 (생성/수정/삭제 버튼 숨김)

---

## 9. Step 6: 테넌트 관리 API + 화면

### 9.1 목표

테넌트(Tenant) CRUD를 구현합니다. SYSTEM_ADMIN만 접근 가능합니다.

### 9.2 산출물

```
Backend 신규:
  app/models/tenant.py                  # 테넌트 Pydantic 모델
  app/api/services/tenant_service.py    # 테넌트 CRUD 서비스
  app/api/routes/tenants.py             # 테넌트 관리 API

Frontend 신규:
  frontend/src/api/tenants.js           # 테넌트 관리 API 클라이언트
  frontend/src/views/admin/TenantsView.vue # 테넌트 관리 화면

Backend 수정:
  app/main.py                           # tenants 라우터 등록
```

### 9.3 Backend API 설계

**`app/api/routes/tenants.py`** — `prefix="/api/v1/tenants"`, `tags=["tenants"]`

| Method | Endpoint | Description | 필요 권한 |
|--------|----------|-------------|-----------|
| GET | `/` | 테넌트 목록 | `admin:tenants` |
| POST | `/` | 테넌트 생성 | `admin:tenants` |
| GET | `/{tenant_id}` | 테넌트 상세 | `admin:tenants` |
| PUT | `/{tenant_id}` | 테넌트 수정 | `admin:tenants` |
| DELETE | `/{tenant_id}` | 테넌트 비활성화 | `admin:tenants` |

### 9.4 `app/models/tenant.py`

```python
"""테넌트 관리 스키마"""
from typing import Optional
from pydantic import BaseModel, Field


class TenantListItem(BaseModel):
    """테넌트 목록 아이템"""
    tenant_id: int
    tenant_code: str
    tenant_name: str
    is_active: bool = True
    user_count: int = 0
    created_at: Optional[str] = None


class TenantCreate(BaseModel):
    """테넌트 생성 요청"""
    tenant_code: str = Field(..., min_length=2, max_length=50)
    tenant_name: str = Field(..., min_length=1, max_length=200)
    metadata: Optional[dict] = None


class TenantUpdate(BaseModel):
    """테넌트 수정 요청"""
    tenant_name: Optional[str] = None
    is_active: Optional[bool] = None
    metadata: Optional[dict] = None
```

### 9.5 Frontend `TenantsView.vue`

**UI 구성**:

```
┌──────────────────────────────────────────────────────────────┐
│  테넌트 관리                                  [+ 테넌트 추가]  │
│ ┌────────┬──────────┬──────┬────────┬──────────┬──────────┐  │
│ │코드    │ 이름     │ 상태 │ 사용자수│ 생성일    │ 액션     │  │
│ ├────────┼──────────┼──────┼────────┼──────────┼──────────┤  │
│ │COMP_A  │ A회사    │ 활성 │ 15     │ 2026-01  │ ✏ 🗑     │  │
│ │COMP_B  │ B회사    │ 활성 │  8     │ 2026-02  │ ✏ 🗑     │  │
│ └────────┴──────────┴──────┴────────┴──────────┴──────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### 9.6 검증 항목

- [ ] SYSTEM_ADMIN만 테넌트 관리 메뉴 접근 가능
- [ ] 테넌트 생성 → 목록 반영
- [ ] 테넌트 수정 → 이름 변경 확인
- [ ] 테넌트 비활성화 → 상태 변경
- [ ] 테넌트별 사용자 수 표시

---

## 10. Step 7: 인증 필수 모드 전환

### 10.1 목표

Phase 3a(선택적 모드)에서 Phase 3b(필수 모드)로 전환합니다. 인증되지 않은 사용자는 모든 API 호출이 차단됩니다.

### 10.2 산출물

```
수정:
  app/middleware/auth.py                # Phase 3b: 필수 모드 전환
  frontend/src/router/index.js          # /chat도 인증 필요
```

### 10.3 `app/middleware/auth.py` 변경

```python
class AuthMiddleware(BaseMiddleware):
    """인증 미들웨어 (Phase 3b: 필수 모드)"""

    EXCLUDE_PATHS: Set[str] = {
        "/", "/health", "/docs", "/redoc", "/openapi.json", "/favicon.ico",
        "/api/v1/auth/login", "/api/v1/auth/refresh",
    }
    EXCLUDE_PREFIXES: Set[str] = {"/static/"}

    async def process_request(self, request: Request, call_next) -> Response:
        path = request.url.path
        request.state.current_user = None

        # 제외 경로는 통과
        if self._is_excluded(path):
            return await call_next(request)

        # Bearer 토큰 추출
        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            # Phase 3b: 토큰 없으면 차단
            return JSONResponse(
                status_code=401,
                content={"success": False, "data": None,
                         "error": {"code": "UNAUTHORIZED", "message": "인증이 필요합니다"}}
            )

        token = auth_header[7:]
        try:
            payload = verify_token(token)
            if payload.token_type == "access":
                request.state.current_user = UserContext(...)
            else:
                return JSONResponse(status_code=401, ...)
        except Exception:
            return JSONResponse(status_code=401, ...)

        return await call_next(request)

    def _is_excluded(self, path: str) -> bool:
        if path in self.EXCLUDE_PATHS:
            return True
        return any(path.startswith(prefix) for prefix in self.EXCLUDE_PREFIXES)
```

### 10.4 `router/index.js` 변경

```javascript
// Step 7: 일반 페이지도 인증 필요
router.beforeEach(async (to, from, next) => {
  const isAuthenticated = store.getters['auth/isAuthenticated']

  // 공개 페이지만 통과
  if (to.meta.public) return next()

  // 로그인 페이지 처리
  if (to.path === '/login') {
    return isAuthenticated ? next(getDefaultRoute()) : next()
  }

  // 미인증 → 로그인 (모든 페이지)
  if (!isAuthenticated) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  // 관리자 페이지 권한 확인
  if (to.meta.requiresAdmin) {
    const canAdmin = store.getters['auth/canAccessAdmin']
    if (!canAdmin) return next('/chat')
  }

  next()
})
```

### 10.5 검증 항목

- [ ] 토큰 없이 API 호출 → 401
- [ ] 만료된 토큰으로 API 호출 → 401 → 자동 refresh → 재시도 성공
- [ ] Refresh Token도 만료 → `/login`으로 리다이렉트
- [ ] `/chat` 미인증 접근 → `/login?redirect=/chat`
- [ ] 로그인 후 `redirect` 파라미터가 있으면 해당 경로로 이동

---

## 11. 산출물 총괄

### 11.1 전체 파일 목록

```
=== Step 1: 인증 인프라 (FE) ===
[신규] frontend/src/api/auth.js
[신규] frontend/src/store/modules/auth.js
[수정] frontend/src/api/index.js
[수정] frontend/src/store/index.js            # auth 모듈 등록

=== Step 2: 로그인 화면 (FE) ===
[신규] frontend/src/views/LoginView.vue
[수정] frontend/src/router/index.js           # /login 라우트 추가

=== Step 3: 라우터 가드 + 레이아웃 (FE) ===
[수정] frontend/src/router/index.js           # beforeEach 가드
[수정] frontend/src/components/layout/AppSidebar.vue  # 권한 메뉴 필터
[수정] frontend/src/components/layout/AppHeader.vue   # 사용자 드롭다운

=== Step 4: 사용자 관리 (BE + FE) ===
[신규] app/models/user.py
[신규] app/api/services/user_service.py
[신규] app/api/routes/users.py
[신규] frontend/src/api/users.js
[신규] frontend/src/views/admin/UsersView.vue
[수정] app/main.py                            # users 라우터 등록
[수정] frontend/src/router/index.js           # /admin/users 라우트

=== Step 5: 역할 관리 (BE + FE) ===
[신규] app/models/role.py
[신규] app/api/services/role_service.py
[신규] app/api/routes/roles.py
[신규] frontend/src/api/roles.js
[신규] frontend/src/views/admin/RolesView.vue
[수정] app/main.py                            # roles 라우터 등록
[수정] frontend/src/router/index.js           # /admin/roles 라우트

=== Step 6: 테넌트 관리 (BE + FE) ===
[신규] app/models/tenant.py
[신규] app/api/services/tenant_service.py
[신규] app/api/routes/tenants.py
[신규] frontend/src/api/tenants.js
[신규] frontend/src/views/admin/TenantsView.vue
[수정] app/main.py                            # tenants 라우터 등록
[수정] frontend/src/router/index.js           # /admin/tenants 라우트

=== Step 7: 인증 필수 모드 (BE + FE) ===
[수정] app/middleware/auth.py                 # Phase 3a → 3b
[수정] frontend/src/router/index.js           # 모든 페이지 인증 필요
```

### 11.2 파일 수 요약

| 구분 | 신규 | 수정 | 합계 |
|------|:----:|:----:|:----:|
| Step 1 | 2 | 2 | 4 |
| Step 2 | 1 | 1 | 2 |
| Step 3 | 0 | 3 | 3 |
| Step 4 | 5 | 2 | 7 |
| Step 5 | 5 | 2 | 7 |
| Step 6 | 5 | 2 | 7 |
| Step 7 | 0 | 2 | 2 |
| **합계** | **18** | **14** | **32** |

---

## 12. 검증 계획

### 12.1 Step별 검증 흐름

```
Step 1+2: 로그인 → 토큰 저장 → API 호출 헤더 확인
     ↓
Step 3:   라우터 가드 → 메뉴 필터링 → 로그아웃
     ↓
Step 4:   사용자 CRUD → scope 기반 필터링
     ↓
Step 5:   역할 CRUD → 권한 할당
     ↓
Step 6:   테넌트 CRUD
     ↓
Step 7:   필수 모드 → 미인증 차단 → 자동 갱신
```

### 12.2 통합 시나리오 테스트

| # | 시나리오 | 예상 결과 |
|---|----------|----------|
| 1 | SYSTEM_ADMIN 로그인 | 모든 메뉴 표시, 전체 데이터 접근 |
| 2 | TENANT_ADMIN 로그인 | 시스템 설정/코드 관리/테넌트 관리 숨김, 테넌트 데이터만 |
| 3 | USER 로그인 | `/chat`으로 이동, 관리 페이지 접근 불가 |
| 4 | 토큰 만료 → 자동 갱신 | 사용자 모르게 토큰 갱신 후 재요청 |
| 5 | Refresh Token 만료 | 로그인 페이지로 리다이렉트 |
| 6 | 사용자 생성 → 역할 부여 → 로그인 | 부여된 역할의 메뉴만 표시 |
| 7 | 역할 권한 변경 → 토큰 갱신 | 다음 Access Token부터 새 권한 반영 |
| 8 | 테넌트 비활성화 → 소속 사용자 로그인 | 로그인 실패 |

### 12.3 테스트 계정 (Phase 1에서 생성)

| login_id | 역할 | scope_type | 테스트 용도 |
|----------|------|-----------|------------|
| `admin` | SYSTEM_ADMIN | GLOBAL | 전체 관리 |
| `tenant_admin` | TENANT_ADMIN | TENANT | 테넌트 범위 테스트 |
| `user1` | USER | USER | 일반 사용자 테스트 |

---

## 부록: app.js 정리

Step 1에서 `auth.js` 모듈 도입 시, `app.js`의 인증 관련 코드를 정리합니다:

### 제거 대상 (app.js → auth.js로 이전)

```javascript
// state에서 제거
user: null,           // → auth.user
userRole: 'admin',    // → auth.roles 기반으로 판단

// mutations에서 제거
SET_USER,             // → auth.SET_AUTH
SET_ROLE,             // → auth.roles

// getters에서 변경
isAdmin: (state) => state.userRole === 'admin',
// → isAdmin: (state, getters, rootState, rootGetters) => rootGetters['auth/canAccessAdmin']

isAuthenticated: (state) => state.user !== null,
// → isAuthenticated: (state, getters, rootState, rootGetters) => rootGetters['auth/isAuthenticated']

// actions에서 제거
async login({ commit }, credentials) { ... },  // → auth/login
logout({ commit }) { ... },                    // → auth/logout
```

> **점진적 마이그레이션**: Step 1에서 auth 모듈을 추가하고, Step 3에서 app.js의 인증 코드를 정리합니다.
> 기존 코드가 `app/isAdmin`을 참조하는 곳이 있으면 `auth/canAccessAdmin`으로 변경합니다.
