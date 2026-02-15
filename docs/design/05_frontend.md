# 프론트엔드 아키텍처

> 최종 수정: 2026-02-15

---

## 1. 기술 스택

| 구분 | 기술 | 버전 |
|------|------|------|
| 프레임워크 | Vue 3 (Composition API) | ^3.3.13 |
| 상태관리 | Vuex | ^4.1.0 |
| 라우터 | Vue Router | ^4.2.5 |
| HTTP | Axios | ^1.6.2 |
| UI | Element Plus | ^2.4.4 |
| 차트 | ECharts + Vue ECharts | ^6.0.0 |
| 빌드 | Vite | ^5.0.10 |
| 스타일 | SCSS (sass ^1.69.5) | |

---

## 2. 디렉토리 구조

```
frontend/src/
├── main.js                          # 앱 진입점 (Vue + ElementPlus + Store + Router)
├── App.vue                          # 루트 컴포넌트 (router-view)
├── views/
│   ├── LoginView.vue                # 로그인
│   ├── user/
│   │   └── UserChatView.vue         # 사용자 채팅 (다크모드 기본)
│   └── admin/
│       ├── AdminLayout.vue          # 관리자 레이아웃 (사이드바+헤더)
│       ├── DashboardView.vue        # 대시보드
│       ├── ChatView.vue             # 관리자 AI 검색
│       ├── DocumentsView.vue        # 문서 목록
│       ├── DocumentDetailView.vue   # 문서 상세
│       ├── DocumentEditView.vue     # 문서 편집
│       ├── SettingsView.vue         # 시스템 설정
│       ├── CodesView.vue            # 코드 관리
│       ├── HistoryView.vue          # 검색 이력
│       ├── HistoryDetailView.vue    # 이력 상세
│       ├── UsersView.vue            # 사용자 관리
│       ├── RolesView.vue            # 역할 관리
│       ├── TenantsView.vue          # 테넌트 관리
│       └── MenusView.vue            # 메뉴 관리
├── components/
│   ├── chat/
│   │   ├── ChatMessage.vue          # 메시지 표시 (마크다운, 소스, SQL 결과)
│   │   ├── ChatInput.vue            # 입력 + 검색모드 선택
│   │   ├── SourceCard.vue           # RAG 소스 카드
│   │   └── PromptGuideModal.vue     # 예제 프롬프트
│   ├── chart/
│   │   └── ChartBuilder.vue         # SQL 결과 차트 (line, bar, pie)
│   ├── layout/
│   │   ├── AppHeader.vue            # 상단 헤더 (테마, 사용자 메뉴)
│   │   └── AppSidebar.vue           # 관리자 사이드바
│   ├── user/
│   │   ├── UserChatLayout.vue       # 사용자 채팅 레이아웃
│   │   ├── UserChatMessage.vue      # 사용자 메시지 표시
│   │   └── UserChatSidebar.vue      # 대화 이력 사이드바
│   └── documents/
│       └── ChunkPreview.vue         # 청킹 미리보기
├── api/                             # Axios API 클라이언트 (13개)
├── store/modules/                   # Vuex 상태 (4개)
├── router/index.js                  # 라우트 + 가드
├── utils/
│   ├── format.js                    # 날짜/숫자 포맷
│   └── markdownParser.js            # 마크다운 → HTML
└── assets/styles/
    ├── _variables.scss              # CSS 변수 (라이트/다크)
    ├── main.scss                    # 글로벌 엔트리
    ├── modules/                     # 리셋, 유틸, 다크 오버라이드
    └── mixins/                      # 재사용 SCSS 믹스인
        ├── _layout.scss             # 레이아웃 (사이드바, 헤더)
        ├── _cards.scss              # 카드 스타일
        ├── _chat.scss               # 채팅 버블
        ├── _forms.scss              # 폼 입력
        ├── _markdown.scss           # 마크다운 (테이블, 코드)
        ├── _animations.scss         # 트랜지션/애니메이션
        └── _chart.scss              # 차트 스타일
```

---

## 3. Vuex Store 모듈

### 3.1 auth — 인증 상태

| 항목 | 내용 |
|------|------|
| **State** | user, accessToken, refreshToken, loginLoading |
| **Actions** | login, logout, refresh, fetchMe, changePassword, initAuth |
| **Getters** | isAuthenticated, hasMenuPermission(menuCode, action), canAccessAdmin, roleCode |
| **저장소** | localStorage: `mureum_access_token`, `mureum_refresh_token`, `mureum_user` |

### 3.2 chat — 채팅 대화

| 항목 | 내용 |
|------|------|
| **State** | messages, searchMode, sessionId, isStreaming, streamProgress, chatHistory |
| **Actions** | sendMessage (일반), sendMessageStream (SSE), cancelStream, setMode, clearChat |
| **검색모드** | auto, rag, nl2sql, agent |
| **멀티턴** | 모드별 sessionId 유지, 모드 변경 시 세션 초기화 |

### 3.3 app — 전역 설정

| 항목 | 내용 |
|------|------|
| **State** | sidebarCollapsed, userDarkMode, adminDarkMode, currentView |
| **Actions** | toggleDarkMode, initTheme, toggleUserSidebar |
| **테마** | 사용자/관리자 독립 다크모드 (localStorage: `user_theme`, `admin_theme`) |

### 3.4 document — 문서 관리

| 항목 | 내용 |
|------|------|
| **State** | documents, currentDocument, selectedIds, filters, pagination |
| **Actions** | fetchDocuments, saveDocument, deleteDocument, executeEmbedding, previewChunks |
| **필터** | docType, sourceType, usageType, indexed, tenantFilter (GLOBAL only) |

---

## 4. 라우팅

### 4.1 라우트 구조

```
/ → /chat (리디렉트)
/login → LoginView
/chat → UserChatView (사용자 채팅, 다크모드 기본)
/admin (관리자 영역 — requiresAdmin)
  ├ dashboard → DashboardView     (DASHBOARD)
  ├ chat      → ChatView          (AI_SEARCH)
  ├ documents → DocumentsView     (DOC_MGMT)
  ├ documents/new → DocumentEditView
  ├ documents/:id → DocumentDetailView
  ├ documents/:id/edit → DocumentEditView
  ├ settings  → SettingsView      (SYS_SETTING)
  ├ codes     → CodesView         (CODE_MGMT)
  ├ history   → HistoryView       (SEARCH_HIST)
  ├ history/:id → HistoryDetailView
  ├ users     → UsersView         (USER_MGMT)
  ├ roles     → RolesView         (ROLE_MGMT)
  ├ tenants   → TenantsView       (TENANT_MGMT)
  └ menus     → MenusView         (MENU_MGMT)
```

### 4.2 가드 로직

```
beforeEach:
  토큰 없음 → /login
  /admin → canAccessAdmin 체크 (메뉴 1개 이상 보유)
  개별 라우트 → hasMenuPermission(menuCode, 'read')
  권한 없음 → landing_page 리디렉트
```

---

## 5. API 클라이언트

### 5.1 Axios 인스턴스 (`api/index.js`)

- Base URL: `VITE_API_URL` (개발: localhost:19090, Docker: 빈값/상대경로)
- Timeout: 120초 (Agent/NL2SQL 긴 처리 고려)
- **Request 인터셉터**: Bearer 토큰 자동 추가
- **Response 인터셉터**: `{success, data, error}` 파싱 → `data` 자동 추출
- **401 자동 갱신**: refresh token → 큐잉으로 동시 요청 처리

### 5.2 API 파일 목록

| 파일 | 대상 | 주요 메서드 |
|------|------|-----------|
| auth.js | 인증 | login, logout, refreshToken, getMe, changePassword |
| search.js | 통합 검색 | search, searchStream (SSE), exportExcel |
| agent.js | Agent | agentSearch, agentSearchStream (SSE), listSessions |
| sse.js | SSE 유틸 | streamSSE (POST 기반 SSE, AbortController) |
| documents.js | 문서 | list, save, update, delete, executeEmbedding |
| settings.js | 설정 | getAll, updateSetting, validateApiKey, testExternalConnection |
| codes.js | 코드 | lookup (공개), getGroups, create, update, reorder |
| history.js | 이력 | list, getStatistics, listSessions, getSessionHistory |
| users.js | 사용자 | list, create, update, delete, getRoleOptions, assignMenus |
| roles.js | 역할 | list, create, update, delete, getDefaultMenus |
| tenants.js | 테넌트 | list, create, update, delete |
| menus.js | 메뉴 | getTree, create, update, delete, reorder |

---

## 6. SSE 스트리밍

### 6.1 동작 방식

```
컴포넌트 → store.dispatch('sendMessageStream')
  → sse.streamSSE(url, body, callbacks)
    → fetch POST (SSE 헤더)
    → ReadableStream으로 이벤트 수신
    → 콜백: onNodeStart, onNodeComplete, onComplete, onError
    → AbortController로 취소 가능
```

### 6.2 UI 진행 표시

- `node_start`: "~중..." 스테이지 표시
- `node_complete`: 스테이지 완료 체크
- `complete`: 최종 답변 렌더링
- `error`: 에러 메시지 표시

---

## 7. 다크모드

- **사용자 채팅**: 기본 다크모드
- **관리자**: 토글 가능 (헤더 아이콘)
- **독립 설정**: 사용자/관리자 각각 localStorage 저장
- **구현**: `[data-theme="dark"]` CSS 변수 + Element Plus 다크 오버라이드

---

## 8. SCSS 스타일 규칙

모든 컴포넌트는 `assets/styles/mixins` 하위 믹스인을 참조한다:

```scss
@use '../../assets/styles/mixins' as mx;

.my-view {
  .page-header { @include mx.page-header; }
  .empty-state { @include mx.empty-state; }
  .pagination-wrapper { @include mx.pagination-wrapper; }
}
```

| 믹스인 파일 | 제공 |
|------------|------|
| _layout.scss | page-header, sidebar, containers |
| _cards.scss | content-card, stat-card |
| _chat.scss | chat-bubble, message-area |
| _forms.scss | form-item, toolbar |
| _markdown.scss | table, code-block, headers |
| _animations.scss | fade, slide 트랜지션 |

---

## 9. 환경 설정

| 파일 | VITE_API_URL | 용도 |
|------|-------------|------|
| .env.development | `http://localhost:19090` | 로컬 개발 |
| .env.docker | (빈값) | Docker (Nginx 프록시) |
| .env.production | `https://api.yourcompany.com` | 운영 |
