# 3. AppSidebar - 관리자 사이드바 (메뉴)

> **파일 위치**: `frontend/src/components/layout/AppSidebar.vue` (253줄)

## 이 컴포넌트가 하는 일

관리자 화면 왼쪽의 **메뉴 사이드바**입니다. 사용자가 접근 가능한 메뉴만 **서버에서 받아와** 동적으로 표시합니다.

```
┌─────────────────┐
│  💬 MUREUM       │  ← 로고
│─────────────────│
│  📊 대시보드     │  ← PAGE 메뉴 (직접 클릭 가능)
│  💬 AI 검색      │
│  📁 문서 관리    │
│  ▼ 시스템 관리   │  ← DIRECTORY 메뉴 (펼치기/접기)
│    👤 사용자     │     └ 하위 PAGE 메뉴
│    🔑 역할       │
│    📋 메뉴       │
│  ⚙️ 시스템 설정  │
│─────────────────│
│     v2.0.0      │  ← 버전 표시
└─────────────────┘
```

---

## 핵심: 메뉴는 하드코딩이 아니다! ⭐

**이 앱의 메뉴는 서버(DB)에서 받아온 데이터**로 렌더링됩니다:

```
❌ 하드코딩 방식:
  <el-menu-item index="/admin/dashboard">대시보드</el-menu-item>
  <el-menu-item index="/admin/users">사용자 관리</el-menu-item>
  → 메뉴 추가/삭제 시 코드 수정 필요

✅ 이 앱의 방식 (DB 기반):
  서버가 사용자별 접근 가능 메뉴 목록을 내려줌
  → 프론트엔드가 동적으로 렌더링
  → 권한에 따라 보이는 메뉴가 다름!

  GLOBAL 관리자 → 모든 메뉴 표시
  TENANT 관리자 → 일부 메뉴만 표시
  USER 사용자   → 관리자 메뉴 없음 (사이드바 자체가 안 보임)
```

---

## 메뉴 데이터의 흐름

```
로그인 성공 → 서버가 user.menus 반환:
[
  { menu_code: 'DIR_ROOT', menu_type: 'DIRECTORY', depth: 0, ... },
  { menu_code: 'DASHBOARD', menu_type: 'PAGE', menu_path: '/admin/dashboard',
    parent_menu_code: 'DIR_ROOT', icon: 'dashboard', sort_order: 1 },
  { menu_code: 'CHAT', menu_type: 'PAGE', menu_path: '/admin/chat',
    parent_menu_code: 'DIR_ROOT', icon: 'chat', sort_order: 2 },
  { menu_code: 'DIR_SYSTEM', menu_type: 'DIRECTORY',
    parent_menu_code: 'DIR_ROOT', icon: 'setup', sort_order: 5 },
  { menu_code: 'USER_MGMT', menu_type: 'PAGE', menu_path: '/admin/users',
    parent_menu_code: 'DIR_SYSTEM', icon: 'users', sort_order: 1 },
  ...
]

→ auth Store에 저장 → AppSidebar가 computed로 트리 구조 생성
```

---

## 트리 구성 알고리즘 ⭐⭐

평평한(flat) 배열을 **트리 구조로 변환**하는 과정:

```javascript
const sidebarMenuItems = computed(() => {
  const menus = store.getters['auth/menus'] || []

  // 1단계: Map 생성 (menu_code → 메뉴 객체 + 빈 children 배열)
  const menuMap = new Map()
  menus.forEach(m => {
    menuMap.set(m.menu_code, { ...m, children: [] })
  })

  // 2단계: 트리 빌드 (parent_menu_code로 부모-자식 연결)
  const roots = []
  menuMap.forEach(m => {
    if (m.parent_menu_code && menuMap.has(m.parent_menu_code)) {
      menuMap.get(m.parent_menu_code).children.push(m)  // 부모에 자식 추가
    } else {
      roots.push(m)   // 부모 없음 → 루트 레벨
    }
  })

  // 3단계: 정렬 (sort_order 기준, 재귀적)
  const sortItems = (items) => {
    items.sort((a, b) => (a.sort_order || 0) - (b.sort_order || 0))
    items.forEach(item => { if (item.children.length) sortItems(item.children) })
  }
  sortItems(roots)

  // 4단계: DIR_ROOT의 자식만 루트 레벨로 승격
  const result = []
  for (const root of roots) {
    if (root.menu_type === 'DIRECTORY' && root.menu_code === 'DIR_ROOT') {
      result.push(...root.children)
    }
  }

  // 5단계: 빈 DIRECTORY 제외
  return result.filter(m => {
    if (m.menu_type === 'DIRECTORY' && m.children.length === 0) return false
    return true
  })
})
```

**단계별 시각화:**

```
[1단계: flat 배열]
  DIR_ROOT, DASHBOARD, CHAT, DOCUMENT, DIR_SYSTEM, USER_MGMT, ROLE_MGMT, ...

[2단계: 트리 빌드]
  DIR_ROOT
  ├── DASHBOARD (sort: 1)
  ├── CHAT (sort: 2)
  ├── DOCUMENT (sort: 3)
  ├── DIR_SYSTEM (sort: 5)
  │   ├── USER_MGMT
  │   ├── ROLE_MGMT
  │   └── MENU_MGMT
  └── SETTINGS (sort: 6)

[3단계: 정렬]
  (sort_order 기준으로 재귀 정렬)

[4단계: DIR_ROOT 자식 승격]
  DASHBOARD        ← DIR_ROOT 아래 있던 것들이 루트 레벨로!
  CHAT
  DOCUMENT
  DIR_SYSTEM       ← 이것은 DIRECTORY이므로 서브메뉴로 렌더링
  ├── USER_MGMT
  ├── ROLE_MGMT
  └── MENU_MGMT
  SETTINGS

[5단계: 빈 DIRECTORY 제외]
  (자식 없는 폴더 숨김)
```

---

## Template — 메뉴 렌더링

```html
<el-menu :default-active="activeMenu" :collapse="isCollapsed" router>
  <template v-for="item in sidebarMenuItems">

    <!-- DIRECTORY with children → 펼치기/접기 서브메뉴 -->
    <el-sub-menu v-if="item.children && item.children.length"
      :key="'dir-' + item.menu_code"
      :index="item.menu_code">
      <template #title>
        <el-icon><component :is="resolveIcon(item.icon)" /></el-icon>
        <span>{{ item.menu_name }}</span>
      </template>
      <!-- 서브메뉴의 자식 항목 -->
      <el-menu-item v-for="child in item.children"
        :key="child.menu_code"
        :index="child.menu_path">
        <el-icon><component :is="resolveIcon(child.icon)" /></el-icon>
        <template #title>{{ child.menu_name }}</template>
      </el-menu-item>
    </el-sub-menu>

    <!-- PAGE → 직접 클릭 가능한 메뉴 항목 -->
    <el-menu-item v-else
      :key="'page-' + item.menu_code"
      :index="item.menu_path">
      <el-icon><component :is="resolveIcon(item.icon)" /></el-icon>
      <template #title>{{ item.menu_name }}</template>
    </el-menu-item>

  </template>
</el-menu>
```

**el-menu의 중요 props:**

| prop | 값 | 설명 |
|------|---|------|
| `:default-active` | `route.path` | 현재 URL과 일치하는 메뉴를 활성화 표시 |
| `:collapse` | `isCollapsed` | true면 아이콘만 표시 |
| `:collapse-transition` | `false` | 접기 시 애니메이션 비활성화 (성능) |
| `router` | - | 메뉴 클릭 시 `index` 값으로 라우터 이동 |

**`router` 속성의 효과:**
```
<el-menu router>
  <el-menu-item index="/admin/users">

→ 클릭 시 자동으로 router.push('/admin/users') 실행!
→ @click 이벤트를 별도로 처리할 필요 없음
```

---

## 아이콘 매핑

DB에 저장된 아이콘 이름을 Element Plus 아이콘 컴포넌트로 변환합니다:

```javascript
const ICON_MAP = {
  dashboard: 'Odometer',        // 📊
  chat: 'ChatDotSquare',        // 💬
  document: 'Document',         // 📄
  users: 'User',                // 👤
  menu: 'Menu',                 // ☰
  role: 'Key',                  // 🔑
  tenant: 'OfficeBuilding',     // 🏢
  settings: 'Setting',          // ⚙️
  setup: 'SetUp',               // 🔧
  code: 'Grid',                 // 📋
  history: 'Histogram',         // 📊
  folder: 'Folder',             // 📁
  department: 'Management',     // 🏬
}

const resolveIcon = (iconName) => {
  return ICON_MAP[iconName] || 'Document'  // 매핑 없으면 기본 아이콘
}
```

```
서버: { icon: 'dashboard' }  → resolveIcon('dashboard') → 'Odometer'
      ↓
<el-icon><component :is="'Odometer'" /></el-icon>
      ↓
main.js에서 전역 등록된 Odometer 컴포넌트가 렌더링!
```

**`<component :is="...">`란?**

```html
<!-- 동적 컴포넌트 렌더링 -->
<component :is="'Odometer'" />   → <Odometer />와 같음
<component :is="'User'" />      → <User />와 같음

→ 문자열로 컴포넌트를 선택할 수 있음!
→ 아이콘이 DB에서 오기 때문에 동적 렌더링이 필요
```

---

## 다크모드 색상 처리

```javascript
const getVar = (name) =>
  getComputedStyle(document.documentElement).getPropertyValue(name).trim()

const menuBgColor = computed(() =>
  getVar('--sidebar-bg') || (isDarkMode.value ? '#1f1f1f' : '#304156')
)
const menuTextColor = computed(() =>
  getVar('--sidebar-text') || (isDarkMode.value ? '#a3a3a3' : '#bfcbd9')
)
const menuActiveColor = computed(() =>
  getVar('--sidebar-active-text') || '#409eff'
)
```

**왜 getComputedStyle을 사용하는가?**

```
el-menu는 inline style로 색상을 받음:
  <el-menu
    :background-color="menuBgColor"     ← 문자열 색상 코드 필요!
    :text-color="menuTextColor"
    :active-text-color="menuActiveColor"
  >

CSS 변수는 inline style에서 직접 사용 불가 → JavaScript로 읽어서 전달
getComputedStyle() = "현재 CSS 변수의 실제 값을 읽어와"
```

---

## 로고 영역

```html
<div class="sidebar-logo" :class="{ collapsed: isCollapsed }">
  <div class="logo-icon">
    <svg viewBox="0 0 24 24" ...>
      <!-- 채팅 아이콘 SVG -->
    </svg>
  </div>
  <span v-if="!isCollapsed" class="logo-text">MUREUM</span>
</div>
```

```
[펼침 상태]           [접힘 상태]
┌─────────────┐      ┌────┐
│ 💬 MUREUM   │      │ 💬 │
└─────────────┘      └────┘

v-if="!isCollapsed" → 접힘 시 텍스트 숨김, 아이콘만 표시
```

---

## 리뷰 체크리스트

- [x] 메뉴가 서버 데이터 기반으로 렌더링되는가? → `store.getters['auth/menus']` ✅
- [x] flat 배열이 트리로 변환되는가? → parent_menu_code 기반 빌드 ✅
- [x] DIR_ROOT 자식이 루트 레벨로 승격되는가? → 4단계 처리 ✅
- [x] 빈 DIRECTORY가 숨겨지는가? → `children.length === 0` 필터 ✅
- [x] sort_order로 정렬되는가? → 재귀 정렬 ✅
- [x] 아이콘이 DB → 컴포넌트로 매핑되는가? → ICON_MAP ✅
- [x] 현재 페이지 메뉴가 활성화 표시되는가? → `route.path` ✅
- [x] 접힘 시 아이콘만 표시되는가? → `collapse` props ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **DB 기반 메뉴** | 메뉴가 하드코딩이 아닌 서버 데이터로 동적 생성 |
| **트리 빌드** | flat 배열 → parent_menu_code로 부모-자식 트리 구성 |
| **DIR_ROOT 승격** | 최상위 DIRECTORY의 자식을 루트 레벨로 올림 |
| **ICON_MAP** | DB 아이콘명 → Element Plus 컴포넌트명 매핑 |
| **`<component :is>`** | 문자열로 동적 컴포넌트 렌더링 |
| **el-menu router** | 메뉴 클릭 시 자동 라우터 이동 |
| **activeMenu** | `route.path`로 현재 페이지 메뉴 하이라이트 |

---
> **이전**: [02_app_header.md](02_app_header.md) - 관리자 헤더
> **다음**: [04_user_chat_layout.md](04_user_chat_layout.md) - 사용자 채팅 레이아웃
