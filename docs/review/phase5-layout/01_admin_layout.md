# 1. AdminLayout - 관리자 화면의 골조

> **파일 위치**: `frontend/src/views/admin/AdminLayout.vue` (129줄)

## 이 컴포넌트가 하는 일

관리자 화면(`/admin/*`)의 **골조(뼈대)**입니다. 사이드바, 헤더, 콘텐츠 영역을 배치합니다.
실제 페이지 내용(사용자 관리, 문서 관리 등)은 `<router-view />`로 교체됩니다.

```
AdminLayout = "건물의 골조"

골조가 제공하는 것:
├── 사이드바 (왼쪽 메뉴)      → AppSidebar
├── 헤더 (상단 바)            → AppHeader
├── 콘텐츠 영역 (가운데 빈 공간) → <router-view />
└── 사이드바 토글 버튼         → 접기/펼치기
```

---

## 화면 구조

```
┌─────────────────────────────────────────────────┐
│                 AdminLayout (100vh)               │
│                                                   │
│  ┌──────────┐  ┌──────────────────────────────┐  │
│  │ sidebar  │  │  admin-main                   │  │
│  │ -wrapper │  │                                │  │
│  │          │  │  ┌──────────────────────────┐  │  │
│  │ AppSide  │  │  │  admin-header (60px)     │  │  │
│  │ bar      │  │  │  AppHeader               │  │  │
│  │          │  │  └──────────────────────────┘  │  │
│  │ 220px    │  │  ┌──────────────────────────┐  │  │
│  │ (64px)   │  │  │  admin-content            │  │  │
│  │          │  │  │  <router-view />          │  │  │
│  │          │  │  │                            │  │  │
│  │     [◀]  │  │  │  (여기에 각 페이지가 표시) │  │  │
│  │          │  │  │                            │  │  │
│  └──────────┘  │  └──────────────────────────┘  │  │
│                └──────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## Template 구조 — Element Plus 레이아웃

```html
<template>
  <el-container class="admin-layout">
    <!-- 사이드바 래퍼 (토글 버튼 포함) -->
    <div class="sidebar-wrapper" :class="{ collapsed: sidebarCollapsed }">
      <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="admin-sidebar">
        <AppSidebar />
      </el-aside>

      <!-- 사이드바 토글 버튼 -->
      <button class="sidebar-toggle" @click="toggleSidebar">
        <el-icon :size="10">
          <ArrowLeft v-if="!sidebarCollapsed" />
          <ArrowRight v-else />
        </el-icon>
      </button>
    </div>

    <!-- 메인 영역 -->
    <el-container class="admin-main">
      <el-header class="admin-header" height="60px">
        <AppHeader />
      </el-header>

      <el-main class="admin-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>
```

**Element Plus 레이아웃 컴포넌트:**

```
el-container  : 레이아웃 컨테이너 (flex 컨테이너)
                자식에 el-header/el-aside가 있으면 자동으로 방향 결정
el-aside      : 사이드바 영역 (width 지정 가능)
el-header     : 상단 영역 (height 지정 가능)
el-main       : 콘텐츠 영역 (나머지 공간을 채움)
```

**중첩 el-container의 의미:**

```html
<el-container>              ← 바깥: 수평 배치 (aside + main)
  <el-aside />              ← 왼쪽 사이드바
  <el-container>            ← 안쪽: 수직 배치 (header + main)
    <el-header />           ← 상단 헤더
    <el-main />             ← 콘텐츠 (나머지 공간)
  </el-container>
</el-container>

el-container는 자식을 보고 방향을 결정:
  - el-header/el-footer 있음 → 세로(column) 배치
  - el-aside 있음            → 가로(row) 배치
```

---

## Script — 사이드바 토글

```javascript
<script setup>
import { computed, onMounted } from 'vue'
import { useStore } from 'vuex'

const store = useStore()
const sidebarCollapsed = computed(() => store.state.app.sidebarCollapsed)

const toggleSidebar = () => {
  store.dispatch('app/toggleSidebar')
}

// 관리자 화면 진입 시 currentView 설정
onMounted(() => {
  store.dispatch('app/setCurrentView', 'admin')
})
</script>
```

**3가지 핵심:**

```
① sidebarCollapsed (computed)
   → app Store의 sidebarCollapsed 상태를 실시간 반영
   → true면 64px, false면 220px

② toggleSidebar()
   → 사이드바 접기/펼치기 토글
   → Store를 통해 상태 변경 → 화면 자동 반영

③ onMounted → setCurrentView('admin')
   → 관리자 화면 진입 시 "지금 관리자 화면이야"라고 Store에 알림
   → 테마 적용에 사용 (Phase 3: 관리자/사용자 테마 분리)
```

---

## Style — CSS 변수와 다크모드

```scss
.admin-layout {
  height: 100vh;       // 브라우저 전체 높이
  overflow: hidden;     // 스크롤 방지 (콘텐츠 영역에서만 스크롤)
}

.admin-sidebar {
  background-color: var(--sidebar-bg);               // CSS 변수 → 테마에 따라 자동 변경!
  transition: width 0.3s ease, background-color 0.3s ease;  // 부드러운 애니메이션
  overflow: hidden;
}

.admin-header {
  background-color: var(--header-bg);
  border-bottom: 1px solid var(--header-border);
  box-shadow: var(--box-shadow-light);
  transition: var(--theme-transition);                // 테마 전환 시 부드럽게
}

.admin-content {
  background-color: var(--bg-color-page);
  padding: 12px;
  overflow-y: auto;     // 콘텐츠만 스크롤 가능
  transition: var(--theme-transition);
}
```

**CSS 변수(`var(--...)`)를 쓰는 이유:**

```
하드코딩:
  background-color: #304156;   ← 다크모드? 일일이 다 바꿔야 함 😵

CSS 변수:
  background-color: var(--sidebar-bg);

  라이트모드: --sidebar-bg = #304156
  다크모드:   --sidebar-bg = #1f1f1f

  → data-theme="dark" 하나만 바꾸면 전체가 변경! ✅
```

**토글 버튼 디자인:**

```scss
.sidebar-toggle {
  position: absolute;       // 사이드바 오른쪽 끝에 절대 위치
  top: 50%;                 // 세로 중앙
  right: -6px;              // 사이드바 밖으로 살짝 나옴
  transform: translateY(-50%);  // 정확한 중앙 정렬

  width: 12px;              // 매우 좁은 버튼 (세련된 디자인)
  height: 48px;
  border-radius: 0 6px 6px 0;  // 오른쪽만 둥글게

  &:hover {
    width: 14px;            // 호버 시 살짝 커짐 (인터랙션 피드백)
  }
}
```

---

## 사이드바 토글 동작

```
[펼침 상태 - sidebarCollapsed: false]
┌────────────────────┐──────────────────────────┐
│                    │◀│                         │
│    AppSidebar      │  │      콘텐츠 영역       │
│    (220px)         │  │                         │
│                    │  │                         │
│  ☰ 대시보드         │  │                         │
│  ☰ 사용자 관리      │  │                         │
│  ☰ 문서 관리        │  │                         │
│                    │  │                         │
└────────────────────┘──────────────────────────┘

     ↓ [◀] 클릭 → toggleSidebar()

[접힘 상태 - sidebarCollapsed: true]
┌──────┐──────────────────────────────────────┐
│      │▶│                                     │
│ 🏠   │  │         콘텐츠 영역 (더 넓어짐!)    │
│ 👤   │  │                                     │
│ 📄   │  │                                     │
│ ⚙️   │  │                                     │
│(64px)│  │                                     │
└──────┘──────────────────────────────────────┘

→ 사이드바가 아이콘만 표시되는 64px로 줄어듦
→ 콘텐츠 영역이 넓어짐
→ width transition: 0.3s ease → 부드러운 애니메이션
```

---

## router-view와 레이아웃의 관계

Phase 2에서 배운 라우터 설정과 연결됩니다:

```javascript
// router/index.js (Phase 2)
{
  path: '/admin',
  component: AdminLayout,        // ← 이 레이아웃이 적용됨!
  children: [
    { path: 'dashboard', component: DashboardView },
    { path: 'users', component: UsersView },
    { path: 'documents', component: DocumentsView },
    // ... 15개 하위 라우트
  ]
}
```

```
/admin/dashboard 접속 시:

AdminLayout이 렌더링:
  ├─ AppSidebar (항상 표시)
  ├─ AppHeader (항상 표시)
  └─ <router-view /> → DashboardView 표시

/admin/users로 이동하면:

AdminLayout은 그대로, <router-view />만 교체:
  ├─ AppSidebar (그대로)
  ├─ AppHeader (그대로)
  └─ <router-view /> → UsersView로 교체!

→ 사이드바와 헤더는 유지되면서 콘텐츠만 바뀜!
```

---

## 리뷰 체크리스트

- [x] 전체 화면 높이를 사용하는가? → `height: 100vh` ✅
- [x] 콘텐츠 영역만 스크롤 가능한가? → `admin-content: overflow-y: auto` ✅
- [x] 사이드바 너비가 토글 가능한가? → 220px ↔ 64px ✅
- [x] 토글 시 부드러운 애니메이션인가? → `transition: width 0.3s ease` ✅
- [x] CSS 변수로 다크모드를 지원하는가? → `var(--sidebar-bg)` 등 ✅
- [x] 관리자 진입 시 currentView가 설정되는가? → `onMounted` ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **el-container** | Element Plus 레이아웃 컨테이너. 자식에 따라 가로/세로 자동 결정 |
| **el-aside** | 사이드바 영역. width props로 너비 제어 |
| **router-view** | 자식 라우트의 컴포넌트가 여기에 렌더링됨 |
| **CSS 변수** | `var(--name)`. 테마 전환 시 한번에 색상 변경 가능 |
| **sidebarCollapsed** | Store 상태. true면 64px, false면 220px |

---
> **다음**: [02_app_header.md](02_app_header.md) - 관리자 헤더
