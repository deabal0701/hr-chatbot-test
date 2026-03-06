# 3. app 모듈 - 앱 전역 설정

> **파일 위치**: `frontend/src/store/modules/app.js` (194줄)

## 이 모듈이 하는 일

**앱의 외관(Look & Feel)**을 관리합니다. 다크모드, 사이드바 열기/닫기 같은 UI 상태입니다.

```
app 모듈이 관리하는 것:
├── 다크모드 / 라이트모드 (사용자/관리자 화면 각각 분리)
├── 관리자 사이드바 접기/펼치기
├── 사용자 채팅 사이드바 보이기/숨기기
└── API 서버 상태 (healthy/unhealthy)
```

## auth와 다른 점

```
auth 모듈: "누구"에 대한 데이터 (사용자, 토큰, 권한)
app 모듈:  "어떻게 보이는가"에 대한 데이터 (테마, 레이아웃)
```

---

## 이 모듈의 핵심: 사용자/관리자 테마 분리 ⭐

이 프로젝트는 **사용자 화면과 관리자 화면의 다크모드를 분리**합니다:

```
사용자 화면 (/chat):           관리자 화면 (/admin/*):
┌─────────────────┐           ┌─────────────────┐
│  다크모드 ON 🌙  │           │  라이트모드 ON ☀️ │
│  (어두운 배경)    │           │  (밝은 배경)      │
│                  │           │                  │
│  독립적으로       │           │  독립적으로       │
│  테마 변경 가능   │           │  테마 변경 가능   │
└─────────────────┘           └─────────────────┘

→ 채팅은 다크, 관리는 라이트로 쓸 수 있음!
```

## 파일 상단 - 헬퍼 함수

```javascript
const STORAGE_KEYS = {
  USER_THEME: 'user_theme',
  ADMIN_THEME: 'admin_theme',
  USER_SIDEBAR: 'user_sidebar_visible'
}

const DEFAULT_THEMES = {
  user: true,     // 사용자 화면: 다크모드 기본
  admin: true     // 관리자 화면: 다크모드 기본
}
```

**`applyTheme()` - 실제로 화면 색상을 바꾸는 함수:**

```javascript
const applyTheme = (isDark) => {
  if (isDark) {
    document.documentElement.setAttribute('data-theme', 'dark')
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.removeAttribute('data-theme')
    document.documentElement.classList.remove('dark')
  }
}
```

이 함수가 하는 일:
```html
<!-- 다크모드 ON -->
<html data-theme="dark" class="dark">

<!-- 라이트모드 -->
<html>
```

CSS에서 이것을 감지해서 색상을 바꿉니다:
```css
/* 라이트모드 (기본) */
:root { --bg-color: #ffffff; --text-color: #333333; }

/* 다크모드 */
[data-theme="dark"] { --bg-color: #1a1a2e; --text-color: #e0e0e0; }
```

---

## State

```javascript
state: () => ({
  sidebarCollapsed: false,        // 관리자 사이드바 접힘 여부
  userSidebarVisible: getStoredSidebarVisible(),  // 채팅 사이드바

  apiHealthy: true,               // API 서버 상태

  userDarkMode: getStoredTheme('user'),    // 사용자 화면 다크모드
  adminDarkMode: getStoredTheme('admin'),  // 관리자 화면 다크모드
  currentView: 'admin'            // 현재 화면 타입 ('user' | 'admin')
})
```

## Mutations - 테마 토글 핵심 로직

```javascript
// 현재 화면의 테마 토글
TOGGLE_CURRENT_DARK_MODE(state) {
  if (state.currentView === 'user') {
    state.userDarkMode = !state.userDarkMode        // 반전
    saveTheme('user', state.userDarkMode)            // localStorage 저장
    applyTheme(state.userDarkMode)                   // DOM에 적용
  } else {
    state.adminDarkMode = !state.adminDarkMode
    saveTheme('admin', state.adminDarkMode)
    applyTheme(state.adminDarkMode)
  }
}
```

**테마 토글 흐름:**
```
사용자가 헤더의 🌙/☀️ 버튼 클릭
    │
    ▼
dispatch('app/toggleDarkMode')
    │
    ▼
commit('TOGGLE_CURRENT_DARK_MODE')
    │
    ├─ currentView === 'user'?
    │   ├─ YES → userDarkMode 반전 → localStorage에 저장 → DOM 적용
    │   └─ NO  → adminDarkMode 반전 → localStorage에 저장 → DOM 적용
    │
    ▼
화면 색상 즉시 변경! (CSS 변수가 바뀌므로)
```

## 화면 전환 시 테마 적용

```javascript
// 화면 타입 변경 시 (user ↔ admin)
SET_CURRENT_VIEW(state, view) {
  state.currentView = view
  const isDark = view === 'user' ? state.userDarkMode : state.adminDarkMode
  applyTheme(isDark)
}
```

```
/chat (사용자 화면) → /admin/dashboard (관리자 화면) 이동 시:

1. 라우트 변경 감지
2. SET_CURRENT_VIEW('admin') 호출
3. adminDarkMode 값 확인 (예: false = 라이트모드)
4. applyTheme(false) → <html>에서 dark 클래스 제거
5. 화면이 라이트모드로 변경!

→ 채팅은 다크, 관리는 라이트로 각각 유지됨
```

## Getters

```javascript
getters: {
  // 현재 화면의 다크모드 상태
  isDarkMode: (state) =>
    state.currentView === 'user' ? state.userDarkMode : state.adminDarkMode,

  isUserDarkMode: (state) => state.userDarkMode,
  isAdminDarkMode: (state) => state.adminDarkMode,
  currentView: (state) => state.currentView,
  isUserSidebarVisible: (state) => state.userSidebarVisible
}
```

컴포넌트에서 사용:
```vue
<template>
  <!-- 현재 화면의 다크모드에 따라 아이콘 변경 -->
  <el-icon @click="toggleTheme">
    <Moon v-if="isDarkMode" />
    <Sunny v-else />
  </el-icon>
</template>

<script setup>
const isDarkMode = computed(() => store.getters['app/isDarkMode'])
const toggleTheme = () => store.dispatch('app/toggleDarkMode')
</script>
```

---

## auth 모듈과의 패턴 비교

| 항목 | auth 모듈 | app 모듈 |
|------|-----------|----------|
| **API 호출** | 있음 (login, logout, fetchMe) | 없음 (로컬 상태만) |
| **localStorage** | 토큰, 사용자 정보 | 테마, 사이드바 상태 |
| **비동기 Action** | 대부분 async | 모두 동기 |
| **복잡도** | 높음 (에러 처리, 토큰 갱신) | 낮음 (단순 토글) |

→ app 모듈은 **API 호출 없이 순수하게 UI 상태만** 관리하는 심플한 모듈입니다.

## 리뷰 체크리스트

- [x] 사용자/관리자 테마가 분리되어 있는가? → userDarkMode / adminDarkMode ✅
- [x] 테마가 localStorage에 영속화되는가? → saveTheme() ✅
- [x] 화면 전환 시 테마가 자동 적용되는가? → SET_CURRENT_VIEW ✅
- [x] 사이드바 상태가 보존되는가? → localStorage 사용 ✅
- [x] 기본값이 정의되어 있는가? → DEFAULT_THEMES (다크모드) ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **테마 분리** | 사용자 화면과 관리자 화면의 다크모드를 독립 관리 |
| **applyTheme()** | `<html>` 태그에 `data-theme="dark"` 적용 → CSS 변수 변경 |
| **currentView** | 현재 화면 타입 ('user' / 'admin'), 테마 적용의 기준 |
| **동기 모듈** | API 호출 없이 localStorage + DOM 조작만 수행 |

---
> **이전**: [02_auth_module.md](02_auth_module.md) - 인증 모듈
> **다음**: [04_chat_module.md](04_chat_module.md) - 채팅 모듈
