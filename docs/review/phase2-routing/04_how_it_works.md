# 4. 동작 원리 종합 - 시나리오별 흐름

## 실제 시나리오로 이해하기

라우터의 모든 개념을 배웠으니, 이제 **실제 사용자의 행동**에 따라 코드가 어떻게 동작하는지 추적해봅니다.

---

## 시나리오 1: 처음 방문한 사용자

**상황**: 로그인한 적 없는 사용자가 `http://localhost:19080`에 접속

```
① 브라우저: http://localhost:19080/ 요청

② 라우트 매칭:
   path: '/' → redirect: '/chat'
   → /chat 으로 리다이렉트 시도

③ beforeEach 가드 실행 (to = /chat):
   /login인가? → NO
   public인가? → NO
   admin인가? → NO
   일반 페이지 → 로그인 체크
   isAuthenticated = false (토큰 없음)
   → next({ path: '/login', query: { redirect: '/chat' } })

④ 다시 beforeEach 실행 (to = /login):
   /login인가? → YES
   isAuthenticated = false
   → next()  ← 통과!

⑤ LoginView.vue 렌더링

⑥ afterEach 실행:
   document.title = "로그인 - MUREUM"

결과: 사용자는 로그인 화면을 봄
URL: http://localhost:19080/login?redirect=/chat
```

---

## 시나리오 2: 로그인 성공 (일반 사용자)

**상황**: USER 역할 사용자가 로그인에 성공

```
① LoginView.vue에서 로그인 성공:
   store.dispatch('auth/login', { id, password })
   → 토큰 저장, 사용자 정보 저장
   → isAuthenticated = true, roleCode = 'USER'

② 리다이렉트 URL 확인:
   route.query.redirect = '/chat'
   → router.push('/chat')

③ beforeEach 가드 실행 (to = /chat):
   /login인가? → NO
   public인가? → NO
   admin인가? → NO
   일반 페이지 → 로그인 체크
   isAuthenticated = true ✅
   → next()  ← 통과!

④ UserChatLayout.vue 렌더링

⑤ afterEach 실행:
   document.title = "MUREUM"  (meta.title 없음)

결과: 사용자는 채팅 화면을 봄
```

---

## 시나리오 3: 로그인 성공 (관리자)

**상황**: GLOBAL 역할 사용자가 로그인에 성공

```
① LoginView.vue에서 로그인 성공:
   roleCode = 'GLOBAL', landingPage = '/admin/dashboard'

② 리다이렉트:
   router.push(landingPage)  → /admin/dashboard

③ beforeEach 가드 실행 (to = /admin/dashboard):
   /login인가? → NO
   public인가? → NO
   admin인가? → YES (to.matched에 requiresAdmin 있음)
     ├─ 로그인? → YES ✅
     ├─ canAccessAdmin? → YES (GLOBAL 역할) ✅
     └─ menuCode 'DASHBOARD'의 read 권한? → YES ✅
   → next()  ← 통과!

④ AdminLayout.vue + DashboardView.vue 렌더링

⑤ afterEach 실행:
   document.title = "대시보드 - MUREUM"

결과: 관리자는 대시보드를 봄
```

---

## 시나리오 4: 권한 없는 페이지 접근 시도

**상황**: TENANT 역할 사용자가 메뉴 관리(MENU_MGMT) 권한 없이 `/admin/menus` 접속 시도

```
① 사용자: /admin/menus 접속 시도

② beforeEach 가드 실행 (to = /admin/menus):
   /login인가? → NO
   public인가? → NO
   admin인가? → YES
     ├─ 로그인? → YES ✅
     ├─ canAccessAdmin? → YES (TENANT 역할) ✅
     └─ menuCode 'MENU_MGMT'의 read 권한?
        hasMenuPermission('MENU_MGMT', 'read')
        → false ❌ (이 사용자에게 MENU_MGMT 권한이 없음)
   → next(landingPage)  → /admin/dashboard로 리다이렉트

③ 다시 beforeEach 실행 (to = /admin/dashboard):
   admin + 로그인 + canAdmin + DASHBOARD read 권한
   → 모두 통과 ✅

결과: 사용자는 대시보드로 보내짐 (메뉴 관리 대신)
```

---

## 시나리오 5: 일반 사용자가 관리자 페이지 접근 시도

**상황**: USER 역할 사용자가 주소창에 `/admin/users` 직접 입력

```
① 사용자: /admin/users 접속 시도

② beforeEach 가드 실행 (to = /admin/users):
   /login인가? → NO
   public인가? → NO
   admin인가? → YES
     ├─ 로그인? → YES ✅
     └─ canAccessAdmin? → false ❌ (USER 역할은 관리자 아님)
   → next('/chat')  → 채팅 화면으로 리다이렉트

결과: 사용자는 채팅 화면으로 보내짐
→ 관리자 페이지에 절대 접근 불가!
```

---

## 시나리오 6: 이미 로그인한 상태에서 /login 접속

**상황**: 로그인된 상태에서 뒤로가기로 `/login`에 도달

```
① 사용자: /login 접속 (뒤로가기 등)

② beforeEach 가드 실행 (to = /login):
   /login인가? → YES
   isAuthenticated → true
   → next(landingPage)  → 역할에 따른 기본 페이지로

결과: 로그인 화면을 다시 보지 않음
→ "이미 로그인했는데 왜 로그인 화면이야?" 방지
```

---

## 시나리오 7: 존재하지 않는 URL 접속

**상황**: `/admin/xyz` 또는 `/blahblah` 접속

```
① 사용자: /blahblah 접속 시도

② 라우트 매칭:
   /blahblah → 일치하는 라우트 없음
   → /:pathMatch(.*)*  에 걸림
   → redirect: '/'
   → /chat 으로 다시 리다이렉트

결과: 채팅 화면으로 보내짐 (404 페이지 없음)
```

---

## 라우터와 Vuex Store의 연계

라우터 가드는 **Vuex Store의 getter**를 사용해서 인증/권한을 판단합니다:

```
router/index.js                     store/modules/auth.js
─────────────────                   ────────────────────

isAuthenticated ◄────────────────── getters.isAuthenticated
  "로그인 했는가?"                    token && user 가 있는가?

canAccessAdmin ◄─────────────────── getters.canAccessAdmin
  "관리자 역할인가?"                   GLOBAL 또는 TENANT 역할인가?

landingPage ◄────────────────────── getters.landingPage
  "기본 페이지는?"                     역할에 따른 기본 페이지 URL

hasMenuPermission ◄──────────────── getters.hasMenuPermission
  "메뉴 권한이 있는가?"                user.menus에서 해당 권한 확인
```

이 연결 관계는 **Phase 3 (상태 관리)**에서 자세히 다룹니다.

---

## 프론트엔드 가드의 한계 (중요!)

```
⚠️  프론트엔드 라우터 가드는 "편의 기능"이지 "보안 기능"이 아닙니다!

  브라우저의 JavaScript는 사용자가 조작할 수 있습니다.
  개발자 도구를 열어서 store.state.auth.user.role_code를 바꾸면?
  → 프론트엔드 가드를 우회할 수 있습니다!

  따라서 진짜 보안은 백엔드에서 처리합니다:
  → 모든 API 엔드포인트에서 JWT 토큰 검증
  → 모든 관리자 API에서 역할/메뉴 권한 재검증
  → 프론트엔드 가드는 "UX 개선용" (비인가 페이지 깜빡임 방지)
```

```
프론트엔드 가드 역할:
  ✅ 사용자가 실수로 권한 없는 페이지 접근 방지
  ✅ 비인가 상태에서 관리 화면 잠깐 보이는 것 방지
  ✅ 자연스러운 리다이렉트 (로그인 → 원래 페이지)
  ❌ 악의적 사용자 차단 (이건 백엔드 몫!)
```

---

## 리뷰 체크리스트 (Phase 2 전체)

- [x] 모든 비공개 라우트에 인증 체크가 있는가? → ✅
- [x] 관리자 라우트에 3단계 권한 체크가 있는가? → 인증 → 역할 → 메뉴 ✅
- [x] 로그인 페이지 무한 루프가 없는가? → 로그인 상태면 landingPage로 ✅
- [x] 404 처리가 있는가? → `/:pathMatch(.*)*` ✅
- [x] 리다이렉트 URL이 보존되는가? → `query.redirect` ✅
- [x] Lazy Loading으로 성능 최적화가 되어 있는가? → 모든 컴포넌트 ✅
- [x] 페이지 타이틀이 동적으로 변하는가? → afterEach ✅
- [x] 중첩 라우트가 올바르게 구성되어 있는가? → `/admin` children ✅
- [x] 고정 경로가 동적 경로보다 앞에 있는가? → `new`가 `:id`보다 앞 ✅

## Phase 2 핵심 용어 정리

| 용어 | 설명 |
|------|------|
| **라우트(Route)** | URL ↔ 화면 매핑 규칙 하나 |
| **라우터(Router)** | 모든 라우트를 관리하는 엔진 |
| **beforeEach** | 모든 이동 전에 실행되는 보안 검문소 |
| **afterEach** | 모든 이동 후에 실행되는 후처리 |
| **next()** | 이동 허용/거부/리다이렉트를 제어하는 함수 |
| **meta** | 라우트에 붙이는 부가 정보 (제목, 권한코드 등) |
| **children** | 중첩 라우트. 부모 레이아웃 유지하면서 내부만 교체 |
| **Lazy Loading** | `() => import(...)`. 필요할 때만 로드하여 성능 향상 |
| **to.matched** | 현재 라우트 + 부모 라우트 배열. 중첩 라우트 체크에 필수 |

## 다음 Phase 미리보기

Phase 2에서 라우터 가드가 `store.getters['auth/isAuthenticated']`를 사용하는 것을 보았습니다.
**Phase 3**에서는 이 **Vuex Store가 어떻게 구성되어 있고, 데이터가 어떻게 흐르는지**를 살펴봅니다.

```
Phase 1: "앱이 어떻게 시작되는가?"
Phase 2 (지금): "화면이 어떻게 전환되는가? 누가 접근할 수 있는가?"
Phase 3 (다음): "데이터가 어디에 저장되고 어떻게 공유되는가?"
```

---
> **이전**: [03_router_guards.md](03_router_guards.md) - 네비게이션 가드
