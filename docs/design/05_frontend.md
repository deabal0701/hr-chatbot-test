# 프론트엔드 아키텍처

> 최종 수정: 2026-03-10

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
│   ├── LoginView.vue                # 로그인 (SSO 테스트 버튼 포함)
│   ├── SSOCallbackView.vue          # SSO 콜백 (Cookie Base64URL → /me → 로그인)
│   ├── user/
│   │   ├── UserChatView.vue         # 사용자 채팅 (다크모드 기본)
│   │   └── PersonalDashboardView.vue # 개인 대시보드
│   └── admin/
│       ├── AdminLayout.vue          # 관리자 레이아웃 (사이드바+헤더)
│       ├── DashboardView.vue        # 관리자 대시보드
│       ├── ChatView.vue             # 관리자 AI 검색
│       ├── DocumentsView.vue        # 문서 목록
│       ├── DocumentDetailView.vue   # 문서 상세
│       ├── DocumentEditView.vue     # 문서 편집
│       ├── UsersView.vue            # 사용자 관리
│       ├── RolesView.vue            # 역할 관리
│       ├── MenusView.vue            # 메뉴 관리
│       ├── TenantsView.vue          # 테넌트 관리
│       ├── DepartmentsView.vue      # 부서(조직) 관리
│       ├── SettingsView.vue         # 시스템 설정
│       ├── CodesView.vue            # 코드 관리
│       ├── HistoryView.vue          # 검색 이력
│       └── HistoryDetailView.vue    # 이력 상세
├── components/
│   ├── chat/
│   │   ├── ChatMessage.vue          # 메시지 표시 (마크다운, 소스, SQL 결과)
│   │   ├── ChatInput.vue            # 입력 + 검색모드 선택
│   │   ├── SourceCard.vue           # RAG 소스 카드
│   │   ├── SqlResultPanel.vue       # SQL 결과 테이블 패널
│   │   └── PromptGuideModal.vue     # 예제 프롬프트
│   ├── chart/
│   │   └── ChartBuilder.vue         # SQL 결과 차트 (line, bar, pie)
│   ├── dashboard/
│   │   ├── KpiCards.vue             # KPI 요약 카드 (4개)
│   │   ├── DailyTrendChart.vue      # 일별 요청 추이 (Stacked Bar)
│   │   ├── RequestTypeChart.vue     # 검색 유형 분포 (Donut)
│   │   ├── RecentActivity.vue       # 최근 검색 피드
│   │   └── SystemStatus.vue         # 시스템 현황
│   ├── dashboard-personal/
│   │   ├── DashboardGrid.vue        # 위젯 그리드 레이아웃
│   │   ├── DashboardWidget.vue      # 개별 위젯 컨테이너
│   │   ├── DashboardToolbar.vue     # 대시보드 툴바
│   │   ├── AddWidgetModal.vue       # 위젯 추가 모달
│   │   ├── WidgetEditModal.vue      # 위젯 편집 모달
│   │   ├── WidgetConfigForm.vue     # 위젯 설정 폼
│   │   ├── DashboardManageModal.vue # 대시보드 관리
│   │   ├── DashboardShareModal.vue  # 대시보드 공유
│   │   ├── SaveToDashboardModal.vue # 차트→대시보드 저장
│   │   ├── DashboardEmptyState.vue  # 빈 상태 표시
│   │   └── widgets/                 # 위젯 렌더러
│   │       ├── WidgetChart.vue      # 차트 위젯
│   │       ├── WidgetKpi.vue        # KPI 위젯
│   │       └── WidgetTable.vue      # 테이블 위젯
│   ├── layout/
│   │   ├── AppHeader.vue            # 상단 헤더 (테마, 사용자 메뉴)
│   │   └── AppSidebar.vue           # 관리자 사이드바
│   ├── user/
│   │   ├── UserChatLayout.vue       # 사용자 채팅 레이아웃
│   │   ├── UserChatMessage.vue      # 사용자 메시지 표시
│   │   ├── UserChatSidebar.vue      # 대화 이력 사이드바
│   │   └── MenuPermissionTable.vue  # 메뉴 권한 테이블
│   └── documents/
│       └── ChunkPreview.vue         # 청킹 미리보기
├── api/                             # Axios API 클라이언트 (16개)
├── store/modules/                   # Vuex 상태 (5개)
├── router/index.js                  # 라우트 + 가드
├── utils/
│   ├── format.js                    # 날짜/숫자 포맷
│   ├── error.js                     # 에러 처리 유틸
│   ├── exportUtils.js               # Excel 내보내기 유틸
│   └── markdownParser.js            # 마크다운 → HTML
└── assets/styles/
    ├── _variables.scss              # CSS 변수 (라이트/다크)
    ├── main.scss                    # 글로벌 엔트리
    ├── modules/                     # 스타일 모듈
    │   ├── _reset.scss              # CSS 리셋
    │   ├── _utilities.scss          # 유틸리티 클래스
    │   ├── _chat-global.scss        # 전역 채팅 스타일
    │   ├── _dropdown.scss           # 드롭다운 스타일
    │   └── _element-dark.scss       # Element Plus 다크 오버라이드
    └── mixins/                      # 재사용 SCSS 믹스인 (10개)
        ├── _index.scss              # 믹스인 인덱스
        ├── _layout.scss             # 레이아웃 (stats-row)
        ├── _cards.scss              # 카드 (stat-card)
        ├── _chat.scss               # 채팅 (toggle-section, SQL 코드, mode-badge)
        ├── _chart.scss              # 차트 (chart-builder, config-panel, render-area)
        ├── _dashboard.scss          # 대시보드 (chart-card, activity-list)
        ├── _forms.scss              # 폼 (settings-section, settings-actions)
        ├── _markdown.scss           # 마크다운 (table, header, list, copy-btn)
        ├── _animations.scss         # 애니메이션 (fade-in, rotating, typing)
        └── _responsive.scss         # 반응형 (mobile, tablet, desktop)
```

---

## 3. Vuex Store 모듈

### 3.1 auth — 인증 상태

| 항목 | 내용 |
|------|------|
| **State** | user, accessToken, refreshToken, loginLoading |
| **Actions** | login, logout, refresh, fetchMe, changePassword, initAuth (SSO는 SSOCallbackView에서 직접 처리) |
| **Getters** | isAuthenticated, hasMenuPermission(menuCode, action), canAccessAdmin, roleCode, accessibleMenus |
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

### 3.5 dashboard — 대시보드 상태

| 항목 | 내용 |
|------|------|
| **State** | dashboards, currentDashboard, widgets, layout |
| **Actions** | fetchDashboards, createDashboard, saveDashboard, fetchWidgets, refreshWidget |
| **개인 대시보드** | 사용자별 위젯 구성, 레이아웃 저장, 공유 기능 |

---

## 4. 라우팅

### 4.1 라우트 구조

```
/ → /chat (리디렉트)
/login → LoginView
/sso → SSOCallbackView (SSO 쿠키 → /me API → 로그인, public: true)
/chat → UserChatView (사용자 채팅, 다크모드 기본)
/personal-dashboard → PersonalDashboardView (개인 대시보드)
/admin (관리자 영역 — requiresAdmin)
  ├ dashboard    → DashboardView     (DASHBOARD)
  ├ chat         → ChatView          (AI_SEARCH)
  ├ documents    → DocumentsView     (DOC_MGMT)
  ├ documents/new → DocumentEditView
  ├ documents/:id → DocumentDetailView
  ├ documents/:id/edit → DocumentEditView
  ├ users        → UsersView         (USER_MGMT)
  ├ roles        → RolesView         (ROLE_MGMT)
  ├ tenants      → TenantsView       (TENANT_MGMT)
  ├ departments  → DepartmentsView   (DEPT_MGMT)
  ├ menus        → MenusView         (MENU_MGMT)
  ├ settings     → SettingsView      (SYS_SETTING)
  ├ codes        → CodesView         (CODE_MGMT)
  ├ history      → HistoryView       (SEARCH_HIST)
  └ history/:id  → HistoryDetailView
```

### 4.2 가드 로직

```
beforeEach:
  public 라우트 (/login, /sso) → 가드 통과
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

### 5.2 API 파일 목록 (16개)

| 파일 | 대상 | 주요 메서드 |
|------|------|-----------|
| auth.js | 인증 | login, logout, refreshToken, getMe, changePassword (SSO는 Cookie 기반으로 별도 API 불필요) |
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
| departments.js | 부서 | getTree, create, update, delete, reorder |
| dashboard.js | 관리자 대시보드 | getSummary |
| personalDashboard.js | 개인 대시보드 | dashboards CRUD, widgets CRUD, saveLayout, executeSql |
| export.js | 내보내기 | exportExcel |

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
- **구현**: `[data-theme="dark"]` CSS 변수 + Element Plus 다크 오버라이드 (`modules/_element-dark.scss`)

---

## 8. SCSS 스타일 규칙

모든 컴포넌트는 `assets/styles/mixins` 하위 믹스인을 참조한다:

```scss
@use '@/assets/styles/mixins' as mx;

.my-view {
  @include mx.stat-card;
  @include mx.mobile { /* 반응형 */ }
}
```

### 8.1 필수 규칙

1. `<style lang="scss" scoped>` 필수 (teleported 요소 예외)
2. `@use '@/assets/styles/mixins' as mx;` 필수
3. CSS Variables 필수 (하드코딩 색상 금지)
4. 반응형 mixin 사용 (`@include mx.mobile { ... }`)

### 8.2 믹스인 목록

| 파일 | 제공 | 용도 |
|------|------|------|
| _layout.scss | stats-row | 통계 행 레이아웃 |
| _cards.scss | stat-card | 통계 카드 |
| _chat.scss | toggle-section-container, toggle-button, sql-code-block, mode-badge | 채팅 토글, SQL 표시 |
| _chart.scss | chart-builder-container, chart-config-panel, chart-render-area | 차트 영역 |
| _dashboard.scss | chart-card, activity-list | 대시보드 차트, 활동 |
| _forms.scss | settings-section, settings-actions | 설정 폼 |
| _markdown.scss | md-table-styles, md-header-styles, md-list-styles, copy-table-btn | 마크다운 렌더링 |
| _animations.scss | fade-in-animation, rotating-animation, typing-animation | 애니메이션 |
| _responsive.scss | mobile, tablet, desktop | 반응형 브레이크포인트 |

---

## 9. 환경 설정

| 파일 | VITE_API_URL | 용도 |
|------|-------------|------|
| .env.development | `http://localhost:19090` | 로컬 개발 |
| .env.docker | (빈값) | Docker (Nginx 프록시) |
| .env.production | `https://api.yourcompany.com` | 운영 |
