# 2. SSE 스트리밍과 chat Store

> **학습 목표**: SSE 스트리밍이 **어떻게 동작하고**, chat Store가 **어떻게 메시지를 관리하는지** 이해한다.

---

## SSE란 무엇인가?

**SSE (Server-Sent Events)** = 서버가 클라이언트에게 **일방향으로** 이벤트를 보내는 기술.

```
일반 HTTP:                    SSE:
──────────                    ────
클라이언트 → 요청              클라이언트 → 연결 요청
서버 → 응답 (한번에 전부)       서버 → 이벤트 1 (의도 분석 중...)
(연결 종료)                    서버 → 이벤트 2 (SQL 생성 완료)
                               서버 → 이벤트 3 (쿼리 실행 중...)
                               서버 → 이벤트 4 (완료! + 최종 데이터)
                               (연결 종료)
```

**비유**:
- 일반 HTTP = 택배 배송 (주문→기다림→물건 도착)
- SSE = 라이브 방송 (연결→실시간 진행 상황 수신)

### MUREUM에서 SSE를 쓰는 이유

NL2SQL은 여러 단계를 거칩니다:

```
의도 분석 → 스키마 로드 → Few-shot → SQL 생성 → 검증 → 실행 → PII 필터 → 답변 생성
```

이 과정이 5~15초 걸릴 수 있어서, 사용자에게 **"지금 어디까지 진행됐는지"** 보여줘야 합니다.

```
SSE 없이:                          SSE 사용:
──────────                         ──────────
"답변을 생성하고 있습니다..."        ✓ 의도 분석 완료
(5초 동안 아무 변화 없음)            ✓ SQL 생성 완료
(10초 동안 아무 변화 없음)           ✓ 쿼리 검증 완료
(사용자: "멈춘건가?")               ● ● ● 쿼리 실행 중...
최종 답변 표시                      ✓ 쿼리 실행 완료
                                    최종 답변 표시

→ 사용자 경험 차이가 큼!
```

---

## chat Store 전체 구조

> **파일**: `store/modules/chat.js` (433줄)

### State — 채팅의 모든 상태

```javascript
state: () => ({
  // 현재 대화
  messages: [],              // 메시지 배열 [{id, role, content, ...}]
  isLoading: false,          // 응답 대기 중
  searchMode: 'nl2sql',     // 현재 검색 모드
  error: null,               // 에러 상태
  sessionId: null,           // 멀티턴 세션 ID

  // 대화 이력 (사이드바용)
  chatHistory: [],           // 과거 대화 목록
  historyLoading: false,     // 이력 로딩 중
  activeChatId: null,        // 선택된 대화 ID

  // SSE 스트리밍
  isStreaming: false,        // 스트리밍 진행 중
  streamProgress: [],        // 완료된 단계들
  streamController: null     // AbortController (취소용)
})
```

```
State 관계도:

messages ─────────── ChatView / UserChatView에서 v-for 렌더링
    │
    ├── message.isStreaming = true → 스트리밍 UI 표시
    ├── message.streamProgress[] → 완료된 단계 체크마크
    └── message.currentStep → 현재 진행 중인 단계 텍스트

isLoading ───────── 입력 비활성화 + 로딩 인디케이터
isStreaming ──────── 스트리밍 전용 로딩 (typing dots)
searchMode ──────── 모드 라디오 / 드롭다운
sessionId ───────── 멀티턴 대화 연속성
streamController ── 취소 기능 (AbortController.abort())
```

### Mutations — 상태 변경 규칙

```javascript
mutations: {
  // 메시지 추가 (id와 timestamp 자동 생성)
  ADD_MESSAGE(state, message) {
    state.messages.push({
      id: Date.now().toString(),
      timestamp: new Date(),
      ...message
    })
  },

  // 마지막 메시지 부분 업데이트 (스트리밍 진행 표시용)
  UPDATE_LAST_MESSAGE(state, updates) {
    const lastIndex = state.messages.length - 1
    state.messages[lastIndex] = {
      ...state.messages[lastIndex],    // 기존 필드 유지
      ...updates                       // 업데이트할 필드만 덮어쓰기
    }
  },

  // SSE 진행 단계 추가
  ADD_STREAM_PROGRESS(state, progress) {
    state.streamProgress.push(progress)
  },
  ...
}
```

```
ADD_MESSAGE 호출 시:

입력: { role: 'user', content: '부서별 직원수?' }

결과: {
  id: '1709234567890',           ← Date.now()로 자동 생성
  timestamp: new Date(),          ← 현재 시각 자동 추가
  role: 'user',
  content: '부서별 직원수?'
}
```

---

## sendMessage — 메시지 전송 라우터

```javascript
async sendMessage({ commit, state, dispatch }, query) {
  // NL2SQL과 Agent는 SSE 스트리밍 사용
  if (state.searchMode === 'agent' || state.searchMode === 'nl2sql') {
    return dispatch('sendMessageStream', query)
  }

  // RAG 모드: 일반 HTTP 요청
  commit('SET_LOADING', true)
  commit('ADD_MESSAGE', { role: 'user', content: query })

  try {
    const response = await searchApi.search({
      query,
      mode: state.searchMode,
      sessionId: state.sessionId
    })

    // 세션 ID 저장 (멀티턴 대화용)
    if (response.session_id) {
      commit('SET_SESSION_ID', response.session_id)
    }

    // AI 응답 추가
    commit('ADD_MESSAGE', {
      role: 'assistant',
      content: response.answer,
      queryType: response.query_type,
      sources: response.sources,            // RAG 전용
      responseTimeMs: response.response_time_ms,
      metadata: response.metadata
    })
  } catch (error) {
    // 에러도 대화에 표시
    commit('ADD_MESSAGE', {
      role: 'assistant',
      content: `죄송합니다. ${error.message}`,
      isError: true
    })
  } finally {
    commit('SET_LOADING', false)
  }
}
```

```
sendMessage(query)
    │
    ├─ searchMode === 'agent' 또는 'nl2sql'
    │   └─→ sendMessageStream(query)  ← SSE 스트리밍
    │
    └─ searchMode === 'rag' (또는 'auto')
        └─→ searchApi.search()  ← 일반 HTTP
            │
            ├─ 성공: ADD_MESSAGE (assistant)
            └─ 실패: ADD_MESSAGE (isError: true)
```

---

## sendMessageStream — SSE 스트리밍 핵심

```javascript
async sendMessageStream({ commit, state, dispatch }, query) {
  // ① 상태 초기화
  commit('SET_LOADING', true)
  commit('SET_STREAMING', true)
  commit('CLEAR_STREAM_PROGRESS')

  // ② 사용자 메시지 추가
  commit('ADD_MESSAGE', { role: 'user', content: query })

  // ③ 빈 AI 메시지 미리 추가 (스트리밍 표시용)
  commit('ADD_MESSAGE', {
    role: 'assistant',
    content: '',               // 아직 내용 없음
    isStreaming: true,         // 스트리밍 중 표시
    streamProgress: [],        // 완료된 단계 없음
    currentStep: null,         // 현재 진행 단계 없음
    queryType: state.searchMode
  })

  // ④ 콜백 정의
  const callbacks = {
    onNodeStart, onNodeComplete, onComplete, onError
  }

  // ⑤ 스트리밍 시작
  const controller = searchApi.searchStream(
    { query, mode: state.searchMode, sessionId: state.sessionId },
    callbacks
  )
  commit('SET_STREAM_CONTROLLER', controller)
}
```

### 4가지 SSE 콜백 상세

```
서버에서 보내는 이벤트:            클라이언트 콜백:
─────────────────────            ──────────────────

event: node_start               → onNodeStart
data: { node: "intent",         현재 단계 텍스트 업데이트
        message: "의도 분석 중"}

event: node_complete            → onNodeComplete
data: { node: "intent",         ✓ 체크마크 추가
        message: "의도 분석"}

event: complete                 → onComplete
data: { answer: "...",          최종 답변으로 메시지 교체
        sql: "...",
        sql_result: {...} }

event: error                    → onError
data: { message: "에러 발생",    에러 메시지 표시
        code: "SQL_ERROR" }
```

#### onNodeStart — "지금 이걸 하는 중이야"

```javascript
onNodeStart: (event) => {
  commit('UPDATE_LAST_MESSAGE', {
    currentStep: event.message     // "의도 분석 중...", "SQL 생성 중..." 등
  })
}
```

```
화면 표시:
● ● ● 의도 분석 중...     ← currentStep = "의도 분석 중..."
```

#### onNodeComplete — "이건 끝났어"

```javascript
onNodeComplete: (event) => {
  commit('ADD_STREAM_PROGRESS', event)

  const lastMsg = state.messages[state.messages.length - 1]
  commit('UPDATE_LAST_MESSAGE', {
    streamProgress: [...(lastMsg.streamProgress || []), event],
    currentStep: null              // 진행 텍스트 초기화
  })
}
```

```
화면 표시:
✓ 의도 분석 완료              ← streamProgress에 추가됨
● ● ● (다음 단계 대기)        ← currentStep이 null이므로 "처리 중..."
```

#### onComplete — "전부 끝났어! 결과야"

```javascript
onComplete: (event) => {
  const data = event.data

  if (state.searchMode === 'agent') {
    // Agent 모드: steps, toolsUsed 등 Agent 전용 데이터
    commit('UPDATE_LAST_MESSAGE', {
      content: data.answer,
      isStreaming: false,
      queryType: 'agent',
      agentResult: {
        steps: data.steps,
        totalIterations: data.total_iterations,
        toolsUsed: data.tools_used,
        success: data.success
      }
    })
  } else {
    // NL2SQL 모드: sql, sqlResult 등 NL2SQL 전용 데이터
    commit('UPDATE_LAST_MESSAGE', {
      content: data.answer,
      isStreaming: false,                   // 스트리밍 종료!
      queryType: data.query_type,
      sql: data.sql,                        // 실행된 SQL
      sqlResult: data.sql_result,           // 조회 결과
      responseTimeMs: data.response_time_ms,
      metadata: data.metadata
    })
  }

  commit('SET_STREAMING', false)
  commit('SET_LOADING', false)
  dispatch('fetchChatHistory')              // 이력 갱신
}
```

```
onComplete 후 메시지 변화:

Before (스트리밍 중):               After (완료):
{                                   {
  content: '',                        content: '부서별 직원 수는...',
  isStreaming: true,          →       isStreaming: false,
  streamProgress: [...],              sql: 'SELECT dept, COUNT(*)...',
  currentStep: '답변 생성 중'          sqlResult: {columns, rows},
}                                     responseTimeMs: 1250
                                    }
```

#### onError — "문제가 생겼어"

```javascript
onError: (error) => {
  commit('UPDATE_LAST_MESSAGE', {
    content: `죄송합니다. ${error.message}`,
    isStreaming: false,
    isError: true
  })
  commit('SET_STREAMING', false)
  commit('SET_LOADING', false)
}
```

---

## 스트리밍 UI — 타임라인 애니메이션

ChatMessage와 UserChatMessage 모두 같은 패턴으로 스트리밍을 표시합니다.

```html
<template v-if="message.isStreaming">
  <div class="streaming-indicator">
    <!-- ① 완료된 단계들 (체크마크) -->
    <div class="stream-steps" v-if="message.streamProgress?.length > 0">
      <div class="stream-step" v-for="(p, idx) in message.streamProgress" :key="idx">
        <span class="step-check-icon">✓</span>
        <span class="step-label">{{ p.message }}</span>
      </div>
    </div>

    <!-- ② 현재 진행 중 (typing dots) -->
    <div class="streaming-current">
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>
      <span class="streaming-text">{{ message.currentStep || '처리 중...' }}</span>
    </div>
  </div>
</template>
```

### 시간 순서로 보는 화면 변화

```
t=0s: 사용자가 "부서별 직원수?" 전송
┌─────────────────────────────┐
│ ● ● ● 처리 중...            │
└─────────────────────────────┘

t=1s: onNodeStart("의도 분석 중...")
┌─────────────────────────────┐
│ ● ● ● 의도 분석 중...       │
└─────────────────────────────┘

t=2s: onNodeComplete("의도 분석") + onNodeStart("SQL 생성 중...")
┌─────────────────────────────┐
│ ✓ 의도 분석                  │
│ ● ● ● SQL 생성 중...        │
└─────────────────────────────┘

t=4s: onNodeComplete("SQL 생성") + onNodeStart("쿼리 검증 중...")
┌─────────────────────────────┐
│ ✓ 의도 분석                  │
│ ✓ SQL 생성                   │
│ ● ● ● 쿼리 검증 중...       │
└─────────────────────────────┘

t=5s: ... (계속)

t=8s: onComplete (최종 데이터)
┌─────────────────────────────┐
│ 부서별 직원 수는 다음과      │
│ 같습니다.                    │
│ | 부서 | 인원 |             │
│ | 개발 | 25  |              │
│ ...                          │
│ [NL2SQL] 턴 1/5  1250ms     │
│ ▶ 실행된 SQL 쿼리            │
│ ▶ 조회 결과                  │
└─────────────────────────────┘
```

### Typing Dots 애니메이션

```scss
.typing-dots span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: var(--color-primary);
  animation: streaming-typing 1.4s infinite ease-in-out both;

  &:nth-child(1) { animation-delay: 0s; }     // 첫번째 점
  &:nth-child(2) { animation-delay: 0.2s; }   // 두번째 점 (0.2초 뒤)
  &:nth-child(3) { animation-delay: 0.4s; }   // 세번째 점 (0.4초 뒤)
}

@keyframes streaming-typing {
  0%, 80%, 100% {
    transform: scale(0.4);     // 작게
    opacity: 0.4;              // 흐리게
  }
  40% {
    transform: scale(1);       // 크게
    opacity: 1;                // 선명하게
  }
}
```

```
시간 →    0.0s  0.2s  0.4s  0.6s  0.8s  1.0s  1.2s  1.4s
점 1:      ●                   ·                   ●
점 2:            ●                   ·                   ●
점 3:                  ●                   ·

● = 크고 선명   · = 작고 흐림

→ 물결처럼 차례로 커졌다 작아지는 효과
```

---

## 모드 변경과 세션 관리

```javascript
setMode({ commit, state }, mode) {
  const previousMode = state.searchMode
  commit('SET_MODE', mode)

  // 다른 모드로 전환 시 세션 ID 초기화
  if (previousMode !== mode && state.sessionId) {
    commit('SET_SESSION_ID', null)
  }
}
```

```
모드 변경 시나리오:

NL2SQL 모드에서 3번 대화 (session_id: "abc123")
    │
    ▼ 사용자가 RAG 모드로 변경
    │
setMode('rag')
    ├── searchMode = 'rag'
    └── sessionId = null          ← 세션 초기화!
                                    (NL2SQL 멀티턴 문맥은 별도 모드에서 의미 없으므로)

다시 NL2SQL 모드로 변경하면:
    ├── searchMode = 'nl2sql'
    └── sessionId = null          ← 새 대화 시작
        (이전 세션은 서버에서 유지되지만, 클라이언트에서 연결 끊김)
```

---

## 대화 이력 관리

### 이력 목록 조회

```javascript
async fetchChatHistory({ commit }, searchQuery = null) {
  commit('SET_HISTORY_LOADING', true)
  try {
    const params = { limit: 50, offset: 0 }
    if (searchQuery) params.search = searchQuery
    const response = await historyApi.listSessions(params)
    commit('SET_CHAT_HISTORY', response.items || [])
  } catch {
    commit('SET_CHAT_HISTORY', [])
  } finally {
    commit('SET_HISTORY_LOADING', false)
  }
}
```

### 과거 대화 불러오기

```javascript
async loadChatSession({ commit }, sessionKey) {
  commit('SET_LOADING', true)
  commit('SET_ACTIVE_CHAT', sessionKey)
  commit('CLEAR_MESSAGES')

  const response = await historyApi.getSessionHistory(sessionKey)
  const records = response.items || []

  // 이력 레코드를 메시지 형태로 변환
  for (const record of records) {
    // 사용자 질문
    commit('ADD_MESSAGE', {
      role: 'user',
      content: record.question,
      timestamp: new Date(record.requested_at)
    })

    // AI 응답 (모드별로 다른 데이터 매핑)
    const assistantMsg = {
      role: 'assistant',
      content: record.answer,
      queryType: record.request_type,
      isHistory: true
    }

    if (record.request_type === 'nl2sql') {
      assistantMsg.sql = record.trace_data.sql
      assistantMsg.sqlResult = record.trace_data.sql_result
    } else if (record.request_type === 'rag') {
      assistantMsg.sources = record.trace_data.sources
    } else if (record.request_type === 'agent') {
      assistantMsg.agentResult = { ... }
    }

    commit('ADD_MESSAGE', assistantMsg)
  }

  // 세션 ID 복원 (멀티턴 대화 재개용)
  if (records.length > 0 && records[0].session_id) {
    commit('SET_SESSION_ID', records[0].session_id)
    commit('SET_MODE', records[records.length - 1].request_type)
  }
}
```

```
이력 불러오기 데이터 변환:

서버 응답 (tb_api_history 레코드):     → 클라이언트 메시지 배열:
┌────────────────────────────────┐    ┌───────────────────────────┐
│ question: "부서별 직원수?"      │    │ {role: 'user',            │
│ answer: "부서별 직원 수는..."   │    │  content: "부서별 직원수?"}│
│ request_type: 'nl2sql'         │    │                           │
│ trace_data: {                  │    │ {role: 'assistant',       │
│   sql: "SELECT ...",           │    │  content: "부서별...",    │
│   sql_result: {columns, rows}  │    │  queryType: 'nl2sql',    │
│ }                              │    │  sql: "SELECT ...",      │
│                                │    │  sqlResult: {...}}       │
└────────────────────────────────┘    └───────────────────────────┘
```

---

## 스트리밍 취소

```javascript
cancelStream({ state, commit }) {
  if (state.streamController) {
    state.streamController.abort()         // fetch 요청 중단
    commit('SET_STREAMING', false)
    commit('SET_LOADING', false)
    commit('SET_STREAM_CONTROLLER', null)
  }
}
```

```
AbortController 동작:

const controller = new AbortController()
fetch(url, { signal: controller.signal })  ← 요청 시 signal 전달

// 나중에 취소:
controller.abort()  → fetch가 AbortError를 throw → 연결 즉시 종료
```

---

## 리뷰 체크리스트

- [x] sendMessage가 모드별로 올바르게 라우팅하는가? → agent/nl2sql→SSE, rag→HTTP ✅
- [x] 빈 AI 메시지가 먼저 추가되는가? → `isStreaming: true` ✅
- [x] 4가지 콜백이 모두 구현되어 있는가? → onNodeStart/Complete/onComplete/onError ✅
- [x] 스트리밍 완료 시 `isStreaming: false`로 변경되는가? ✅
- [x] 에러 시에도 로딩/스트리밍 상태가 정리되는가? → finally 패턴 ✅
- [x] 모드 변경 시 세션이 초기화되는가? → `SET_SESSION_ID(null)` ✅
- [x] 이력 불러오기가 모드별 데이터를 올바르게 매핑하는가? → request_type 분기 ✅
- [x] 스트리밍 취소가 가능한가? → AbortController.abort() ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **SSE** | 서버→클라이언트 단방향 스트리밍. 실시간 진행 표시에 사용 |
| **sendMessage** | 모드별 라우터. RAG→HTTP, NL2SQL/Agent→SSE |
| **sendMessageStream** | SSE 전송. 빈 메시지 선 추가 → 콜백으로 업데이트 |
| **onNodeStart** | 현재 단계 텍스트 표시 ("SQL 생성 중...") |
| **onNodeComplete** | 완료 체크마크 추가 (✓ SQL 생성) |
| **onComplete** | 최종 데이터로 메시지 교체 (answer, sql, sqlResult) |
| **UPDATE_LAST_MESSAGE** | 스프레드 연산자로 부분 업데이트. 스트리밍의 핵심 mutation |
| **AbortController** | fetch 요청을 프로그래밍 방식으로 취소하는 Web API |
| **session_id** | 멀티턴 대화 식별자. 모드 변경 시 초기화 |

---
> **다음**: [03_user_chat_view.md](03_user_chat_view.md) — 사용자 화면 (UserChatView)
