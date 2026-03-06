# 3. SSE 스트리밍 클라이언트 - 실시간 진행 상태

> **파일 위치**: `frontend/src/api/sse.js` (165줄)

## 이 파일이 하는 일

AI가 질문에 답하는 데 2~5초가 걸립니다. 그 동안 **빈 화면**이 보이면 사용자는 불안합니다.
SSE 스트리밍은 서버가 **"지금 이 단계를 처리 중이에요"**라고 실시간으로 알려주는 기술입니다.

```
[SSE 없이 — 일반 HTTP]                  [SSE 사용 — 실시간]

사용자: "2024년 입사자 수?"              사용자: "2024년 입사자 수?"

(2초 동안 아무 반응 없음...)              (0.3초) ⏳ 의도 분석 중...
(3초 동안 아무 반응 없음...)              (0.5초) ✓ 의도 분석 완료
(4초 동안 아무 반응 없음...)              (1.0초) ⏳ SQL 생성 중...
                                         (1.5초) ✓ SQL 생성 완료
AI: "15명입니다"                         (2.0초) ✓ SQL 실행 완료
                                         AI: "15명입니다"

→ "멈춘 건가?" 불안함 😟               → "아~ 지금 처리하고 있구나" 안심 😊
```

---

## SSE란 무엇인가?

**SSE(Server-Sent Events)**는 서버가 클라이언트에게 **일방향으로 데이터를 보내는** 기술입니다.

```
[일반 HTTP]                    [SSE]
클라이언트 → 서버: 요청         클라이언트 → 서버: 연결 시작
서버 → 클라이언트: 응답 (1번)   서버 → 클라이언트: 데이터1
(연결 종료)                     서버 → 클라이언트: 데이터2
                               서버 → 클라이언트: 데이터3
                               서버 → 클라이언트: 완료! (연결 종료)
```

**왜 EventSource를 안 쓰는가?**

```
브라우저 내장 EventSource:
  ✅ 간편함
  ❌ GET 요청만 지원 (POST 불가)
  ❌ 요청 body를 보낼 수 없음

이 프로젝트:
  질문 데이터를 body로 보내야 함 → POST 필요!
  → fetch API + ReadableStream을 직접 사용
```

---

## 전체 구조 한눈에

```
streamSSE(url, body, callbacks)
│
├─ ① fetch()로 POST 요청
│     Method: POST
│     Headers: Authorization, Content-Type
│     Body: { query, mode, session_id }
│
├─ ② 응답 스트림 읽기 (ReadableStream)
│     reader = response.body.getReader()
│     while (true) { reader.read() }
│
├─ ③ SSE 이벤트 파싱
│     "event: node_start\ndata: {...}" → { type, data }
│
├─ ④ 콜백 호출
│     node_start    → callbacks.onNodeStart(data)
│     node_complete → callbacks.onNodeComplete(data)
│     complete      → callbacks.onComplete(data)
│     error         → callbacks.onError(data)
│
└─ ⑤ AbortController 반환 (중단 가능)
```

---

## 코드 상세 설명

### ① 함수 시그니처

```javascript
export function streamSSE(url, body, callbacks, { idleTimeoutMs = 60000 } = {}) {
  const controller = new AbortController()
  const fullUrl = `${BASE_URL}${url}`
  // ...
  return controller  // ← 호출자가 stream을 중단할 수 있도록
}
```

**매개변수 설명:**

| 매개변수 | 예시 | 설명 |
|----------|------|------|
| `url` | `'/api/v1/search/stream'` | SSE 엔드포인트 |
| `body` | `{ query: '입사자 수?', mode: 'nl2sql' }` | POST 요청 데이터 |
| `callbacks` | `{ onNodeStart, onComplete, ... }` | 이벤트별 처리 함수 |
| `idleTimeoutMs` | `60000` (60초) | 무응답 타임아웃 |

**AbortController란?**

```
AbortController = "리모컨"

streamSSE() → 연결 시작 → controller 반환
                              │
                    [사용자가 "중지" 클릭]
                              │
                    controller.abort()  → 서버 연결 끊기!
                              │
                    스트림 즉시 종료 ✅
```

### ② 헤더 설정 + 토큰 첨부

```javascript
const headers = { 'Content-Type': 'application/json' }
const token = localStorage.getItem('mureum_access_token')
if (token) {
  headers['Authorization'] = `Bearer ${token}`
}
```

**왜 apiClient를 안 쓰고 직접 fetch를 쓰는가?**

```
apiClient (Axios):
  → JSON 응답을 기대 → 인터셉터가 자동 파싱
  → SSE 스트림은 JSON이 아님! (줄 단위 텍스트)

fetch API:
  → 원시 응답 스트림(ReadableStream)에 직접 접근 가능
  → 바이트 단위로 데이터를 읽을 수 있음

→ SSE에는 fetch가 적합!
→ 대신 토큰 첨부를 직접 해야 함 (인터셉터 없으니까)
```

### ③ Idle 타임아웃

```javascript
let idleTimer = null

const resetIdleTimer = () => {
  if (idleTimer) clearTimeout(idleTimer)
  idleTimer = setTimeout(() => {
    if (!controller.signal.aborted) {
      controller.abort()
      callbacks.onError?.({ code: 'IDLE_TIMEOUT', message: '서버 응답이 지연되어 연결을 종료합니다' })
    }
  }, idleTimeoutMs)  // 기본 60초
}
```

```
Idle 타임아웃 = "무응답 감지기"

이벤트 수신 → 타이머 리셋 (60초 재시작)
이벤트 수신 → 타이머 리셋
이벤트 수신 → 타이머 리셋
(60초 동안 아무것도 안 옴)
→ "서버가 응답하지 않네?" → 자동 연결 종료!

→ 서버가 멈추거나 네트워크 끊어져도 무한 대기 방지
```

### ④ 스트림 읽기 — 핵심 루프

```javascript
fetch(fullUrl, {
  method: 'POST',
  headers,
  body: JSON.stringify(body),
  signal: controller.signal,    // abort() 시 요청 취소됨
})
.then(async (response) => {
  // HTTP 에러 체크
  if (!response.ok) {
    callbacks.onError?.(error)
    return
  }

  // ReadableStream으로 바이트 단위 읽기
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  resetIdleTimer()  // 타이머 시작

  while (true) {
    const { done, value } = await reader.read()
    if (done) break   // 서버가 연결 종료

    resetIdleTimer()  // 데이터 수신 → 타이머 리셋
    buffer += decoder.decode(value, { stream: true })

    // SSE 이벤트 분리 (이중 줄바꿈으로 구분)
    const events = buffer.split('\n\n')
    buffer = events.pop()  // 마지막 불완전한 이벤트는 버퍼에 유지

    for (const eventStr of events) {
      // ... 이벤트 파싱 및 콜백 호출
    }
  }
})
```

**ReadableStream의 동작 원리:**

```
서버가 보내는 데이터 (시간 순):

t=0.3s: "event: node_start\ndata: {\"message\":\"의도 분석 중...\"}\n\n"
t=0.5s: "event: node_complete\ndata: {\"stage\":\"intent\"}\n\n"
t=1.0s: "event: node_start\ndata: {\"message\":\"SQL 생성 중...\"}\n\n"

reader.read()가 반복적으로 호출:
  1차: { done: false, value: "event: node_start\ndata: {...}\n\n" }
  2차: { done: false, value: "event: node_complete\ndata: {...}\n\n" }
  ...
  마지막: { done: true, value: undefined }  → 루프 종료
```

**버퍼링이 필요한 이유:**

```
네트워크에서 데이터가 항상 깔끔하게 오지는 않습니다:

이상적인 경우:                   현실:
  "event: node_start\n            "event: node_st"     ← 잘림!
   data: {...}\n\n"               "art\ndata: {...}\n"  ← 나머지 옴
                                  "\nevent: node..."    ← 다음 이벤트 시작

buffer가 이것을 해결:
  buffer += 받은 데이터
  이중 줄바꿈(\n\n)으로 분리
  마지막 불완전한 부분은 buffer에 남겨둠
  → 다음 데이터가 오면 합쳐서 완전한 이벤트 완성!
```

### ⑤ SSE 이벤트 파싱

```javascript
function parseSSEEvent(eventStr) {
  const lines = eventStr.split('\n')
  let eventType = null
  let dataStr = null

  for (const line of lines) {
    if (line.startsWith('event: ')) {
      eventType = line.slice(7).trim()    // "event: node_start" → "node_start"
    } else if (line.startsWith('data: ')) {
      dataStr = line.slice(6)             // "data: {...}" → "{...}"
    }
  }

  if (!dataStr) return null

  try {
    const data = JSON.parse(dataStr)       // JSON 문자열 → 객체
    return { type: eventType || data.type, data }
  } catch {
    return null   // 파싱 실패 → 무시
  }
}
```

**SSE 이벤트의 텍스트 형식:**

```
서버가 보내는 원본 텍스트:
  "event: node_start\ndata: {\"message\":\"의도 분석 중...\",\"stage\":\"intent\"}\n\n"

파싱 결과:
  {
    type: "node_start",
    data: { message: "의도 분석 중...", stage: "intent" }
  }
```

### ⑥ 이벤트별 콜백 호출

```javascript
switch (parsed.type) {
  case 'node_start':
    callbacks.onNodeStart?.(parsed.data)
    // 브라우저 렌더링 양보
    await new Promise(resolve => requestAnimationFrame(resolve))
    break

  case 'node_complete':
    callbacks.onNodeComplete?.(parsed.data)
    await new Promise(resolve => requestAnimationFrame(resolve))
    break

  case 'complete':
    callbacks.onComplete?.(parsed.data)
    break

  case 'error':
    callbacks.onError?.(parsed.data)
    break
}
```

**4가지 이벤트 타입:**

```
시간 ──→

node_start     "의도 분석 중..."     ← 단계 시작 (⏳ 표시)
node_complete  "의도 분석 완료"      ← 단계 완료 (✓ 표시)
node_start     "SQL 생성 중..."
node_complete  "SQL 생성 완료"
node_start     "SQL 실행 중..."
node_complete  "SQL 실행 완료"
complete       { answer, sql, ... }  ← 최종 결과 (답변 표시!)
error          { code, message }     ← 에러 발생 (에러 표시)
```

**`requestAnimationFrame`이란?**

```
문제:
  이벤트가 빠르게 연속으로 오면 브라우저가 화면을 갱신할 틈이 없음
  → "의도 분석 중..." 표시가 보이지 않고 바로 "완료"로 넘어감

해결:
  requestAnimationFrame = "브라우저야, 화면 한 번 그리고 나서 계속할게"
  → 사용자가 각 단계를 눈으로 확인 가능!
```

**`?.` (옵셔널 체이닝)의 역할:**

```javascript
callbacks.onNodeStart?.(parsed.data)

// 이것은 아래와 같습니다:
if (callbacks.onNodeStart) {
  callbacks.onNodeStart(parsed.data)
}

// 콜백이 정의되지 않아도 에러가 나지 않음!
// → 필요한 콜백만 선택적으로 제공 가능
```

---

## Store에서 SSE를 사용하는 방법

Phase 3에서 배운 chat 모듈의 `sendMessageStream`이 이 SSE 클라이언트를 사용합니다:

```javascript
// store/modules/chat.js (간략화)
import { streamSSE } from '@/api/sse'

async sendMessageStream({ commit, state }, query) {
  // 빈 assistant 메시지 추가 (스트리밍 표시용)
  commit('ADD_MESSAGE', { role: 'assistant', content: '', isStreaming: true })

  const callbacks = {
    onNodeStart: (event) => {
      commit('UPDATE_LAST_MESSAGE', { currentStep: event.message })
    },
    onNodeComplete: (event) => {
      commit('ADD_STREAM_PROGRESS', event)
    },
    onComplete: (data) => {
      commit('UPDATE_LAST_MESSAGE', {
        content: data.answer,
        isStreaming: false,
        sql: data.sql,
        sqlResult: data.sql_result
      })
    },
    onError: (error) => {
      commit('UPDATE_LAST_MESSAGE', {
        content: `죄송합니다. ${error.message}`,
        isStreaming: false,
        isError: true
      })
    }
  }

  // SSE 연결 시작 → AbortController 반환
  const controller = streamSSE('/api/v1/search/stream', payload, callbacks)
  commit('SET_STREAM_CONTROLLER', controller)  // 중단용 저장
}
```

**연결 관계:**

```
사용자 입력 → chat Store (sendMessageStream)
                │
                ├─ streamSSE() 호출
                │   ├─ fetch() → 서버 SSE 연결
                │   ├─ reader.read() 루프
                │   └─ 이벤트 파싱 → 콜백 호출
                │
                ├─ onNodeStart → commit('UPDATE_LAST_MESSAGE')
                ├─ onNodeComplete → commit('ADD_STREAM_PROGRESS')
                ├─ onComplete → commit('UPDATE_LAST_MESSAGE', 최종 답변)
                └─ onError → commit('UPDATE_LAST_MESSAGE', 에러)
                      │
                      ▼
                  Vue 반응성 → 화면 자동 갱신!
```

---

## 에러 처리

```javascript
.catch((err) => {
  clearIdleTimer()

  // 사용자가 의도적으로 중단한 경우
  if (err.name === 'AbortError') {
    console.log('[SSE] Stream aborted')  // 에러 아님, 정상 중단
    return
  }

  // 네트워크 오류
  callbacks.onError?.({
    code: 'NETWORK_ERROR',
    message: '네트워크 연결을 확인해주세요',
    detail: err.message,
  })
})
```

**에러 종류 정리:**

```
① HTTP 에러 (response.ok === false)
   → 서버가 에러 응답 (400, 500 등)
   → onError 콜백 호출

② Idle 타임아웃 (60초 무응답)
   → 서버가 멈췄거나 네트워크 끊김
   → abort() + onError 호출

③ AbortError (사용자 중단)
   → 사용자가 "중지" 버튼 클릭
   → 정상 처리 (에러 아님)

④ 네트워크 오류 (fetch 실패)
   → 인터넷 연결 끊김
   → onError 콜백 호출
```

---

## 리뷰 체크리스트

- [x] POST 요청으로 SSE를 사용하는가? → fetch + ReadableStream ✅
- [x] 토큰이 헤더에 포함되는가? → localStorage에서 직접 읽어 첨부 ✅
- [x] 버퍼링으로 불완전한 이벤트를 처리하는가? → split('\n\n') + buffer ✅
- [x] 4가지 이벤트 타입을 처리하는가? → node_start/complete/complete/error ✅
- [x] 무응답 타임아웃이 있는가? → idleTimeoutMs (기본 60초) ✅
- [x] 스트림 중단이 가능한가? → AbortController.abort() ✅
- [x] 화면 갱신 타이밍이 보장되는가? → requestAnimationFrame ✅
- [x] 사용자 중단 시 에러로 처리하지 않는가? → AbortError 체크 ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **SSE** | Server-Sent Events. 서버가 클라이언트에게 실시간 데이터 전송 |
| **fetch + ReadableStream** | POST 지원을 위해 EventSource 대신 사용 |
| **parseSSEEvent** | `"event: type\ndata: {...}"` → `{ type, data }` 변환 |
| **AbortController** | 스트리밍 연결을 중단하는 리모컨 |
| **idleTimeout** | 무응답 자동 감지. 서버 멈춤 시 자동 종료 |
| **requestAnimationFrame** | 브라우저에게 화면 갱신 기회 제공 |
| **buffer** | 네트워크에서 잘린 데이터를 모아서 완전한 이벤트로 조립 |

---
> **이전**: [02_api_modules.md](02_api_modules.md) - API 모듈 패턴
> **다음**: [04_how_it_works.md](04_how_it_works.md) - 동작 원리 종합
