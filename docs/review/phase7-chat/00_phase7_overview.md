# Phase 7 — Chat & AI (채팅과 AI 응답)

> **학습 목표**: 사용자가 질문을 입력하고 AI 답변을 받는 **전체 흐름**을 이해한다.

---

## 이 Phase에서 다루는 것

MUREUM의 핵심 기능인 **채팅 인터페이스**입니다.
두 가지 화면이 있고, 여러 컴포넌트가 협력합니다.

```
┌─────────────────────────────────────────────────────────────┐
│                    Phase 7 전체 구성                          │
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐   │
│  │  ChatView   │    │ UserChatView │    │  chat.js     │   │
│  │  (관리자)    │    │  (사용자)     │    │  (Store)     │   │
│  └──────┬──────┘    └──────┬───────┘    └──────┬───────┘   │
│         │                  │                    │            │
│   ┌─────┴─────┐     ┌─────┴──────┐       ┌────┴────┐      │
│   │ ChatInput │     │UserChat    │       │ SSE     │      │
│   │ ChatMessage│     │ Message    │       │ Stream  │      │
│   │ SourceCard │     │ ChartBuilder│      │ 콜백    │      │
│   └───────────┘     └────────────┘       └─────────┘      │
└─────────────────────────────────────────────────────────────┘
```

---

## 두 가지 채팅 화면 비교

| 구분 | ChatView (관리자) | UserChatView (사용자) |
|------|-------------------|----------------------|
| **파일** | `views/admin/ChatView.vue` | `views/user/UserChatView.vue` |
| **경로** | `/admin/chat` | `/chat` |
| **레이아웃** | AdminLayout 내부 | 독립 전체화면 |
| **모드 선택** | 오버레이 사이드바 (radio) | 하단 드롭다운 버튼 |
| **입력** | ChatInput 컴포넌트 사용 | 자체 textarea (auto-resize) |
| **메시지** | ChatMessage 컴포넌트 | UserChatMessage 컴포넌트 |
| **디자인** | 관리 도구 스타일 | ChatGPT 스타일 |
| **다크모드** | 시스템 설정 따름 | 자체 토글 버튼 |
| **반응형** | 미지원 | 768px / 375px 대응 |

```
관리자 화면 (ChatView)                사용자 화면 (UserChatView)
┌──────────────────────┐            ┌──────────────────────────┐
│  AdminLayout 헤더     │            │ ☾  MUREUM      사용자명  │
├──────────────────────┤            ├──────────────────────────┤
│                   « │◀ 사이드바  │                          │
│  환영 메시지          │  트리거    │     무엇을 도와드릴까요?   │
│  예시 질문 버튼       │            │                          │
│                      │            │  [재택근무 정책...]       │
│  (메시지 목록)        │            │  [연차 휴가 신청...]      │
│                      │            │                          │
│                      │            │  (메시지 목록)            │
│                      │            │                          │
├──────────────────────┤            ├──────────────────────────┤
│  [ChatInput 컴포넌트] │            │ [RAG▾] [입력...]   [➤]  │
└──────────────────────┘            │ 본 AI 어시스턴트...       │
                                    └──────────────────────────┘
```

---

## 검색 모드 — 3가지 AI 엔진

| 모드 | 설명 | API | 통신 방식 |
|------|------|-----|-----------|
| **RAG** | 문서 기반 검색 (정책, 가이드) | `searchApi.search()` | 일반 HTTP |
| **NL2SQL** | 데이터베이스 조회 (통계, 수치) | `searchApi.searchStream()` | SSE 스트리밍 |
| **Agent** | AI가 도구를 선택하여 복합 처리 | `agentApi.agentSearchStream()` | SSE 스트리밍 |

```
사용자 질문 입력
    │
    ▼
chat Store: sendMessage(query)
    │
    ├─ searchMode === 'rag'
    │   └─ 일반 HTTP 요청 → searchApi.search()
    │       → 응답 한번에 수신 → ADD_MESSAGE
    │
    └─ searchMode === 'nl2sql' 또는 'agent'
        └─ sendMessageStream(query) → SSE 스트리밍
            → 빈 메시지 추가 (isStreaming: true)
            → onNodeStart → 현재 단계 표시
            → onNodeComplete → 체크마크 추가
            → onComplete → 최종 답변으로 교체
```

---

## 컴포넌트 계층 구조

```
ChatView.vue (관리자)
├── ChatMessage.vue          ← 메시지 표시
│   ├── SourceCard.vue       ← RAG 출처 카드
│   └── ChartBuilder.vue     ← NL2SQL 차트
├── ChatInput.vue            ← 입력 컴포넌트
└── PromptGuideModal.vue     ← 프롬프트 가이드

UserChatView.vue (사용자)
├── UserChatMessage.vue      ← 메시지 표시 (ChatGPT 스타일)
│   ├── ChartBuilder.vue     ← NL2SQL 차트
│   └── SaveToDashboardModal.vue ← 대시보드 저장
└── PromptGuideModal.vue     ← 프롬프트 가이드 (현재 주석)
```

---

## Store (chat.js) — 상태 관리 중심

```
chat Store
├── state
│   ├── messages[]         ← 현재 대화 메시지 목록
│   ├── isLoading          ← 응답 대기 중
│   ├── searchMode         ← 'rag' | 'nl2sql' | 'agent'
│   ├── sessionId          ← 멀티턴 대화용 세션 ID
│   ├── isStreaming         ← SSE 스트리밍 중
│   ├── streamProgress[]   ← 완료된 스트리밍 단계
│   ├── streamController   ← AbortController (취소용)
│   ├── chatHistory[]      ← 과거 대화 목록
│   └── activeChatId       ← 현재 선택된 대화
│
├── actions
│   ├── sendMessage()      ← 메시지 전송 (라우팅)
│   ├── sendMessageStream()← SSE 스트리밍 전송
│   ├── cancelStream()     ← 스트리밍 취소
│   ├── setMode()          ← 모드 변경 + 세션 초기화
│   ├── clearChat()        ← 대화 초기화
│   ├── fetchChatHistory() ← 대화 이력 목록 조회
│   ├── loadChatSession()  ← 과거 대화 불러오기
│   └── deleteChatHistory()← 대화 이력 삭제
│
└── mutations
    ├── ADD_MESSAGE         ← 메시지 추가 (id, timestamp 자동)
    ├── UPDATE_LAST_MESSAGE ← 마지막 메시지 갱신 (스트리밍용)
    ├── SET_STREAMING       ← 스트리밍 상태 변경
    └── ADD_STREAM_PROGRESS ← 완료 단계 추가
```

---

## 문서 구성

| 파일 | 내용 |
|------|------|
| [01_chat_input_message.md](01_chat_input_message.md) | 입력과 메시지 표시 컴포넌트 |
| [02_sse_streaming_ui.md](02_sse_streaming_ui.md) | SSE 스트리밍과 chat Store |
| [03_user_chat_view.md](03_user_chat_view.md) | 사용자 화면 (UserChatView) |
| [04_how_it_works.md](04_how_it_works.md) | 시나리오별 전체 흐름 |

---

## 핵심 개념 미리보기

| 개념 | 설명 |
|------|------|
| **SSE (Server-Sent Events)** | 서버→클라이언트 단방향 스트리밍. 실시간 진행 상태 표시에 사용 |
| **스트리밍 콜백** | onNodeStart, onNodeComplete, onComplete, onError — 4가지 이벤트 |
| **멀티턴 대화** | session_id 기반. 이전 질문 문맥을 유지하여 후속 질문 가능 |
| **마크다운 렌더링** | AI 답변을 `formatMarkdownToHtml()`로 HTML 변환 후 `v-html`로 표시 |
| **오버레이 사이드바** | 마우스 호버 500ms 후 슬라이드 등장, 클릭으로 즉시 토글 |
| **auto-resize textarea** | 입력 내용에 따라 높이 자동 조절 (scrollHeight 활용) |
