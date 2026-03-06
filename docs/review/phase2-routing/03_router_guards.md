# 3. 네비게이션 가드 - 인증과 권한 체크

> **파일 위치**: `frontend/src/router/index.js` (149~197줄)

## 네비게이션 가드란?

사용자가 페이지를 이동할 때 **"이 사용자가 이 페이지에 가도 되는가?"**를 판단하는 **보안 검문소**입니다.

```
사용자가 URL 이동 요청
    │
    ▼
┌── beforeEach 가드 (이동 "전" 실행) ──┐
│                                      │
│  "로그인했나? 권한있나? 확인!"          │
│                                      │
│  ├─ 통과 → next()       → 이동 허용   │
│  └─ 차단 → next('/login') → 로그인으로 │
│                                      │
└──────────────────────────────────────┘
    │
    ▼ (통과한 경우)
┌── afterEach 가드 (이동 "후" 실행) ───┐
│                                      │
│  "브라우저 탭 제목을 바꿔야지"          │
│                                      │
└──────────────────────────────────────┘
    │
    ▼
화면 표시!
```

## afterEach - 페이지 타이틀 변경

```javascript
router.afterEach((to) => {
  const appTitle = import.meta.env.VITE_APP_TITLE || 'MUREUM'
  document.title = to.meta.title ? `${to.meta.title} - ${appTitle}` : appTitle
})
```

**한 줄씩 이해하기:**

```javascript
// to = 이동한 목적지 라우트 객체

const appTitle = import.meta.env.VITE_APP_TITLE || 'MUREUM'
// .env 파일에서 앱 제목을 읽음. 없으면 'MUREUM' 사용

document.title = to.meta.title
  ? `${to.meta.title} - ${appTitle}`   // meta.title 있으면: "사용자 관리 - MUREUM"
  : appTitle                            // meta.title 없으면: "MUREUM"
```

**결과:**
```
/login           → 브라우저 탭: "로그인 - MUREUM"
/chat            → 브라우저 탭: "MUREUM"  (meta.title 없음)
/admin/users     → 브라우저 탭: "사용자 관리 - MUREUM"
/admin/dashboard → 브라우저 탭: "대시보드 - MUREUM"
```

이 가드는 단순하고 안전합니다. **차단 기능 없이** 부가 작업만 수행합니다.

---

## beforeEach - 인증/권한 가드 ⭐⭐⭐

이것이 이 파일에서 **가장 중요한 코드**입니다. 4단계로 분석합니다.

### 전체 코드

```javascript
router.beforeEach((to, from, next) => {
  const isAuthenticated = store.getters['auth/isAuthenticated']

  // 1. 로그인 페이지: 이미 인증됐으면 랜딩 페이지로
  if (to.path === '/login') {
    if (isAuthenticated) {
      return next(store.getters['auth/landingPage'])
    }
    return next()
  }

  // 2. 공개 페이지: 인증 불필요
  if (to.meta.public) return next()

  // 3. 관리자 페이지: 인증 + 메뉴 권한 필요
  if (to.meta.requiresAdmin || to.matched.some(r => r.meta.requiresAdmin)) {
    if (!isAuthenticated) {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }
    const canAdmin = store.getters['auth/canAccessAdmin']
    if (!canAdmin) {
      return next('/chat')
    }
    const menuCode = to.meta.menuCode
    if (menuCode) {
      const hasAccess = store.getters['auth/hasMenuPermission'](menuCode, 'read')
      if (!hasAccess) {
        return next(store.getters['auth/landingPage'])
      }
    }
    return next()
  }

  // 4. 일반 페이지: 인증 필요
  if (!isAuthenticated) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }
  next()
})
```

### 매개변수 이해하기

```javascript
router.beforeEach((to, from, next) => { ... })
```

| 매개변수 | 의미 | 예시 |
|----------|------|------|
| `to` | **가려는** 라우트 | `{ path: '/admin/users', meta: { menuCode: 'USER_MGMT' } }` |
| `from` | **현재** 라우트 (어디에서 왔는가) | `{ path: '/admin/dashboard' }` |
| `next` | **이동 제어** 함수 | `next()` = 통과, `next('/login')` = 리다이렉트 |

**next() 사용법:**
```javascript
next()                 // ✅ 통과! 목적지로 이동
next('/login')         // 🔄 /login으로 리다이렉트
next({ path: '/login', query: { redirect: '/admin/users' } })
                       // 🔄 /login으로 보내되, 원래 가려던 URL을 쿼리에 저장
next(false)            // ❌ 이동 취소 (현재 페이지에 머묾)
```

---

### 단계 1: 로그인 페이지 처리

```javascript
// 1. 로그인 페이지: 이미 인증됐으면 랜딩 페이지로
if (to.path === '/login') {
  if (isAuthenticated) {
    return next(store.getters['auth/landingPage'])
  }
  return next()
}
```

```
시나리오 A: 비로그인 사용자 → /login
  to.path === '/login' ✅
  isAuthenticated === false
  → next() 호출 → 로그인 화면 표시 ✅

시나리오 B: 이미 로그인한 사용자 → /login
  to.path === '/login' ✅
  isAuthenticated === true
  → next(landingPage) 호출 → 랜딩 페이지로 보냄
  → 관리자면 /admin/dashboard, 일반 사용자면 /chat
  → "이미 로그인했는데 왜 로그인 페이지에 가?" 를 방지
```

**landingPage란?** 역할에 따라 달라지는 기본 페이지:

| 역할 | landingPage |
|------|-------------|
| GLOBAL (전체 관리자) | `/admin/dashboard` |
| TENANT (테넌트 관리자) | `/admin/dashboard` |
| USER (일반 사용자) | `/chat` |

---

### 단계 2: 공개 페이지 처리

```javascript
// 2. 공개 페이지: 인증 불필요
if (to.meta.public) return next()
```

`meta: { public: true }`가 설정된 라우트는 무조건 통과. 현재는 로그인 페이지만 해당됩니다.

(단계 1에서 이미 `/login`을 처리했으므로, 미래에 다른 공개 페이지가 추가될 때를 대비한 코드)

---

### 단계 3: 관리자 페이지 처리 ⭐⭐

```javascript
// 3. 관리자 페이지: 인증 + 메뉴 권한 필요
if (to.meta.requiresAdmin || to.matched.some(r => r.meta.requiresAdmin)) {
```

**`to.matched.some(r => r.meta.requiresAdmin)`가 필요한 이유:**

```javascript
// 부모 라우트
{ path: '/admin', meta: { requiresAdmin: true }, children: [
  // 자식 라우트 - 자체적으로 requiresAdmin이 없음!
  { path: 'users', meta: { menuCode: 'USER_MGMT' } }
]}

// /admin/users 접속 시:
to.meta.requiresAdmin → undefined (자식에는 없으니까)
to.matched → [부모 라우트, 자식 라우트] (매칭된 모든 라우트)
to.matched.some(r => r.meta.requiresAdmin) → true! (부모에 있으니까)

// matched를 안 쓰면?
// → 자식 라우트에 전부 requiresAdmin을 넣어야 함 (중복!)
```

**3단계 권한 체크 플로우:**

```
/admin/users 접속 시도
│
├─ ① 로그인 했는가?
│   ├─ NO  → /login?redirect=/admin/users  (로그인 후 원래 페이지로)
│   └─ YES → 다음 체크
│
├─ ② 관리자 역할인가? (canAccessAdmin)
│   ├─ NO  → /chat  (일반 사용자용 페이지로)
│   └─ YES → 다음 체크
│
├─ ③ 이 메뉴의 read 권한이 있는가? (menuCode: 'USER_MGMT')
│   ├─ NO  → landingPage  (접근 가능한 기본 페이지로)
│   └─ YES → 통과! ✅
│
└─ next() → /admin/users 화면 표시
```

**코드를 다시 한줄씩:**

```javascript
// ① 로그인 체크
if (!isAuthenticated) {
  return next({ path: '/login', query: { redirect: to.fullPath } })
  //                                     ^^^^^^^^^^^^^^^^^^^^^^^^
  //  원래 가려던 URL을 저장! 로그인 후 돌아올 수 있도록
}

// ② 관리자 역할 체크
const canAdmin = store.getters['auth/canAccessAdmin']
// canAccessAdmin = GLOBAL 또는 TENANT 역할인지 확인
if (!canAdmin) {
  return next('/chat')   // USER 역할은 관리자 페이지에 못 감
}

// ③ 메뉴 권한 체크
const menuCode = to.meta.menuCode    // 예: 'USER_MGMT'
if (menuCode) {
  const hasAccess = store.getters['auth/hasMenuPermission'](menuCode, 'read')
  // hasMenuPermission('USER_MGMT', 'read')
  // → 이 사용자가 사용자 관리 메뉴의 읽기 권한이 있는가?
  if (!hasAccess) {
    return next(store.getters['auth/landingPage'])
  }
}
return next()   // 모든 체크 통과! 이동 허용
```

---

### 단계 4: 일반 페이지 처리

```javascript
// 4. 일반 페이지 (/chat 등): 인증 필요
if (!isAuthenticated) {
  return next({ path: '/login', query: { redirect: to.fullPath } })
}
next()
```

- `/chat`, `/dashboard` 같은 일반 페이지는 로그인만 확인
- 로그인 안 했으면 → `/login`으로 보냄
- 로그인 했으면 → 통과

---

## redirect 쿼리 파라미터의 활용

```javascript
next({ path: '/login', query: { redirect: to.fullPath } })
```

이 코드가 만드는 URL: `/login?redirect=/admin/users`

```
[로그인 전]
사용자: /admin/users 접속 시도
  → 비로그인 → /login?redirect=/admin/users 로 이동
  → 로그인 화면에서 ID/PW 입력

[로그인 후]
LoginView.vue에서:
  const redirect = route.query.redirect    // "/admin/users"
  router.push(redirect || '/chat')          // 원래 가려던 페이지로!

→ 사용자 입장에서 자연스러운 흐름!
→ /admin/users 가려다가 로그인하면, 다시 /admin/users로 감
```

## 전체 가드 동작 플로우차트

```
beforeEach 시작
│
├─ 가려는 곳이 /login인가?
│   ├─ YES ─ 이미 로그인? ─ YES → landingPage로 ─────────────┐
│   │                       NO  → next() (로그인 화면 표시) ──┤
│   └─ NO                                                    │
│       │                                                    │
│       ├─ public 페이지인가?                                  │
│       │   ├─ YES → next() (무조건 통과) ──────────────────┤
│       │   └─ NO                                           │
│       │       │                                           │
│       │       ├─ admin 페이지인가?                          │
│       │       │   ├─ YES                                  │
│       │       │   │   ├─ 로그인? ── NO → /login ──────────┤
│       │       │   │   │            YES                    │
│       │       │   │   │    ├─ 관리자? ── NO → /chat ─────┤
│       │       │   │   │    │             YES              │
│       │       │   │   │    │    ├─ 메뉴권한? ── NO → landing
│       │       │   │   │    │    │               YES       │
│       │       │   │   │    │    └─ next() ✅ ─────────────┤
│       │       │   │   │    │                              │
│       │       │   └─ NO (일반 페이지)                       │
│       │       │       ├─ 로그인? ── NO → /login ──────────┤
│       │       │       │            YES                    │
│       │       │       └─ next() ✅ ───────────────────────┤
│       │       │                                           │
└───────┴───────┴───────────────────────────────────────────┘
                                                     화면 표시!
```

## 리뷰 체크리스트

- [x] 비로그인 사용자의 접근이 차단되는가? → 모든 비공개 페이지에서 체크 ✅
- [x] 로그인 페이지 무한 루프가 없는가? → 로그인된 상태면 landingPage로 ✅
- [x] 관리자 권한이 3단계로 체크되는가? → 인증 → 역할 → 메뉴 권한 ✅
- [x] 리다이렉트 URL이 보존되는가? → `query: { redirect: to.fullPath }` ✅
- [x] 중첩 라우트에서도 가드가 동작하는가? → `to.matched.some()` 사용 ✅
- [x] 페이지 타이틀이 업데이트되는가? → afterEach에서 처리 ✅
- [ ] 보안: URL 직접 입력(주소창)으로도 가드가 동작하는가? → 동작함 (beforeEach는 모든 이동에 적용)

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **beforeEach** | 모든 페이지 이동 **전**에 실행. 인증/권한 체크 |
| **afterEach** | 모든 페이지 이동 **후**에 실행. 부가 작업 (타이틀 등) |
| **next()** | 이동 허용 |
| **next('/path')** | 다른 경로로 리다이렉트 |
| **to.matched** | 현재 라우트 + 부모 라우트 배열 (중첩 라우트 체크에 필수) |
| **isAuthenticated** | Vuex에서 가져온 로그인 여부 |
| **canAccessAdmin** | GLOBAL/TENANT 역할인지 확인 |
| **hasMenuPermission** | 특정 메뉴의 특정 권한(CRUD) 확인 |

---
> **이전**: [02_route_definitions.md](02_route_definitions.md) - 라우트 정의
> **다음**: [04_how_it_works.md](04_how_it_works.md) - 동작 원리 종합
