# 5. App.vue - 루트 컴포넌트

> **파일 위치**: `frontend/src/App.vue`

## 이 파일은 뭐하는 파일인가?

**레스토랑의 메인 홀**입니다. 손님(사용자)이 들어오면 이 공간에서 모든 것이 시작됩니다. 메인 홀 자체는 심플하고, URL에 따라 적절한 "방"(페이지)으로 안내합니다.

Vue 앱의 **최상위 컴포넌트**로, 모든 화면은 이 컴포넌트 안에서 표시됩니다.

## 전체 코드

```vue
<template>
  <router-view />
</template>

<script setup>
// App.vue - 루트 컴포넌트
</script>

<style>
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
}
</style>
```

**고작 16줄!** 왜 이렇게 간단할까요?

## .vue 파일의 구조 (SFC - Single File Component)

Vue에서는 하나의 `.vue` 파일 안에 **3가지 영역**을 함께 작성합니다:

```vue
<template>    ← HTML (화면에 보이는 것)
  ...
</template>

<script setup> ← JavaScript (동작/로직)
  ...
</script>

<style>        ← CSS (스타일/꾸미기)
  ...
</style>
```

이것을 **SFC (Single File Component, 단일 파일 컴포넌트)**라고 합니다:

```
[일반 웹 개발]                    [Vue SFC]
──────────                       ──────────
index.html   (구조)              MyComponent.vue 하나에
script.js    (동작)       →→→    HTML + JS + CSS 모두 포함!
style.css    (스타일)

장점: 관련 코드가 한 파일에 모여있어 관리가 쉬움
```

## 코드 상세 설명

### `<template>` - 화면

```vue
<template>
  <router-view />
</template>
```

**`<router-view />`가 이 파일의 전부입니다!**

이것은 **"현재 URL에 해당하는 화면을 여기에 표시해라"**라는 뜻입니다:

```
URL이 바뀌면 <router-view>의 내용이 자동으로 바뀜:

http://localhost:19080/login
    └─ <router-view /> → LoginView.vue 표시

http://localhost:19080/chat
    └─ <router-view /> → UserChatView.vue 표시

http://localhost:19080/admin/dashboard
    └─ <router-view /> → AdminLayout.vue → DashboardView.vue 표시
```

**비유: TV 화면**
```
App.vue = TV 본체 (항상 그대로)
<router-view> = TV 화면 (채널에 따라 내용이 바뀜)
URL = 리모컨 (채널을 바꾸는 역할)

TV 본체를 바꾸지 않고, 채널만 바꾸면 다른 프로그램이 나오듯이
App.vue는 그대로이고, URL만 바뀌면 다른 화면이 표시됩니다.
```

### `<script setup>` - 로직

```vue
<script setup>
// App.vue - 루트 컴포넌트
</script>
```

- 주석 한 줄만 있고, 실제 로직은 없음
- App.vue는 "틀"만 제공하고, 실제 로직은 각 하위 컴포넌트가 담당
- `<script setup>`은 Vue 3의 **Composition API** 문법 (가장 간결한 방식)

**`<script setup>` vs `<script>` 차이:**
```vue
<!-- Vue 3 Composition API (이 프로젝트 방식) -->
<script setup>
import { ref } from 'vue'
const count = ref(0)           // 바로 사용 가능!
</script>

<!-- Vue 3 Options API (전통적 방식) -->
<script>
export default {
  data() {
    return { count: 0 }        // 더 많은 코드 필요
  }
}
</script>
```

### `<style>` - 글로벌 스타일

```css
html, body, #app {
  margin: 0;
  padding: 0;
  height: 100%;
}
```

| 속성 | 값 | 이유 |
|------|-----|------|
| `margin: 0` | 바깥 여백 제거 | 브라우저 기본 여백 제거 |
| `padding: 0` | 안쪽 여백 제거 | 화면 가장자리까지 꽉 차도록 |
| `height: 100%` | 높이 100% | 전체 화면을 다 사용하도록 |

**왜 이 3줄이 필요한가?**

```
[이 스타일이 없으면]                [이 스타일이 있으면]
┌──────────────────┐              ┌──────────────────┐
│  ┌────────────┐  │              │                  │
│  │            │  │              │                  │
│  │  콘텐츠     │  │     →→→     │     콘텐츠        │
│  │            │  │              │                  │
│  └────────────┘  │              │                  │
│  (여백이 있음)    │              │  (화면 꽉 참)      │
└──────────────────┘              └──────────────────┘

브라우저는 기본적으로 body에                margin/padding을 0으로
8px 정도의 margin이 있음                   설정해서 제거
```

**`<style>` vs `<style scoped>` 차이:**
```vue
<!-- 글로벌 스타일 (App.vue에서 사용) -->
<style>
html, body { ... }    ← 앱 전체에 적용됨!
</style>

<!-- 스코프 스타일 (일반 컴포넌트에서 사용) -->
<style scoped>
.button { ... }        ← 이 컴포넌트에서만 적용됨
</style>
```

App.vue에서는 `scoped` 없이 사용합니다. `html`, `body`는 앱 전체에 해당하는 요소이므로 글로벌 스타일이 맞습니다.

## 왜 이렇게 간단한가?

App.vue가 간단한 이유는 **관심사의 분리 (Separation of Concerns)** 원칙 때문입니다:

```
[나쁜 설계 - 모든 것이 App.vue에]
App.vue (500줄+)
├─ 로그인 폼
├─ 채팅 화면
├─ 관리자 대시보드
├─ 사용자 관리
└─ ... (유지보수 불가능! 😱)

[좋은 설계 - 역할 분리 (이 프로젝트)] ✅
App.vue (16줄)
└─ <router-view /> 하나만!
   │
   ├─ /login      → LoginView.vue
   ├─ /chat       → UserChatView.vue
   ├─ /admin/...  → AdminLayout.vue
   │                 ├─ DashboardView.vue
   │                 ├─ UsersView.vue
   │                 └─ ...
   └─ 각 화면이 자기 역할만 담당 (유지보수 편리 😊)
```

## 컴포넌트 트리 (전체 구조)

```
App.vue                              ← 루트 (여기!)
└─ <router-view>
   │
   ├─ LoginView.vue                  ← /login
   │
   ├─ UserChatLayout.vue             ← /chat
   │   ├─ UserChatSidebar.vue
   │   ├─ ChatInput.vue
   │   └─ UserChatMessage.vue
   │
   └─ AdminLayout.vue                ← /admin/*
       ├─ AppHeader.vue
       ├─ AppSidebar.vue
       └─ <router-view>  (중첩)
          ├─ DashboardView.vue       ← /admin/dashboard
          ├─ ChatView.vue            ← /admin/chat
          ├─ UsersView.vue           ← /admin/users
          └─ ...
```

## 리뷰 체크리스트

- [x] `<template>`에 `<router-view />`만 있는가? → 루트 컴포넌트의 올바른 패턴 ✅
- [x] 불필요한 로직이 App.vue에 없는가? → 빈 script, 깔끔 ✅
- [x] 글로벌 리셋 스타일이 있는가? → margin/padding 0, height 100% ✅
- [x] `<style scoped>`가 아닌 `<style>`인가? → html/body는 글로벌이어야 함 ✅
- [x] `<script setup>` 방식을 사용하는가? → Vue 3 권장 패턴 ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| SFC | Single File Component. 하나의 .vue 파일에 HTML+JS+CSS |
| `<template>` | 화면에 보이는 HTML 구조 |
| `<script setup>` | Vue 3 Composition API의 간결한 문법 |
| `<style>` | CSS 스타일. `scoped` 없으면 전역 적용 |
| `<router-view />` | 현재 URL에 맞는 컴포넌트를 표시하는 자리 |
| 루트 컴포넌트 | 모든 컴포넌트의 최상위 부모. 간결할수록 좋음 |

---
> **이전**: [04_main_js.md](04_main_js.md) - 앱 초기화의 핵심
> **다음**: [06_how_it_works.md](06_how_it_works.md) - 전체 동작 원리 종합
