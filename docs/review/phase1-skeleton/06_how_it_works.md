# 6. 전체 동작 원리 - Phase 1 종합

## 브라우저에서 앱이 뜨기까지

사용자가 `http://localhost:19080`을 브라우저에 입력하면 벌어지는 일을 **시간순으로** 따라가 보겠습니다.

---

### Stage 1. 브라우저가 HTML을 받는다

```
사용자: http://localhost:19080 입력
         │
         ▼
┌─── Vite 개발 서버 (port 19080) ───┐
│                                    │
│  "index.html 보내줄게!"             │
│                                    │
└────────────────────────────────────┘
         │
         ▼
브라우저: index.html 수신
```

**관련 파일**: `index.html`, `vite.config.js` (port: 19080)

---

### Stage 2. HTML을 파싱(해석)하면서 리소스를 로드

```
브라우저가 index.html을 위에서 아래로 읽음:

  <!DOCTYPE html>           ← "HTML5 문서구나"
  <html lang="ko">          ← "한국어 페이지구나"

  <head>
    <meta charset="UTF-8">   ← "UTF-8 인코딩 사용"
    <link rel="icon" ...>    ← favicon.svg 다운로드 요청
    <meta viewport ...>      ← "모바일 대응 설정"
    <title>MUREUM</title>    ← 브라우저 탭 제목 설정
  </head>

  <body>
    <div id="app"></div>      ← ⭐ 빈 div 생성 (여기에 Vue가 그릴 예정)

    <script type="module"
      src="/src/main.js">     ← ⭐⭐ main.js 다운로드 + 실행 시작!
    </script>
  </body>
```

이 시점에서 화면은 **완전히 빈 백지**입니다.

---

### Stage 3. main.js 실행 - import 처리

```
main.js가 실행되면, 먼저 import된 모든 모듈을 가져옴:

  import { createApp } from 'vue'          ← Vue 프레임워크 로드
  import ElementPlus from 'element-plus'    ← UI 라이브러리 로드
  import 'element-plus/dist/index.css'      ← UI 기본 스타일 적용
  import 'element-plus/.../dark/css-vars.css' ← 다크모드 CSS 적용
  import * as Icons from '@element-plus/icons-vue' ← 아이콘 로드

  import App from './App.vue'               ← 루트 컴포넌트 로드
  import router from './router'             ← 라우터 설정 로드
  import store from './store'               ← 상태 관리 로드
  import './assets/styles/main.scss'        ← 전역 스타일 적용

  import { GridLayout, GridItem } from 'vue3-grid-layout-next'  ← 그리드 로드
```

**이 단계에서 중요한 점**: CSS import는 즉시 `<head>`에 `<style>` 태그로 삽입됩니다.

---

### Stage 4. Vue 앱 생성 + 플러그인 설치

```
const app = createApp(App)        ← Vue 앱 인스턴스 생성

┌─── 플러그인 설치 순서 ───┐
│                          │
│  1. 아이콘 전역 등록       │  ← 200+ 아이콘을 app.component()로 등록
│  2. app.use(ElementPlus)  │  ← <el-button>, <el-table> 등 사용 가능
│  3. app.use(router)       │  ← URL → 화면 매칭 기능 활성화
│  4. app.use(store)        │  ← 전역 상태 관리 활성화
│  5. grid-layout 전역 등록  │  ← 대시보드 그리드 컴포넌트
│                          │
└──────────────────────────┘

이 시점에서도 아직 화면은 빈 백지!
(mount 전이니까)
```

---

### Stage 5. 테마 초기화

```
store.dispatch('app/initTheme')
    │
    ├─ localStorage에서 테마 설정 읽기
    │   └─ 예: { userDarkMode: true, adminDarkMode: true }
    │
    ├─ <html> 태그에 data-theme="dark" 속성 추가
    │
    └─ 완료! (동기 작업이라 즉시 끝남)
```

---

### Stage 6. 인증 초기화 (비동기!) ⭐

```
store.dispatch('auth/initAuth')
    │
    ├─ localStorage에서 토큰 확인
    │   ├─ 토큰 없음 → 즉시 완료 (Promise resolve)
    │   └─ 토큰 있음 → 서버에 /api/v1/auth/me 호출
    │                    │
    │                    ├─ 성공 → 사용자 정보 + 메뉴 권한 저장
    │                    └─ 실패 → 토큰 만료. localStorage 정리
    │
    └─ .finally(() => { ... })
         │
         ▼
```

---

### Stage 7. 마운트! - 화면이 그려진다!

```
app.mount('#app')
    │
    ├─ index.html의 <div id="app"> 을 찾음
    │
    ├─ App.vue의 <template>을 그 안에 렌더링
    │   └─ <router-view /> 가 현재 URL을 확인
    │
    ├─ 현재 URL에 맞는 컴포넌트 결정
    │   │
    │   ├─ URL이 "/" → 라우터 가드가 체크
    │   │               ├─ 로그인됨 → landingPage로 이동
    │   │               └─ 비로그인 → /login으로 이동
    │   │
    │   ├─ URL이 "/login" → LoginView.vue 렌더링
    │   ├─ URL이 "/chat" → UserChatLayout.vue 렌더링
    │   └─ URL이 "/admin/..." → AdminLayout.vue 렌더링
    │
    └─ 화면 표시 완료! 🎉
```

---

## 전체 타임라인 (한눈에)

```
시간 ───────────────────────────────────────────────────→

 0ms        50ms       100ms      200ms       300ms
  │          │          │          │           │
  ▼          ▼          ▼          ▼           ▼
 HTML       import     create    initTheme   initAuth
 로드       모듈로드    App +      테마적용     인증확인
            CSS적용    use()                    │
                       플러그인                  ▼
                                             mount!
                                               │
                                               ▼
                                            화면 표시!

  ← - - - - - - 이 동안 빈 화면 - - - - - - - →
```

## 파일 간의 관계도

```
index.html
│
├─ <div id="app"> ─── mount 대상 ──→ App.vue
│                                      │
├─ <script src="main.js"> ──────────→ main.js
│                                      │
│                                      ├─ import vue ←──── package.json에 명시
│                                      ├─ import router ←── router/index.js
│                                      ├─ import store ←── store/index.js
│                                      │
│                                      ├─ createApp(App) ── App.vue 사용
│                                      ├─ app.use(router)
│                                      ├─ app.use(store)
│                                      └─ app.mount('#app') ── index.html의 div와 연결!
│
└─ Vite가 서빙 ←──── vite.config.js
                      │
                      ├─ port: 19080
                      ├─ @ → src/ 매핑
                      └─ proxy: /api → 백엔드
```

## 개발 vs 프로덕션 차이

```
┌─── 개발 모드 (npm run dev) ───────────────────────────────┐
│                                                           │
│  브라우저 → Vite 서버(19080) → index.html 직접 서빙         │
│  .vue 파일 → Vite가 실시간 변환 → 브라우저로 전달           │
│  코드 수정 → HMR으로 즉시 반영 (새로고침 불필요)            │
│  /api → Vite 프록시 → 백엔드(19090)                       │
│                                                           │
└───────────────────────────────────────────────────────────┘

┌─── 프로덕션 (npm run build + 배포) ──────────────────────┐
│                                                           │
│  npm run build                                            │
│    ├─ 모든 .vue, .js, .scss → 최적화된 JS/CSS 번들        │
│    ├─ dist/index.html (최종 HTML)                         │
│    ├─ dist/assets/index-abc123.js (앱 코드 전체)           │
│    └─ dist/assets/index-def456.css (스타일 전체)           │
│                                                           │
│  브라우저 → Nginx(19080) → dist/ 정적 파일 서빙            │
│  /api → Nginx 리버스 프록시 → 백엔드(19090)                │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

## Phase 1 핵심 용어 정리

| 용어 | 설명 |
|------|------|
| **SPA** | Single Page Application. HTML 하나로 모든 화면을 처리 |
| **SFC** | Single File Component. .vue 파일 = HTML + JS + CSS |
| **Vite** | 빌드 도구. 개발 서버 + 번들링 |
| **HMR** | Hot Module Replacement. 코드 저장 → 즉시 브라우저 반영 |
| **마운트(mount)** | Vue 앱을 HTML 요소에 연결하여 화면에 그리는 것 |
| **플러그인(plugin)** | app.use()로 설치하는 확장 기능 |
| **루트 컴포넌트** | App.vue. 모든 컴포넌트의 최상위 부모 |
| **`<router-view>`** | URL에 따라 다른 컴포넌트를 표시하는 자리 |
| **프록시(proxy)** | 개발 시 CORS 우회를 위해 요청을 중계하는 역할 |
| **번들링(bundling)** | 여러 파일을 하나로 합치고 최적화하는 과정 |

## 다음 Phase 미리보기

Phase 1에서 `<router-view />`가 URL에 따라 화면을 바꾼다는 것을 배웠습니다.
**Phase 2**에서는 이 라우팅이 **어떤 규칙**으로 동작하는지, **권한 체크**는 어떻게 하는지를 살펴봅니다.

```
Phase 1 (지금): "앱이 어떻게 시작되는가?"
Phase 2 (다음): "화면이 어떻게 전환되는가? 누가 접근할 수 있는가?"
```

---
> **이전**: [05_app_vue.md](05_app_vue.md) - 루트 컴포넌트
