# 5. 동작 원리 종합 - 데이터 흐름 추적

## 시나리오별로 Vuex 데이터 흐름을 추적합니다

---

## 시나리오 1: 앱 시작 (새로고침 포함)

**상황**: 이전에 로그인한 상태로 브라우저를 새로고침

```
main.js 실행
│
├─ store 생성 (각 모듈의 state 초기화)
│   ├─ auth.state.accessToken = localStorage('mureum_access_token') → "eyJhb..."
│   ├─ auth.state.user = localStorage('mureum_user') → { login_id: 'admin', ... }
│   ├─ app.state.userDarkMode = localStorage('user_theme') → true
│   └─ app.state.adminDarkMode = localStorage('admin_theme') → false
│
├─ dispatch('app/initTheme')
│   └─ applyTheme(false) → 관리자 화면이 기본 → 라이트모드 적용
│
├─ dispatch('auth/initAuth')
│   ├─ state.accessToken 있음 → fetchMe() 호출
│   ├─ GET /api/v1/auth/me → 서버가 최신 사용자 정보 반환
│   ├─ commit('SET_USER', 최신 user) → menus 등 갱신
│   └─ return true
│
└─ app.mount('#app') → 화면 표시
    └─ router beforeEach → isAuthenticated = true → 통과!
```

---

## 시나리오 2: 로그인 전체 흐름

```
LoginView.vue                    auth 모듈                      서버
─────────────                    ──────────                     ──────

[로그인 버튼 클릭]
dispatch('auth/login',
  {loginId, password})
        │
        ▼
                          login() action 시작
                          commit(SET_LOGIN_LOADING, true)
                                    │
                                    ▼
                          authApi.login()  ──────────────→ POST /api/v1/auth/login
                                                                    │
                                                          200 { access_token,
                                                                refresh_token,
                                                                user }
                                    │◄──────────────────────────────┘
                                    ▼
                          dispatch('chat/clearChat')     ← 이전 데이터 정리
                          dispatch('dashboard/clearState')
                          commit(SET_AUTH, {token, user})
                             ├─ state.accessToken = "eyJ..."
                             ├─ state.user = { login_id: 'admin', menus: [...] }
                             └─ localStorage에도 저장
                                    │
                                    ▼
                          commit(SET_LOGIN_LOADING, false)
                          return user
        │◄──────────────────────────┘
        ▼
router.push(landingPage)
  → isAuthenticated = true ✅
  → /admin/dashboard 표시
```

---

## 시나리오 3: NL2SQL 질문 → SSE 스트리밍

```
시간 ──→

[0s] 사용자가 입력: "2024년 입사자 수는?"
     dispatch('chat/sendMessage', query)
     │
     ├─ searchMode === 'nl2sql' → sendMessageStream() 호출
     │
     ├─ commit(ADD_MESSAGE, {role:'user', content:'2024년 입사자 수는?'})
     │   messages: [{role:'user', content:'2024년 입사자 수는?'}]
     │
     ├─ commit(ADD_MESSAGE, {role:'assistant', content:'', isStreaming:true})
     │   messages: [..., {role:'assistant', content:'', isStreaming:true}]
     │
     └─ SSE 연결 시작 → POST /api/v1/nl2sql/stream

[0.3s] 서버 → onNodeStart({message: '의도 분석 중...'})
       commit(UPDATE_LAST_MESSAGE, {currentStep: '의도 분석 중...'})
       화면: [⏳ 의도 분석 중...]

[0.5s] 서버 → onNodeComplete({stage: 'intent', message: '의도 분석 완료'})
       commit(ADD_STREAM_PROGRESS, event)
       화면: [✓ 의도 분석 완료]

[0.8s] 서버 → onNodeStart({message: 'SQL 생성 중...'})
       화면: [✓ 의도 분석 완료] [⏳ SQL 생성 중...]

[1.2s] 서버 → onNodeComplete({stage: 'generate', ...})
       화면: [✓ 의도 분석] [✓ SQL 생성]

[1.5s] 서버 → onNodeComplete({stage: 'execute', ...})
       화면: [✓ 의도 분석] [✓ SQL 생성] [✓ SQL 실행]

[2.0s] 서버 → onComplete({
         answer: "2024년 입사자는 총 15명입니다.",
         sql: "SELECT COUNT(*) ...",
         sql_result: { columns: ['count'], rows: [[15]] }
       })

       commit(UPDATE_LAST_MESSAGE, {
         content: "2024년 입사자는 총 15명입니다.",
         isStreaming: false,
         sql: "SELECT COUNT(*) ...",
         sqlResult: ...
       })

       최종 messages:
       [
         { role: 'user',      content: '2024년 입사자 수는?' },
         { role: 'assistant', content: '2024년 입사자는 총 15명입니다.',
           queryType: 'nl2sql', sql: '...', sqlResult: {...},
           isStreaming: false, streamProgress: [...] }
       ]
```

---

## 시나리오 4: 다크모드 토글

```
AppHeader.vue에서 🌙 버튼 클릭
│
├─ dispatch('app/toggleDarkMode')
│
├─ commit(TOGGLE_CURRENT_DARK_MODE)
│   ├─ currentView === 'admin'
│   ├─ adminDarkMode: false → true (반전)
│   ├─ saveTheme('admin', true) → localStorage('admin_theme', 'dark')
│   └─ applyTheme(true) → <html data-theme="dark" class="dark">
│
└─ CSS 변수 변경 → 화면 색상 즉시 전환!
     :root → [data-theme="dark"] 적용
     --bg-color: #ffffff → #1a1a2e
     --text-color: #333333 → #e0e0e0
```

---

## 시나리오 5: 토큰 만료 → 자동 갱신

이 시나리오는 **chat 모듈이 아닌 api/index.js**(Axios 인터셉터)에서 처리되지만, store와 연계됩니다:

```
[API 호출 중 401 에러 발생]

chat 모듈: searchApi.search() → 401 Unauthorized
    │
    ▼
Axios 인터셉터 (api/index.js):
    │
    ├─ "401이네? 토큰 갱신 시도!"
    ├─ refreshToken = localStorage('mureum_refresh_token')
    ├─ POST /api/v1/auth/refresh → 새 access_token 발급
    │
    ├─ 성공 →
    │   ├─ localStorage에 새 토큰 저장
    │   └─ 원래 API 요청을 새 토큰으로 재시도!
    │       → 사용자는 에러를 모르고 정상 응답을 받음
    │
    └─ 실패 (refresh도 만료) →
        ├─ localStorage 토큰 삭제
        └─ router.push('/login') → 로그인 페이지로
```

---

## 5개 모듈 간의 데이터 의존 관계

```
┌─────────────────────────────────────────────────────┐
│                     store                            │
│                                                      │
│  ┌── auth ──┐     ┌── app ──┐     ┌── chat ──┐     │
│  │          │     │         │     │          │     │
│  │ user     │     │ darkMode│     │ messages │     │
│  │ token    │     │ sidebar │     │ mode     │     │
│  │ menus    │     │ view    │     │ session  │     │
│  │          │     │         │     │ streaming│     │
│  └─┬──┬──┬─┘     └─────────┘     └──────────┘     │
│    │  │  │                                          │
│    │  │  └──────────────────────────────────┐       │
│    │  │                                     │       │
│    │  │  ┌── document ─┐     ┌─ dashboard ─┐│       │
│    │  │  │ documents   │     │ widgets     ││       │
│    │  │  │ filters     │     │ dashboards  ││       │
│    │  └──│ pagination  │     │ layout      │┘       │
│    │     └─────────────┘     └─────────────┘        │
│    │                                                 │
│    └─── 로그인/로그아웃 시 chat, dashboard 초기화 ──→  │
│                                                      │
└─────────────────────────────────────────────────────┘

모듈 간 의존:
  auth → chat      : 로그인/로그아웃 시 clearChat
  auth → dashboard : 로그인/로그아웃 시 clearState
  auth ← router    : isAuthenticated, canAccessAdmin, hasMenuPermission
  app  ← header    : isDarkMode, toggleDarkMode
```

---

## Phase 3 종합 리뷰 체크리스트

### 설계 원칙
- [x] 모듈이 기능별로 분리되어 있는가? → 5개 모듈 ✅
- [x] namespaced: true로 이름 충돌을 방지하는가? → 모든 모듈 ✅
- [x] 단방향 데이터 흐름을 따르는가? → Action → Mutation → State ✅

### 데이터 영속성
- [x] 인증 토큰이 새로고침에도 유지되는가? → localStorage ✅
- [x] 테마 설정이 유지되는가? → localStorage ✅
- [x] 채팅 메시지는 새로고침 시 사라지는가? → 이력 API로 복원 가능 ✅

### 에러 처리
- [x] API 실패 시 사용자에게 표시되는가? → 에러 메시지 mutation ✅
- [x] 스트리밍 에러 시 처리되는가? → onError 콜백 ✅
- [x] localStorage 실패를 처리하는가? → try/catch ✅

### 보안
- [x] 로그아웃 시 모든 민감 데이터가 삭제되는가? → CLEAR_AUTH + clearChat ✅
- [x] 사용자 전환 시 이전 데이터가 정리되는가? → login에서 clearChat ✅

## Phase 3 핵심 용어 정리

| 용어 | 설명 |
|------|------|
| **Vuex Store** | 앱 전체에서 공유하는 중앙 데이터 저장소 |
| **State** | 원본 데이터. 직접 수정 금지 |
| **Mutation** | State를 변경하는 유일한 방법. 동기만 가능 |
| **Action** | 비동기 작업 후 Mutation 호출. API 호출은 여기서 |
| **Getter** | State에서 계산된 값. 자동 캐싱 |
| **Module** | Store를 기능별로 분리. namespaced로 격리 |
| **localStorage** | 브라우저 영구 저장소. 새로고침에도 유지 |
| **SSE** | Server-Sent Events. 서버→클라이언트 실시간 데이터 전송 |

## 다음 Phase 미리보기

Phase 3에서 Store가 API를 호출하는 것을 보았습니다 (authApi.login, searchApi.search 등).
**Phase 4**에서는 이 **API 통신 계층(Axios)**이 어떻게 구성되어 있는지 살펴봅니다.

```
Phase 1: "앱이 어떻게 시작되는가?"
Phase 2: "화면이 어떻게 전환되는가?"
Phase 3 (지금): "데이터가 어디에 저장되고 어떻게 공유되는가?"
Phase 4 (다음): "백엔드와 어떻게 통신하는가?"
```

---
> **이전**: [04_chat_module.md](04_chat_module.md) - 채팅 모듈
