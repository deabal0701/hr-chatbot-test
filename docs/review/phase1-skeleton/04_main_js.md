# 4. main.js - 앱 초기화의 핵심

> **파일 위치**: `frontend/src/main.js`

## 이 파일은 뭐하는 파일인가?

**레스토랑 오픈 준비 과정**입니다. 건물(index.html)은 준비되었고, 재료(package.json)도 있고, 주방 설비(vite.config.js)도 갖추었습니다. 이제 이 파일에서 **직원을 배치하고, 테이블을 세팅하고, 문을 여는** 과정을 수행합니다.

Vue 앱이 시작되는 **가장 핵심적인 파일**입니다.

## 전체 코드

```javascript
import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'
import store from './store'
import './assets/styles/main.scss'

// vue3-grid-layout
import { GridLayout, GridItem } from 'vue3-grid-layout-next'
import 'vue3-grid-layout-next/dist/style.css'

const app = createApp(App)

// Element Plus Icons 등록
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(ElementPlus, { locale: undefined })
app.use(router)
app.use(store)

// Grid Layout 전역 컴포넌트 등록
app.component('grid-layout', GridLayout)
app.component('grid-item', GridItem)

// 앱 마운트 전 저장된 테마 적용
store.dispatch('app/initTheme')

// 저장된 토큰이 있으면 /me 호출하여 최신 사용자 정보(menus) 갱신
store.dispatch('auth/initAuth').finally(() => {
  app.mount('#app')
})
```

## 단계별 상세 설명

### Step 1. 필요한 모듈 가져오기 (import)

```javascript
// ─── Vue 프레임워크 ───
import { createApp } from 'vue'          // Vue 앱을 만드는 함수

// ─── UI 라이브러리 ───
import ElementPlus from 'element-plus'                        // UI 컴포넌트 (버튼, 테이블 등)
import 'element-plus/dist/index.css'                          // Element Plus 기본 스타일
import 'element-plus/theme-chalk/dark/css-vars.css'           // 다크모드 스타일
import * as ElementPlusIconsVue from '@element-plus/icons-vue' // 아이콘 모음

// ─── 앱 핵심 모듈 ───
import App from './App.vue'              // 루트 컴포넌트
import router from './router'            // 페이지 라우팅 (→ router/index.js)
import store from './store'              // 전역 상태 관리 (→ store/index.js)
import './assets/styles/main.scss'       // 전역 스타일시트

// ─── 대시보드 레이아웃 ───
import { GridLayout, GridItem } from 'vue3-grid-layout-next'  // 드래그 가능한 그리드
import 'vue3-grid-layout-next/dist/style.css'                 // 그리드 스타일
```

**import의 두 가지 종류:**
```javascript
import router from './router'           // ① 모듈 가져오기 → 변수에 저장해서 나중에 사용
import './assets/styles/main.scss'      // ② 파일 실행만 → 변수 없이 CSS가 적용됨
```

### Step 2. Vue 앱 인스턴스 생성

```javascript
const app = createApp(App)
```

이 한 줄이 하는 일:
```
createApp(App)
    │
    ├─ Vue 앱 인스턴스를 만듦
    ├─ App.vue를 루트 컴포넌트로 설정
    └─ 아직 화면에 표시되진 않음! (mount 전)

비유: 자동차를 조립했지만 아직 시동은 안 건 상태
```

### Step 3. Element Plus 아이콘 전역 등록

```javascript
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}
```

**이 코드가 하는 일:**

```javascript
// ElementPlusIconsVue 객체 안에는 200개+ 아이콘이 들어있음:
// { Search: SearchComponent, Edit: EditComponent, Delete: DeleteComponent, ... }

// Object.entries()로 [이름, 컴포넌트] 쌍을 하나씩 꺼내서
// app.component()로 전역 등록

// 등록 후 어디서든 이렇게 사용 가능:
// <el-icon><Search /></el-icon>
// <el-icon><Edit /></el-icon>
// <el-icon><Delete /></el-icon>
```

**전역 등록 vs 지역 등록:**
```
전역 등록 (이 프로젝트 방식):
  ✅ 어떤 .vue 파일에서든 바로 사용 가능
  ❌ 사용하지 않는 아이콘도 메모리에 올라감

지역 등록 (대안):
  ✅ 필요한 아이콘만 import → 메모리 절약
  ❌ 사용할 때마다 import 해야 해서 번거로움

→ 프로젝트가 크지 않으면 전역 등록이 편리함
```

### Step 4. 플러그인 설치 (app.use)

```javascript
app.use(ElementPlus, { locale: undefined })   // UI 라이브러리 설치
app.use(router)                               // 라우터 설치
app.use(store)                                // 상태 관리 설치
```

**app.use()란?**

Vue 앱에 기능을 추가하는 방법입니다. 스마트폰에 앱을 설치하는 것과 비슷합니다:

```
app.use(ElementPlus)  →  "버튼, 테이블, 폼 등 UI 컴포넌트를 사용할 수 있게 해줘"
app.use(router)       →  "URL에 따라 다른 화면을 보여주는 기능을 추가해줘"
app.use(store)        →  "여러 컴포넌트가 데이터를 공유할 수 있게 해줘"
```

**`{ locale: undefined }`의 의미:**
```javascript
app.use(ElementPlus, { locale: undefined })
// Element Plus의 언어 설정
// undefined = 기본값(영어) 사용
// 한국어가 필요하면 나중에 locale을 추가하면 됨
```

### Step 5. 전역 컴포넌트 등록

```javascript
app.component('grid-layout', GridLayout)
app.component('grid-item', GridItem)
```

대시보드에서 위젯을 드래그로 배치할 수 있는 그리드 컴포넌트입니다:

```html
<!-- 등록 후 이렇게 사용 가능 -->
<grid-layout :layout="widgets" :col-num="12">
  <grid-item v-for="item in widgets" :key="item.i">
    차트나 KPI 위젯
  </grid-item>
</grid-layout>
```

### Step 6. 테마 초기화 ⭐

```javascript
store.dispatch('app/initTheme')
```

**dispatch란?** Vuex 스토어에게 "이 작업을 수행해줘"라고 요청하는 것입니다.

```
store.dispatch('app/initTheme')
         │       │      │
         │       │      └── 실행할 작업 이름
         │       └──── store의 'app' 모듈
         └──── "요청을 보내다"

이 작업이 하는 일:
  1. localStorage에서 저장된 테마 설정을 읽음
  2. 다크모드/라이트모드를 <html> 태그에 적용
  3. 사용자가 마지막에 선택한 테마를 기억하고 있다가 복원
```

### Step 7. 인증 초기화 + 앱 마운트 ⭐⭐⭐

```javascript
store.dispatch('auth/initAuth').finally(() => {
  app.mount('#app')
})
```

이 부분이 **이 파일에서 가장 중요한 코드**입니다!

```
store.dispatch('auth/initAuth')
│
├─ localStorage에 저장된 토큰이 있는가?
│   ├─ 있다면 → 서버에 /me API 호출 → 최신 사용자 정보 갱신
│   │          (메뉴 권한, 역할 정보 등)
│   └─ 없다면 → 아무것도 안 함
│
└─ .finally(() => { app.mount('#app') })
   │
   └─ 성공이든 실패든 → 반드시 앱을 마운트!
```

**왜 인증을 먼저 하고 마운트하는가?**

```
[잘못된 순서 - 마운트 먼저]
1. app.mount('#app')        → 화면 표시
2. auth/initAuth 실행 중... → 아직 권한 모름
3. 라우터 가드 체크           → 권한 없다고 판단!
4. 로그인 페이지로 강제 이동!  → 이미 로그인한 사용자인데... 😤

[올바른 순서 - 인증 먼저] ← 이 프로젝트의 방식
1. auth/initAuth 실행       → 권한 정보 획득
2. app.mount('#app')        → 화면 표시
3. 라우터 가드 체크           → 권한 있음! 통과 ✅
4. 올바른 페이지 표시         → 사용자 만족 😊
```

**`.finally()`가 중요한 이유:**
```javascript
// .then()만 쓰면:
store.dispatch('auth/initAuth')
  .then(() => app.mount('#app'))
// → 인증 실패 시 mount가 안 됨! 빈 화면! 😱

// .finally()를 쓰면:
store.dispatch('auth/initAuth')
  .finally(() => app.mount('#app'))
// → 인증 성공이든 실패든 무조건 mount! ✅
//   실패하면 로그인 화면으로 이동시키면 됨
```

## 전체 실행 순서 (시간순)

```
 시간 ──→

  ①          ②          ③         ④           ⑤
import    createApp   app.use   initTheme   initAuth
 모듈       (App)     플러그인    테마 복원    인증 확인
가져오기    생성        설치                    │
                                              ▼
                                          app.mount('#app')
                                              │
                                              ▼
                                     App.vue가 화면에 표시!
                                     <router-view>가 현재
                                     URL에 맞는 페이지 렌더링
```

## import 순서의 의미

이 프로젝트의 import 순서는 **관례(Convention)**를 따릅니다:

```javascript
// 1) 외부 라이브러리 (node_modules)
import { createApp } from 'vue'
import ElementPlus from 'element-plus'

// 2) 내부 모듈 (프로젝트 코드)
import App from './App.vue'
import router from './router'
import store from './store'

// 3) 스타일 파일
import './assets/styles/main.scss'
```

이 순서를 지키면 코드를 읽을 때 **외부 → 내부 → 스타일** 순으로 자연스럽게 파악할 수 있습니다.

## 리뷰 체크리스트

- [x] Vue 3의 `createApp` 방식을 사용하는가? → Vue 3 표준 방식 ✅
- [x] 플러그인 등록 순서가 적절한가? → UI → Router → Store 순서 ✅
- [x] 인증 초기화가 마운트보다 먼저인가? → `.finally()` 패턴으로 보장 ✅
- [x] 테마 초기화가 마운트 전에 수행되는가? → 화면 깜빡임 방지 ✅
- [x] 다크모드 CSS가 import 되어있는가? → `dark/css-vars.css` ✅
- [x] 전역 스타일이 로드되는가? → `main.scss` import ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| `createApp(App)` | Vue 앱 인스턴스 생성. App.vue를 루트로 설정 |
| `app.use()` | 플러그인 설치 (기능 추가) |
| `app.component()` | 전역 컴포넌트 등록 (어디서든 사용 가능) |
| `store.dispatch()` | Vuex 스토어에 작업 요청 (action 실행) |
| `app.mount('#app')` | 앱을 HTML의 `<div id="app">`에 연결 → 화면 표시! |
| `.finally()` | 성공/실패와 무관하게 반드시 실행되는 코드 |

---
> **이전**: [03_vite_config.md](03_vite_config.md) - 빌드 도구 설정
> **다음**: [05_app_vue.md](05_app_vue.md) - 루트 컴포넌트
