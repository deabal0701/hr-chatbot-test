# Phase 6: 프론트엔드 메뉴 기반 권한 UI 구현 설계서

> **문서 버전**: 2.0
> **작성일**: 2026-02-12
> **수정일**: 2026-02-13
> **상태**: Draft
> **선행 조건**: Phase 2 (Core Security), Phase 3 (인증 API + 미들웨어), Phase 4 (관리 CRUD API) 완료
> **참조**: `docs/design/user_permission_system.md` (v2.0 - 메뉴 기반 권한)
> **변경 사유**: v1.0 permission 코드 기반 → v2.0 메뉴 기반 권한 체계 전면 전환

---

## 목차

1. [개요](#1-개요)
2. [현재 상태 분석](#2-현재-상태-분석)
3. [단계별 구현 계획 (Step 1~7)](#3-단계별-구현-계획)
4. [Step 1: Auth Store 메뉴 기반 전환](#4-step-1-auth-store-메뉴-기반-전환)
5. [Step 2: 사이드바 동적 메뉴 렌더링](#5-step-2-사이드바-동적-메뉴-렌더링)
6. [Step 3: 라우터 가드 메뉴 기반 전환](#6-step-3-라우터-가드-메뉴-기반-전환)
7. [Step 4: 사용자 관리 화면 v2.0](#7-step-4-사용자-관리-화면-v20)
8. [Step 5: 메뉴/권한 관리 화면 (신규)](#8-step-5-메뉴권한-관리-화면-신규)
9. [Step 6: 역할 관리 + 테넌트 관리 화면](#9-step-6-역할-관리--테넌트-관리-화면)
10. [Step 7: 인증 필수 모드 전환](#10-step-7-인증-필수-모드-전환)
11. [산출물 총괄](#11-산출물-총괄)
12. [검증 계획](#12-검증-계획)

---

## 1. 개요

### 1.1 목적

v2.0 메뉴 기반 권한 체계에 맞춰 프론트엔드를 전면 전환합니다.

**v1.0 → v2.0 프론트엔드 핵심 변경**:

| 구분 | v1.0 (현행) | v2.0 (목표) |
|------|:---:|:---:|
| 메뉴 목록 | 하드코딩 (`allMenuItems` 배열) | **DB에서 `menus` 배열 수신, 동적 렌더링** |
| 권한 체크 | `hasPermission('admin:users')` | **`hasMenuPermission('USER_MGMT', 'read')`** |
| 사용자 정보 | `roles: []`, `permissions: []` | **`role_code: str`, `menus: [{...CRUD}]`** |
| 역할 할당 | `role_ids: List[int]` (M:N) | **`role_id: int` (1:N 단일)** |
| 권한 할당 | permission 코드 체크박스 | **메뉴 트리 + CRUD 체크박스 (`tb_user_menu`)** |
| 관리 화면 | UsersView만 구현 | **Users + Menus(★신규) + Roles + Tenants** |

### 1.2 핵심 원칙

```
┌──────────────────────────────────────────────────────────────────┐
│  1. 메뉴 기반 — 모든 UI 제어는 user.menus 배열에서 결정           │
│  2. DB 기반 동적 렌더링 — 프론트엔드에 메뉴 목록 하드코딩 없음     │
│  3. CRUD 세분화 — 읽기/등록/수정/삭제/내보내기를 개별 제어          │
│  4. 점진적 적용 — 각 Step 완료 후 기존 기능이 정상 동작해야 함     │
│  5. 하위 호환 — Step 7 전까지 토큰 없이도 기존 API 사용 가능       │
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
│  │Guard    │    │★동적 메뉴│    │(interceptors)│               │
│  │(메뉴기반)│   │(DB 기반) │    │401→refresh   │               │
│  └─────────┘    │AppHeader │    │403→alert     │               │
│                 └──────────┘    └──────┬───────┘               │
│                                        │                        │
├────────────────────────────────────────┼────────────────────────┤
│  Backend (FastAPI)                     │                        │
│                                        ▼                        │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  POST /api/v1/auth/login → { user: { menus: [...] } }│      │
│  │  GET  /api/v1/auth/me    → { menus: [...] }          │      │
│  │  ★ 로그인 응답에 메뉴 + CRUD 권한 포함                 │      │
│  └──────────────────────────────────────────────────────┘      │
│  ┌──────────────────────────────────────────────────────┐      │
│  │  관리 API (require_menu_permission 보호)               │      │
│  │  /api/admin/v1/users   → USER_MGMT:read/create/...   │      │
│  │  /api/admin/v1/menus   → MENU_MGMT:read/create/...   │      │
│  │  /api/admin/v1/roles   → ROLE_MGMT:read/create/...   │      │
│  │  /api/admin/v1/tenants → TENANT_MGMT:read/create/... │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 현재 상태 분석

### 2.1 프론트엔드 현황

| 파일 | 현재 상태 | v2.0 변경 필요 |
|------|----------|---------------|
| `api/auth.js` | ✅ 구현 완료 (5개 엔드포인트) | 응답 구조 변경 반영 (`menus` 처리) |
| `api/users.js` | ✅ 구현 완료 (CRUD + assignRoles) | `assignRoles` → `assignMenus` 전환 |
| `api/menus.js` | ❌ **미존재** | ★ 신규 생성 (메뉴 CRUD + 사용자 메뉴 권한) |
| `api/tenants.js` | ✅ 구현 완료 (CRUD) | 변경 없음 |
| `api/index.js` | ✅ 인터셉터 활성화 | 변경 없음 |
| `store/modules/auth.js` | ✅ 구현 완료 | **v2.0 전환 필요** (permissions → menus) |
| `store/index.js` | ✅ auth 모듈 등록 | 변경 없음 |
| `views/LoginView.vue` | ✅ 구현 완료 | 랜딩 페이지 로직 변경 (`landing_page` 사용) |
| `views/admin/UsersView.vue` | ✅ 구현 완료 (v1.0) | **v2.0 전환 필요** (role_id 단일 + 메뉴 권한) |
| `views/admin/RolesView.vue` | ⚠️ 스텁 | 구현 필요 |
| `views/admin/TenantsView.vue` | ⚠️ 스텁 | 구현 필요 |
| `views/admin/MenusView.vue` | ❌ **미존재** | ★ 신규 생성 |
| `components/layout/AppSidebar.vue` | ✅ 하드코딩 메뉴 + permission 필터 | **v2.0 전환 필요** (DB 동적 메뉴) |
| `components/layout/AppHeader.vue` | ✅ 구현 완료 (사용자 드롭다운) | `role_code` 표시로 변경 |
| `router/index.js` | ✅ 로그인 라우트 + auth 가드 | 메뉴 기반 라우트 가드로 전환 |

### 2.2 백엔드 현황 (Phase 4 완료 기준)

| 구분 | 파일 | 상태 |
|------|------|------|
| 인증 API | `app/api/routes/auth.py` | ✅ 5개 엔드포인트 |
| 사용자 관리 | `app/api/routes/users.py` | ✅ 7개 엔드포인트 (v2.0: `menus` 포함) |
| 역할 관리 | `app/api/routes/roles.py` | ✅ 5개 엔드포인트 |
| 테넌트 관리 | `app/api/routes/tenants.py` | ✅ 5개 엔드포인트 |
| 메뉴 관리 | `app/api/routes/menus.py` | ✅ 4개 엔드포인트 (★ 신규) |
| 권한 체크 | `app/core/security/permission.py` | ✅ `require_menu_permission(menu_code, action)` |

### 2.3 v1.0 → v2.0 프론트엔드 핵심 변경점

#### 로그인 응답 구조 변경

```javascript
// v1.0 (현행): permission 코드 리스트
{
  user: {
    roles: ["SYSTEM_ADMIN"],
    role_names: ["시스템 관리자"],
    permissions: ["nl2sql:execute", "admin:users", "admin:settings"]
  }
}

// v2.0 (목표): role_code 단일 + menus 배열
{
  user: {
    role_code: "SYSTEM_ADMIN",
    scope_type: "GLOBAL",
    landing_page: "/admin/dashboard",
    menus: [
      {
        menu_code: "DASHBOARD", menu_name: "대시보드",
        menu_path: "/admin/dashboard", menu_type: "PAGE",
        icon: "dashboard", depth: 1, sort_order: 1,
        can_create: false, can_read: true,
        can_update: false, can_delete: false, can_export: false
      },
      // ...
    ]
  }
}
```

#### 권한 체크 방식 변경

```javascript
// v1.0: permission 코드 기반
const canManageUsers = hasPermission('admin:users')

// v2.0: 메뉴 코드 + CRUD 액션 기반
const canReadUsers = hasMenuPermission('USER_MGMT', 'read')
const canCreateUsers = hasMenuPermission('USER_MGMT', 'create')
const canDeleteUsers = hasMenuPermission('USER_MGMT', 'delete')
```

---

## 3. 단계별 구현 계획

### 3.1 Step 의존성 다이어그램

```
Step 1 ─────► Step 2 ─────► Step 3 ─────► Step 7
(Auth Store   (사이드바     (라우터 가드   (필수모드)
 v2.0 전환)    동적 메뉴)    메뉴 기반)
                               │
                               ├──► Step 4 (사용자 관리 v2.0)
                               ├──► Step 5 (메뉴/권한 관리 ★신규)
                               └──► Step 6 (역할/테넌트 관리)
                                       │
                                       └──► Step 7 (필수모드)
```

### 3.2 Step 요약

| Step | 이름 | 범위 | 핵심 변경 |
|------|------|------|----------|
| **1** | Auth Store v2.0 전환 | FE | permissions → menus, hasMenuPermission |
| **2** | 사이드바 동적 메뉴 렌더링 | FE | 하드코딩 → DB 기반 `user.menus` |
| **3** | 라우터 가드 메뉴 기반 전환 | FE | requiresAdmin → menu path 매칭 |
| **4** | 사용자 관리 화면 v2.0 | FE | role_id 단일 + 메뉴 CRUD 체크박스 |
| **5** | 메뉴/권한 관리 화면 | FE | ★ 신규 (MenusView + api/menus.js) |
| **6** | 역할 + 테넌트 관리 화면 | FE | 스텁 → 완전 구현 |
| **7** | 인증 필수 모드 전환 | BE+FE | Phase 3a → 3b |

---

## 4. Step 1: Auth Store 메뉴 기반 전환

### 4.1 목표

`store/modules/auth.js`의 권한 체크 체계를 v1.0 permission 코드에서 v2.0 메뉴 기반으로 전환합니다.

### 4.2 산출물

```
수정:
  frontend/src/store/modules/auth.js    # permissions → menus 전환
```

### 4.3 `store/modules/auth.js` 변경 사항

#### State 변경

```javascript
// v1.0 (현행) — user 객체 구조
// user.roles: ["SYSTEM_ADMIN"]
// user.permissions: ["admin:users", "admin:settings", ...]

// v2.0 (목표) — user 객체 구조
// user.role_code: "SYSTEM_ADMIN"
// user.scope_type: "GLOBAL"
// user.landing_page: "/admin/dashboard"
// user.menus: [{ menu_code, menu_name, menu_path, can_create, can_read, ... }, ...]
```

#### Getters 변경

```javascript
getters: {
  isAuthenticated: (state) => !!state.accessToken && !!state.user,
  currentUser: (state) => state.user,

  // ===== v2.0 메뉴 기반 권한 헬퍼 =====

  // 역할 코드 (단일)
  roleCode: (state) => state.user?.role_code || 'USER',
  scopeType: (state) => state.user?.scope_type || 'USER',
  landingPage: (state) => state.user?.landing_page || '/chat',

  // 사용자의 메뉴 목록 (PAGE 타입만, can_read가 true인 것)
  accessibleMenus: (state) => {
    const menus = state.user?.menus || []
    return menus
      .filter(m => m.menu_type === 'PAGE' && m.can_read)
      .sort((a, b) => a.sort_order - b.sort_order)
  },

  // 메뉴 코드로 특정 메뉴 권한 조회
  getMenuPermission: (state) => (menuCode) => {
    if (!state.user?.menus) return null
    return state.user.menus.find(m => m.menu_code === menuCode) || null
  },

  // 메뉴 코드 + 액션으로 권한 체크
  hasMenuPermission: (state) => (menuCode, action = 'read') => {
    if (!state.user?.menus) return false
    const menu = state.user.menus.find(m => m.menu_code === menuCode)
    if (!menu) return false
    return menu[`can_${action}`] === true
  },

  // 관리자 영역 접근 가능 여부 (ADMIN 하위 PAGE 메뉴가 하나라도 있는지)
  canAccessAdmin: (state) => {
    if (!state.user?.menus) return false
    return state.user.menus.some(
      m => m.menu_type === 'PAGE' && m.can_read && m.menu_path?.startsWith('/admin')
    )
  }
},
```

#### 제거 대상 (v1.0 전용)

```javascript
// 아래 getters 제거
permissions: (state) => state.user?.permissions || [],           // 삭제
roles: (state) => state.user?.roles || [],                       // 삭제
hasPermission: (state) => (code) => { ... },                     // 삭제
hasAnyPermission: (state) => (...codes) => { ... },              // 삭제
```

#### Actions — login 응답 처리 변경

```javascript
async login({ commit }, { loginId, password }) {
  commit('SET_LOGIN_LOADING', true)
  commit('SET_LOGIN_ERROR', null)
  try {
    const data = await authApi.login(loginId, password)
    commit('SET_AUTH', {
      accessToken: data.access_token,
      refreshToken: data.refresh_token,
      user: data.user  // v2.0: { role_code, scope_type, landing_page, menus: [...] }
    })
    return data.user
  } catch (err) {
    commit('SET_LOGIN_ERROR', err.message || '로그인에 실패했습니다')
    throw err
  } finally {
    commit('SET_LOGIN_LOADING', false)
  }
}
```

### 4.4 LoginView.vue 변경

로그인 성공 후 리다이렉트를 `landing_page` 기반으로 변경:

```javascript
// v1.0 (현행)
const canAdmin = store.getters['auth/canAccessAdmin']
router.push(canAdmin ? '/admin' : '/chat')

// v2.0 (목표)
const landingPage = store.getters['auth/landingPage']
router.push(landingPage)
// SYSTEM_ADMIN → /admin/dashboard
// TENANT_ADMIN → /admin/dashboard
// USER → /chat
```

### 4.5 검증 항목

- [ ] 로그인 → `user.menus` 배열이 저장됨 (localStorage `mureum_user` 확인)
- [ ] `hasMenuPermission('DASHBOARD', 'read')` → `true`
- [ ] `hasMenuPermission('MENU_MGMT', 'create')` → SYSTEM_ADMIN만 `true`
- [ ] `canAccessAdmin` → 관리 메뉴가 하나라도 있으면 `true`
- [ ] `landingPage` → 역할별 올바른 페이지 반환
- [ ] v1.0 `hasPermission`, `permissions` getter 제거 확인

---

## 5. Step 2: 사이드바 동적 메뉴 렌더링

### 5.1 목표

`AppSidebar.vue`의 하드코딩된 메뉴를 DB에서 받은 `user.menus` 배열로 동적 렌더링합니다.

> **핵심**: 프론트엔드 코드에 메뉴 목록을 하드코딩하지 않음.
> DB에서 메뉴를 추가/삭제하면 프론트엔드 코드 변경 없이 메뉴가 자동으로 나타남/사라짐.

### 5.2 산출물

```
수정:
  frontend/src/components/layout/AppSidebar.vue   # 동적 메뉴 렌더링
  frontend/src/components/layout/AppHeader.vue    # role_code 표시
```

### 5.3 `AppSidebar.vue` 변경

#### 메뉴 아이콘 매핑

DB의 `icon` 문자열을 Element Plus 아이콘 컴포넌트로 매핑합니다:

```javascript
import {
  Odometer, ChatDotSquare, Document, User, Menu as MenuIcon,
  Key, OfficeBuilding, Setting, Grid, Histogram
} from '@element-plus/icons-vue'

const iconMap = {
  dashboard: Odometer,
  chat: ChatDotSquare,
  document: Document,
  user: User,
  menu: MenuIcon,
  key: Key,
  building: OfficeBuilding,
  setting: Setting,
  grid: Grid,
  histogram: Histogram,
}
```

#### 동적 메뉴 생성

```javascript
const store = useStore()

// v2.0: DB에서 받은 메뉴 목록으로 사이드바 생성
const sidebarMenus = computed(() => {
  const menus = store.getters['auth/accessibleMenus']  // PAGE + can_read
  return menus
    .filter(m => m.menu_path?.startsWith('/admin'))  // 관리자 메뉴만
    .map(m => ({
      path: m.menu_path,
      title: m.menu_name,
      icon: iconMap[m.icon] || Document,
      menuCode: m.menu_code,
    }))
})

// 비인증 상태 폴백 (Phase 3a 호환)
const menuItems = computed(() => {
  if (store.getters['auth/isAuthenticated']) {
    return sidebarMenus.value
  }
  // Phase 3a: 인증 없이도 기본 메뉴 표시 (하드코딩 폴백)
  return [
    { path: '/admin/chat', title: '자연어 검색', icon: ChatDotSquare },
    { path: '/admin/documents', title: '지식문서 관리', icon: Document },
    { path: '/admin/history', title: '검색 이력', icon: Histogram },
  ]
})
```

#### Template

```html
<el-menu :default-active="activeMenu" :collapse="isCollapse" router>
  <el-menu-item v-for="item in menuItems" :key="item.path" :index="item.path">
    <el-icon><component :is="item.icon" /></el-icon>
    <template #title>{{ item.title }}</template>
  </el-menu-item>
</el-menu>
```

### 5.4 `AppHeader.vue` 변경

사용자 드롭다운에 `role_code`를 표시합니다:

```javascript
// v1.0 (현행)
// user.roles → ["SYSTEM_ADMIN"] 배열

// v2.0 (목표)
const roleLabel = computed(() => {
  const map = {
    SYSTEM_ADMIN: '시스템 관리자',
    TENANT_ADMIN: '테넌트 관리자',
    USER: '일반 사용자'
  }
  return map[currentUser.value?.role_code] || currentUser.value?.role_code
})
```

```html
<el-dropdown-item disabled>
  <el-tag size="small" type="info">{{ currentUser.scope_type }}</el-tag>
  {{ roleLabel }}
</el-dropdown-item>
```

### 5.5 역할별 사이드바 메뉴 비교

| 메뉴 | menu_code | 경로 | SYSTEM_ADMIN | TENANT_ADMIN | USER |
|------|-----------|------|:---:|:---:|:---:|
| 대시보드 | DASHBOARD | /admin/dashboard | O | O | - |
| 자연어 검색 | CHAT | /admin/chat | O | O | - |
| 문서 관리 | DOCUMENTS | /admin/documents | O | O | - |
| 사용자 관리 | USER_MGMT | /admin/users | O | O | - |
| 메뉴/권한 관리 | MENU_MGMT | /admin/menus | O | - | - |
| 역할 관리 | ROLE_MGMT | /admin/roles | O | - | - |
| 테넌트 관리 | TENANT_MGMT | /admin/tenants | O | - | - |
| 시스템 설정 | SETTINGS | /admin/settings | O | - | - |
| 코드 관리 | CODES | /admin/codes | O | - | - |
| 검색 이력 | HISTORY | /admin/history | O | O | - |
| 채팅 | USER_CHAT | /chat | O | O | O |

> USER 역할은 관리자 메뉴 없음 → `/chat`으로 직행 (landing_page 기반)

### 5.6 검증 항목

- [ ] SYSTEM_ADMIN 로그인 → 10개 관리 메뉴 표시
- [ ] TENANT_ADMIN 로그인 → 할당된 메뉴만 표시 (약 6개)
- [ ] USER 로그인 → `/chat`으로 이동, 관리 사이드바 없음
- [ ] DB에서 메뉴 비활성화(`is_active=false`) → 사이드바에서 자동 제거
- [ ] 비인증 상태 → 폴백 메뉴 표시 (Phase 3a 호환)

---

## 6. Step 3: 라우터 가드 메뉴 기반 전환

### 6.1 목표

라우터 `beforeEach` 가드를 메뉴 기반으로 전환합니다. URL 경로와 `user.menus`의 `menu_path`를 매칭하여 접근 제어합니다.

### 6.2 산출물

```
수정:
  frontend/src/router/index.js    # 메뉴 기반 라우트 가드
```

### 6.3 `router/index.js` 변경

```javascript
import store from '@/store'

router.beforeEach(async (to, from, next) => {
  const isAuthenticated = store.getters['auth/isAuthenticated']

  // 1. 로그인 페이지: 이미 인증됐으면 landing_page로 이동
  if (to.path === '/login') {
    if (isAuthenticated) {
      return next(store.getters['auth/landingPage'])
    }
    return next()
  }

  // 2. 공개 페이지: 인증 불필요
  if (to.meta.public) return next()

  // 3. 관리자 영역 (/admin/*): 인증 + 메뉴 접근 권한 필요
  if (to.path.startsWith('/admin')) {
    if (!isAuthenticated) {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }

    // 관리자 영역 접근 가능 여부
    if (!store.getters['auth/canAccessAdmin']) {
      return next(store.getters['auth/landingPage'])
    }

    // 특정 관리 페이지 접근 시 해당 메뉴 read 권한 확인
    const menus = store.state.auth.user?.menus || []
    const targetMenu = menus.find(m => m.menu_path === to.path)
    if (targetMenu && !targetMenu.can_read) {
      // 해당 메뉴에 read 권한 없음 → 대시보드로
      return next('/admin/dashboard')
    }

    return next()
  }

  // 4. 일반 페이지 (/chat): 통과 (Phase 3a 선택적 모드)
  next()
})
```

### 6.4 라우트 정의에 MenusView 추가

```javascript
// admin 하위 라우트에 추가
{
  path: 'menus',
  name: 'Menus',
  component: () => import('@/views/admin/MenusView.vue'),
  meta: { title: '메뉴/권한 관리', requiresAdmin: true }
}
```

### 6.5 검증 항목

- [ ] 미인증 상태에서 `/admin/users` 접근 → `/login?redirect=/admin/users`
- [ ] SYSTEM_ADMIN 로그인 → 모든 `/admin/*` 경로 접근 가능
- [ ] TENANT_ADMIN 로그인 → `/admin/menus` 접근 시 대시보드로 리다이렉트
- [ ] USER 로그인 → `/admin/*` 접근 시 `/chat`으로 리다이렉트
- [ ] 로그인 후 `redirect` 쿼리 파라미터가 있으면 해당 경로로 이동
- [ ] 이미 인증된 상태에서 `/login` → `landing_page`로 리다이렉트

---

## 7. Step 4: 사용자 관리 화면 v2.0

### 7.1 목표

기존 `UsersView.vue`를 v2.0 메뉴 기반 권한 체계에 맞게 전환합니다:
- 역할 할당: M:N `role_ids` → 1:N `role_id` (단일 선택)
- 메뉴 권한 할당: 메뉴 트리 + CRUD 체크박스 UI 추가

### 7.2 산출물

```
수정:
  frontend/src/views/admin/UsersView.vue   # v2.0 전환
  frontend/src/api/users.js               # menus 엔드포인트 추가
```

### 7.3 `api/users.js` 변경

```javascript
// v1.0 → 제거
// assignRoles(userId, roleIds) → 삭제

// v2.0 → 추가
getUserMenus(userId) {
  return apiClient.get(`${USERS_BASE}/${userId}/menus`)
},

updateUserMenus(userId, menus) {
  // menus: [{ menu_id, can_create, can_read, can_update, can_delete, can_export }]
  return apiClient.put(`${USERS_BASE}/${userId}/menus`, { menus })
}
```

### 7.4 UI 설계 — 사용자 생성/수정 다이얼로그

```
┌──────────────────────────────────────────────────────────────┐
│  사용자 수정                                           [×]    │
│                                                              │
│  ┌───────── 기본 정보 ────────┐  ┌──── 역할/테넌트 ─────┐    │
│  │ 로그인 ID: [user02       ] │  │ 역할: [테넌트 관리자▼]│    │
│  │ 이메일:    [user@co.kr   ] │  │ 테넌트: [A회사    ▼] │    │
│  │ 표시 이름: [김철수        ] │  └─────────────────────┘    │
│  │ 비밀번호:  [••••••••     ] │                              │
│  └───────────────────────────┘                              │
│                                                              │
│  ┌─────── 메뉴 권한 설정 ──────────────────────────────────┐ │
│  │ ※ 역할 선택 시 기본 메뉴 권한이 자동 체크됩니다          │ │
│  │                                                          │ │
│  │ 메뉴              │ 조회 │ 등록 │ 수정 │ 삭제 │ 내보내기 │ │
│  │ ─────────────────┼──────┼──────┼──────┼──────┼────────│ │
│  │ ☑ 대시보드        │  ☑  │  □  │  □  │  □  │  □     │ │
│  │ ☑ 자연어 검색     │  ☑  │  ☑  │  □  │  □  │  □     │ │
│  │ ☑ 문서 관리       │  ☑  │  ☑  │  ☑  │  ☑  │  ☑     │ │
│  │ ☑ 사용자 관리     │  ☑  │  ☑  │  ☑  │  □  │  □     │ │
│  │ □ 메뉴/권한 관리  │  □  │  □  │  □  │  □  │  □     │ │
│  │ □ 역할 관리       │  □  │  □  │  □  │  □  │  □     │ │
│  │ □ 테넌트 관리     │  □  │  □  │  □  │  □  │  □     │ │
│  │ ☑ 시스템 설정     │  ☑  │  □  │  □  │  □  │  □     │ │
│  │ ☑ 검색 이력       │  ☑  │  □  │  □  │  □  │  ☑     │ │
│  │ ☑ 채팅            │  ☑  │  ☑  │  □  │  □  │  □     │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                              │
│                            [취소]  [저장]                      │
└──────────────────────────────────────────────────────────────┘
```

### 7.5 역할 선택 → 기본 메뉴 자동 체크

역할을 선택하면 해당 역할의 기본 메뉴 권한이 자동 체크됩니다:

```javascript
// 역할별 기본 메뉴 권한 (user_permission_system.md §2.2.5 참조)
const DEFAULT_MENU_PERMISSIONS = {
  SYSTEM_ADMIN: {
    DASHBOARD: { c: true, r: true, u: true, d: true, e: true },
    CHAT: { c: true, r: true, u: false, d: false, e: false },
    DOCUMENTS: { c: true, r: true, u: true, d: true, e: true },
    USER_MGMT: { c: true, r: true, u: true, d: true, e: true },
    MENU_MGMT: { c: true, r: true, u: true, d: true, e: true },
    ROLE_MGMT: { c: true, r: true, u: true, d: true, e: true },
    TENANT_MGMT: { c: true, r: true, u: true, d: true, e: true },
    SETTINGS: { c: false, r: true, u: true, d: false, e: false },
    CODES: { c: true, r: true, u: true, d: true, e: false },
    HISTORY: { c: false, r: true, u: false, d: false, e: true },
    USER_CHAT: { c: true, r: true, u: false, d: false, e: false },
    // API 메뉴도 포함
  },
  TENANT_ADMIN: { /* ... 9개 메뉴 */ },
  USER: { /* ... 4개 메뉴 (USER_CHAT + API 3개) */ }
}

// 역할 변경 핸들러
const onRoleChange = async (roleId) => {
  const role = roles.value.find(r => r.role_id === roleId)
  if (!role) return
  const defaults = DEFAULT_MENU_PERMISSIONS[role.role_code]
  if (defaults) {
    // 메뉴 체크박스 테이블 자동 갱신
    menuPermissions.value = allMenus.value.map(menu => ({
      menu_id: menu.menu_id,
      menu_code: menu.menu_code,
      menu_name: menu.menu_name,
      ...( defaults[menu.menu_code] || { c: false, r: false, u: false, d: false, e: false } )
    }))
  }
}
```

> **참고**: 기본값은 자동 체크만 하고, 관리자가 개별 조정할 수 있습니다.

### 7.6 사용자 목록 테이블 컬럼 변경

```
v1.0: ID | 아이디 | 이름 | 이메일 | 역할(태그들) | 테넌트 | 상태 | 액션
v2.0: ID | 아이디 | 이름 | 이메일 | 역할(단일) | 테넌트 | 메뉴수 | 상태 | 액션
```

- `역할` 컬럼: 복수 태그 → 단일 태그 (`role_code`)
- `메뉴수` 컬럼: `menu_count` 표시 (해당 사용자의 접근 가능 메뉴 수)

### 7.7 CRUD 버튼 권한 제어

```javascript
// 현재 사용자의 USER_MGMT 메뉴 권한에 따라 버튼 표시
const userMgmtPerm = computed(() => store.getters['auth/getMenuPermission']('USER_MGMT'))

const canCreate = computed(() => userMgmtPerm.value?.can_create)
const canUpdate = computed(() => userMgmtPerm.value?.can_update)
const canDelete = computed(() => userMgmtPerm.value?.can_delete)
```

```html
<el-button v-if="canCreate" type="primary" @click="openCreateDialog">+ 사용자 추가</el-button>
<el-button v-if="canUpdate" @click="openEditDialog(row)">수정</el-button>
<el-button v-if="canDelete" type="danger" @click="deleteUser(row)">삭제</el-button>
```

### 7.8 검증 항목

- [ ] 사용자 생성: role_id 단일 선택 + 메뉴 CRUD 체크박스 표시
- [ ] 역할 변경 시 기본 메뉴 자동 체크
- [ ] 메뉴 체크박스 개별 조정 가능
- [ ] 사용자 수정: 기존 메뉴 권한 로드 → 수정 → 저장
- [ ] TENANT_ADMIN: can_create=true면 추가 버튼 표시, can_delete=false면 삭제 버튼 숨김
- [ ] 사용자 목록에 역할(단일) + 메뉴수 표시

---

## 8. Step 5: 메뉴/권한 관리 화면 (신규)

### 8.1 목표

메뉴 트리를 조회/관리하는 `MenusView.vue`와 `api/menus.js`를 신규 생성합니다. SYSTEM_ADMIN만 접근 가능합니다.

### 8.2 산출물

```
신규:
  frontend/src/api/menus.js                 # 메뉴 관리 API 클라이언트
  frontend/src/views/admin/MenusView.vue    # 메뉴/권한 관리 화면

수정:
  frontend/src/router/index.js              # /admin/menus 라우트 추가
```

### 8.3 `api/menus.js`

```javascript
/**
 * 메뉴 관리 API 클라이언트
 *
 * Backend: /api/admin/v1/menus
 */
import apiClient from './index'

const MENUS_BASE = '/api/admin/v1/menus'

export default {
  // 메뉴 트리 조회
  getTree() {
    return apiClient.get(`${MENUS_BASE}`)
  },

  // 메뉴 생성
  create(data) {
    return apiClient.post(`${MENUS_BASE}`, data)
  },

  // 메뉴 수정
  update(menuId, data) {
    return apiClient.put(`${MENUS_BASE}/${menuId}`, data)
  },

  // 메뉴 삭제
  delete(menuId) {
    return apiClient.delete(`${MENUS_BASE}/${menuId}`)
  }
}
```

### 8.4 `MenusView.vue` UI 설계

```
┌──────────────────────────────────────────────────────────────────┐
│  메뉴/권한 관리                                   [+ 메뉴 추가]   │
│                                                                   │
│  ┌─── 메뉴 트리 ──────────────┐  ┌─── 메뉴 상세 ──────────────┐  │
│  │                             │  │                             │  │
│  │ ▼ 관리자 (ADMIN)            │  │ 메뉴 코드: DASHBOARD       │  │
│  │   ├ 대시보드                │  │ 메뉴 이름: 대시보드         │  │
│  │   ├ 자연어 검색             │  │ 메뉴 타입: PAGE             │  │
│  │   ├ 문서 관리               │  │ URL 경로: /admin/dashboard  │  │
│  │   ├ 사용자 관리             │  │ 아이콘: dashboard            │  │
│  │   ├ ★메뉴/권한 관리         │  │ 정렬순서: 1                 │  │
│  │   ├ 역할 관리               │  │ 상태: ☑ 활성               │  │
│  │   ├ 테넌트 관리             │  │                             │  │
│  │   ├ 시스템 설정             │  │ [수정]  [삭제]              │  │
│  │   ├ 코드 관리               │  │                             │  │
│  │   └ 검색 이력               │  └─────────────────────────────┘  │
│  │ ▼ 사용자 (USER_AREA)       │                                   │
│  │   └ 채팅                    │                                   │
│  │ ▼ API 접근 (API_ACCESS)    │                                   │
│  │   ├ Agent API               │                                   │
│  │   ├ RAG API                 │                                   │
│  │   └ NL2SQL API              │                                   │
│  │                             │                                   │
│  └─────────────────────────────┘                                   │
└──────────────────────────────────────────────────────────────────┘
```

### 8.5 핵심 기능

| 기능 | 설명 |
|------|------|
| 메뉴 트리 조회 | `el-tree` 컴포넌트로 계층 표시 |
| 메뉴 상세 보기 | 트리에서 노드 선택 시 우측 패널에 상세 정보 |
| 메뉴 추가 | DIRECTORY/PAGE/API 타입 선택, 상위 메뉴 지정 |
| 메뉴 수정 | 이름, 경로, 아이콘, 정렬순서, 활성화 수정 |
| 메뉴 삭제 | 하위 메뉴가 없는 메뉴만 삭제 가능 |

### 8.6 `el-tree` 바인딩

```html
<el-tree
  :data="menuTree"
  :props="{ label: 'menu_name', children: 'children' }"
  node-key="menu_id"
  highlight-current
  default-expand-all
  @node-click="onNodeClick"
>
  <template #default="{ data }">
    <span class="menu-tree-node">
      <el-tag size="small" :type="typeTagMap[data.menu_type]">
        {{ data.menu_type }}
      </el-tag>
      <span>{{ data.menu_name }}</span>
      <span class="menu-code">({{ data.menu_code }})</span>
    </span>
  </template>
</el-tree>
```

### 8.7 검증 항목

- [ ] 메뉴 트리 조회: 루트 3개 + 하위 14개 표시
- [ ] 메뉴 타입별 태그 색상 구분 (DIRECTORY, PAGE, API)
- [ ] 메뉴 선택 시 우측 상세 패널 표시
- [ ] 메뉴 추가 → 트리에 반영
- [ ] 메뉴 수정 → 변경 사항 반영
- [ ] 하위 메뉴가 있는 DIRECTORY 삭제 시 에러 메시지
- [ ] SYSTEM_ADMIN만 접근 가능 (TENANT_ADMIN 접근 불가)

---

## 9. Step 6: 역할 관리 + 테넌트 관리 화면

### 9.1 역할 관리 — `RolesView.vue`

#### 9.1.1 목표

역할(Role) CRUD를 구현합니다. v2.0에서는 역할에 권한(permission) 코드를 할당하지 않고, 역할의 `scope_type`과 `landing_page`를 관리합니다.

> **v2.0 핵심**: 역할은 "데이터 범위(scope_type)"만 결정하고, "메뉴 접근 권한"은 `tb_user_menu`에서 사용자별로 직접 관리합니다.

#### 9.1.2 산출물

```
수정:
  frontend/src/views/admin/RolesView.vue   # 스텁 → 완전 구현
```

> `api/users.js`에 이미 `listRoles()` 함수가 있으므로, 역할 CRUD를 위한 별도 API는 기존 `roles.py` 백엔드 엔드포인트를 호출합니다. 필요시 `api/roles.js` 신규 생성.

#### 9.1.3 UI 설계

```
┌──────────────────────────────────────────────────────────────┐
│  역할 관리                                      [+ 역할 추가]  │
│ ┌────────┬──────┬──────────┬─────────┬──────┬──────┬───────┐ │
│ │역할 코드│역할명│데이터 범위│ 랜딩페이지│시스템│사용자수│ 액션  │ │
│ ├────────┼──────┼──────────┼─────────┼──────┼──────┼───────┤ │
│ │SYS_ADM │시스템│ GLOBAL   │/admin/..│ ✓   │  1   │ 👁    │ │
│ │TEN_ADM │테넌트│ TENANT   │/admin/..│ ✓   │  3   │ 👁    │ │
│ │USER    │일반  │ USER     │/chat    │ ✓   │ 10   │ 👁    │ │
│ │AUDITOR │감사자│ TENANT   │/admin/..│     │  2   │ ✏ 🗑  │ │
│ └────────┴──────┴──────────┴─────────┴──────┴──────┴───────┘ │
│                                                               │
│  ┌── 역할 상세: AUDITOR (감사자) ────────────────────────┐    │
│  │  역할 코드: AUDITOR                                    │    │
│  │  역할 이름: [감사자        ]                            │    │
│  │  데이터 범위: [TENANT  ▼]                               │    │
│  │  랜딩 페이지: [/admin/dashboard]                        │    │
│  │  설명: [감사 목적으로 이력만 조회하는 역할]               │    │
│  │                                                         │    │
│  │  [저장]  [취소]                                          │    │
│  └─────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

#### 9.1.4 핵심 기능

- 역할 목록 테이블: `role_code`, `role_name`, `scope_type`, `landing_page`, `is_system`, `user_count`
- 시스템 역할(`is_system=true`): 수정/삭제 불가 (읽기 전용, 상세 보기만)
- 커스텀 역할 CRUD: `scope_type` 선택 (GLOBAL/TENANT/USER), `landing_page` 입력
- CRUD 버튼 제어: `hasMenuPermission('ROLE_MGMT', 'create/update/delete')` 기반

### 9.2 테넌트 관리 — `TenantsView.vue`

#### 9.2.1 목표

테넌트(Tenant) CRUD를 구현합니다. SYSTEM_ADMIN만 접근 가능합니다.

#### 9.2.2 산출물

```
수정:
  frontend/src/views/admin/TenantsView.vue   # 스텁 → 완전 구현
```

> `api/tenants.js`는 이미 구현 완료되어 있으므로 그대로 사용합니다.

#### 9.2.3 UI 설계

```
┌──────────────────────────────────────────────────────────────┐
│  테넌트 관리                                  [+ 테넌트 추가]  │
│ ┌────────┬──────────┬──────┬────────┬──────────┬──────────┐  │
│ │코드    │ 이름     │ 상태 │ 사용자수│ 생성일    │ 액션     │  │
│ ├────────┼──────────┼──────┼────────┼──────────┼──────────┤  │
│ │SYSTEM  │ 시스템   │ 활성 │  1     │ 2026-02  │ 👁       │  │
│ │DEMO    │ 데모     │ 활성 │  2     │ 2026-02  │ ✏ 🗑     │  │
│ │COMP_A  │ A회사    │ 활성 │ 15     │ 2026-01  │ ✏ 🗑     │  │
│ └────────┴──────────┴──────┴────────┴──────────┴──────────┘  │
└──────────────────────────────────────────────────────────────┘
```

#### 9.2.4 핵심 기능

- 테넌트 목록: `tenant_code`, `tenant_name`, `is_active`, `user_count`, `created_at`
- 테넌트 생성: `tenant_code` (영문 대문자+숫자+언더스코어), `tenant_name`
- 테넌트 수정: `tenant_name`, `is_active`, `metadata` (JSONB)
- 테넌트 비활성화: soft delete (`is_active = false`)
- CRUD 버튼 제어: `hasMenuPermission('TENANT_MGMT', 'create/update/delete')` 기반

### 9.3 검증 항목

- [ ] 역할 목록: scope_type, landing_page, user_count 표시
- [ ] 시스템 역할 수정/삭제 불가
- [ ] 커스텀 역할 CRUD 정상 동작
- [ ] SYSTEM_ADMIN만 역할 생성/수정/삭제 가능
- [ ] 테넌트 목록: user_count 표시
- [ ] 테넌트 CRUD 정상 동작
- [ ] SYSTEM_ADMIN만 테넌트 관리 접근 가능

---

## 10. Step 7: 인증 필수 모드 전환

### 10.1 목표

Phase 3a(선택적 모드)에서 Phase 3b(필수 모드)로 전환합니다. 모든 API 호출과 페이지 접근에 인증을 요구합니다.

### 10.2 산출물

```
수정:
  app/middleware/auth.py                # Phase 3b: 필수 모드 전환
  frontend/src/router/index.js          # /chat도 인증 필요
  frontend/src/components/layout/AppSidebar.vue  # 폴백 메뉴 제거
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

        if self._is_excluded(path):
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"success": False, "data": None,
                         "error": {"code": "UNAUTHORIZED", "message": "인증이 필요합니다"}}
            )

        token = auth_header[7:]
        try:
            payload = verify_token(token)
            if payload.token_type == "access":
                request.state.current_user = UserContext(
                    user_id=payload.sub, login_id=payload.login_id,
                    tenant_id=payload.tenant_id, role_code=payload.role_code,
                    scope_type=payload.scope_type, is_superuser=payload.is_superuser
                )
            else:
                return JSONResponse(status_code=401, content={...})
        except Exception:
            return JSONResponse(status_code=401, content={...})

        return await call_next(request)
```

### 10.4 `router/index.js` 변경

```javascript
// Step 7: 모든 페이지 인증 필요 (/login과 public 제외)
router.beforeEach(async (to, from, next) => {
  const isAuthenticated = store.getters['auth/isAuthenticated']

  // 공개 페이지
  if (to.meta.public) return next()

  // 로그인 페이지
  if (to.path === '/login') {
    return isAuthenticated ? next(store.getters['auth/landingPage']) : next()
  }

  // 미인증 → 로그인 (모든 페이지)
  if (!isAuthenticated) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  // 관리자 영역 접근 권한 확인
  if (to.path.startsWith('/admin')) {
    if (!store.getters['auth/canAccessAdmin']) {
      return next(store.getters['auth/landingPage'])
    }
    // 메뉴 경로 매칭으로 세부 접근 제어
    const menus = store.state.auth.user?.menus || []
    const targetMenu = menus.find(m => m.menu_path === to.path)
    if (targetMenu && !targetMenu.can_read) {
      return next('/admin/dashboard')
    }
  }

  next()
})
```

### 10.5 `AppSidebar.vue` 변경

```javascript
// Step 7: 폴백 메뉴 제거 (인증 필수이므로 비인증 상태 불가)
const menuItems = computed(() => {
  return sidebarMenus.value  // DB 기반 메뉴만
})
```

### 10.6 검증 항목

- [ ] 토큰 없이 모든 API 호출 → 401
- [ ] 만료된 토큰 → 401 → 자동 refresh → 재시도 성공
- [ ] Refresh Token도 만료 → `/login`으로 리다이렉트
- [ ] `/chat` 미인증 접근 → `/login?redirect=/chat`
- [ ] 로그인 후 `redirect` 파라미터가 있으면 해당 경로로 이동
- [ ] 비인증 폴백 메뉴 제거 확인

---

## 11. 산출물 총괄

### 11.1 전체 파일 목록

```
=== Step 1: Auth Store v2.0 전환 ===
[수정] frontend/src/store/modules/auth.js      # permissions → menus
[수정] frontend/src/views/LoginView.vue         # landing_page 기반 리다이렉트

=== Step 2: 사이드바 동적 메뉴 렌더링 ===
[수정] frontend/src/components/layout/AppSidebar.vue   # 하드코딩 → DB 동적 메뉴
[수정] frontend/src/components/layout/AppHeader.vue    # role_code 표시

=== Step 3: 라우터 가드 메뉴 기반 전환 ===
[수정] frontend/src/router/index.js                    # 메뉴 경로 매칭 가드

=== Step 4: 사용자 관리 v2.0 ===
[수정] frontend/src/views/admin/UsersView.vue          # role_id 단일 + 메뉴 CRUD 체크박스
[수정] frontend/src/api/users.js                       # getUserMenus, updateUserMenus 추가

=== Step 5: 메뉴/권한 관리 (★ 신규) ===
[신규] frontend/src/api/menus.js                       # 메뉴 관리 API 클라이언트
[신규] frontend/src/views/admin/MenusView.vue          # 메뉴 트리 관리 화면
[수정] frontend/src/router/index.js                    # /admin/menus 라우트 추가

=== Step 6: 역할 + 테넌트 관리 ===
[신규] frontend/src/api/roles.js                       # 역할 관리 API 클라이언트 (선택)
[수정] frontend/src/views/admin/RolesView.vue          # 스텁 → 완전 구현
[수정] frontend/src/views/admin/TenantsView.vue        # 스텁 → 완전 구현

=== Step 7: 인증 필수 모드 (Phase 3a → 3b) ===
[수정] app/middleware/auth.py                          # 필수 모드 전환
[수정] frontend/src/router/index.js                    # 모든 페이지 인증 필요
[수정] frontend/src/components/layout/AppSidebar.vue   # 폴백 메뉴 제거
```

### 11.2 파일 수 요약

| 구분 | 신규 | 수정 | 합계 |
|------|:----:|:----:|:----:|
| Step 1 | 0 | 2 | 2 |
| Step 2 | 0 | 2 | 2 |
| Step 3 | 0 | 1 | 1 |
| Step 4 | 0 | 2 | 2 |
| Step 5 | 2 | 1 | 3 |
| Step 6 | 1 | 2 | 3 |
| Step 7 | 0 | 3 | 3 |
| **합계** | **3** | **13** | **16** |

---

## 12. 검증 계획

### 12.1 Step별 검증 흐름

```
Step 1:   auth store v2.0 전환 → hasMenuPermission 동작 확인
     ↓
Step 2:   사이드바 동적 메뉴 → 역할별 메뉴 표시 확인
     ↓
Step 3:   라우터 가드 → 메뉴 경로 매칭 접근 제어
     ↓
Step 4:   사용자 관리 v2.0 → role_id 단일 + 메뉴 CRUD 체크박스
     ↓
Step 5:   메뉴 관리 → 트리 조회/추가/수정/삭제
     ↓
Step 6:   역할/테넌트 관리 → CRUD + scope_type
     ↓
Step 7:   필수 모드 → 미인증 전면 차단
```

### 12.2 역할별 통합 시나리오 테스트

| # | 시나리오 | 예상 결과 |
|---|----------|----------|
| 1 | SYSTEM_ADMIN 로그인 | landing_page `/admin/dashboard`, 10개 관리 메뉴 표시 |
| 2 | TENANT_ADMIN 로그인 | landing_page `/admin/dashboard`, 할당된 메뉴만 표시 (약 6개) |
| 3 | USER 로그인 | landing_page `/chat`, 관리 페이지 접근 불가 |
| 4 | 사용자 생성 (메뉴 권한 포함) → 로그인 | 부여된 메뉴만 사이드바에 표시 |
| 5 | 사용자 메뉴 권한 변경 → 재로그인 | 변경된 메뉴 반영 |
| 6 | DB에서 메뉴 비활성화 → 재로그인 | 해당 메뉴 사이드바에서 사라짐 |
| 7 | 토큰 만료 → 자동 갱신 | 사용자 모르게 토큰 갱신 후 재요청 |
| 8 | Refresh Token 만료 | 로그인 페이지로 리다이렉트 |
| 9 | CRUD 버튼 권한 제어 | can_create=false → 추가 버튼 숨김, can_delete=false → 삭제 버튼 숨김 |
| 10 | 메뉴 트리에 새 메뉴 추가 → 사용자에 할당 → 로그인 | 새 메뉴가 사이드바에 표시 |

### 12.3 테스트 계정 (Phase 1 DDL 초기 데이터)

| login_id | 역할 | scope_type | landing_page | 메뉴 수 |
|----------|------|-----------|-------------|--------|
| `admin` | SYSTEM_ADMIN | GLOBAL | /admin/dashboard | 14 |
| `tenant_admin` | TENANT_ADMIN | TENANT | /admin/dashboard | 9 |
| `user01` | USER | USER | /chat | 4 |

### 12.4 CRUD 권한 세분화 테스트 매트릭스

| 테스트 | 조건 | 예상 결과 |
|--------|------|----------|
| 사용자 관리 - 목록 조회 | USER_MGMT can_read=true | 목록 표시 |
| 사용자 관리 - 추가 버튼 | USER_MGMT can_create=false | 버튼 숨김 |
| 사용자 관리 - 삭제 버튼 | USER_MGMT can_delete=false | 버튼 숨김 |
| 메뉴 관리 - 접근 | MENU_MGMT 없음 | `/admin/dashboard`로 리다이렉트 |
| 검색 이력 - 내보내기 | HISTORY can_export=true | 내보내기 버튼 표시 |
| 검색 이력 - 내보내기 | HISTORY can_export=false | 내보내기 버튼 숨김 |
