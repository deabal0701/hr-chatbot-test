# Phase 1. 프로젝트 뼈대 - 앱이 어떻게 시작되는가?

## 이 Phase에서 배우는 것

웹 애플리케이션이 **브라우저에 열리는 순간부터 화면이 그려지기까지** 어떤 일이 벌어지는지를 이해합니다.

## 비유로 이해하기

Vue.js 앱이 실행되는 과정을 **레스토랑 오픈**에 비유해 볼까요?

```
1. index.html     → 건물 (빈 식당 공간)
2. package.json   → 재료 목록 (어떤 식재료가 필요한지)
3. vite.config.js → 주방 설비 (어떻게 요리할지 설정)
4. main.js        → 오픈 준비 (직원 배치, 테이블 세팅, 문 열기)
5. App.vue        → 메인 홀 (손님이 앉는 공간, 여기서 모든 서비스 시작)
```

## 실행 순서 (이 순서대로 읽으세요!)

```
브라우저가 index.html 로드
    │
    ├─ <div id="app"> 빈 공간 준비
    │
    └─ <script> main.js 실행
         │
         ├─ 1. Vue 앱 인스턴스 생성
         ├─ 2. Element Plus (UI 라이브러리) 설치
         ├─ 3. Router (페이지 이동) 설치
         ├─ 4. Store (데이터 저장소) 설치
         ├─ 5. 테마 적용 (다크모드/라이트모드)
         ├─ 6. 인증 초기화 (로그인 상태 확인)
         │
         └─ 7. app.mount('#app') → App.vue가 <div id="app">에 삽입됨!
              │
              └─ App.vue의 <router-view /> 가 현재 URL에 맞는 화면을 표시
```

## 리뷰 파일 목록

| 순서 | 파일 | 리뷰 문서 | 핵심 |
|------|------|-----------|------|
| 1 | `frontend/index.html` | [01_index_html.md](01_index_html.md) | SPA의 유일한 HTML |
| 2 | `frontend/package.json` | [02_package_json.md](02_package_json.md) | 의존성과 스크립트 |
| 3 | `frontend/vite.config.js` | [03_vite_config.md](03_vite_config.md) | 빌드 도구 설정 |
| 4 | `frontend/src/main.js` | [04_main_js.md](04_main_js.md) | 앱 초기화의 핵심 |
| 5 | `frontend/src/App.vue` | [05_app_vue.md](05_app_vue.md) | 루트 컴포넌트 |
| 종합 | - | [06_how_it_works.md](06_how_it_works.md) | 전체 동작 원리 |

## 리뷰 시 스스로 답해볼 질문

1. SPA(Single Page Application)에서 HTML 파일이 왜 하나뿐인가?
2. `npm run dev`를 실행하면 내부적으로 무슨 일이 벌어지는가?
3. `main.js`에서 플러그인을 등록하는 순서가 왜 중요한가?
4. 브라우저에서 `http://localhost:19080`에 접속하면 어떤 순서로 코드가 실행되는가?
5. `App.vue`가 왜 이렇게 간단한가?
