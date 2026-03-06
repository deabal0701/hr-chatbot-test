# 5. 동작 원리 종합 - 레이아웃 전환과 반응형

## 시나리오별로 레이아웃의 동작을 추적합니다

---

## 시나리오 1: 로그인 → 관리자 화면 진입

**상황**: GLOBAL 관리자가 로그인하면 /admin/dashboard로 이동

```
[로그인 성공]
router.push('/admin/dashboard')
    │
    ▼
[라우터 매칭]
path: '/admin'
  component: AdminLayout        ← 이 레이아웃이 렌더링!
  children:
    path: 'dashboard'
    component: DashboardView    ← router-view에 들어감
    │
    ▼
[AdminLayout 렌더링]
┌─────────────────────────────────────────┐
│ AdminLayout (100vh)                      │
│                                          │
│  AdminLayout.onMounted()                 │
│  → dispatch('app/setCurrentView', 'admin')│
│  → adminDarkMode 적용 (Phase 3)          │
│                                          │
│  ┌──────────┐  ┌────────────────────┐   │
│  │AppSidebar│  │AppHeader           │   │
│  │          │  │ "대시보드"          │   │
│  │ 대시보드  │  │──────────────────── │   │
│  │ AI 검색  │  │                     │   │
│  │ 문서관리  │  │ DashboardView      │   │
│  │ ▼시스템   │  │ (KPI, 차트, ...)   │   │
│  │  사용자  │  │                     │   │
│  │  역할    │  │                     │   │
│  └──────────┘  └────────────────────┘   │
└─────────────────────────────────────────┘

→ AdminLayout이 골조, DashboardView가 내용물
```

---

## 시나리오 2: 관리자 → 사용자 채팅 화면 전환

**상황**: 관리자가 헤더에서 채팅 화면으로 이동

```
/admin/dashboard → /chat 이동
    │
    ▼
[라우터 매칭]
path: '/chat'
  component: UserChatLayout    ← 레이아웃이 완전히 교체!

    │
    ▼
[AdminLayout 언마운트 → UserChatLayout 마운트]

┌──────────────────────────────────────┐
│ UserChatLayout (100vh)                │
│                                       │
│  UserChatLayout.onMounted()           │
│  → dispatch('app/setCurrentView',     │
│                'user')   ← 중요!      │
│  → userDarkMode 적용 (Phase 3)        │
│                                       │
│  ┌──────────┬────────────────────┐   │
│  │UserChat  │ Desktop Header     │   │
│  │Sidebar   │   [공유] [저장]     │   │
│  │          │────────────────────│   │
│  │ 새 채팅   │                    │   │
│  │ 대화 이력 │  UserChatView      │   │
│  │          │  (채팅 화면)        │   │
│  │ [사용자]  │                    │   │
│  └──────────┴────────────────────┘   │
└──────────────────────────────────────┘

→ 골조가 AdminLayout에서 UserChatLayout으로 변경!
→ currentView가 'admin' → 'user'로 변경 → 테마도 변경!
```

**테마 전환 상세:**

```
AdminLayout (currentView = 'admin')
  → adminDarkMode = false (라이트모드)
  → <html> → 밝은 배경

     ↓ /chat 이동

UserChatLayout (currentView = 'user')
  → userDarkMode = true (다크모드)
  → <html data-theme="dark" class="dark"> → 어두운 배경

→ 관리자 화면은 밝게, 채팅 화면은 어둡게 — 각각 독립!
```

---

## 시나리오 3: 관리자 사이드바 메뉴 클릭

**상황**: 사이드바에서 "사용자 관리" 클릭

```
AppSidebar                   el-menu                라우터              AdminLayout
──────────                   ───────                ──────              ───────────

[사용자 관리 클릭]
el-menu-item
  index="/admin/users"
        │
        ▼
  el-menu (router props)
  → router.push('/admin/users')
                              │
                              ▼
                        [라우터 매칭]
                        children에서
                        path: 'users'
                        component: UsersView
                              │
                              ▼
                                                          AdminLayout 유지!
                                                          (사이드바, 헤더 그대로)
                                                          │
                                                          ▼
                                                    <router-view />만 교체
                                                    DashboardView → UsersView

[동시에 헤더 업데이트]
route.meta.title = '사용자 관리'
  → AppHeader의 pageTitle 자동 변경!

[동시에 사이드바 활성 메뉴 변경]
route.path = '/admin/users'
  → AppSidebar의 activeMenu 자동 변경!
  → "사용자 관리" 메뉴 항목이 하이라이트 됨
```

---

## 시나리오 4: 모바일 사이드바 열기/닫기

**상황**: 모바일에서 채팅 화면의 ☰ 버튼 클릭

```
시간 ──→

[초기 상태 - 모바일]
┌─────────────────────┐
│☰ MUREUM    📤 💾 👤 │
│─────────────────────│
│                     │
│   UserChatView      │
│   (사이드바 숨김)    │
│                     │
└─────────────────────┘

[☰ 클릭]
toggleSidebar()
  → dispatch('app/toggleUserSidebar')
  → userSidebarVisible: false → true

┌──────────┬──────────┐
│UserChat  │ ██████ │ ← sidebar-overlay (반투명)
│Sidebar   │ ██████ │   @click="closeSidebar"
│          │ ██████ │
│ 새 채팅   │ ██████ │
│ 오늘      │ ██████ │
│  대화1    │ ██████ │
│          │ ██████ │
│ [사용자]  │ ██████ │
└──────────┴──────────┘
  (position: fixed)
  (transform: translateX(0))  ← 슬라이드 인 애니메이션

[대화1 클릭]
handleSelectChat('session_key')
  → dispatch('chat/selectChat', 'session_key')
  → emit('close')                ← isMobile이면 자동 닫기
      → closeSidebar()
      → userSidebarVisible: true → false

[오버레이 클릭]
@click="closeSidebar"
  → userSidebarVisible: true → false
  → 사이드바 닫힘 (transform: translateX(-100%))
```

---

## 시나리오 5: 역할별 다른 메뉴 표시

**상황**: 다른 역할로 로그인하면 사이드바 메뉴가 달라짐

```
[GLOBAL 관리자 로그인]                  [TENANT 관리자 로그인]
user.menus = 12개                      user.menus = 5개

┌─────────────────┐                    ┌─────────────────┐
│ 📊 대시보드      │                    │ 📊 대시보드      │
│ 💬 AI 검색       │                    │ 💬 AI 검색       │
│ 📄 문서 관리     │                    │ 📄 문서 관리     │
│ 📊 검색 이력     │                    │ ▼ 시스템 관리    │
│ ▼ 시스템 관리    │                    │   👤 사용자      │
│   👤 사용자      │                    └─────────────────┘
│   🔑 역할        │
│   📋 메뉴        │                    TENANT는 역할/메뉴/테넌트
│   🏢 테넌트      │                    관리 권한이 없으므로 안 보임
│ 📋 코드 관리     │
│ ⚙️ 시스템 설정   │
└─────────────────┘

[USER 사용자 로그인]
user.menus = 0개 (또는 사용자 메뉴만)

→ canAccessAdmin = false
→ /admin 접근 자체가 라우터 가드에서 차단!
→ /chat으로 리다이렉트
→ UserChatLayout 표시 (관리자 사이드바 없음)
```

---

## 5개 레이아웃 컴포넌트 관계도

```
┌─────────────────────────────────────────────────────────┐
│                        App.vue                           │
│                      <router-view />                     │
│                            │                             │
│              ┌─────────────┼──────────────┐              │
│              │             │              │              │
│              ▼             ▼              ▼              │
│      LoginView.vue   AdminLayout    UserChatLayout       │
│      (레이아웃 없음)      │                │              │
│                      ┌────┴────┐     ┌────┴────┐        │
│                      │         │     │         │        │
│                  AppSidebar  AppHeader  UserChat  UserChat│
│                                       Sidebar    View    │
│                      │                                   │
│               ┌──────┼──────┐                            │
│               ▼      ▼      ▼                            │
│          Dashboard  Users  Documents  ...                │
│          View       View   View                          │
│                                                          │
└─────────────────────────────────────────────────────────┘

데이터 흐름:
  auth Store → menus     → AppSidebar (메뉴 렌더링)
  auth Store → user      → AppHeader (사용자 이름)
  auth Store → user      → UserChatSidebar (사용자 정보)
  app Store  → collapsed → AdminLayout (사이드바 너비)
  app Store  → visible   → UserChatLayout (사이드바 표시)
  app Store  → darkMode  → 모든 컴포넌트 (CSS 변수 변경)
  route      → meta      → AppHeader (페이지 제목)
  route      → path      → AppSidebar (활성 메뉴)
  chat Store → history   → UserChatSidebar (대화 이력)
```

---

## Phase 5 종합 리뷰 체크리스트

### AdminLayout
- [x] el-container로 레이아웃이 구성되는가? → el-aside + el-header + el-main ✅
- [x] 사이드바 토글이 동작하는가? → 220px ↔ 64px ✅
- [x] currentView가 'admin'으로 설정되는가? → onMounted ✅

### AppHeader
- [x] 페이지 제목이 라우트에서 추출되는가? → route.meta.title ✅
- [x] API 상태가 주기 체크되는가? → 30초 setInterval ✅
- [x] 비밀번호 검증 규칙이 있는가? → 8자, 대소문자+숫자 ✅

### AppSidebar
- [x] 메뉴가 서버 데이터 기반인가? → auth Store menus ✅
- [x] flat → tree 변환이 되는가? → parent_menu_code 빌드 ✅
- [x] 아이콘 매핑이 되는가? → ICON_MAP ✅
- [x] 현재 페이지가 하이라이트되는가? → route.path ✅

### UserChatLayout
- [x] 반응형 디자인이 적용되는가? → 768px 기준 ✅
- [x] 모바일 오버레이가 있는가? → sidebar-overlay ✅
- [x] 공유/저장 기능이 있는가? → 클립보드 + 마크다운 ✅

### UserChatSidebar
- [x] 날짜 그룹핑이 되는가? → 오늘/어제/7일/30일/이전 ✅
- [x] 검색 디바운스가 적용되는가? → 300ms ✅
- [x] emit으로 부모에게 이벤트 전달하는가? → close, toggle ✅

## Phase 5 핵심 용어 정리

| 용어 | 설명 |
|------|------|
| **레이아웃 컴포넌트** | 사이드바+헤더+콘텐츠 영역을 배치하는 골조 |
| **el-container** | Element Plus 레이아웃 컨테이너 |
| **router-view** | 자식 라우트 컴포넌트가 렌더링되는 위치 |
| **반응형 디자인** | 화면 크기에 따라 레이아웃이 자동 전환 |
| **모바일 오버레이** | 모바일에서 사이드바 열릴 때 배경 어둡게 처리 |
| **트리 빌드** | flat 메뉴 배열을 parent_menu_code로 계층 구조 변환 |
| **디바운스** | 연속 이벤트 중 마지막만 실행 (검색 최적화) |
| **스켈레톤 로딩** | 데이터 로딩 중 표시하는 반짝이는 플레이스홀더 |
| **emit 패턴** | 자식 → 부모 방향 이벤트 전달 (`defineEmits`) |

## 다음 Phase 미리보기

Phase 5에서 화면의 골조(레이아웃)를 이해했습니다.
**Phase 6**에서는 이 골조 안에 들어가는 **실제 CRUD 페이지**를 살펴봅니다.

```
Phase 1: "앱이 어떻게 시작되는가?"
Phase 2: "화면이 어떻게 전환되는가?"
Phase 3: "데이터가 어디에 저장되고 어떻게 공유되는가?"
Phase 4: "백엔드와 어떻게 통신하는가?"
Phase 5 (지금): "화면 레이아웃이 어떻게 구성되는가?"
Phase 6 (다음): "CRUD 화면은 어떻게 만들어지는가?"
```

---
> **이전**: [04_user_chat_layout.md](04_user_chat_layout.md) - 사용자 채팅 레이아웃
