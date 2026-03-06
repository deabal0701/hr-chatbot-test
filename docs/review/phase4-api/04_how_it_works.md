# 4. 동작 원리 종합 - 요청에서 응답까지

## 시나리오별로 API 통신의 전체 흐름을 추적합니다

---

## 시나리오 1: 로그인 API 호출

**상황**: 사용자가 로그인 버튼을 클릭

```
LoginView.vue                 auth Store                 api/auth.js              api/index.js                서버
─────────────                 ──────────                 ───────────              ────────────                ──────

[로그인 클릭]
dispatch('auth/login',
  {loginId, password})
        │
        ▼
                    login() action 시작
                    commit(SET_LOGIN_LOADING, true)
                              │
                              ▼
                    authApi.login(loginId, password)
                                          │
                                          ▼
                                    apiClient.post(
                                      '/api/v1/auth/login',
                                      { login_id, password })
                                                    │
                                                    ▼
                                              [요청 인터셉터]
                                              토큰 없음 → 그냥 통과
                                                    │
                                                    ▼
                                              POST /api/v1/auth/login ──────────→ FastAPI
                                                                                     │
                                              200 OK ◄──────────────── { success: true,
                                                                          data: {
                                                                            access_token,
                                                                            refresh_token,
                                                                            user } }
                                                    │
                                                    ▼
                                              [응답 인터셉터]
                                              success === true
                                              → return result.data
                                              → { access_token, user }만 반환!
                                          │
                              ◄────────────
                              ▼
                    commit(SET_AUTH, data)
                      ├─ state.accessToken = "eyJ..."
                      ├─ state.user = { login_id: 'admin', ... }
                      └─ localStorage에도 저장
                              │
        ◄──────────────────────
        ▼
router.push(landingPage)
  → /admin/dashboard 표시
```

**핵심 포인트:**
- 로그인 요청에는 토큰이 없음 (아직 로그인 전이니까)
- 인터셉터가 `{ success, data }` → `data`만 추출
- Store가 토큰을 localStorage에 저장 → 이후 모든 요청에 자동 첨부

---

## 시나리오 2: 사용자 목록 조회 (일반 CRUD)

**상황**: 관리자가 사용자 관리 페이지에 진입

```
UsersView.vue        document Store          api/users.js         api/index.js             서버
─────────────        ──────────              ────────────         ────────────             ──────

[페이지 진입]
(mounted)
usersApi.list({
  page: 1,
  page_size: 20 })
        │
        ▼
                                    apiClient.get(
                                      '/api/admin/v1/users',
                                      { params: { page:1, page_size:20 } })
                                                    │
                                                    ▼
                                              [요청 인터셉터]
                                              localStorage에서 토큰 읽음
                                              headers.Authorization = 'Bearer eyJ...'
                                                    │
                                                    ▼
                                              GET /api/admin/v1/users?page=1&page_size=20
                                              Authorization: Bearer eyJhbG... ────────→ FastAPI
                                                                                          │
                                                                              require_menu_permission
                                                                              ("USER_MGMT", "read")
                                                                                          │
                                              200 OK ◄──────────── { success: true,
                                                                      data: {
                                                                        items: [{...}, ...],
                                                                        total: 25 } }
                                                    │
                                                    ▼
                                              [응답 인터셉터]
                                              → return { items: [...], total: 25 }
        │
        ◄──────────────────────────────────────────
        ▼
const data = await usersApi.list(...)
// data = { items: [...], total: 25 }
this.users = data.items
this.total = data.total
```

**핵심 포인트:**
- `params` 객체가 쿼리 스트링(`?page=1&page_size=20`)으로 자동 변환
- 토큰이 요청 인터셉터에서 자동 첨부
- 서버의 권한 체크(`require_menu_permission`)를 통과해야 데이터 수신

---

## 시나리오 3: 토큰 만료 → 자동 갱신 → 재시도

**상황**: 30분 경과 후 API 호출 시 토큰 만료

```
시간 ──→

[30분 경과]

UsersView                           api/index.js                          서버
──────────                          ────────────                          ──────

usersApi.list()
        │
        ▼
                              [요청 인터셉터]
                              만료된 토큰 첨부 (아직 모름)
                                    │
                                    ▼
                              GET /api/admin/v1/users
                              Authorization: Bearer (만료된 토큰) ──────→ FastAPI
                                                                            │
                              401 Unauthorized ◄────────── "토큰 만료됨!"
                                    │
                                    ▼
                              [응답 인터셉터 - 에러]
                              status === 401?  → YES!
                              _retry?          → NO (첫 시도)
                              isRefreshing?    → NO
                                    │
                                    ▼
                              isRefreshing = true
                              _retry = true
                                    │
                                    ▼
                              POST /api/v1/auth/refresh
                              { refresh_token: "eyJ..." } ────────────→ FastAPI
                                                                            │
                              200 OK ◄──── { access_token: "새토큰", ... }
                                    │
                                    ▼
                              localStorage에 새 토큰 저장
                              isRefreshing = false
                                    │
                                    ▼
                              [원래 요청 재시도!]
                              GET /api/admin/v1/users
                              Authorization: Bearer (새 토큰!) ────────→ FastAPI
                                                                            │
                              200 OK ◄────── { items: [...], total: 25 }
                                    │
                                    ▼
                              [응답 인터셉터 - 성공]
                              → return data
        │
        ◄──────────────────────
        ▼
const data = await usersApi.list()
// 사용자는 401이 발생했다는 것을 전혀 모름!
// 정상적으로 데이터를 받음 ✅
```

---

## 시나리오 4: 동시 요청 + 토큰 만료

**상황**: 대시보드 진입 시 여러 API를 동시에 호출했는데 토큰이 만료됨

```
시간 ──→

DashboardView                         api/index.js                        서버
──────────────                        ────────────                        ──────

[대시보드 진입 - 3개 API 동시 호출]
dashApi.getKpi()     ─┐
dashApi.getTrend()   ─┤
dashApi.getRecent()  ─┘
        │
        ▼ (3개 동시 전송)

                                GET /dashboard/kpi      → 401 ◄── (요청A)
                                GET /dashboard/trend    → 401 ◄── (요청B)
                                GET /dashboard/recent   → 401 ◄── (요청C)

[요청A 처리]                    isRefreshing = false → true
                                POST /auth/refresh ──────────→ (갱신 시작)

[요청B 처리]                    isRefreshing === true
                                → failedQueue에 대기 ⏳

[요청C 처리]                    isRefreshing === true
                                → failedQueue에 대기 ⏳

[갱신 응답 도착]                ◄── { access_token: "새토큰" }
                                    │
                                    ├─ localStorage 저장
                                    ├─ 요청A 재시도 → 성공 ✅
                                    │
                                    └─ processQueue("새토큰")
                                        ├─ 요청B 재시도 → 성공 ✅
                                        └─ 요청C 재시도 → 성공 ✅

→ 토큰 갱신은 1회만!
→ 3개 요청 모두 성공!
→ 사용자는 아무것도 모름!
```

---

## 시나리오 5: NL2SQL SSE 스트리밍 전체 흐름

**상황**: "2024년 입사자 수는?" 질문

```
시간 ──→

ChatView       chat Store         api/search.js      api/sse.js           서버
────────       ──────────         ─────────────      ──────────           ──────

[전송 클릭]
dispatch('chat/
 sendMessage',
 query)
    │
    ▼
         searchMode === 'nl2sql'
         → sendMessageStream()
              │
              ├─ ADD_MESSAGE (user)
              ├─ ADD_MESSAGE (assistant, empty, isStreaming)
              │
              ▼
         searchApi.searchStream(
           params, callbacks)
                    │
                    ▼
                              streamSSE(
                                '/api/v1/search/stream',
                                { query, mode },
                                callbacks )
                                    │
                                    ▼
                              fetch POST ─────────────────────→ FastAPI
                              Authorization: Bearer eyJ...       │
                              { query: "2024년 입사자 수?" }      │
                                                                  │
                                                            NL2SQL 그래프 실행
                                                                  │
[0.3초]                       ◄── "event: node_start\n
                                    data: {\"message\":\"의도 분석 중...\"}\n\n"
                                    │
                              parseSSEEvent() → { type: 'node_start', data }
                              callbacks.onNodeStart(data)
              │
              ◄────
              ▼
         UPDATE_LAST_MESSAGE
         { currentStep: '의도 분석 중...' }
         → 화면: [⏳ 의도 분석 중...]

[0.5초]                       ◄── "event: node_complete\n
                                    data: {\"stage\":\"intent\"}\n\n"
              │
              ◄────
              ▼
         ADD_STREAM_PROGRESS(event)
         → 화면: [✓ 의도 분석 완료]

[1.0초]                       ◄── node_start: "SQL 생성 중..."
              │
              ▼
         → 화면: [✓ 의도 분석] [⏳ SQL 생성 중...]

[1.5초]                       ◄── node_complete: "SQL 생성 완료"
              │
              ▼
         → 화면: [✓ 의도 분석] [✓ SQL 생성]

[2.0초]                       ◄── node_complete: "SQL 실행 완료"
              │
              ▼
         → 화면: [✓ 의도 분석] [✓ SQL 생성] [✓ SQL 실행]

[2.5초]                       ◄── "event: complete\n
                                    data: {\"answer\":\"15명입니다\",
                                           \"sql\":\"SELECT...\",
                                           \"sql_result\":{...}}\n\n"
              │
              ◄────
              ▼
         callbacks.onComplete(data)
         UPDATE_LAST_MESSAGE {
           content: "15명입니다",
           isStreaming: false,
           sql: "SELECT...",
           sqlResult: {...}
         }
         SET_STREAMING(false)
    │
    ◄────
    ▼
화면에 최종 답변 표시!
"2024년 입사자는 총 15명입니다."
[SQL 보기] [차트 보기] [Excel 내보내기]
```

---

## 시나리오 6: 스트리밍 중단

**상황**: 사용자가 답변 생성 중에 "중지" 버튼 클릭

```
ChatView       chat Store         api/sse.js           서버
────────       ──────────         ──────────           ──────

[중지 클릭]
dispatch('chat/
 cancelStream')
    │
    ▼
         cancelStream()
         state.streamController
           .abort()        ←── AbortController!
              │
              ▼
                           controller.signal →
                           fetch 즉시 중단!
                           AbortError 발생
                              │
                              ▼
                           err.name === 'AbortError'
                           → return (에러 아님!)

         SET_STREAMING(false)
         SET_LOADING(false)
         SET_STREAM_CONTROLLER(null)
    │
    ◄────
    ▼
화면: 스트리밍 중단됨
(마지막으로 받은 상태까지만 표시)
```

---

## 시나리오 7: 네트워크 에러

**상황**: 인터넷 연결이 끊긴 상태에서 API 호출

```
컴포넌트                    api/index.js                    서버
────────                    ────────────                    ──────

apiClient.get('/users')
    │
    ▼
                      [요청 인터셉터]
                      토큰 첨부
                           │
                           ▼
                      GET /users  ──── ✕ ──── (연결 불가!)
                           │
                           ▼
                      [응답 인터셉터 - 에러]
                      !error.response  → true (response 없음)
                           │
                           ▼
                      const networkError = new Error(
                        '네트워크 연결을 확인해주세요'
                      )
                      networkError.code = 'NETWORK_ERROR'
    │
    ◄────────────────────
    ▼
catch (error) {
  // error.message = "네트워크 연결을 확인해주세요"
  // error.code = "NETWORK_ERROR"
  → 사용자에게 에러 표시
}
```

---

## API 계층 전체 구조 정리

```
┌─────────────────────────────────────────────────────────────┐
│                      프론트엔드                              │
│                                                              │
│  ┌─── View (컴포넌트) ───┐                                  │
│  │  dispatch / 직접 호출  │                                  │
│  └──────────┬────────────┘                                  │
│             │                                                │
│  ┌──────────▼────────────┐                                  │
│  │  Store (Vuex 모듈)     │ ← 비즈니스 로직, 상태 관리       │
│  │  auth, chat, app, ... │                                  │
│  └──────────┬────────────┘                                  │
│             │                                                │
│  ┌──────────▼────────────┐                                  │
│  │  API 모듈 (얇은 계층)  │ ← URL, 메서드, 데이터만 정의     │
│  │  auth.js, users.js    │                                  │
│  │  search.js, agent.js  │                                  │
│  └──────┬─────────┬──────┘                                  │
│         │         │                                          │
│  ┌──────▼──┐  ┌───▼──────┐                                  │
│  │ index.js│  │  sse.js  │ ← 통신 엔진                      │
│  │ (Axios) │  │ (fetch)  │                                  │
│  │         │  │          │                                  │
│  │ 인터셉터 │  │ SSE 파싱  │                                  │
│  │ 토큰갱신 │  │ 콜백호출  │                                  │
│  └────┬────┘  └────┬─────┘                                  │
│       │            │                                         │
└───────┼────────────┼─────────────────────────────────────────┘
        │            │
────────▼────────────▼──── 네트워크 ────────────────────────────
        │            │
┌───────▼────────────▼─────────────────────────────────────────┐
│                     백엔드 (FastAPI)                          │
│                                                              │
│  CORS → Logging → Auth → History → Route Handler             │
│                                         │                    │
│                              Service → Graph (LangGraph)     │
│                                         │                    │
│                                   응답 / SSE 스트림           │
└──────────────────────────────────────────────────────────────┘
```

---

## Phase 4 종합 리뷰 체크리스트

### 통신 기반
- [x] Axios 인스턴스가 공통 설정을 제공하는가? → baseURL, timeout, headers ✅
- [x] 환경별 baseURL이 분리되어 있는가? → .env.development/docker/production ✅
- [x] 모든 요청에 토큰이 자동 첨부되는가? → 요청 인터셉터 ✅

### 응답 처리
- [x] 서버 응답의 data가 자동 추출되는가? → 응답 인터셉터 ✅
- [x] 에러 형식이 통일되어 있는가? → { message, code, detail } ✅
- [x] 네트워크 에러가 구분되는가? → NETWORK_ERROR 코드 ✅

### 토큰 갱신
- [x] 401 시 자동 갱신되는가? → refresh + 재시도 ✅
- [x] 동시 401 처리가 되는가? → failedQueue ✅
- [x] 무한 루프가 방지되는가? → _retry 플래그 ✅
- [x] 갱신 실패 시 로그아웃되는가? → clearAuthAndRedirect ✅

### API 모듈
- [x] 모든 모듈이 같은 패턴인가? → apiClient import + BASE_URL + CRUD ✅
- [x] 비즈니스 로직 없이 순수 HTTP 호출만 하는가? → 얇은 계층 ✅
- [x] camelCase ↔ snake_case 변환이 되는가? → API 모듈에서 처리 ✅

### SSE 스트리밍
- [x] POST 요청으로 SSE를 사용하는가? → fetch + ReadableStream ✅
- [x] 이벤트 파싱이 정확한가? → parseSSEEvent ✅
- [x] 스트림 중단이 가능한가? → AbortController ✅
- [x] 무응답 타임아웃이 있는가? → idleTimeout (60초) ✅
- [x] 화면 갱신이 보장되는가? → requestAnimationFrame ✅

## Phase 4 핵심 용어 정리

| 용어 | 설명 |
|------|------|
| **Axios** | JavaScript HTTP 클라이언트 라이브러리 |
| **인터셉터** | 요청/응답을 가로채서 자동으로 처리하는 미들웨어 |
| **Bearer 토큰** | HTTP 헤더에 `Authorization: Bearer <token>` 형태로 전달하는 인증 방식 |
| **401 자동 갱신** | 토큰 만료 → refresh → 재시도, 사용자는 에러를 모름 |
| **failedQueue** | 동시 401 처리용 대기열. 갱신 1회로 여러 요청 해결 |
| **SSE** | Server-Sent Events. 서버 → 클라이언트 실시간 전송 |
| **ReadableStream** | 바이트 단위로 데이터를 읽는 브라우저 API |
| **AbortController** | fetch/SSE 연결을 중단하는 컨트롤러 |
| **Blob** | Binary Large Object. 파일 다운로드에 사용 |

## 다음 Phase 미리보기

Phase 4에서 API 호출의 구조와 데이터 흐름을 이해했습니다.
**Phase 5**에서는 이 데이터를 **화면에 어떻게 배치하는지** — 레이아웃 컴포넌트를 살펴봅니다.

```
Phase 1: "앱이 어떻게 시작되는가?"
Phase 2: "화면이 어떻게 전환되는가?"
Phase 3: "데이터가 어디에 저장되고 어떻게 공유되는가?"
Phase 4 (지금): "백엔드와 어떻게 통신하는가?"
Phase 5 (다음): "화면 레이아웃이 어떻게 구성되는가?"
```

---
> **이전**: [03_sse_streaming.md](03_sse_streaming.md) - SSE 스트리밍
