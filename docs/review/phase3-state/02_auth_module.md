# 2. auth 모듈 - 인증과 권한

> **파일 위치**: `frontend/src/store/modules/auth.js` (227줄)

## 이 모듈이 하는 일

**앱의 보안 핵심**입니다. "누가 로그인했는가? 어떤 권한이 있는가?"를 관리합니다.

```
auth 모듈이 관리하는 것:
├── 로그인/로그아웃
├── JWT 토큰 (Access + Refresh)
├── 사용자 정보 (이름, 역할, 메뉴 권한)
└── localStorage 영속성 (새로고침해도 유지)
```

## 전체 구조 한눈에

```
┌─── auth 모듈 ─────────────────────────────────────┐
│                                                    │
│  State:    user, accessToken, refreshToken,        │
│            loginLoading, loginError                 │
│                                                    │
│  Getters:  isAuthenticated, canAccessAdmin,         │
│            hasMenuPermission, landingPage, ...       │
│                                                    │
│  Mutations: SET_AUTH, CLEAR_AUTH, SET_USER,          │
│             SET_LOGIN_LOADING, SET_LOGIN_ERROR       │
│                                                    │
│  Actions:  login, logout, refresh, fetchMe,         │
│            changePassword, initAuth                 │
│                                                    │
│  Helper:   localStorage 읽기/쓰기/삭제              │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## localStorage 헬퍼 함수 (파일 상단)

```javascript
const TOKEN_KEYS = {
  ACCESS: 'mureum_access_token',
  REFRESH: 'mureum_refresh_token',
  USER: 'mureum_user'
}

const getStoredToken = (key) => {
  try { return localStorage.getItem(key) } catch { return null }
}

const getStoredUser = () => {
  try {
    const json = localStorage.getItem(TOKEN_KEYS.USER)
    return json ? JSON.parse(json) : null
  } catch { return null }
}

const saveTokens = (accessToken, refreshToken, user) => { ... }
const clearTokens = () => { ... }
```

**왜 localStorage를 사용하는가?**

```
Vuex Store의 문제:
  브라우저 새로고침 → 메모리가 초기화됨 → 로그인 풀림! 😱

localStorage를 함께 사용하면:
  로그인 → Store + localStorage에 동시 저장
  새로고침 → Store는 초기화되지만, localStorage에서 복원!
  → 로그인 상태 유지! ✅
```

```
┌─── 메모리 (Vuex Store) ───┐    ┌─── 디스크 (localStorage) ───┐
│  state.accessToken         │    │  mureum_access_token         │
│  state.refreshToken        │←──→│  mureum_refresh_token        │
│  state.user                │    │  mureum_user (JSON)          │
└────────────────────────────┘    └──────────────────────────────┘
   새로고침 시 초기화됨              새로고침해도 유지됨!
```

**try/catch를 쓰는 이유**: 프라이빗 브라우징 모드에서 localStorage가 차단될 수 있어서, 에러가 나도 앱이 죽지 않도록 보호합니다.

---

## State - 저장하는 데이터

```javascript
state: () => ({
  user: getStoredUser(),                          // localStorage에서 복원
  accessToken: getStoredToken(TOKEN_KEYS.ACCESS), // localStorage에서 복원
  refreshToken: getStoredToken(TOKEN_KEYS.REFRESH),
  loginLoading: false,    // 로그인 API 호출 중인지
  loginError: null        // 로그인 실패 메시지
})
```

`state`가 함수 `() => ({})` 형태인 이유:
```javascript
// 함수로 하면 모듈이 여러 번 사용되어도 각각 독립된 객체 생성
state: () => ({ user: null })   // ✅ 매번 새 객체

// 객체로 하면 모든 인스턴스가 같은 객체를 공유 (위험!)
state: { user: null }           // ❌ 참조 공유 문제
```

**user 객체의 구조** (서버에서 받아오는 형태):
```javascript
{
  user_id: 1,
  login_id: "admin",
  display_name: "관리자",
  role_code: "GLOBAL",        // 역할: GLOBAL / TENANT / USER
  role_name: "전체 관리자",
  landing_page: "/admin/dashboard",
  menus: [                     // 접근 가능한 메뉴 목록
    { menu_code: "DASHBOARD", can_create: false, can_read: true, ... },
    { menu_code: "USER_MGMT", can_create: true, can_read: true, ... },
    // ...
  ]
}
```

---

## Getters - 가공된 데이터

```javascript
getters: {
  // ① 로그인 여부
  isAuthenticated: (state) => !!state.accessToken && !!state.user,

  // ② 사용자 표시명
  displayName: (state) => state.user?.display_name || state.user?.login_id || '',

  // ③ 메뉴 목록
  menus: (state) => state.user?.menus || [],

  // ④ 역할 코드/이름
  roleCode: (state) => state.user?.role_code || 'USER',
  landingPage: (state) => state.user?.landing_page || '/chat',

  // ⑤ 관리자 접근 가능 여부
  canAccessAdmin: (state) => {
    if (!state.user) return false
    return (state.user.menus?.length || 0) > 0
  },

  // ⑥ 메뉴별 CRUD 권한 체크 (함수를 반환하는 getter!)
  hasMenuPermission: (state) => (menuCode, action = 'read') => {
    if (!state.user?.menus) return false
    const menu = state.user.menus.find(m => m.menu_code === menuCode)
    if (!menu) return false
    return !!menu[`can_${action}`]
  }
}
```

**`hasMenuPermission` 상세 설명:**

이것은 **함수를 반환하는 getter**입니다 (파라미터를 받아야 하므로):

```javascript
// 사용법:
store.getters['auth/hasMenuPermission']('USER_MGMT', 'read')

// 동작 과정:
hasMenuPermission: (state) => (menuCode, action) => { ... }
//                             ↑ 이 부분이 반환되는 함수

// 1단계: getter 호출 → 함수 반환
const checkFn = store.getters['auth/hasMenuPermission']

// 2단계: 반환된 함수에 인자 전달
checkFn('USER_MGMT', 'read')
// → menus에서 menu_code가 'USER_MGMT'인 항목을 찾고
// → 그 항목의 can_read가 true인지 확인

// 실제 데이터 예시:
// menus: [{ menu_code: 'USER_MGMT', can_create: true, can_read: true, can_update: true, can_delete: false }]
// hasMenuPermission('USER_MGMT', 'delete') → false (can_delete = false)
```

---

## Actions - 비동기 비즈니스 로직

### login - 로그인 ⭐

```javascript
async login({ commit, dispatch }, { loginId, password }) {
  commit('SET_LOGIN_LOADING', true)           // 로딩 시작
  commit('SET_LOGIN_ERROR', null)             // 이전 에러 초기화
  try {
    const data = await authApi.login(loginId, password)  // API 호출

    // 이전 사용자의 채팅/대시보드 상태 초기화
    dispatch('chat/clearChat', null, { root: true })
    dispatch('dashboard/clearState', null, { root: true })

    commit('SET_AUTH', {                      // 토큰 + 사용자 저장
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      user: data.user
    })
    return data.user
  } catch (err) {
    // 에러 코드별 한국어 메시지 분기
    if (code === 'ACCOUNT_LOCKED') message = '계정이 잠겼습니다...'
    else if (code === 'UNAUTHORIZED') message = '아이디 또는 비밀번호가...'
    commit('SET_LOGIN_ERROR', message)
    throw err
  } finally {
    commit('SET_LOGIN_LOADING', false)        // 로딩 종료 (성공/실패 무관)
  }
}
```

**흐름도:**
```
LoginView.vue에서 dispatch('auth/login', {loginId, password})
│
├─ SET_LOGIN_LOADING → true (버튼 비활성화, 로딩 표시)
│
├─ authApi.login() → POST /api/v1/auth/login
│   ├─ 성공 → { access_token, refresh_token, user }
│   │         ├─ chat/clearChat (이전 채팅 데이터 정리)
│   │         ├─ SET_AUTH (토큰+사용자 저장 → localStorage도)
│   │         └─ return user
│   │
│   └─ 실패 → { code: 'ACCOUNT_LOCKED', message: '...' }
│             ├─ SET_LOGIN_ERROR (에러 메시지 저장)
│             └─ throw err (LoginView에서 catch 가능)
│
└─ SET_LOGIN_LOADING → false (무조건 실행)
```

**`{ root: true }` 의미:**
```javascript
dispatch('chat/clearChat', null, { root: true })
//                                ^^^^^^^^^^^^^^
// 다른 모듈의 action을 호출할 때 필요
// root: true가 없으면 → 'auth/chat/clearChat' 찾으려 함 (에러!)
// root: true가 있으면 → 'chat/clearChat' 찾음 (정상!)
```

### initAuth - 앱 시작 시 토큰 검증 ⭐

```javascript
async initAuth({ commit, state, dispatch }) {
  if (!state.accessToken) return false   // 토큰 없음 → 스킵
  try {
    await dispatch('fetchMe')            // GET /api/v1/auth/me
    return true                          // 토큰 유효!
  } catch {
    commit('CLEAR_AUTH')                 // 토큰 만료 → 정리
    return false
  }
}
```

이 action이 `main.js`에서 호출됩니다 (Phase 1 참조):
```javascript
store.dispatch('auth/initAuth').finally(() => {
  app.mount('#app')
})
```

### logout - 로그아웃

```javascript
async logout({ commit, state, dispatch }) {
  try {
    if (state.accessToken) {
      await authApi.logout()           // 서버에 로그아웃 알림 (세션 삭제)
    }
  } catch {
    // 서버 에러 무시 (이미 만료 등)
  } finally {
    commit('CLEAR_AUTH')               // 토큰 + 사용자 삭제
    dispatch('chat/clearChat', null, { root: true })
    dispatch('dashboard/clearState', null, { root: true })
  }
}
```

**서버 에러를 무시하는 이유**: 토큰이 이미 만료되었거나 서버가 다운된 경우에도, 프론트엔드에서는 **무조건 로그아웃 처리**를 해야 합니다.

---

## Mutations - State 변경

```javascript
mutations: {
  SET_AUTH(state, { accessToken, refreshToken, user }) {
    state.accessToken = accessToken
    state.refreshToken = refreshToken
    state.user = user
    state.loginError = null
    saveTokens(accessToken, refreshToken, user)  // localStorage에도 저장!
  },

  CLEAR_AUTH(state) {
    state.accessToken = null
    state.refreshToken = null
    state.user = null
    state.loginError = null
    clearTokens()   // localStorage에서도 삭제!
  },

  SET_USER(state, user) {
    state.user = user
    localStorage.setItem(TOKEN_KEYS.USER, JSON.stringify(user))
  }
}
```

**모든 mutation이 localStorage와 동기화**되는 것에 주목하세요. Store와 localStorage를 항상 일치시킵니다.

---

## 리뷰 체크리스트

- [x] localStorage와 Vuex state가 동기화되는가? → SET_AUTH, CLEAR_AUTH 모두 양쪽 처리 ✅
- [x] try/catch로 localStorage 실패를 처리하는가? → 모든 헬퍼 함수에 적용 ✅
- [x] 로그인 실패 시 에러 메시지가 구분되는가? → LOCKED, DISABLED, UNAUTHORIZED ✅
- [x] 로그아웃 시 관련 모듈 상태가 초기화되는가? → chat, dashboard clearState ✅
- [x] initAuth가 토큰 만료를 처리하는가? → catch에서 CLEAR_AUTH ✅
- [x] `{ root: true }`로 다른 모듈 호출하는가? → chat/clearChat 등 ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **localStorage 동기화** | Store + localStorage 이중 저장으로 새로고침에도 유지 |
| **initAuth** | 앱 시작 시 저장된 토큰의 유효성을 서버에 검증 |
| **hasMenuPermission** | 함수를 반환하는 getter. 메뉴별 CRUD 권한 체크 |
| **canAccessAdmin** | 메뉴가 1개라도 있으면 관리자 영역 접근 허용 |
| **`{ root: true }`** | 다른 모듈의 action/mutation 호출 시 필수 |
| **에러 코드 분기** | 백엔드 에러 코드에 따른 한국어 메시지 분기 |

---
> **이전**: [01_vuex_basics.md](01_vuex_basics.md) - Vuex 기초
> **다음**: [03_app_module.md](03_app_module.md) - 앱 설정 모듈
