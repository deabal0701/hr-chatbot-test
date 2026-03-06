# 4. 시나리오별 전체 흐름

> **학습 목표**: 실제 사용 시나리오를 따라가며 **코드가 어떤 순서로 실행되는지** 이해한다.

---

## 시나리오 1: RAG 질문 (문서 검색)

> 관리자가 RAG 모드에서 "재택근무 정책이 뭐야?"를 질문하는 경우

```
ChatView                    chat Store                  서버
────────                    ──────────                  ──────

[RAG 모드 선택됨]
사용자가 입력:
"재택근무 정책이 뭐야?"

Enter 키 누름
    │
    ▼
ChatInput:
  handleSend()
  emit('send', text) ──→

ChatView:
  handleSend(query) ──→  dispatch('chat/sendMessage', query)
                              │
                              │ searchMode === 'rag'
                              │ → 일반 HTTP 모드
                              │
                              ├─ SET_LOADING(true)
                              ├─ ADD_MESSAGE({role:'user', content:query})
                              │
                              ├─ searchApi.search({        ──→  POST /api/v1/search
                              │    query, mode:'rag'       ←── {answer, sources,
                              │  })                              query_type:'rag'}
                              │
                              ├─ SET_SESSION_ID(session_id)
                              ├─ ADD_MESSAGE({
                              │    role:'assistant',
                              │    content: response.answer,
                              │    queryType: 'rag',
                              │    sources: [{title, content, vector_score, ...}]
                              │  })
                              │
                              └─ SET_LOADING(false)

ChatView:
  watch(messages) 감지
    │
    ▼
  await nextTick()
  scrollTop = scrollHeight       ← 스크롤 이동

ChatMessage 렌더링:
  ┌─────────────────────────────────────┐
  │  v-html="formattedContent"           │ ← 마크다운 → HTML
  │  재택근무 정책은 다음과 같습니다...    │
  │  ──────────────────────              │
  │  [RAG]  320ms                        │ ← 메타 정보
  │  ──────────────────────              │
  │  📄 참고 문서 (3개)                   │ ← sources.length > 0
  │  ┌──────────────────────────────┐    │
  │  │[정책] 재택근무 가이드  V 85%  │    │ ← SourceCard
  │  │재택근무는 입사 1년 이상...    │    │
  │  └──────────────────────────────┘    │
  │  ┌──────────────────────────────┐    │
  │  │[FAQ] 재택근무 Q&A    V 72%   │    │ ← SourceCard
  │  │Q: 재택근무 신청은...         │    │
  │  └──────────────────────────────┘    │
  └─────────────────────────────────────┘
```

---

## 시나리오 2: NL2SQL 질문 (SSE 스트리밍)

> 사용자 화면에서 NL2SQL 모드로 "부서별 직원수는?"을 질문하는 경우

```
UserChatView                chat Store                  서버 (SSE)
────────────                ──────────                  ──────────

[NL2SQL 모드 선택됨]
사용자 입력:
"부서별 직원수는?"

Enter 키 누름
    │
    ▼
handleSend()
  inputText = ''
  height = 'auto'
  dispatch('chat/sendMessage', query)
                              │
                              │ searchMode === 'nl2sql'
                              │ → sendMessageStream(query) 호출
                              │
                              ├─ SET_LOADING(true)
                              ├─ SET_STREAMING(true)
                              ├─ CLEAR_STREAM_PROGRESS
                              │
                              ├─ ADD_MESSAGE({role:'user'})
                              ├─ ADD_MESSAGE({               ← 빈 AI 메시지 선 추가
                              │    role:'assistant',
                              │    content:'',
                              │    isStreaming: true
                              │  })
                              │
                              ├─ searchApi.searchStream(     ──→  GET /api/v1/search/stream
                              │    {query, mode:'nl2sql'},         (SSE 연결)
                              │    callbacks
                              │  )
                              │
  ┌─────────────┐             │
  │● ● ● 처리중  │             │
  └─────────────┘             │
                              │     ←─── event: node_start
                              │           {message: "의도 분석 중..."}
                              ├─ onNodeStart:
                              │    UPDATE_LAST_MESSAGE({
                              │      currentStep: "의도 분석 중..."
                              │    })
  ┌──────────────────┐        │
  │● ● ● 의도분석 중  │        │
  └──────────────────┘        │
                              │     ←─── event: node_complete
                              │           {message: "의도 분석"}
                              ├─ onNodeComplete:
                              │    streamProgress 추가
                              │    UPDATE_LAST_MESSAGE({
                              │      streamProgress: [✓ 의도 분석],
                              │      currentStep: null
                              │    })
  ┌──────────────────┐        │
  │✓ 의도 분석        │        │
  │● ● ● 처리 중     │        │     ←─── event: node_start / node_complete
  └──────────────────┘        │           (반복: SQL생성, 검증, 실행, PII필터, 답변생성)
                              │
  ┌──────────────────┐        │
  │✓ 의도 분석        │        │
  │✓ SQL 생성         │        │
  │✓ 쿼리 검증        │        │
  │✓ 쿼리 실행        │        │
  │✓ PII 필터         │        │
  │● ● ● 답변 생성 중 │        │
  └──────────────────┘        │
                              │     ←─── event: complete
                              │           {answer, sql, sql_result, ...}
                              ├─ onComplete:
                              │    UPDATE_LAST_MESSAGE({
                              │      content: data.answer,
                              │      isStreaming: false,    ← 스트리밍 종료!
                              │      sql: data.sql,
                              │      sqlResult: data.sql_result
                              │    })
                              │    SET_STREAMING(false)
                              │    SET_LOADING(false)
                              │    fetchChatHistory()

UserChatMessage 렌더링:
  ┌──────────────────────────────────────┐
  │🤖│ 부서별 직원 수는 다음과 같습니다.  │
  │  │                                    │
  │  │ | 부서 | 인원 |                    │ ← answer (마크다운)
  │  │ | 개발 | 25  |                     │
  │  │ | 영업 | 18  |                     │
  │  │                                    │
  │  │ ┌──────────────────────────┐       │
  │  │ │📊 조회 결과 (43건)     ▼ │       │ ← result-toggle
  │  │ └──────────────────────────┘       │
  │  │                                    │
  │  │ [NL2SQL] · 1/5   14:30       [📋] │ ← 메타 + 복사
  └──────────────────────────────────────┘
```

---

## 시나리오 3: 모드 변경

> RAG에서 NL2SQL로 모드를 변경하는 경우

```
관리자 화면:                              사용자 화면:
───────────                              ──────────

사이드바에서 NL2SQL 선택                   드롭다운에서 NL2SQL 선택
    │                                         │
    ▼                                         ▼
el-radio-group                            el-dropdown
@change="handleModeChange"                @command="handleModeChange"
    │                                         │
    ▼                                         ▼
handleModeChange('nl2sql')                handleModeChange('nl2sql')
    │                                         │
    └─────────────┬───────────────────────────┘
                  │
                  ▼
    store.dispatch('chat/setMode', 'nl2sql')
                  │
                  ▼
    setMode 액션:
    ├─ previousMode = 'rag'
    ├─ SET_MODE('nl2sql')
    │
    ├─ previousMode !== 'nl2sql'?  → YES
    │   └─ SET_SESSION_ID(null)    ← 세션 초기화!
    │
    └─ 완료

    화면 변화:
    ├─ 환영 메시지: "데이터베이스 기반 질문을 자유롭게 해주세요."
    ├─ 예시 질문: nl2sqlExampleQueries로 변경
    └─ 플레이스홀더: "[NL2SQL] 질문을 입력하세요..."
```

---

## 시나리오 4: 대화 이력 불러오기

> 사용자가 과거 대화를 클릭하여 불러오는 경우

```
사이드바                     chat Store                  서버
────────                    ──────────                  ──────

대화 목록 표시 중:
┌─────────────────┐
│ 부서별 직원수?   │ ← chatHistory[0]
│ 재택근무 정책?   │ ← chatHistory[1]
│ 입사자 현황?     │ ← chatHistory[2]
└─────────────────┘

"부서별 직원수?" 클릭
    │
    ▼
dispatch('chat/selectChat', sessionKey)
                              │
                              ▼
    loadChatSession(sessionKey)
    ├─ SET_LOADING(true)
    ├─ SET_ACTIVE_CHAT(sessionKey)
    ├─ CLEAR_MESSAGES                    ← 현재 대화 비우기
    │
    ├─ historyApi.getSessionHistory()   ──→  GET /api/v1/history/sessions/{key}
    │                                   ←── {items: [record1, record2, ...]}
    │
    │  records 순회:
    │  ┌─────────────────────────────┐
    │  │ record1:                    │
    │  │   question: "부서별 직원수?" │
    │  │   answer: "부서별 직원..."   │
    │  │   request_type: "nl2sql"    │
    │  │   trace_data: {             │
    │  │     sql: "SELECT ...",      │
    │  │     sql_result: {...}       │
    │  │   }                         │
    │  └─────────────────────────────┘
    │
    │  → ADD_MESSAGE({role:'user', content:'부서별 직원수?'})
    │  → ADD_MESSAGE({
    │       role:'assistant',
    │       content:'부서별 직원...',
    │       queryType:'nl2sql',
    │       sql:'SELECT ...',
    │       sqlResult: {...},
    │       isHistory: true           ← 이력에서 불러온 표시
    │     })
    │
    │  record2, record3도 동일하게 변환...
    │
    ├─ SET_SESSION_ID(records[0].session_id)   ← 멀티턴 재개용
    ├─ SET_MODE(records[last].request_type)     ← 마지막 모드로 설정
    └─ SET_LOADING(false)

화면:
  ┌─────────────────────────────────────┐
  │ 사용자: 부서별 직원수?               │ ← record1의 question
  │                                     │
  │ AI: 부서별 직원 수는...              │ ← record1의 answer
  │     [NL2SQL] · 1/5                  │
  │     📊 조회 결과 (43건) ▼           │ ← trace_data.sql_result
  │                                     │
  │ 사용자: 그중 개발부서만 알려줘        │ ← record2 (멀티턴 후속)
  │                                     │
  │ AI: 개발부서 직원은...               │
  │     [NL2SQL] · 2/5                  │
  └─────────────────────────────────────┘

이 상태에서 새 질문을 하면?
→ sessionId가 복원되어 있으므로 멀티턴 대화 **계속** 가능!
→ "그중 여성 직원만 알려줘" → 턴 3/5로 이어짐
```

---

## 시나리오 5: NL2SQL 결과 → Excel + 차트 + 대시보드

> 사용자 화면에서 NL2SQL 조회 결과를 활용하는 경우

```
NL2SQL 응답 수신 완료:
┌────────────────────────────────────────┐
│🤖│ 부서별 직원 수는 다음과 같습니다.    │
│  │                                      │
│  │ ┌──────────────────────────────┐     │
│  │ │📊 조회 결과 (43건)         ▼ │     │ ← 클릭하여 펼침
│  │ └──────────────────────────────┘     │
└────────────────────────────────────────┘
    │
    ▼ 토글 클릭 (showResult = true)

┌────────────────────────────────────────┐
│  │ 📊 조회 결과 (43건)            ▲    │
│  │ ┌──────┬──────┬──────┐              │
│  │ │ 부서  │ 인원  │ 비율  │              │ ← el-table (최대 100행)
│  │ ├──────┼──────┼──────┤              │
│  │ │ 개발  │  25  │ 35%  │              │
│  │ │ 영업  │  18  │ 25%  │              │
│  │ └──────┴──────┴──────┘              │
│  │                                      │
│  │ ┌──── ChartBuilder ────┐            │
│  │ │  📊 (자동 생성 차트)   │            │ ← columns + rows 기반
│  │ └──────────────────────┘            │
│  │                                      │
│  │ [📊 대시보드에 추가]  [📥 Excel]     │
│  └──────────────────────────────────────┘
└────────────────────────────────────────┘

[Excel 다운로드] 클릭:
    │
    ▼
exportToExcel()
  ├─ chartBuilderRef.value?.chartGenerated → true
  ├─ searchApi.exportExcel({
  │    columns, rows,
  │    question, sql, answer,
  │    include_chart: true,
  │    chart_config: {chart_type, x_column, y_columns}
  │  })
  │  → 서버가 .xlsx 생성 → Blob 다운로드
  └─ ElMessage.success('다운로드 완료')

[대시보드에 추가] 클릭:
    │
    ▼
showDashboardModal = true
  → SaveToDashboardModal 열림
  → 차트 설정 + 이름 입력
  → 개인 대시보드에 저장
```

---

## 시나리오 6: 에러 처리

> NL2SQL 스트리밍 중 에러가 발생한 경우

```
UserChatView                chat Store                  서버 (SSE)
────────────                ──────────                  ──────────

사용자 질문 전송...
(스트리밍 시작)
  ┌──────────────────┐
  │✓ 의도 분석        │
  │✓ SQL 생성         │
  │● ● ● 쿼리 실행 중 │
  └──────────────────┘
                              │
                              │     ←─── event: error
                              │           {code: "SQL_EXECUTION_ERROR",
                              │            message: "테이블이 존재하지 않습니다"}
                              │
                              ├─ onError:
                              │    SET_ERROR({code, message})
                              │    UPDATE_LAST_MESSAGE({
                              │      content: "죄송합니다. 테이블이 존재하지 않습니다",
                              │      isStreaming: false,
                              │      isError: true
                              │    })
                              │    SET_STREAMING(false)
                              │    SET_LOADING(false)
                              │    SET_STREAM_CONTROLLER(null)

화면:
  ┌──────────────────────────────────────┐
  │🤖│ 죄송합니다. 테이블이 존재하지      │
  │  │ 않습니다                           │ ← isError: true → 에러 스타일
  │  │                                    │
  │  │ [NL2SQL]   14:30              [📋] │
  └──────────────────────────────────────┘
    입력란 다시 활성화 (isLoading = false)
    → 사용자가 다시 질문 가능
```

---

## 시나리오 7: 관리자 → 사용자 화면 새 창

> 관리자가 "사용자 화면" 버튼을 클릭하는 경우

```
ChatView의 사이드바:
┌────────────────────┐
│ 사용자 화면         │
│ [📺 새 창으로 열기] │ ← 클릭
└────────────────────┘
    │
    ▼
openUserChat()
  const width = window.screen.availWidth      // 화면 전체 너비
  const height = window.screen.availHeight    // 화면 전체 높이
  window.open('/chat', '_blank',
    `width=${width},height=${height},left=0,top=0`)
    │
    ▼
새 브라우저 창 열림:
┌──────────────────────────────────────┐
│  ☾  MUREUM                  사용자명  │
├──────────────────────────────────────┤
│                                      │
│         무엇을 도와드릴까요?          │
│                                      │
│  [재택근무 정책...]  [연차 휴가...]   │
│                                      │
├──────────────────────────────────────┤
│  [RAG▾] [입력...]               [➤] │
└──────────────────────────────────────┘

* 새 창은 독립 Vuex 인스턴스
  → 관리자 창의 대화와 공유되지 않음
  → 각자 별도의 messages[], sessionId 관리
```

---

## 데이터 흐름 요약

```
┌──────────────────────────────────────────────────────────────────┐
│                         사용자 질문                               │
│                             │                                    │
│                    ┌────────┴────────┐                           │
│                    │  chat Store     │                           │
│                    │  sendMessage()  │                           │
│                    └───┬─────────┬───┘                           │
│                        │         │                               │
│              RAG 모드   │         │  NL2SQL / Agent 모드          │
│                        │         │                               │
│                ┌───────┴──┐  ┌───┴──────────┐                   │
│                │ HTTP 요청  │  │ SSE 스트리밍  │                   │
│                │ (한번에)   │  │ (실시간)      │                   │
│                └───────┬──┘  └───┬──────────┘                   │
│                        │         │                               │
│                        │    ┌────┴─────┐                         │
│                        │    │콜백 4종   │                         │
│                        │    │onNodeStart│ → currentStep 갱신     │
│                        │    │onNodeComp │ → streamProgress 추가  │
│                        │    │onComplete │ → 최종 데이터 설정      │
│                        │    │onError    │ → 에러 메시지           │
│                        │    └────┬─────┘                         │
│                        │         │                               │
│                ┌───────┴─────────┴──────┐                       │
│                │    ADD_MESSAGE 또는      │                       │
│                │    UPDATE_LAST_MESSAGE   │                       │
│                └───────────┬─────────────┘                       │
│                            │                                     │
│                     ┌──────┴──────┐                              │
│                     │ messages[]  │                               │
│                     └──────┬──────┘                              │
│                            │ v-for                               │
│                   ┌────────┴────────┐                            │
│                   │                 │                             │
│            ChatMessage      UserChatMessage                      │
│            (관리자용)         (사용자용)                            │
│                   │                 │                             │
│           SourceCard          ChartBuilder                       │
│           ChartBuilder        SaveToDashboard                    │
└──────────────────────────────────────────────────────────────────┘
```

---

## 리뷰 체크리스트

- [x] RAG 질문이 일반 HTTP로 처리되는가? ✅
- [x] NL2SQL 질문이 SSE 스트리밍으로 처리되는가? ✅
- [x] 스트리밍 진행 UI가 시간순으로 표시되는가? (체크마크 누적) ✅
- [x] 스트리밍 완료 시 최종 답변으로 정확히 교체되는가? ✅
- [x] 모드 변경 시 세션이 초기화되는가? ✅
- [x] 이력 불러오기가 멀티턴 재개를 지원하는가? (sessionId 복원) ✅
- [x] Excel/차트/대시보드 연동이 동작하는가? ✅
- [x] 에러 시 UI가 정상 복구되는가? (isLoading/isStreaming false) ✅
- [x] 새 창 열기가 전체화면으로 열리는가? ✅

---
> **이전**: [03_user_chat_view.md](03_user_chat_view.md) — 사용자 화면
>
> **Phase 7 완료!** 다음은 Phase 8 (Style & Utilities)입니다.
