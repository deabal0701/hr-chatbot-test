# 4. chat 모듈 - 채팅과 SSE 스트리밍

> **파일 위치**: `frontend/src/store/modules/chat.js` (433줄)

## 이 모듈이 하는 일

이 앱의 **핵심 기능**인 AI 채팅을 관리합니다. 메시지 목록, 검색 모드, SSE 스트리밍, 채팅 이력까지 모든 채팅 관련 상태를 담당합니다.

```
chat 모듈이 관리하는 것:
├── 메시지 목록 (사용자 질문 + AI 답변)
├── 검색 모드 (nl2sql / rag / agent)
├── SSE 스트리밍 (실시간 진행 상태)
├── 세션 관리 (멀티턴 대화)
└── 채팅 이력 (과거 대화 불러오기)
```

## State - 저장하는 데이터

```javascript
state: () => ({
  // ─── 메시지 ───
  messages: [],           // 채팅 메시지 배열 [{role, content, ...}, ...]
  isLoading: false,       // API 호출 중
  error: null,            // 에러 정보

  // ─── 검색 모드 ───
  searchMode: 'nl2sql',   // 'auto' | 'rag' | 'nl2sql' | 'agent'

  // ─── 세션 ───
  sessionId: null,        // 서버 생성 세션 ID (멀티턴 대화용)

  // ─── 채팅 이력 ───
  chatHistory: [],        // 과거 대화 목록
  historyLoading: false,
  activeChatId: null,     // 현재 선택된 대화의 session_key

  // ─── SSE 스트리밍 ───
  isStreaming: false,     // 스트리밍 진행 중
  streamProgress: [],     // 스트리밍 단계별 진행 이벤트
  streamController: null  // 스트리밍 중단용 컨트롤러
})
```

**messages 배열의 구조:**
```javascript
messages = [
  {
    id: "1709123456789",
    role: "user",           // 사용자 메시지
    content: "2024년 입사자 수는?",
    timestamp: Date
  },
  {
    id: "1709123456790",
    role: "assistant",      // AI 응답
    content: "2024년 입사자는 총 15명입니다.",
    queryType: "nl2sql",    // 어떤 방식으로 답했는지
    sql: "SELECT COUNT(*) FROM employee WHERE ...",
    sqlResult: { columns: [...], rows: [...] },
    isStreaming: false,      // 스트리밍 완료 여부
    streamProgress: [...]    // 진행 단계
  }
]
```

---

## 4가지 검색 모드

```
searchMode의 종류:

  'nl2sql'  → 자연어 → SQL 변환 → DB 조회 → 답변
              "2024년 입사자 수는?" → SELECT COUNT(*)...

  'rag'     → 문서 검색 → 유사 문서 찾기 → 답변
              "재택근무 정책이 뭐야?" → 관련 문서에서 답변

  'agent'   → AI가 도구를 스스로 선택 → 복합 질문 처리
              "입사자 수와 재택근무 정책 둘 다 알려줘"

  'auto'    → 질문을 분석해서 자동으로 모드 선택
```

---

## 핵심 Action: sendMessage

```javascript
async sendMessage({ commit, state, dispatch }, query) {
  // Agent/NL2SQL → SSE 스트리밍
  if (state.searchMode === 'agent' || state.searchMode === 'nl2sql') {
    return dispatch('sendMessageStream', query)
  }

  // RAG → 일반 HTTP 요청
  commit('SET_LOADING', true)
  commit('ADD_MESSAGE', { role: 'user', content: query })

  try {
    const response = await searchApi.search({ query, mode: state.searchMode })
    commit('ADD_MESSAGE', {
      role: 'assistant',
      content: response.answer,
      sources: response.sources  // RAG 출처 문서
    })
  } catch (error) {
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

**모드에 따른 분기:**
```
sendMessage("2024년 입사자 수는?")
    │
    ├─ searchMode === 'agent' 또는 'nl2sql'
    │   └─ sendMessageStream() → SSE 스트리밍 방식 (실시간)
    │
    └─ searchMode === 'rag' 또는 'auto'
        └─ searchApi.search() → 일반 HTTP 방식 (한번에 응답)
```

---

## SSE 스트리밍 (sendMessageStream) ⭐⭐

**SSE(Server-Sent Events)**란 서버가 클라이언트에게 **실시간으로 데이터를 보내는** 기술입니다.

```
[일반 HTTP]
클라이언트 → 서버: "질문!"
(3초 대기...)
서버 → 클라이언트: "최종 답변" (한 번에)

[SSE 스트리밍]
클라이언트 → 서버: "질문!"
서버 → 클라이언트: "의도 분석 중..."     (0.5초)
서버 → 클라이언트: "SQL 생성 중..."     (1초)
서버 → 클라이언트: "SQL 실행 중..."     (0.5초)
서버 → 클라이언트: "답변 생성 중..."     (1초)
서버 → 클라이언트: "최종 답변!"         (완료)

→ 사용자가 진행 상황을 실시간으로 볼 수 있음!
```

**sendMessageStream의 콜백 구조:**

```javascript
const callbacks = {
  // ① 노드 시작 - "의도 분석 중..."
  onNodeStart: (event) => {
    commit('UPDATE_LAST_MESSAGE', { currentStep: event.message })
  },

  // ② 노드 완료 - "의도 분석 완료 ✓"
  onNodeComplete: (event) => {
    commit('ADD_STREAM_PROGRESS', event)
    // assistant 메시지의 streamProgress에 추가
  },

  // ③ 전체 완료 - 최종 답변 수신
  onComplete: (event) => {
    commit('UPDATE_LAST_MESSAGE', {
      content: data.answer,       // 최종 답변
      isStreaming: false,          // 스트리밍 종료
      sql: data.sql,              // 생성된 SQL (NL2SQL)
      sqlResult: data.sql_result  // SQL 실행 결과
    })
    commit('SET_STREAMING', false)
  },

  // ④ 에러 발생
  onError: (error) => {
    commit('UPDATE_LAST_MESSAGE', {
      content: `죄송합니다. ${error.message}`,
      isStreaming: false,
      isError: true
    })
  }
}
```

**스트리밍 시 화면 변화:**
```
시간 ──→

[0초]  사용자: "2024년 입사자 수는?"
       AI: ⏳ (빈 메시지, isStreaming: true)

[0.5초] AI: "의도 분석 중..."           ← onNodeStart
        AI: "✓ 의도 분석 완료"          ← onNodeComplete

[1초]   AI: "SQL 생성 중..."            ← onNodeStart
        AI: "✓ SQL 생성 완료"           ← onNodeComplete

[1.5초] AI: "SQL 실행 중..."
        AI: "✓ SQL 실행 완료"

[2초]   AI: "답변 생성 중..."
        AI: "2024년 입사자는 총 15명입니다." ← onComplete (최종!)
        AI: isStreaming: false
```

**빈 assistant 메시지를 먼저 추가하는 이유:**
```javascript
// 빈 assistant 메시지를 먼저 추가 (스트리밍 진행 표시용)
commit('ADD_MESSAGE', {
  role: 'assistant',
  content: '',            // 아직 내용 없음
  isStreaming: true,      // "진행 중" 표시
  streamProgress: [],
  currentStep: null
})

// 이후 UPDATE_LAST_MESSAGE로 이 메시지를 계속 업데이트
// → 메시지가 "자라나는" 효과!
```

---

## 채팅 이력 관리

```javascript
// 과거 대화 목록 조회
async fetchChatHistory({ commit }) {
  const response = await historyApi.listSessions({ limit: 50 })
  commit('SET_CHAT_HISTORY', response.items || [])
}

// 과거 대화 불러오기 (클릭 시)
async loadChatSession({ commit }, sessionKey) {
  const response = await historyApi.getSessionHistory(sessionKey)
  // 이력 레코드를 메시지 배열로 변환
  for (const record of records) {
    commit('ADD_MESSAGE', { role: 'user', content: record.question })
    commit('ADD_MESSAGE', { role: 'assistant', content: record.answer, ... })
  }
}
```

**사이드바에서 대화 선택 시 흐름:**
```
사이드바에서 "3월 4일 대화" 클릭
    │
    ▼
dispatch('chat/loadChatSession', sessionKey)
    │
    ├─ CLEAR_MESSAGES (현재 메시지 비움)
    ├─ API 호출 → 이력 데이터 수신
    ├─ 각 레코드를 ADD_MESSAGE로 추가
    │   ├─ user 메시지
    │   └─ assistant 메시지 (queryType별 데이터 매핑)
    └─ SET_SESSION_ID (멀티턴 재개 가능하도록)
```

---

## 스트리밍 중단 (cancelStream)

```javascript
cancelStream({ state, commit }) {
  if (state.streamController) {
    state.streamController.abort()     // 서버 연결 끊기
    commit('SET_STREAMING', false)
    commit('SET_LOADING', false)
    commit('SET_STREAM_CONTROLLER', null)
  }
}
```

사용자가 "중지" 버튼을 누르면 SSE 연결을 끊습니다. `AbortController`의 `abort()` 메서드를 호출합니다.

---

## 3개 모듈 패턴 비교

| 항목 | auth | app | chat |
|------|------|-----|------|
| **API 호출** | 인증 API | 없음 | 검색/이력 API |
| **localStorage** | 토큰, 사용자 | 테마, 사이드바 | 없음 |
| **복잡도** | 중 | 낮 | **높** |
| **비동기** | login, fetchMe | 없음 | sendMessage, 스트리밍 |
| **실시간** | 없음 | 없음 | **SSE 스트리밍** |
| **다른 모듈 연동** | → chat, dashboard | 없음 | 없음 |

## 리뷰 체크리스트

- [x] 메시지가 순서대로 추가되는가? → user → assistant 순서 ✅
- [x] 에러 발생 시 사용자에게 표시되는가? → isError 메시지 추가 ✅
- [x] 스트리밍 중 상태가 관리되는가? → isStreaming, streamProgress ✅
- [x] 스트리밍 중단이 가능한가? → cancelStream, AbortController ✅
- [x] 모드 변경 시 세션이 초기화되는가? → setMode에서 sessionId null ✅
- [x] 이력 로드 시 기존 메시지가 정리되는가? → CLEAR_MESSAGES ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **messages[]** | 사용자 + AI 메시지 배열. 화면에 순서대로 표시 |
| **searchMode** | nl2sql/rag/agent 중 선택. 모드에 따라 다른 API 호출 |
| **SSE 스트리밍** | 서버가 실시간으로 진행 상태를 보내는 기술 |
| **streamProgress** | 스트리밍 단계별 이벤트 배열 (의도분석 → SQL생성 → 실행 → 답변) |
| **sessionId** | 멀티턴 대화용. 같은 세션에서 문맥 유지 |
| **UPDATE_LAST_MESSAGE** | 마지막 assistant 메시지를 점진적으로 업데이트 |

---
> **이전**: [03_app_module.md](03_app_module.md) - 앱 설정 모듈
> **다음**: [05_how_it_works.md](05_how_it_works.md) - 동작 원리 종합
