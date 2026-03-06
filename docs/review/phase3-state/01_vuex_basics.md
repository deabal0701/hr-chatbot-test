# 1. Vuex 기초 - 상태 관리란?

> **파일 위치**: `frontend/src/store/index.js`

## 왜 상태 관리가 필요한가?

Vue 컴포넌트는 기본적으로 **부모 → 자식**으로만 데이터를 전달할 수 있습니다 (props). 자식 → 부모는 이벤트(emit)로 전달합니다. 하지만 **관계가 먼 컴포넌트** 사이에서 데이터를 공유하려면?

```
[Props/Emit만으로 통신하면]

App.vue → AdminLayout → AppHeader     ← 사용자 이름 필요!
                       → AppSidebar    ← 메뉴 권한 필요!
                       → UsersView     ← 사용자 역할 필요!
                       → ChatView      ← 세션 ID 필요!

사용자 정보를 App.vue → AdminLayout → 각 컴포넌트로
일일이 props로 전달해야 함 → "Props Drilling" 지옥!

[Vuex Store를 사용하면]

         ┌── Store (중앙 저장소) ──┐
         │  user, token, menus   │
         └──┬───┬───┬───┬───────┘
            │   │   │   │
    AppHeader  AppSidebar  UsersView  ChatView

    → 어디서든 store에 직접 접근! Props Drilling 없음!
```

## Vuex의 4가지 핵심 개념

```
┌─────────────────────────────────────────────┐
│                 Vuex Store                  │
│                                             │
│  ┌─── State ───┐    ┌─── Getters ───┐      │
│  │ 원본 데이터  │    │ 가공된 데이터  │      │
│  │ (창고)       │    │ (진열대)      │      │
│  └──────┬──────┘    └──────┬────────┘      │
│         │                  │                │
│         │  읽기             │  읽기          │
│         ▼                  ▼                │
│     컴포넌트에서 사용                        │
│         │                                   │
│         │  변경 요청                         │
│         ▼                                   │
│  ┌─── Actions ──┐   ┌── Mutations ──┐      │
│  │ 비동기 작업   │──→│ 동기 변경     │      │
│  │ (API 호출)   │   │ (실제 수정)   │      │
│  └──────────────┘   └──────────────┘      │
│                                             │
└─────────────────────────────────────────────┘
```

### 1. State (상태) - "창고"

```javascript
state: () => ({
  user: null,           // 현재 로그인한 사용자 정보
  accessToken: null,    // JWT 토큰
  loginLoading: false   // 로그인 중인지 여부
})
```

- 앱의 **원본 데이터**가 저장되는 곳
- 컴포넌트에서 직접 읽을 수 있음
- **직접 수정하면 안 됨!** (반드시 mutation을 통해서)

### 2. Mutations (변이) - "창고 관리자"

```javascript
mutations: {
  SET_AUTH(state, { accessToken, user }) {
    state.accessToken = accessToken    // state를 직접 수정
    state.user = user
  }
}
```

- state를 **실제로 변경**하는 유일한 방법
- **동기적**으로만 작동 (즉시 완료)
- `commit('MUTATION_NAME', payload)`으로 호출

### 3. Actions (액션) - "업무 담당자"

```javascript
actions: {
  async login({ commit }, { loginId, password }) {
    const data = await authApi.login(loginId, password)  // API 호출 (비동기)
    commit('SET_AUTH', { accessToken: data.access_token, user: data.user })
  }
}
```

- **비동기 작업**을 수행 (API 호출, 타이머 등)
- 작업이 끝나면 `commit()`으로 mutation을 호출
- `dispatch('ACTION_NAME', payload)`로 호출

### 4. Getters (게터) - "진열대"

```javascript
getters: {
  isAuthenticated: (state) => !!state.accessToken && !!state.user,
  displayName: (state) => state.user?.display_name || ''
}
```

- state를 **가공하여** 제공 (computed처럼)
- 여러 컴포넌트에서 같은 계산을 반복하지 않도록
- state가 변하면 자동으로 재계산

## 왜 Mutations과 Actions를 분리하는가?

```
[왜 직접 state를 바꾸면 안 되는가?]

❌ 나쁜 방법:
  this.$store.state.user = newUser    // 어디서 바꿨는지 추적 불가!

✅ 올바른 방법:
  commit('SET_USER', newUser)          // Vue DevTools에서 추적 가능!

[왜 Mutation에서 API를 호출하면 안 되는가?]

❌ 나쁜 방법 (Mutation에서 비동기):
  mutations: {
    async SET_USER(state) {
      const user = await api.getMe()   // 언제 끝날지 모름!
      state.user = user                // state 변경 시점이 불확실
    }
  }

✅ 올바른 방법 (Action → Mutation):
  actions: {
    async fetchMe({ commit }) {
      const user = await api.getMe()   // 비동기 작업은 Action에서
      commit('SET_USER', user)          // 완료 후 Mutation 호출
    }
  }
```

**규칙 요약:**
```
Mutation = 동기 = state 직접 변경 = commit()으로 호출
Action   = 비동기 OK = API 호출 등 = dispatch()로 호출
           Action이 끝나면 commit()으로 Mutation 호출
```

## store/index.js - 모듈 합치기

```javascript
import { createStore } from 'vuex'
import chat from './modules/chat'
import document from './modules/document'
import app from './modules/app'
import auth from './modules/auth'
import dashboard from './modules/dashboard'

export default createStore({
  modules: {
    chat,        // store.state.chat.*
    document,    // store.state.document.*
    app,         // store.state.app.*
    auth,        // store.state.auth.*
    dashboard    // store.state.dashboard.*
  }
})
```

`createStore()`에 `modules`로 등록하면, 각 모듈이 **독립된 영역**을 가집니다:

```
store
├── state.auth.user           ← auth 모듈
├── state.auth.accessToken
├── state.app.userDarkMode    ← app 모듈
├── state.app.sidebarCollapsed
├── state.chat.messages       ← chat 모듈
├── state.chat.searchMode
├── state.document.documents  ← document 모듈
└── state.dashboard.widgets   ← dashboard 모듈
```

## namespaced: true 의 의미

```javascript
// auth.js
export default {
  namespaced: true,    // ⭐ 이름공간 사용!
  // ...
}
```

이것이 있으면 모듈 이름을 **접두사**로 붙여야 합니다:

```javascript
// namespaced: true 일 때 (이 프로젝트 방식)
store.getters['auth/isAuthenticated']     // 'auth/' 접두사 필요
store.dispatch('auth/login', payload)
store.commit('auth/SET_AUTH', payload)

// namespaced 없으면 (충돌 위험!)
store.getters.isAuthenticated             // 다른 모듈과 이름 충돌 가능!
```

## 컴포넌트에서 Store 사용하기

```vue
<template>
  <!-- getter 읽기 -->
  <span>{{ displayName }}</span>
  <span v-if="isAuthenticated">로그인됨</span>
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'

const store = useStore()

// State 직접 읽기
const user = computed(() => store.state.auth.user)

// Getter 읽기 (가공된 값)
const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])
const displayName = computed(() => store.getters['auth/displayName'])

// Action 호출 (비동기 작업)
const login = async () => {
  await store.dispatch('auth/login', { loginId: 'admin', password: 'pass' })
}

// Mutation 직접 호출 (보통은 Action을 통해)
const clearAuth = () => {
  store.commit('auth/CLEAR_AUTH')
}
</script>
```

## 데이터 흐름 (단방향)

```
  컴포넌트가 Action 호출
       │
       ▼
  Action이 API 호출 (비동기)
       │
       ▼
  Action이 Mutation 호출 (commit)
       │
       ▼
  Mutation이 State 변경
       │
       ▼
  State 변경 → Getter 재계산 → 컴포넌트 자동 업데이트
```

이 **단방향 흐름**이 Vuex의 핵심입니다. 데이터가 항상 같은 방향으로 흐르기 때문에 **디버깅이 쉽습니다**.

## 핵심 정리

| 개념 | 역할 | 호출 방법 | 비동기 |
|------|------|-----------|--------|
| **State** | 원본 데이터 저장 | `store.state.모듈.속성` | - |
| **Getters** | 가공된 데이터 제공 | `store.getters['모듈/이름']` | - |
| **Mutations** | State 직접 변경 | `store.commit('모듈/이름', 값)` | ❌ 동기만 |
| **Actions** | 비동기 작업 + Mutation 호출 | `store.dispatch('모듈/이름', 값)` | ✅ 비동기 OK |
| **Modules** | 기능별 Store 분리 | `namespaced: true` | - |

---
> **다음**: [02_auth_module.md](02_auth_module.md) - 인증 모듈 상세
