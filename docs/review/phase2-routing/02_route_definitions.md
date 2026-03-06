# 2. 라우트 정의 - URL과 화면의 매핑

> **파일 위치**: `frontend/src/router/index.js` (4~142줄)

## 이 코드가 하는 일

"어떤 URL에 접속하면 어떤 화면을 보여줄 것인가"를 정의합니다.

## 라우트 유형 4가지

이 프로젝트의 라우트는 **4가지 유형**으로 분류됩니다:

```
routes 배열
│
├─ ① 리다이렉트 라우트    → 다른 URL로 자동 이동
├─ ② 공개 라우트          → 로그인 없이 접근 가능
├─ ③ 일반 사용자 라우트    → 로그인만 하면 접근 가능
├─ ④ 관리자 라우트 (중첩)  → 로그인 + 관리자 권한 필요
└─ ⑤ 404 라우트           → 존재하지 않는 URL 처리
```

---

### ① 리다이렉트 라우트

```javascript
{
  path: '/',
  redirect: '/chat'
}
```

- `/` (루트)에 접속하면 `/chat`으로 자동 이동
- 화면 컴포넌트 없이 **방향 전환만** 수행

```
사용자: http://localhost:19080/ 접속
  ↓
라우터: "/ 는 /chat으로 가라고 되어있네"
  ↓
자동으로 http://localhost:19080/chat 으로 이동
```

---

### ② 공개 라우트 (로그인 불필요)

```javascript
{
  path: '/login',
  name: 'Login',
  component: () => import('@/views/LoginView.vue'),
  meta: { title: '로그인', public: true }    // ⭐ public: true
}
```

- `meta.public: true` → 로그인 없이 접근 가능
- 현재 이 프로젝트에서 공개 라우트는 **로그인 페이지뿐**

---

### ③ 일반 사용자 라우트

```javascript
// 채팅 화면
{
  path: '/chat',
  name: 'UserChat',
  component: () => import('@/components/user/UserChatLayout.vue')
}

// 개인 대시보드
{
  path: '/dashboard',
  name: 'PersonalDashboard',
  component: () => import('@/views/user/PersonalDashboardView.vue'),
  meta: { title: '나의 대시보드', requiresAuth: true }
}
```

- 로그인한 모든 사용자가 접근 가능
- 관리자 권한 불필요

---

### ④ 관리자 라우트 (중첩 라우트) ⭐⭐

이것이 이 파일에서 **가장 중요하고 복잡한 부분**입니다:

```javascript
{
  path: '/admin',
  component: () => import('@/views/admin/AdminLayout.vue'),
  meta: { requiresAdmin: true },     // ⭐ 관리자 전용!
  children: [                         // ⭐ 중첩 라우트!
    { path: '',          redirect: '/admin/dashboard' },
    { path: 'dashboard', component: DashboardView,  meta: { menuCode: 'DASHBOARD' } },
    { path: 'chat',      component: ChatView,        meta: { menuCode: 'AI_SEARCH' } },
    { path: 'users',     component: UsersView,       meta: { menuCode: 'USER_MGMT' } },
    // ... 더 많은 자식 라우트
  ]
}
```

**중첩 라우트(Nested Routes)란?**

```
일반 라우트:
  /login  → LoginView.vue (전체 화면을 차지)
  /chat   → UserChatLayout.vue (전체 화면을 차지)

중첩 라우트:
  /admin/dashboard → AdminLayout.vue 안에 DashboardView.vue
  /admin/users     → AdminLayout.vue 안에 UsersView.vue
  /admin/roles     → AdminLayout.vue 안에 RolesView.vue

  AdminLayout(사이드바+헤더)는 고정, 안쪽 내용만 바뀜!
```

**화면 구조로 보면:**

```
/admin/users 에 접속했을 때:

┌─ AdminLayout.vue ──────────────────────────┐
│ ┌─ AppSidebar ─┐ ┌─ AppHeader ──────────┐  │
│ │ 대시보드      │ │ MUREUM    [사용자명] │  │
│ │ 자연어 검색   │ └─────────────────────┘  │
│ │ 지식문서 관리  │                          │
│ │ ► 사용자 관리  │ ┌─ <router-view> ─────┐  │
│ │ 역할 관리     │ │                      │  │
│ │ 테넌트 관리   │ │  UsersView.vue       │  │  ← children의 화면
│ │ 메뉴 관리     │ │  사용자 목록 표시     │  │
│ │ ...          │ │                      │  │
│ └──────────────┘ └──────────────────────┘  │
└────────────────────────────────────────────┘

/admin/roles 로 이동하면:

┌─ AdminLayout.vue ──────────────────────────┐
│ ┌─ AppSidebar ─┐ ┌─ AppHeader ──────────┐  │
│ │ (동일)       │ │ (동일)               │  │
│ │              │ └─────────────────────┘  │
│ │              │                          │
│ │              │ ┌─ <router-view> ─────┐  │
│ │              │ │                      │  │
│ │              │ │  RolesView.vue       │  │  ← 이 부분만 바뀜!
│ │              │ │  역할 목록 표시       │  │
│ │              │ │                      │  │
│ └──────────────┘ └──────────────────────┘  │
└────────────────────────────────────────────┘
```

**왜 중첩 라우트를 사용하는가?**

```
[중첩 없이 - 나쁜 방법] ❌
/admin/users → 사이드바 + 헤더 + 사용자 목록  (전부 매번 다시 렌더링)
/admin/roles → 사이드바 + 헤더 + 역할 목록    (사이드바, 헤더가 깜빡!)

[중첩 사용 - 좋은 방법] ✅
/admin/users → AdminLayout(고정) + 사용자 목록만 교체
/admin/roles → AdminLayout(고정) + 역할 목록만 교체
→ 사이드바, 헤더가 깜빡이지 않음! 부드러운 전환!
```

---

### ⑤ 404 라우트 (없는 페이지 처리)

```javascript
{
  path: '/:pathMatch(.*)*',
  redirect: '/'
}
```

- `/:pathMatch(.*)*` → **모든 URL**에 매칭 (위의 라우트에 매칭되지 않은 것만)
- 존재하지 않는 URL로 접속하면 `/`로 보냄 → `/chat`으로 리다이렉트

```
사용자: http://localhost:19080/xyz 접속
  ↓
라우터: "/xyz? 그런 페이지 없는데... 위 라우트에 다 안 걸리네"
  ↓
/:pathMatch(.*)* 에 걸림 → / 로 리다이렉트 → /chat으로 이동
```

**주의**: 이 라우트는 반드시 배열의 **맨 마지막**에 있어야 합니다. 위에 있으면 모든 URL을 가로챕니다!

---

## 관리자 라우트 전체 목록

| path | name | 화면 | menuCode | 설명 |
|------|------|------|----------|------|
| `/admin` | - | AdminLayout | - | 레이아웃 (사이드바+헤더) |
| `/admin/dashboard` | AdminDashboard | DashboardView | DASHBOARD | 시스템 대시보드 |
| `/admin/chat` | AdminChat | ChatView | AI_SEARCH | 자연어 검색 |
| `/admin/documents` | AdminDocuments | DocumentsView | DOC_MGMT | 지식문서 목록 |
| `/admin/documents/new` | AdminDocumentNew | DocumentEditView | DOC_MGMT | 새 문서 등록 |
| `/admin/documents/:id` | AdminDocumentDetail | DocumentDetailView | DOC_MGMT | 문서 상세 |
| `/admin/documents/:id/edit` | AdminDocumentEdit | DocumentEditView | DOC_MGMT | 문서 수정 |
| `/admin/settings` | AdminSettings | SettingsView | SYS_SETTING | 시스템 설정 |
| `/admin/codes` | AdminCodes | CodesView | CODE_MGMT | 코드 관리 |
| `/admin/history` | AdminHistory | HistoryView | SEARCH_HIST | 검색 이력 |
| `/admin/history/:requestId` | AdminHistoryDetail | HistoryDetailView | SEARCH_HIST | 이력 상세 |
| `/admin/users` | AdminUsers | UsersView | USER_MGMT | 사용자 관리 |
| `/admin/roles` | AdminRoles | RolesView | ROLE_MGMT | 역할 관리 |
| `/admin/tenants` | AdminTenants | TenantsView | TENANT_MGMT | 테넌트 관리 |
| `/admin/menus` | AdminMenus | MenusView | MENU_MGMT | 메뉴 관리 |
| `/admin/departments` | AdminDepartments | DepartmentsView | DEPT_MGMT | 조직 관리 |

## 동적 라우트 파라미터 (`:id`, `:requestId`)

```javascript
{ path: 'documents/:id', ... }
{ path: 'history/:requestId', ... }
```

`:id`는 **변하는 값**을 의미합니다:

```
/admin/documents/1     → :id = 1
/admin/documents/42    → :id = 42
/admin/documents/100   → :id = 100

하나의 라우트 정의로 여러 문서를 처리!
```

컴포넌트 안에서 이 값을 읽는 방법:
```javascript
// DocumentDetailView.vue에서
import { useRoute } from 'vue-router'
const route = useRoute()
const documentId = route.params.id    // "42"
```

## 라우트 정의 순서가 중요한 이유 ⭐

```javascript
// documents 관련 라우트:
{ path: 'documents',          ... },   // /admin/documents
{ path: 'documents/new',      ... },   // /admin/documents/new
{ path: 'documents/:id',      ... },   // /admin/documents/42
{ path: 'documents/:id/edit', ... },   // /admin/documents/42/edit
```

**`documents/new`가 `documents/:id`보다 앞에 있어야 합니다!**

```
만약 :id 가 먼저라면:
  /admin/documents/new → :id = "new" 로 해석됨! 😱
  → 문서 ID가 "new"인 문서를 찾으려 함... 에러!

현재 순서(올바름):
  /admin/documents/new → 정확히 "new" 경로에 매칭 ✅
  /admin/documents/42  → :id = "42" 로 매칭 ✅
```

## 리뷰 체크리스트

- [x] 모든 화면에 대한 라우트가 정의되어 있는가? → 16개 관리자 + 3개 일반 ✅
- [x] Lazy Loading을 사용하는가? → 모든 component에 `() => import(...)` ✅
- [x] 중첩 라우트가 적절히 사용되는가? → `/admin` 하위 children ✅
- [x] 404 처리가 있는가? → `/:pathMatch(.*)*` → `/` ✅
- [x] 고정 경로가 동적 경로보다 앞에 있는가? → `documents/new`가 `documents/:id`보다 앞 ✅
- [x] `menuCode`가 모든 관리자 라우트에 있는가? → 권한 체크를 위해 필수 ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **redirect** | 다른 URL로 자동 이동 |
| **meta.public** | `true`면 로그인 없이 접근 가능 |
| **meta.requiresAdmin** | `true`면 관리자 권한 필요 |
| **meta.menuCode** | 특정 메뉴 권한 코드 (가드에서 체크) |
| **children** | 중첩 라우트. 부모 레이아웃 안에서 자식 화면만 교체 |
| **`:id`** | 동적 파라미터. URL의 변하는 부분을 변수로 받음 |
| **`/:pathMatch(.*)*`** | 모든 URL에 매칭. 404 처리에 사용 |

---
> **이전**: [01_router_basics.md](01_router_basics.md) - Vue Router 핵심 개념
> **다음**: [03_router_guards.md](03_router_guards.md) - 네비게이션 가드 (인증 + 권한)
