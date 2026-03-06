# 1. Vue Router란? - 핵심 개념

> **파일 위치**: `frontend/src/router/index.js`

## Vue Router가 필요한 이유

Phase 1에서 배웠듯이, SPA는 HTML 파일이 **하나**뿐입니다. 그런데 우리 앱에는 로그인, 채팅, 관리자 페이지 등 **여러 화면**이 있습니다. 이 화면들을 URL에 따라 전환해주는 것이 **Vue Router**입니다.

```
[Vue Router가 없다면]
http://localhost:19080       → 항상 같은 화면만 보임 😢

[Vue Router가 있으면]
http://localhost:19080/login       → 로그인 화면
http://localhost:19080/chat        → 채팅 화면
http://localhost:19080/admin/users → 사용자 관리 화면
URL만 바꾸면 화면이 바뀜! (페이지 새로고침 없이!) 🎉
```

## 라우터의 3가지 핵심 개념

### 1. 라우트(Route) - "URL과 화면의 매핑 규칙"

```javascript
{
  path: '/login',                                      // URL 경로
  name: 'Login',                                       // 라우트 이름 (고유)
  component: () => import('@/views/LoginView.vue'),    // 표시할 화면
  meta: { title: '로그인', public: true }               // 부가 정보
}
```

```
비유: 전화번호부

이름      | 전화번호
─────────|──────────
Login     | /login     → LoginView.vue
UserChat  | /chat      → UserChatLayout.vue
AdminUsers| /admin/users → UsersView.vue
```

### 2. 라우터(Router) - "URL 변경을 감지하고 화면을 바꾸는 엔진"

```javascript
const router = createRouter({
  history: createWebHistory(),    // URL 모드 설정
  routes                          // 위에서 정의한 라우트 목록
})
```

**`createWebHistory()`의 의미:**

```
[History 모드] ← 이 프로젝트가 사용하는 방식
  http://localhost:19080/admin/users
  깔끔한 URL! 일반 웹사이트처럼 보임

[Hash 모드] (대안)
  http://localhost:19080/#/admin/users
  URL에 #이 붙음. 서버 설정 불필요하지만 덜 깔끔함
```

### 3. 라우터 뷰(`<router-view>`) - "화면이 표시되는 자리"

```
App.vue:
┌────────────────────────────┐
│  <router-view />            │  ← 여기에 현재 URL에 맞는 화면이 들어감
└────────────────────────────┘

URL = /login 일 때:
┌────────────────────────────┐
│  ┌──────────────────────┐  │
│  │   LoginView.vue       │  │
│  │   [아이디] [비밀번호]  │  │
│  │   [로그인 버튼]        │  │
│  └──────────────────────┘  │
└────────────────────────────┘

URL = /chat 일 때:
┌────────────────────────────┐
│  ┌──────────────────────┐  │
│  │  UserChatLayout.vue   │  │
│  │  [사이드바] [채팅창]   │  │
│  └──────────────────────┘  │
└────────────────────────────┘
```

## 코드의 기본 구조

`router/index.js` 파일은 크게 **4개 파트**로 구성됩니다:

```javascript
// ──── Part 1: import ────
import { createRouter, createWebHistory } from 'vue-router'
import store from '@/store'

// ──── Part 2: 라우트 정의 (routes 배열) ────
const routes = [
  { path: '/login', ... },
  { path: '/chat', ... },
  { path: '/admin', children: [...] },
  ...
]

// ──── Part 3: 라우터 생성 ────
const router = createRouter({
  history: createWebHistory(),
  routes
})

// ──── Part 4: 네비게이션 가드 ────
router.afterEach(...)     // 페이지 이동 "후" 실행 (타이틀 변경)
router.beforeEach(...)    // 페이지 이동 "전" 실행 (인증/권한 체크)

export default router
```

## Lazy Loading (지연 로딩) ⭐

이 프로젝트의 모든 화면 컴포넌트는 **Lazy Loading** 방식으로 import됩니다:

```javascript
// ❌ 일반 import (Eager Loading)
import LoginView from '@/views/LoginView.vue'
// → 앱이 시작될 때 모든 화면을 한꺼번에 로드
// → 첫 화면이 뜨는데 오래 걸림

// ✅ 동적 import (Lazy Loading) - 이 프로젝트 방식
component: () => import('@/views/LoginView.vue')
// → 해당 URL에 접근할 때만 로드
// → 첫 화면은 빠르게, 나머지는 필요할 때 로드
```

**비유:**
```
[Eager Loading]
도서관에 가서 책 500권을 모두 빌려온 뒤에야 첫 책을 읽기 시작 📚📚📚

[Lazy Loading]
도서관에 가서 읽을 책 1권만 빌려옴. 다 읽으면 다음 책 빌리러 감 📖
→ 처음 시작이 훨씬 빠름!
```

**실제 효과:**
```
                     Eager Loading       Lazy Loading
첫 화면 로딩 시간      느림 (3초+)         빠름 (1초)
번들 크기             하나의 큰 파일       여러 작은 파일
네트워크 요청         1번 (큰 파일)       여러 번 (작은 파일)
사용하지 않는 코드     모두 다운로드        안 됨
```

## meta 속성 - 라우트의 부가 정보

각 라우트에 `meta` 객체로 추가 정보를 붙일 수 있습니다:

```javascript
{
  path: '/login',
  meta: {
    title: '로그인',      // 브라우저 탭 제목
    public: true          // 로그인 없이 접근 가능
  }
}

{
  path: 'users',
  meta: {
    title: '사용자 관리',
    menuCode: 'USER_MGMT'  // 이 메뉴 권한이 있어야 접근 가능
  }
}
```

이 meta 정보는 **네비게이션 가드**에서 읽어서 권한을 체크합니다. (03_router_guards.md에서 자세히 설명)

```
meta는 "라우트에 붙이는 메모지"

라우트 정의 시:  meta: { title: '로그인', public: true }
가드에서 읽을 때: to.meta.public === true → "공개 페이지구나, 통과!"
타이틀 변경 시:  to.meta.title → "로그인" → 탭 제목 변경
```

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **Route** | URL ↔ 화면의 매핑 규칙 하나 |
| **Router** | 모든 Route를 관리하고 URL 변경을 처리하는 엔진 |
| **`<router-view>`** | 현재 URL에 맞는 화면이 표시되는 자리 |
| **createWebHistory** | 깔끔한 URL 사용 (`/admin/users`) |
| **Lazy Loading** | `() => import(...)` 형태, 필요할 때만 로드 |
| **meta** | 라우트의 부가 정보 (제목, 권한코드, 공개 여부 등) |

---
> **다음**: [02_route_definitions.md](02_route_definitions.md) - 라우트 정의 상세
