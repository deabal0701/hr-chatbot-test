# 개인 BI 대시보드 설계서

> **현행화 일자**: 2026-02-28 (최종 코드 리뷰 및 버그 수정 반영)
> **구현 상태**: 프론트엔드 + 백엔드 전체 구현 완료 (멀티 대시보드, 공유, DB 연동, 컬럼 별칭, SQL 편집, 내보내기 포함)
> **테스트 상태**: 37/37 TC PASSED (`tests/test_12_personal_dashboard.py`)

---

## 1. 개요

### 1.1 목적

사용자 화면(Chat)에서 NL2SQL 쿼리 결과를 개인화하여 **경량 BI 도구** 역할을 하는 "개인 대시보드" 기능을 제공한다.
자연어로 질문하고, 결과를 저장하고, 드래그앤드롭으로 자신만의 대시보드를 구성할 수 있다.
**멀티 대시보드**를 지원하여 사용자당 최대 10개의 대시보드를 생성/선택할 수 있으며, 관리자(GLOBAL/TENANT)는 대시보드를 **공유**하여 다른 사용자가 읽기 전용으로 조회할 수 있다.

### 1.2 핵심 가치

| 항목 | 기존 BI 도구 | 개인 대시보드 (NL2SQL) |
|------|-------------|----------------------|
| 진입 장벽 | SQL/UI 학습 필요 | 자연어 질문만으로 가능 |
| 대시보드 구성 | IT팀 의존 | 사용자 셀프서비스 |
| 쿼리 작성 | SQL 직접 작성 | 멀티턴 대화로 점진적 정제 |
| 워크플로우 | 별도 도구 진입 | Chat 탐색 → 발견 → 대시보드 고정 |

### 1.3 설계 결정

| 항목 | 결정 | 이유 |
|------|------|------|
| 대시보드 위치 | 별도 페이지 (`/dashboard`) | Chat과 분리된 독립적 BI 화면 |
| 위젯 배치 방식 | 드래그앤드롭 그리드 (vue3-grid-layout-next) | 사용자 자유도 극대화 |
| 데이터 갱신 | 수동 새로고침 (SQL 재실행) | 성능 부담 최소화, 캐시 데이터 기본 표시 |
| 위젯 유형 | 테이블/Bar/H-Bar/Line/Pie/Scatter/KPI | 다양한 BI 시각화 커버 |
| 테마 | auto/light/dark 3단계 토글 | 사용자 기본 다크모드와 독립 제어 가능 |
| 컬러 팔레트 | 6종 프리셋 (기본/비비드/파스텔/따뜻한/시원한/어스톤) | 위젯별 차트 색상 개인화 |
| 저장소 | PostgreSQL DB (`tb_dashboard` + `tb_dashboard_widget`) | 서버 저장으로 브라우저 간 동기화, 데이터 영속성 보장 |
| 테마 저장소 | localStorage | UI 프리퍼런스, DB 저장 불필요 |
| SQL 편집 | WidgetEditModal 내 편집 + 테스트 실행 | 별도 모달 불필요, 기존 UI 확장 |
| 컬럼 별칭 | `chart_config.column_aliases` JSONB 내 저장 | 선택적 매핑, 추가 테이블 불필요 |
| 인증 방식 | `get_current_active_user` (로그인만 필수) | 개인 기능이므로 메뉴 권한 불필요 |
| 데이터 스코프 | `user_id` 기반 (본인 위젯만 접근) | 개인 대시보드이므로 USER 레벨 격리 |
| 멀티 대시보드 | `tb_dashboard` 테이블로 대시보드 관리 | 사용자당 최대 10개, 대시보드당 최대 20개 위젯 |
| 기본 대시보드 | 삭제 불가, 자동 생성 (`get_or_create_default_dashboard`) | 하위 호환성 보장 |
| 공유 모델 | `is_shared` + `share_scope` (별도 공유 테이블 없음) | 단순 공유 — 전체/테넌트 범위만 필요 |
| 공유 권한 | GLOBAL→all/tenant, TENANT→tenant만, USER→공유 불가 | 기존 RBAC 계층 준수 |
| 공유 대시보드 접근 | 읽기 전용 (새로고침만 허용) | 데이터 무결성 보장 |
| 라우트 | `/dashboard?id=X` (쿼리 파라미터) | 기존 라우트 유지, 기본 대시보드는 파라미터 없이 |

### 1.4 구현 상태 요약

| 영역 | 상태 | 비고 |
|------|------|------|
| 프론트엔드 컴포넌트 | ✅ 완료 | 14개 컴포넌트 + composable (DashboardManageModal, DashboardShareModal 추가) |
| Vuex 스토어 | ✅ 완료 | Backend API 연동 + 멀티 대시보드 상태 관리 |
| 라우터 | ✅ 완료 | `/dashboard` 등록 |
| Chat 연동 | ✅ 완료 | UserChatMessage "대시보드에 추가" 버튼 |
| 사이드바 메뉴 | ✅ 완료 | UserChatSidebar "대시보드" 항목 |
| 컬럼 별칭 | ✅ 완료 | SaveToDashboardModal, WidgetEditModal, 위젯 렌더러 전체 적용 |
| SQL 편집 | ✅ 완료 | WidgetEditModal 내 SQL 편집 + 테스트 실행 + 미리보기 |
| 백엔드 API | ✅ 완료 | 13개 엔드포인트 (대시보드 CRUD 6개 + 위젯 CRUD 7개) |
| 데이터베이스 | ✅ 완료 | `tb_dashboard` + `tb_dashboard_widget` 테이블 + 인덱스 |
| 멀티 대시보드 | ✅ 완료 | 사용자당 최대 10개, 기본 대시보드 자동 생성 |
| 대시보드 공유 | ✅ 완료 | GLOBAL/TENANT 관리자 공유, 읽기 전용 접근 |
| API 클라이언트 | ✅ 완료 | `personalDashboard.js` 대시보드 6개 + 위젯 7개 메서드 |
| Vuex API 연동 | ✅ 완료 | localStorage → API 호출 전환 완료 |
| 내보내기 | ✅ 완료 | 위젯 PNG, 대시보드 PNG/PDF (`html2canvas` + `jspdf`) |
| 테스트 | ✅ 완료 | `test_12_personal_dashboard.py` 37 TC (대시보드 CRUD, 공유, 멀티 대시보드 위젯, 위젯 CRUD, Layout, SQL, Auth) |

---

## 2. 사용자 흐름

### 2.1 Flow A: Chat에서 쿼리 결과를 대시보드에 저장

```
┌──────────────────────────────────────────────────────────────────┐
│  UserChatMessage (NL2SQL 결과 영역)                              │
│                                                                  │
│  ┌─────────────────────────────────┐                             │
│  │ 조회 결과 (15건)            [▼] │                             │
│  │ ┌─────────┬──────────────────┐  │                             │
│  │ │ 부서명   │ 직원수          │  │                             │
│  │ │ 개발팀   │ 42              │  │                             │
│  │ │ 인사팀   │ 15              │  │                             │
│  │ └─────────┴──────────────────┘  │                             │
│  │                                  │                             │
│  │ [Chart] [Excel 다운로드]         │                             │
│  │ [★ 대시보드에 추가]              │                             │
│  └─────────────────────────────────┘                             │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼  클릭
┌──────────────────────────────────────────────────────────────────┐
│  SaveToDashboardModal                                            │
│                                                                  │
│  위젯 제목: [부서별 직원 수 현황___________________]             │
│                                                                  │
│  위젯 유형: (●)테이블 ( )Bar ( )H-Bar ( )Line ( )Pie            │
│             ( )Scatter ( )KPI                                    │
│                                                                  │
│  [차트 설정 영역 - Bar/H-Bar/Line/Pie/Scatter 선택 시 표시]     │
│  X축: [부서명          ▼]   Y축: [직원수          ▼]            │
│  컬러 팔레트: [기본         ▼] (5색 미리보기 ●●●●●)             │
│                                                                  │
│  [KPI 설정 - KPI 선택 시 표시]                                   │
│  값 컬럼: [total_count  ▼]  단위: [명_________]                  │
│                                                                  │
│  ── 컬럼 표시명 (선택사항) ──────────────────────────────────────│
│  원본 컬럼명           표시명                                     │
│  department_name   [부서명_______________] ← placeholder: 원본명 │
│  employee_count    [직원수_______________]                        │
│  avg_salary        [___________________] ← 빈칸이면 원본명 유지  │
│  (빈칸 = 원본 컬럼명 사용, 영한/영영 모두 가능)                  │
│                                                                  │
│                          [취소]  [저장]                           │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼  저장
   store.dispatch('dashboard/saveWidget', config)
   → POST /api/v1/dashboard/widgets → DB 저장
   → ElMessage.success("위젯이 대시보드에 추가되었습니다")
```

**구현 파일**: `SaveToDashboardModal.vue` → props로 query, sql, columns, rows, rowCount 수신
- ChartBuilder에서 이미 설정한 차트 config가 있으면 초기값으로 전달 가능
- cached_data는 최대 500행까지 제한

### 2.2 Flow B: 개인 대시보드 조회

```
┌─────────┐
│ 사이드바  │
│          │
│ 새 대화   │
│ ─────── │
│ 대화 목록 │
│          │
│ ─────── │
│ 대시보드  │
│          │
└─────────┘
     │
     ▼  클릭 → /dashboard 이동
┌──────────────────────────────────────────────────────────────────┐
│  PersonalDashboardView                                           │
│                                                                  │
│  store.dispatch('dashboard/fetchWidgets')                        │
│  → GET /api/v1/dashboard/widgets → DB 조회                      │
│  → vue3-grid-layout-next 그리드에 위젯 렌더링                    │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 Flow C: 대시보드 편집 (드래그앤드롭)

```
┌────────────────────────────────────────────────────────────┐
│  "편집" 클릭 → 편집 모드 진입                               │
│                                                            │
│  ● 위젯 드래그 이동 가능 (헤더 전체가 드래그 핸들)           │
│  ● 위젯 크기 변경 가능 (우하단 핸들)                        │
│  ● 각 위젯에 [수정] [삭제] 아이콘 표시                      │
│  ● "위젯 추가" 플로팅 버튼 (FAB) 표시 (우하단 고정)         │
│                                                            │
│  "레이아웃 저장" → PUT /api/v1/dashboard/layout → DB 저장   │
│  "취소" → 이전 레이아웃으로 복원 (pendingLayout 백업)        │
│                                                            │
│  ※ 모바일(<=768px): 편집 버튼 클릭 시 경고 메시지 표시      │
└────────────────────────────────────────────────────────────┘
```

### 2.4 Flow D: 위젯 데이터 새로고침

```
┌────────────────────────────────────────────────────────────┐
│  위젯 새로고침 버튼 클릭                                    │
│  → store.dispatch('dashboard/refreshWidget', widgetId)      │
│  → POST /api/v1/dashboard/widgets/{id}/refresh              │
│  → 저장된 SQL을 External DB에서 재실행                      │
│  → PII 마스킹 적용 → cached_data 갱신                      │
│  → last_refreshed_at 타임스탬프 갱신                        │
│  → 실패 시: ElMessage.error 표시                            │
└────────────────────────────────────────────────────────────┘
```

### 2.5 Flow E: 대시보드에서 직접 위젯 추가

편집 모드에서 "+" 플로팅 버튼 클릭 시 AddWidgetModal이 열리며, **탭으로 2가지 모드**를 제공한다.

#### Flow E-1: 히스토리에서 선택 (기존)

```
┌────────────────────────────────────────────────────────────┐
│  [히스토리에서 선택]  [직접 질문하기]     ← 탭 전환         │
│  ─────────────────                                        │
│                                                            │
│  Step 1: 대화 히스토리에서 세션 선택                         │
│    → history API로 최근 100개 세션 로드                     │
│    → nl2sql 또는 agent 타입 세션만 필터                     │
│                                                            │
│  Step 2: 세션 내 NL2SQL 결과 선택                           │
│    → trace_data.sql_result가 있는 레코드만 필터             │
│    → 결과가 1개뿐이면 자동 선택                             │
│                                                            │
│  Step 3: 위젯 설정 + 미리보기 → "추가"                      │
│    → 위젯 생성 + 저장                                       │
└────────────────────────────────────────────────────────────┘
```

#### Flow E-2: 직접 질문하기 (신규)

```
┌────────────────────────────────────────────────────────────┐
│  [히스토리에서 선택]  [직접 질문하기]     ← 탭 전환         │
│                       ────────────────                     │
│                                                            │
│  Step 1: 자연어 질문 입력 + [실행] 클릭                     │
│    → POST /api/v1/search/stream { query, mode: "nl2sql" }  │
│    → SSE 이벤트로 실행 진행 상황 실시간 표시                 │
│    → 실행 취소 가능 (AbortController)                       │
│                                                            │
│  Step 2: 실행 결과 확인                                     │
│    → 생성된 SQL 표시                                        │
│    → 결과 테이블 미리보기 (최대 10행)                       │
│    → 실패 시: 에러 메시지 + 질문 재입력 유도                │
│                                                            │
│  Step 3: 위젯 설정 + 미리보기 → "추가"                      │
│    → 위젯 생성 + 저장 (히스토리 모드와 동일한 위젯 설정 UI) │
└────────────────────────────────────────────────────────────┘
```

**참조 API**: 기존 Chat의 `searchApi.searchStream()` (SSE) 재사용 — 별도 API 불필요

### 2.6 Flow F: 뷰 전환 (표 ↔ 차트)

```
┌────────────────────────────────────────────────────────────┐
│  각 위젯 헤더의 뷰 전환 토글 버튼 클릭                       │
│                                                            │
│  ● 차트 위젯(bar/line/pie/scatter/hbar): 차트 → 표 전환    │
│  ● 테이블 위젯: 표 → 차트 전환 (컬럼 자동 추론)             │
│    → detectColumnTypes()로 숫자/텍스트 컬럼 자동 분류       │
│    → 기본 bar 차트로 표시                                   │
│  ● KPI 위젯: KPI → 표 전환                                 │
│                                                            │
│  ※ 전환은 viewMode ref로 로컬 관리 (저장하지 않음)          │
└────────────────────────────────────────────────────────────┘
```

---

## 3. 화면 레이아웃

### 3.1 대시보드 메인 화면 (View Mode)

```
┌──────────────────────────────────────────────────────────────────────┐
│  TOOLBAR                                                             │
│  [←] [📊] BI 대시보드 (위젯 4개)     [🖥️테마] [전체 새로고침] [편집] │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  GRID AREA (vue3-grid-layout-next, 12컬럼, 16px 간격)               │
│                                                                      │
│  ┌────────────────────────────┐  ┌────────────────────────────┐      │
│  │ [📊] 부서별 직원 수 [↔][🔄]│  │ [📈] 월별 입사자 추이[↔][🔄]│      │
│  │                            │  │                            │      │
│  │  ┌──┐                      │  │    ╱╲                      │      │
│  │  │  │ ┌──┐                 │  │   ╱  ╲   ╱╲               │      │
│  │  │  │ │  │ ┌──┐            │  │  ╱    ╲_╱  ╲              │      │
│  │  │  │ │  │ │  │            │  │ ╱            ╲             │      │
│  │  └──┘ └──┘ └──┘            │  │                            │      │
│  │  (Bar Chart)               │  │  (Line Chart)              │      │
│  │────────────────────────────│  │────────────────────────────│      │
│  │ 방금 전                     │  │ 5분 전                     │      │
│  └────────────────────────────┘  └────────────────────────────┘      │
│                                                                      │
│  ┌────────────────────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │ [🥧] 직급별 인원 분포[↔][🔄]│  │ 전체 직원수  │  │ 평균 연봉    │   │
│  │                            │  │             │  │             │   │
│  │      ┌───┐                 │  │    342      │  │   5,280     │   │
│  │   ╱──│   │──╲              │  │     명      │  │    만원      │   │
│  │  │   │   │   │             │  │             │  │             │   │
│  │   ╲──│   │──╱              │  │  (KPI)     │  │  (KPI)     │   │
│  │      └───┘                 │  │             │  │             │   │
│  │  (Pie Chart)               │  └─────────────┘  └─────────────┘   │
│  └────────────────────────────┘                                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

- `[↔]` = 뷰 전환 토글 (표 ↔ 차트)
- `[🔄]` = 새로고침 버튼
- 각 위젯 하단에 "마지막 갱신" 타임스탬프 표시

### 3.2 대시보드 편집 모드 (Edit Mode)

```
┌──────────────────────────────────────────────────────────────────────┐
│  TOOLBAR                                                             │
│  [←] [📊] BI 대시보드 (위젯 4개)                  [취소] [레이아웃 저장]│
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐  ┌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┐  │
│  ┆ [≡] 부서별 직원 수  [✏️][🗑] ┆  ┆ [≡] 월별 입사자    [✏️][🗑] ┆  │
│  ┆                              ┆  ┆                              ┆  │
│  ┆  (차트 내용)                 ┆  ┆  (차트 내용)                 ┆  │
│  ┆                              ┆  ┆                              ┆  │
│  ┆                          ◢◣  ┆  ┆                          ◢◣  ┆  │
│  └╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘  └╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌╌┘  │
│                                                                      │
│  [≡] = 드래그 핸들 (헤더 전체)                                        │
│  ◢◣  = 리사이즈 핸들                                                 │
│  ╌╌  = 점선 테두리 (편집 중 primary 색상)                             │
│  [✏️] = 위젯 수정 모달 열기                                          │
│  [🗑] = 삭제 확인 (el-popconfirm)                                    │
│                                                                      │
│                                                    [+] (FAB, 56px)   │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.3 빈 상태 (Empty State)

3가지 빈 상태를 표시하며, 각 상태에 맞는 안내 메시지와 액션 버튼을 제공한다.

#### A. 대시보드 없음 (noDashboard)

```
┌──────────────────────────────────────────────────────────────────────┐
│  TOOLBAR                                                             │
│  [←] [📊] BI 대시보드                                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                         [📊 큰 아이콘]                               │
│                                                                      │
│                  대시보드가 없습니다                                   │
│           새 대시보드를 만들어 시작해보세요                            │
│                                                                      │
│                     [대시보드 만들기]                                  │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

#### B. 공유 대시보드 (readOnly)

```
│                  공유된 대시보드입니다                                │
│         이 대시보드는 읽기 전용으로 수정할 수 없습니다                │
```

#### C. 내 대시보드 위젯 없음

```
┌──────────────────────────────────────────────────────────────────────┐
│  TOOLBAR                                                             │
│  [←] [📊] BI 대시보드                                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                         [📊 큰 아이콘]                               │
│                                                                      │
│                     위젯이 없습니다                                   │
│       대화에서 NL2SQL 결과를 대시보드에 추가하거나,                   │
│           편집 모드에서 직접 위젯을 추가할 수 있습니다.               │
│                                                                      │
│               [위젯 추가]  [대화로 이동]                              │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

- "위젯 추가": 편집 모드 진입 + AddWidgetModal 자동 열기
- "대화로 이동": Chat 페이지(`/chat`)로 이동

### 3.4 SaveToDashboardModal (Chat에서 저장)

```
┌──────────────────────────────────────────────────────┐
│  대시보드에 추가                              [X]    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  위젯 제목                                           │
│  ┌────────────────────────────────────────────────┐  │
│  │ 부서별 직원 수 현황                            │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  위젯 유형                                           │
│  ┌────────┬────────┬────────┬────────┬────────┐     │
│  │ 테이블  │  Bar   │ H-Bar  │  Line  │  Pie   │     │
│  ├────────┼────────┼────────┘        └────────┘     │
│  │ Scatter │  KPI   │                                │
│  └────────┴────────┘                                 │
│                                                      │
│  ── 차트 설정 (Bar/H-Bar/Line/Pie/Scatter 선택 시) ──│
│                                                      │
│  ┌──────────────────┐ ┌──────────────────┐           │
│  │ X축/항목 컬럼  ▼ │ │ Y축/값 컬럼   ▼  │           │
│  └──────────────────┘ └──────────────────┘           │
│                                                      │
│  컬러 팔레트                                         │
│  ┌──────────────────────────────────────────┐        │
│  │ 기본  ●●●●●                          ▼  │        │
│  └──────────────────────────────────────────┘        │
│                                                      │
│  ── KPI 설정 (KPI 선택 시) ──                        │
│                                                      │
│  ┌──────────────────┐ ┌──────────────────┐           │
│  │ 값 컬럼       ▼  │ │ 단위   명        │           │
│  └──────────────────┘ └──────────────────┘           │
│                                                      │
├──────────────────────────────────────────────────────┤
│                           [취소]  [저장 (Primary)]   │
└──────────────────────────────────────────────────────┘
```

### 3.5 WidgetEditModal (위젯 수정 + SQL 편집 + 컬럼 별칭)

SaveToDashboardModal과 동일 구조에 기존 위젯 설정을 초기값으로 로드.
**SQL 편집 기능**과 **컬럼 별칭 기능**이 추가되어 기존 읽기 전용에서 변경됨.

```
┌──────────────────────────────────────────────────────┐
│  위젯 수정                                    [X]    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  위젯 제목 / 위젯 유형 / 차트 설정                    │
│  (SaveToDashboardModal과 동일 구조)                   │
│                                                      │
│  ── 컬럼 표시명 (선택사항) ──────────────────────────│
│  원본 컬럼명           표시명                         │
│  dept_nm           [부서명_________]                  │
│  emp_cnt           [Employee Count_]                  │
│  avg_sal           [________________]                 │
│  (빈칸 = 원본 컬럼명 사용, 영한/영영 모두 가능)      │
│                                                      │
│  ── 쿼리 정보 (접기/펼치기) ─────────────────────── │
│                                                      │
│  원본 질문 (읽기 전용)                                │
│  ┌────────────────────────────────────────────────┐  │
│  │ 부서별 직원 수를 알려줘                         │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  SQL (수정 가능)                                     │
│  ┌────────────────────────────────────────────────┐  │
│  │ SELECT dept_nm, COUNT(*) as emp_cnt            │  │
│  │ FROM employee                                  │  │
│  │ GROUP BY dept_nm                               │  │
│  │ ORDER BY emp_cnt DESC                          │  │
│  └────────────────────────────────────────────────┘  │
│  [SQL 실행]  ← SQL 변경 시 활성화                     │
│                                                      │
│  ── 실행 결과 미리보기 (SQL 실행 후 표시) ──         │
│  ┌────────────────────────────────────────────────┐  │
│  │ dept_nm     │ emp_cnt                          │  │
│  │ 개발팀       │ 42                              │  │
│  │ 영업팀       │ 35                              │  │
│  └────────────────────────────────────────────────┘  │
│  5건 조회됨 (15ms)                                   │
│  ※ 에러 시: 빨간 박스에 에러 메시지 표시              │
│                                                      │
├──────────────────────────────────────────────────────┤
│                           [취소]  [저장 (Primary)]   │
└──────────────────────────────────────────────────────┘
```

**SQL 편집 동작 규칙**:
1. SQL textarea에 변경 발생 → `sqlModified = true` → [SQL 실행] 버튼 활성화
2. [SQL 실행] 클릭 → `POST /api/v1/dashboard/execute-sql` 호출
   - 성공: 미리보기 테이블 표시 (최대 10행) + `execution_time_ms`
   - 실패: 에러 메시지 인라인 표시 (검증 실패, 실행 오류)
3. [저장] 클릭 시:
   - SQL 변경 + 실행 결과 있음 → 수정된 SQL + 새 cached_data 포함하여 PUT
   - SQL 변경 + 실행 미완료 → `ElMessage.warning('SQL을 먼저 실행해주세요')` 경고
   - SQL 미변경 → 제목/유형/설정/별칭만 PUT (기존 동작)

### 3.6 AddWidgetModal (대시보드에서 직접 추가)

`el-tabs`로 **히스토리에서 선택** / **직접 질문하기** 2가지 모드를 제공한다.

#### 탭 1: 히스토리에서 선택 (기존)

```
┌──────────────────────────────────────────────────────────┐
│  위젯 추가                                        [X]    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [히스토리에서 선택]  [직접 질문하기]       ← el-tabs     │
│  ─────────────────                                       │
│                                                          │
│  대화 히스토리                                           │
│  ┌──────────────────────────────────────────┐            │
│  │ 대화를 선택하세요                     ▼  │            │
│  └──────────────────────────────────────────┘            │
│  (최근 100개 세션, nl2sql/agent 필터, 검색 가능)         │
│                                                          │
│  쿼리 결과 선택 (세션 선택 후 표시)                      │
│  ┌──────────────────────────────────────────┐            │
│  │ 쿼리 결과를 선택하세요                ▼  │            │
│  └──────────────────────────────────────────┘            │
│  (trace_data.sql_result가 있는 레코드만 표시)            │
│  (결과 1개 시 자동 선택)                                 │
│                                                          │
│  ── 실행 결과 (선택 후 표시) ──                          │
│  ┌──────────────────────────────────────────┐            │
│  │ 부서명    │ 직원수                       │            │
│  │ 개발팀    │ 42                           │            │
│  │ 인사팀    │ 15                           │            │
│  └──────────────────────────────────────────┘            │
│  ... 외 N건                                              │
│                                                          │
│  (이하 공통 위젯 설정 UI)                                │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                              [취소]  [추가 (Primary)]    │
└──────────────────────────────────────────────────────────┘
```

#### 탭 2: 직접 질문하기 (신규)

```
┌──────────────────────────────────────────────────────────┐
│  위젯 추가                                        [X]    │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [히스토리에서 선택]  [직접 질문하기]       ← el-tabs     │
│                       ────────────────                    │
│                                                          │
│  질문 입력                                               │
│  ┌──────────────────────────────────────┐                │
│  │ 2024년 부서별 직원 수를 알려줘        │  [실행] [취소] │
│  └──────────────────────────────────────┘                │
│  (el-input + el-button, Enter 키로도 실행 가능)          │
│                                                          │
│  ── 실행 진행 상황 (실행 중 표시) ──────────────────     │
│  ✓ 쿼리 분석 완료                                        │
│  ✓ SQL 생성 완료                                         │
│  ● SQL 실행 중...                  [실행 취소]           │
│  ─────────────────────────────────────────────────       │
│                                                          │
│  ── 실행 결과 (완료 후 표시) ──────────────────────      │
│  생성된 SQL:                                             │
│  ┌─────────────────────────────────────────────┐         │
│  │ SELECT department_name, COUNT(*) as cnt     │         │
│  │ FROM employee                               │         │
│  │ WHERE hire_date >= '2024-01-01'             │         │
│  │ GROUP BY department_name                    │         │
│  └─────────────────────────────────────────────┘         │
│                                                          │
│  결과 데이터 (15건, 0.12초):                             │
│  ┌──────────────────────────────────────────┐            │
│  │ department_name │ cnt                    │            │
│  │ 개발팀          │ 42                     │            │
│  │ 인사팀          │ 15                     │            │
│  └──────────────────────────────────────────┘            │
│  ... 외 N건                                              │
│                                                          │
│  ── 실행 실패 시 (에러 표시) ───────────────────────     │
│  ⚠ SQL 생성에 실패했습니다. 다른 표현으로 질문해 보세요.  │
│  ─────────────────────────────────────────────────       │
│                                                          │
│  (이하 공통 위젯 설정 UI — 결과 확보 후 표시)            │
│                                                          │
├──────────────────────────────────────────────────────────┤
│                              [취소]  [추가 (Primary)]    │
└──────────────────────────────────────────────────────────┘
```

#### 직접 질문 탭 상태 관리

```javascript
// AddWidgetModal 내부 상태 (직접 질문 모드)
const activeTab = ref('history')     // 'history' | 'direct'
const directQuery = ref('')          // 사용자 입력 질문
const isExecuting = ref(false)       // NL2SQL 실행 중
const abortController = ref(null)    // 실행 취소용
const streamProgress = ref([])       // SSE 진행 단계 [{message, done}]
const executeError = ref('')         // 실행 에러 메시지
const executedSql = ref('')          // 생성된 SQL
const executionTimeMs = ref(0)       // 실행 시간
```

#### 직접 질문 실행 흐름

```
1. 사용자 질문 입력 → [실행] 클릭 (또는 Enter)
   → isExecuting = true
   → streamProgress = []
   → abortController = new AbortController()

2. SSE 스트리밍 호출
   → searchApi.searchStream({ query: directQuery, mode: 'nl2sql' }, callbacks)
   → onNodeStart: streamProgress에 진행 단계 추가 (● 실행 중...)
   → onNodeComplete: 해당 단계 완료 처리 (✓ 완료)

3. 실행 완료 (onComplete)
   → executedSql = event.sql
   → resultColumns = event.sql_result.columns
   → resultRows = event.sql_result.rows
   → executionTimeMs = event.sql_result.execution_time_ms
   → form.queryText = directQuery  (위젯의 query 필드)
   → form.title = directQuery.slice(0, 100)
   → isExecuting = false
   → 위젯 설정 UI 활성화

4. 실행 실패 (onError)
   → executeError = 에러 메시지
   → isExecuting = false

5. [실행 취소] 클릭
   → abortController.abort()
   → isExecuting = false
   → streamProgress 초기화

6. 재실행
   → 질문 수정 후 [실행] 다시 클릭 → 2번부터 반복
```

#### 공통 위젯 설정 UI

두 탭 모두 NL2SQL 결과를 확보한 후 동일한 위젯 설정 UI를 표시한다:
- 위젯 제목, 위젯 유형, 차트 설정 (X축/Y축/컬러팔레트)
- KPI 설정 (값 컬럼/단위 접미사)
- 컬럼 별칭 입력 (16장 참조)
- 미리보기 (차트/KPI)

**구현 참조**: `searchApi.searchStream()` (`frontend/src/api/search.js`, `sse.js`) 재사용

---

## 4. 위젯 유형 상세

### 4.1 위젯 유형별 사양

| 유형 | 기본 크기 (w x h) | 최소 크기 (w x h) | 렌더링 | 설명 |
|------|-------------------|-------------------|--------|------|
| table | 6 x 10 | 4 x 6 | el-table | 스크롤, 컬럼 자동 생성, 다크모드 지원 |
| bar | 6 x 10 | 4 x 6 | ECharts bar | 30개 이상 시 dataZoom 슬라이더 |
| hbar | 6 x 10 | 4 x 6 | ECharts bar (가로) | 수평 Bar, 축 반전 |
| line | 6 x 10 | 4 x 6 | ECharts line | 추세 분석용, smooth, areaStyle |
| pie | 5 x 10 | 4 x 6 | ECharts pie (도넛) | Top-N 그룹핑 + "기타" 버킷 |
| scatter | 6 x 10 | 4 x 6 | ECharts scatter | 산점도, 상관관계 분석 |
| kpi | 3 x 5 | 2 x 3 | 숫자 강조 | 단일 수치 + 단위 표시 |

### 4.2 WidgetTable (테이블 위젯)

```
┌──────────────────────────────────────┐
│ [📋] 부서별 직원 현황    [↔]  [🔄]   │
├──────────────────────────────────────┤
│ ┌──────────┬──────────┬──────────┐  │
│ │ 부서명    │ 직원수    │ 평균급여  │  │
│ ├──────────┼──────────┼──────────┤  │
│ │ 개발팀    │ 42       │ 5,200    │  │
│ │ 인사팀    │ 15       │ 4,800    │  │
│ │ 영업팀    │ 28       │ 5,100    │  │
│ └──────────┴──────────┴──────────┘  │
├──────────────────────────────────────┤
│ 5분 전                               │
└──────────────────────────────────────┘
```

- el-table, size="small", border
- 위젯 높이에 맞춰 max-height 자동 계산 (`contentHeight - 20`)
- [↔] 클릭 시 auto-detect된 bar 차트로 전환
- 다크 모드 지원

### 4.3 WidgetChart (차트 위젯 - Bar/H-Bar/Line/Pie/Scatter)

```
┌──────────────────────────────────────┐
│ [📊] 부서별 직원 수         [↔] [🔄] │
├──────────────────────────────────────┤
│                                      │
│   42 ┌──┐                            │
│      │  │                            │
│   28 │  │ ┌──┐                       │
│      │  │ │  │                       │
│   15 │  │ │  │ ┌──┐                  │
│      │  │ │  │ │  │                  │
│      └──┘ └──┘ └──┘                  │
│      개발  영업  인사                  │
│                                      │
├──────────────────────────────────────┤
│ 방금 전                               │
└──────────────────────────────────────┘
```

- vue-echarts (ECharts) 사용, autoresize 활성화
- `useChartOptions.js` composable의 `buildChartOption()` 함수 공유
- 다크/라이트 모드: `darkMode` prop으로 직접 색상 결정
- 6종 컬러 팔레트 지원 (`chart_config.color_palette`)
- Pie: Top-N 그룹핑 + "기타 (N건)" 버킷, 도넛형 (radius `['35%', '65%']`)
- Bar/Line: 30개 이상 시 dataZoom 슬라이더
- Line: smooth + areaStyle(opacity 0.08) 기본 적용
- H-Bar: 가로 bar (X축=값, Y축=카테고리, borderRadius 우측)
- Scatter: 산점도 (X/Y 모두 value 축)
- [↔] 클릭 시 표 모드로 전환

### 4.4 WidgetKpi (KPI 위젯)

```
┌─────────────────┐
│ 전체 직원수      │
│                  │
│      342        │
│       명         │
│                  │
│ 방금 전          │
└─────────────────┘
```

- `cached_data.rows[0]`에서 `kpi_column`으로 지정된 값 추출
- 숫자: 대형 표시 (font-weight: 700)
- 단위: `kpi_suffix` 값 표시 ("명", "%", "만원" 등)
- 수직/수평 중앙 정렬
- 컬러 카드 배경

---

## 5. 반응형 디자인

### 5.1 화면 크기별 동작

| 화면 | 그리드 컬럼 | 드래그앤드롭 | 편집 모드 | 비고 |
|------|------------|------------|----------|------|
| Desktop (>1024px) | 12 | 가능 | 전체 기능 | 2~3열 위젯 배치 |
| Tablet (769-1024px) | 8 | 가능 | 전체 기능 | 2열 위주 |
| Mobile (<=768px) | 1 | 비활성 | 경고 메시지 | 세로 스택, 새로고침만 가능 |

### 5.2 모바일 대응

- 위젯: 전체 폭 (1컬럼) 세로 스택
- 대시보드 콘텐츠: padding 8px
- 툴바: padding 축소, 편집 버튼 텍스트 숨김 (아이콘만)
- "편집" 버튼 클릭 시 `ElMessage.warning('모바일에서는 편집 모드를 지원하지 않습니다')` 표시
- FAB 위치: bottom/right 20px

---

## 6. 컴포넌트 구조

### 6.1 컴포넌트 트리

```
PersonalDashboardView.vue
├── DashboardToolbar.vue
│   ├── 대시보드 선택 드롭다운 (el-dropdown + my/shared 분리)
│   │   ├── 내 대시보드 목록 (기본 대시보드 표시)
│   │   ├── 공유 대시보드 목록
│   │   └── [대시보드 관리] 버튼 → DashboardManageModal
│   ├── 채팅으로 이동 버튼 (ArrowLeft)
│   ├── 테마 토글 버튼 (Monitor/Sunny/Moon)
│   ├── 전체 새로고침 버튼
│   ├── 내보내기 드롭다운 (PNG/PDF)
│   ├── 대시보드 공유 버튼 (GLOBAL/TENANT만 표시)
│   ├── 편집 모드 전환 버튼
│   └── 편집 모드: 취소 / 레이아웃 저장 버튼
│   ※ toolbar-right 영역: currentDashboard가 있을 때만 표시
├── DashboardEmptyState.vue (3가지 빈 상태)
│   ├── 대시보드 없음: [대시보드 만들기] 버튼
│   ├── 공유 대시보드 (읽기 전용 안내)
│   └── 위젯 없음: [위젯 추가] + [대화로 이동] 버튼
├── DashboardGrid.vue (vue3-grid-layout-next 래퍼)
│   └── DashboardWidget.vue (v-for 각 위젯)
│       ├── 위젯 헤더 (타입 아이콘, 제목, 뷰전환, 이미지 다운로드, 새로고침/수정/삭제)
│       ├── 위젯 콘텐츠 (동적):
│       │   ├── WidgetTable.vue    (table 또는 뷰전환 시)
│       │   ├── WidgetChart.vue    (bar/hbar/line/pie/scatter 또는 뷰전환 시)
│       │   └── WidgetKpi.vue      (kpi)
│       └── 위젯 푸터 (마지막 갱신 타임스탬프)
├── WidgetEditModal.vue (위젯 수정 + SQL 편집 + 컬럼 별칭)
├── AddWidgetModal.vue (히스토리/직접 질문 탭 추가 모달)
├── DashboardManageModal.vue (대시보드 목록 관리 CRUD)
├── DashboardShareModal.vue (대시보드 공유 설정)
└── [+] FAB 플로팅 버튼 (편집 모드 시)

UserChatMessage.vue (기존 파일 수정)
└── SaveToDashboardModal.vue (NL2SQL 결과 → 대시보드 저장 + 대시보드 선택)
```

### 6.2 파일 구조 (전체 구현 완료)

```
frontend/src/
├── views/user/
│   └── PersonalDashboardView.vue          ✅ 메인 대시보드 페이지
├── components/dashboard-personal/
│   ├── DashboardGrid.vue                  ✅ vue3-grid-layout-next 래퍼
│   ├── DashboardWidget.vue                ✅ 위젯 컨테이너 + 뷰전환 + 내보내기
│   ├── DashboardEmptyState.vue            ✅ 빈 상태 (3가지: 대시보드 없음/공유 읽기전용/위젯 없음)
│   ├── DashboardToolbar.vue               ✅ 상단 툴바 + 대시보드 선택 + 테마 토글 + 내보내기(PNG/PDF)
│   ├── SaveToDashboardModal.vue           ✅ Chat에서 저장 모달 + 대시보드 선택 + 컬럼 별칭
│   ├── WidgetEditModal.vue                ✅ 위젯 수정 + SQL 편집 + 컬럼 별칭
│   ├── AddWidgetModal.vue                 ✅ 히스토리/직접 질문 탭 추가 모달
│   ├── DashboardManageModal.vue           ✅ 대시보드 목록 관리 (생성/수정/삭제/기본 설정)
│   ├── DashboardShareModal.vue            ✅ 대시보드 공유 설정 (all/tenant 범위)
│   └── widgets/
│       ├── WidgetTable.vue                ✅ 테이블 렌더러 + 컬럼 별칭
│       ├── WidgetChart.vue                ✅ 차트 렌더러 + 컬럼 별칭 + 팔레트
│       └── WidgetKpi.vue                  ✅ KPI 렌더러 + 컬럼 별칭
├── composables/
│   └── useChartOptions.js                 ✅ 차트 옵션 공유 로직 + columnAliases
├── store/modules/
│   └── dashboard.js                       ✅ Vuex 대시보드 모듈 (멀티 대시보드 + 위젯 API 연동)
├── api/
│   └── personalDashboard.js               ✅ Axios API 클라이언트 (대시보드 6개 + 위젯 7개 메서드)
└── router/index.js                        ✅ /dashboard 라우트 등록

app/
├── api/
│   ├── routes/
│   │   └── personal_dashboard.py          ✅ 13개 API 엔드포인트 (대시보드 6 + 위젯 7)
│   └── services/
│       └── personal_dashboard_service.py   ✅ 대시보드/위젯 CRUD + 공유 + refresh + execute-sql
├── models/
│   └── personal_dashboard.py              ✅ Pydantic 모델 (대시보드 + 위젯 + 공유)
└── main.py                                ✅ 라우터 등록 완료

tests/
└── test_12_personal_dashboard.py          ✅ 37 TC (6 클래스: CRUD, 공유, 위젯, Layout, SQL, Auth)
```

### 6.3 수정된 기존 파일

| 파일 | 변경 내용 | 상태 |
|------|----------|------|
| `frontend/src/router/index.js` | `/dashboard` 라우트 추가 | ✅ |
| `frontend/src/store/index.js` | dashboard 모듈 등록 | ✅ |
| `frontend/src/store/modules/auth.js` | logout 시 `dashboard/clearState` dispatch 추가 | ✅ |
| `frontend/src/components/user/UserChatMessage.vue` | "대시보드에 추가" 버튼 추가 | ✅ |
| `frontend/src/components/user/UserChatSidebar.vue` | "대시보드" 네비게이션 메뉴 추가 | ✅ |
| `frontend/src/components/chart/ChartBuilder.vue` | 차트 옵션 로직을 composable로 추출 | ✅ |
| `app/main.py` | personal_dashboard 라우터 등록 | ✅ |
| `frontend/src/store/modules/dashboard.js` | 멀티 대시보드 + API 연동 (데모 위젯 코드 삭제) | ✅ |
| `frontend/src/composables/useChartOptions.js` | `buildChartOption`에 `columnAliases` 파라미터 추가 | ✅ |
| `frontend/src/components/dashboard-personal/DashboardEmptyState.vue` | 3가지 빈 상태 (데모→위젯추가 버튼 교체) | ✅ |
| `frontend/src/components/dashboard-personal/DashboardToolbar.vue` | 대시보드 선택 + 공유 + 내보내기 + toolbar-right 조건부 렌더링 | ✅ |
| `frontend/src/components/dashboard-personal/DashboardWidget.vue` | columnAliases 하위 전달 + 내보내기 | ✅ |
| `frontend/src/components/dashboard-personal/widgets/WidgetTable.vue` | columnAliases prop, label 매핑 | ✅ |
| `frontend/src/components/dashboard-personal/widgets/WidgetChart.vue` | columnAliases prop + colorPalette prop | ✅ |
| `frontend/src/components/dashboard-personal/widgets/WidgetKpi.vue` | columnAliases prop | ✅ |
| `frontend/src/components/dashboard-personal/SaveToDashboardModal.vue` | 대시보드 선택 + 컬럼 별칭 입력 UI + 미리보기 | ✅ |
| `frontend/src/components/dashboard-personal/WidgetEditModal.vue` | SQL 편집 + 컬럼 별칭 UI | ✅ |
| `frontend/src/components/dashboard-personal/AddWidgetModal.vue` | 히스토리 + 직접 질문 탭 + 대시보드 선택 | ✅ |
| `docs/sql/psql-hermes_db.sql` | `tb_dashboard` + `tb_dashboard_widget` DDL 추가 | ✅ |

---

## 7. 상태 관리 (Vuex)

### 7.1 Dashboard Store 모듈

**파일**: `frontend/src/store/modules/dashboard.js`
**저장소**: Backend API (`/api/v1/dashboard/`) + localStorage (테마만)
**네임스페이스**: `dashboard` (namespaced: true)

```javascript
state: () => ({
  // 대시보드 관리
  dashboards: [],          // 내 대시보드 목록
  sharedDashboards: [],    // 공유 대시보드 목록
  currentDashboardId: null,// 현재 선택된 대시보드 ID
  isLoadingDashboards: false,
  isReadOnly: false,       // 공유 대시보드 읽기 전용

  // 위젯 관리
  widgets: [],             // 현재 대시보드의 위젯 목록
  isLoading: false,        // 위젯 로딩 상태
  editMode: false,         // 편집 모드 여부
  pendingLayout: null,     // 편집 모드 진입 시 백업 (취소용)
  refreshingWidgets: {},   // { widgetId: true/false } 개별 위젯 로딩
  dashboardTheme: 'auto'   // 'auto' | 'light' | 'dark' (localStorage 저장)
})

// Getters - 대시보드
currentDashboard          // dashboards + sharedDashboards에서 currentDashboardId로 검색
defaultDashboard          // dashboards.find(d => d.is_default)
myDashboards              // dashboards
sharedDashboardList       // sharedDashboards
isReadOnly                // 공유 대시보드 읽기 전용
canShare                  // GLOBAL/TENANT 역할만 공유 가능

// Getters - 위젯
widgetCount               // widgets.length
isEditMode                // editMode
widgetById(id)            // 위젯 검색
isWidgetRefreshing(id)    // 새로고침 중 여부
dashboardTheme            // 현재 테마
gridLayout                // vue-grid-layout용 [{i, x, y, w, h, minW, minH}] 변환

// Actions - 대시보드
fetchDashboards()         // GET /api/v1/dashboard/dashboards → SET_DASHBOARDS + currentDashboardId 유효성 검증
selectDashboard(id)       // 대시보드 전환 → fetchWidgets
createDashboard(data)     // POST /api/v1/dashboard/dashboards → ADD_DASHBOARD
updateDashboard(id, data) // PUT /api/v1/dashboard/dashboards/{id} → UPDATE_DASHBOARD
deleteDashboard(id)       // DELETE → REMOVE_DASHBOARD → 마지막 대시보드 삭제 시 상태 초기화
setDefaultDashboard(id)   // PUT /api/v1/dashboard/dashboards/{id}/default → fetchDashboards
shareDashboard(id, data)  // PUT /api/v1/dashboard/dashboards/{id}/share → UPDATE_DASHBOARD

// Actions - 위젯
fetchWidgets()            // GET /api/v1/dashboard/widgets?dashboard_id → SET_WIDGETS + SET_READ_ONLY
saveWidget(config)        // POST → ADD_WIDGET (현재 대시보드일 때만 로컬 반영)
updateWidget(id, updates) // PUT → UPDATE_WIDGET
deleteWidget(id)          // DELETE → REMOVE_WIDGET
saveLayout()              // PUT /api/v1/dashboard/layout → 현재 대시보드 모든 위젯 grid_position 저장
refreshWidget(id)         // POST .../refresh → cached_data 갱신
refreshAllWidgets()       // 모든 SQL 위젯 병렬 refreshWidget (Promise.allSettled)
enterEditMode()           // 현재 위젯 깊은 복사 백업 + 편집 모드 진입
cancelEditMode()          // 백업 레이아웃 복원 + 편집 모드 종료
saveEditMode()            // saveLayout API 호출 + 편집 모드 종료
clearState()              // 로그아웃 시 전체 상태 초기화
setDashboardTheme(theme)  // 테마 변경 → localStorage 저장
```

**주요 구현 특징**:
- `deleteDashboard`: 삭제된 대시보드가 현재 선택된 대시보드인 경우 기본 대시보드로 전환, 마지막 대시보드 삭제 시 `currentDashboardId=null`, `widgets=[]` 초기화
- `saveWidget`: `widgetConfig.dashboard_id`가 명시되어 있으면 그대로 사용, 없으면 `currentDashboardId` 사용. 현재 대시보드의 위젯만 로컬 상태에 반영
- `fetchDashboards`: 현재 `currentDashboardId`가 유효하지 않으면 기본 대시보드로 자동 전환
- `clearState`: `auth.js:logout`에서 `dispatch('dashboard/clearState')` 호출하여 사용자 전환 시 이전 상태 잔존 방지

### 7.2 위젯 데이터 구조

```javascript
{
  widget_id: 1,
  title: "부서별 직원 수",
  widget_type: "bar",              // table | bar | hbar | line | pie | scatter | kpi
  query: "부서별 직원 수를 알려줘", // 원본 자연어 질문
  sql: "SELECT department_name, COUNT(*) ...",  // 생성된 SQL
  chart_config: {
    x_column: "department_name",   // X축 컬럼
    y_columns: ["count"],          // Y축 컬럼 (배열)
    pie_top_n: null,               // Pie Top N (null=전체)
    kpi_column: null,              // KPI 값 컬럼
    kpi_suffix: null,              // KPI 단위 ("명", "%", "원")
    color_palette: "default",      // 컬러 팔레트 (default|vivid|pastel|warm|cool|earth)
    column_aliases: {              // 컬럼 표시명 매핑 (선택사항, null 또는 {} = 미사용)
      "department_name": "부서명", // 원본 → 표시명 (영한, 영영 모두 가능)
      "count": "직원수"            // 매핑하지 않은 컬럼은 원본명 사용
    }
  },
  cached_data: {
    columns: ["department_name", "count"],
    rows: [{"department_name": "개발팀", "count": 42}, ...],
    row_count: 15,
    cached_at: "2026-02-26T10:30:00"
  },
  grid_position: {
    x: 0, y: 0, w: 6, h: 10      // vue-grid-layout 좌표
  },
  created_at: "2026-02-26T10:30:00",
  updated_at: "2026-02-26T10:30:00",
  last_refreshed_at: "2026-02-26T10:30:00"
}
```

### 7.3 컬러 팔레트 프리셋

| 키 | 라벨 | 설명 |
|-----|------|------|
| default | 기본 | ECharts 기본 색상 (#5470c6, #91cc75, ...) |
| vivid | 비비드 | 강렬한 색상 (#e74c3c, #3498db, ...) |
| pastel | 파스텔 | 부드러운 색상 (#a1c4fd, #c2e9fb, ...) |
| warm | 따뜻한 | 난색 계열 (#ff6b6b, #ffa502, ...) |
| cool | 시원한 | 한색 계열 (#0984e3, #00cec9, ...) |
| earth | 어스톤 | 자연 색상 (#8b6914, #6b8e23, ...) |

### 7.4 데이터 흐름

```
[Chat → 저장]
UserChatMessage.vue
  → message.sqlResult (columns, rows), message.sql, message.content
  → SaveToDashboardModal (props로 전달)
  → 사용자가 제목/유형/차트설정/컬러팔레트/컬럼별칭 입력
  → store.dispatch('dashboard/saveWidget', config)
  → POST /api/v1/dashboard/widgets → 서버 저장 → widget_id 발급
  → commit ADD_WIDGET (서버 반환 객체)

[대시보드 로드]
PersonalDashboardView.onMounted
  → store.dispatch('dashboard/fetchWidgets')
  → GET /api/v1/dashboard/widgets → {items: [...], total: N}
  → commit SET_WIDGETS
  → DashboardGrid ← Vuex gridLayout getter 바인딩
  → DashboardWidget ← v-for 개별 위젯

[대시보드에서 추가 - 히스토리 탭]
AddWidgetModal (탭: 히스토리에서 선택)
  → historyApi.listSessions() → 세션 목록 로드 (nl2sql/agent 필터)
  → historyApi.getSessionHistory() → NL2SQL 결과 있는 레코드 필터
  → 결과 선택 → 위젯 설정 + 컬럼별칭 → store.dispatch('dashboard/saveWidget')
  → POST /api/v1/dashboard/widgets → 서버 저장

[대시보드에서 추가 - 직접 질문 탭]
AddWidgetModal (탭: 직접 질문하기)
  → 사용자 질문 입력 → [실행] 클릭
  → searchApi.searchStream({ query, mode: 'nl2sql' }, callbacks)
  → SSE 이벤트: 진행 상황 표시 (쿼리 분석 → SQL 생성 → 실행)
  → onComplete: sql, sql_result.columns, sql_result.rows 추출
  → 위젯 설정 + 컬럼별칭 → store.dispatch('dashboard/saveWidget')
  → POST /api/v1/dashboard/widgets → 서버 저장

[위젯 수정 + SQL 편집]
WidgetEditModal
  → 제목/유형/차트설정/컬럼별칭 수정
  → SQL 수정 시: POST /api/v1/dashboard/execute-sql → 미리보기 표시
  → 저장: PUT /api/v1/dashboard/widgets/{id} → 서버 갱신
  → commit UPDATE_WIDGET (서버 반환 객체)

[위젯 새로고침]
DashboardWidget 새로고침 버튼
  → store.dispatch('dashboard/refreshWidget', widgetId)
  → POST /api/v1/dashboard/widgets/{id}/refresh
  → 서버에서 저장된 SQL 재실행 (sql_executor) → PII 필터
  → 최신 cached_data + last_refreshed_at 반환
  → commit UPDATE_WIDGET
  → 실패 시: ElMessage.error 표시

[레이아웃 저장]
편집 모드에서 "레이아웃 저장" 클릭
  → PUT /api/v1/dashboard/layout → 모든 위젯의 grid_position 일괄 갱신
  → commit UPDATE_LAYOUT + 편집 모드 종료
```

---

## 8. 차트 옵션 Composable

### 8.1 useChartOptions.js

**파일**: `frontend/src/composables/useChartOptions.js`

ChartBuilder.vue와 Dashboard WidgetChart.vue에서 공유하는 차트 로직.

**Export 함수/상수**:

| 이름 | 용도 |
|------|------|
| `getThemeColor(varName)` | CSS 변수에서 색상값 추출 |
| `detectColumnTypes(columns, rows)` | 샘플 10행 기반 숫자/텍스트 컬럼 자동 분류 |
| `buildChartOption(options)` | ECharts 옵션 생성 (bar/hbar/line/pie/scatter 지원) |
| `CHART_PALETTES` | 6종 컬러 팔레트 프리셋 객체 |

**`buildChartOption` 파라미터**:

```javascript
buildChartOption({
  chartType,       // 'bar' | 'hbar' | 'line' | 'pie' | 'scatter'
  xColumn,         // X축 컬럼명
  yColumns,        // Y축 컬럼명 (배열 또는 단일 문자열)
  rows,            // 데이터 행 배열
  pieTopN,         // Pie Top N (기본 10)
  whiteBg,         // 흰색 배경 모드 (Excel 내보내기 등)
  darkMode,        // true/false/null (null이면 CSS 변수에서 추론)
  colorPalette,    // 팔레트 키 (기본 'default')
  columnAliases    // 컬럼 표시명 매핑 (선택사항, null이면 원본명 사용)
                   // 예: {"dept_nm": "부서명", "emp_cnt": "Employee Count"}
})
```

**columnAliases 적용 지점**:
- 범례(Legend) `data` → `yCols.map(col => aliases[col] || col)`
- 시리즈 `name` → `aliases[col] || col`
- 산점도 축명 → `aliases[xColumn] || xColumn`
- 산점도 툴팁 → alias 적용된 컬럼명 표시
- **미적용**: 데이터 바인딩 키 (`:prop`, `r[col]` 등은 원본 컬럼명 유지)

---

## 9. Backend API 설계

> **상태**: ✅ 전체 구현 완료 (13개 엔드포인트)
> **인증**: 모든 엔드포인트에 `Depends(get_current_active_user)` 적용 (로그인 필수, 메뉴 권한 불필요)
> **데이터 스코프**: `user_id` 기반 본인 데이터만 접근 + 공유 대시보드 읽기 전용 접근
> **보안**: 이중 검증 패턴 — 사전 소유권 검증(`_get_dashboard`/`_get_widget`) + SQL WHERE `AND user_id = %s`
> **URL 네임스페이스**: admin dashboard (`GET /api/v1/dashboard/summary`)와 동일 prefix 사용, 경로 충돌 없음

### 9.1 엔드포인트

#### 대시보드 CRUD (6개)

| # | Method | Path | 설명 | Status | 응답 data |
|---|--------|------|------|--------|-----------|
| 1 | GET | `/api/v1/dashboard/dashboards` | 내 대시보드 + 공유 대시보드 목록 | 200 | `{my_dashboards: [...], shared_dashboards: [...]}` |
| 2 | POST | `/api/v1/dashboard/dashboards` | 대시보드 생성 (최대 10개) | 201 | 생성된 대시보드 객체 |
| 3 | PUT | `/api/v1/dashboard/dashboards/{id}` | 대시보드 수정 (이름/설명) | 200 | 수정된 대시보드 객체 |
| 4 | DELETE | `/api/v1/dashboard/dashboards/{id}` | 대시보드 삭제 (기본 대시보드 불가) | 200 | `{message, deleted_count}` |
| 5 | PUT | `/api/v1/dashboard/dashboards/{id}/default` | 기본 대시보드 설정 | 200 | 수정된 대시보드 객체 |
| 6 | PUT | `/api/v1/dashboard/dashboards/{id}/share` | 대시보드 공유 설정 (GLOBAL/TENANT만) | 200 | 수정된 대시보드 객체 |

#### 위젯 CRUD + SQL (7개)

| # | Method | Path | 설명 | Status | 응답 data |
|---|--------|------|------|--------|-----------|
| 7 | GET | `/api/v1/dashboard/widgets` | 위젯 목록 (dashboard_id 파라미터) | 200 | `{items: [...], total: N, dashboard_id, is_read_only}` |
| 8 | POST | `/api/v1/dashboard/widgets` | 위젯 생성 (대시보드당 최대 20개) | 201 | 생성된 위젯 객체 |
| 9 | PUT | `/api/v1/dashboard/widgets/{id}` | 위젯 수정 (제목/유형/SQL/설정/별칭) | 200 | 수정된 위젯 객체 |
| 10 | DELETE | `/api/v1/dashboard/widgets/{id}` | 위젯 삭제 | 200 | `{message, deleted_count}` |
| 11 | PUT | `/api/v1/dashboard/layout` | 레이아웃 일괄 저장 | 200 | `{message, updated_count}` |
| 12 | POST | `/api/v1/dashboard/widgets/{id}/refresh` | 저장된 SQL 재실행 → 데이터 갱신 | 200 | `{widget_id, cached_data, last_refreshed_at}` |
| 13 | POST | `/api/v1/dashboard/execute-sql` | SQL 테스트 실행 (편집 미리보기용) | 200 | `{columns, rows, row_count, execution_time_ms}` |

### 9.2 요청/응답 예시

**위젯 생성 (POST)**:
```json
// Request
{
  "title": "부서별 직원 수",
  "widget_type": "bar",
  "query": "부서별 직원 수를 알려줘",
  "sql": "SELECT department_name, COUNT(*) as cnt FROM employee GROUP BY department_name",
  "chart_config": {
    "x_column": "department_name",
    "y_columns": ["cnt"],
    "color_palette": "default",
    "column_aliases": {
      "department_name": "부서명",
      "cnt": "직원수"
    }
  },
  "cached_data": {
    "columns": ["department_name", "cnt"],
    "rows": [{"department_name": "개발팀", "cnt": 42}],
    "row_count": 15
  }
}

// Response (201)
{
  "success": true,
  "data": {
    "widget_id": 1,
    "user_id": 5,
    "tenant_id": 2,
    "title": "부서별 직원 수",
    "widget_type": "bar",
    "query": "부서별 직원 수를 알려줘",
    "sql": "SELECT department_name, COUNT(*) as cnt FROM employee GROUP BY department_name",
    "chart_config": {
      "x_column": "department_name",
      "y_columns": ["cnt"],
      "color_palette": "default",
      "column_aliases": {"department_name": "부서명", "cnt": "직원수"}
    },
    "cached_data": {
      "columns": ["department_name", "cnt"],
      "rows": [{"department_name": "개발팀", "cnt": 42}],
      "row_count": 15,
      "cached_at": "2026-02-27T10:30:00"
    },
    "grid_position": {"x": 0, "y": 0, "w": 6, "h": 10},
    "sort_order": 0,
    "created_at": "2026-02-27T10:30:00",
    "updated_at": "2026-02-27T10:30:00",
    "last_refreshed_at": "2026-02-27T10:30:00"
  }
}
```

**위젯 수정 (PUT)** - SQL 편집 + 컬럼 별칭 포함:
```json
// Request (변경된 필드만 전송)
{
  "title": "부서별 인원 현황",
  "sql": "SELECT department_name, COUNT(*) as cnt FROM employee WHERE is_active = true GROUP BY department_name",
  "chart_config": {
    "x_column": "department_name",
    "y_columns": ["cnt"],
    "color_palette": "vivid",
    "column_aliases": {
      "department_name": "Department",
      "cnt": "Head Count"
    }
  },
  "cached_data": {
    "columns": ["department_name", "cnt"],
    "rows": [{"department_name": "개발팀", "cnt": 38}],
    "row_count": 7,
    "cached_at": "2026-02-27T11:00:00"
  }
}

// Response (200) — 전체 위젯 객체 반환
```

**레이아웃 저장 (PUT)**:
```json
// Request
{
  "layout": [
    {"widget_id": 1, "x": 0, "y": 0, "w": 6, "h": 10},
    {"widget_id": 2, "x": 6, "y": 0, "w": 6, "h": 10},
    {"widget_id": 3, "x": 0, "y": 10, "w": 5, "h": 10}
  ]
}

// Response (200)
{
  "success": true,
  "data": {
    "message": "레이아웃이 저장되었습니다",
    "updated_count": 3
  }
}
```

**데이터 새로고침 (POST)**:
```json
// Request: body 없음 (저장된 SQL 재실행)
// Response (200)
{
  "success": true,
  "data": {
    "widget_id": 1,
    "cached_data": {
      "columns": ["department_name", "cnt"],
      "rows": [{"department_name": "개발팀", "cnt": 45}, ...],
      "row_count": 7,
      "cached_at": "2026-02-27T14:30:00"
    },
    "last_refreshed_at": "2026-02-27T14:30:00"
  }
}
```

**SQL 테스트 실행 (POST)** — SQL 편집 미리보기용:
```json
// Request
{
  "sql": "SELECT department_name, COUNT(*) as cnt FROM employee GROUP BY department_name ORDER BY cnt DESC"
}

// Response (200) — 성공
{
  "success": true,
  "data": {
    "columns": ["department_name", "cnt"],
    "rows": [{"department_name": "개발팀", "cnt": 45}, {"department_name": "영업팀", "cnt": 38}],
    "row_count": 7,
    "execution_time_ms": 15
  }
}

// Response (400) — SQL 검증 실패
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "데이터 조회만 가능합니다. 데이터 변경이 포함된 질문은 처리할 수 없습니다."
  }
}
```

### 9.3 Backend 파일 구조

```
app/
├── api/
│   ├── routes/
│   │   └── personal_dashboard.py        # 13개 API 엔드포인트 (대시보드 6 + 위젯 7) ✅
│   └── services/
│       └── personal_dashboard_service.py # 대시보드/위젯 CRUD + 공유 + refresh + execute-sql ✅
├── models/
│   └── personal_dashboard.py            # Pydantic 모델 (대시보드 + 위젯 + 공유) ✅
└── main.py                              # 라우터 등록 완료 ✅

frontend/src/
└── api/
    └── personalDashboard.js             # Axios API 클라이언트 (대시보드 6 + 위젯 7 메서드) ✅
```

### 9.4 Pydantic 모델 (구현 완료)

```python
# app/models/personal_dashboard.py

VALID_WIDGET_TYPES = {"table", "bar", "hbar", "line", "pie", "scatter", "kpi"}
VALID_SHARE_SCOPES = {"all", "tenant"}

# ─── 대시보드 모델 ───

class DashboardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class DashboardUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

class DashboardShareRequest(BaseModel):
    is_shared: bool = False
    share_scope: Optional[str] = None
    # @field_validator: share_scope는 is_shared=True일 때만 'all' | 'tenant' 허용

# ─── 위젯 모델 ───

class ChartConfig(BaseModel):
    x_column: Optional[str] = None
    y_columns: Optional[List[str]] = None
    pie_top_n: Optional[int] = None
    kpi_column: Optional[str] = None
    kpi_suffix: Optional[str] = None
    color_palette: Optional[str] = "default"
    column_aliases: Optional[Dict[str, str]] = None  # {"eng_col": "표시명"}

class CachedData(BaseModel):
    columns: List[str] = []
    rows: List[Dict[str, Any]] = []
    row_count: int = 0
    cached_at: Optional[str] = None

class GridPosition(BaseModel):
    x: int = 0
    y: int = 0
    w: int = 6
    h: int = 10

class WidgetCreate(BaseModel):
    dashboard_id: Optional[int] = None  # 미지정 시 기본 대시보드
    title: str = Field(..., min_length=1, max_length=200)
    widget_type: str = Field(default="table")
    query: Optional[str] = None
    sql: Optional[str] = None
    chart_config: Optional[ChartConfig] = None
    cached_data: Optional[CachedData] = None
    grid_position: Optional[GridPosition] = None

class WidgetUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    widget_type: Optional[str] = None
    query: Optional[str] = None
    sql: Optional[str] = None
    chart_config: Optional[ChartConfig] = None
    cached_data: Optional[CachedData] = None

class LayoutItem(BaseModel):
    widget_id: int
    x: int
    y: int
    w: int
    h: int

class LayoutSaveRequest(BaseModel):
    dashboard_id: Optional[int] = None  # 미지정 시 기본 대시보드
    layout: List[LayoutItem] = Field(..., min_length=1)

class ExecuteSqlRequest(BaseModel):
    sql: str = Field(..., min_length=1)
```

**참고**: `WidgetCreate`/`WidgetUpdate`에 `@field_validator`로 `widget_type` 유효성 검사, `DashboardShareRequest`에 `share_scope` 유효성 검사를 수행한다.

### 9.5 Service 계층 (구현 완료)

```python
# app/api/services/personal_dashboard_service.py
# 싱글톤: personal_dashboard_service = PersonalDashboardService()

class PersonalDashboardService:
    """개인 대시보드 + 위젯 CRUD + 공유 + SQL 실행 서비스"""

    MAX_DASHBOARDS_PER_USER = 10  # 사용자당 최대 대시보드 수
    MAX_WIDGETS_PER_DASHBOARD = 20  # 대시보드당 최대 위젯 수
    MAX_CACHED_ROWS = 500         # cached_data 최대 행 수

    # 위젯 유형별 기본 그리드 크기
    DEFAULT_GRID_SIZES = {
        "kpi": {"w": 3, "h": 5},
        "pie": {"w": 5, "h": 10},
        # table, bar, hbar, line, scatter: {"w": 6, "h": 10}
    }

    # ── 대시보드 CRUD ──

    def list_dashboards(self, user_id, tenant_id, role_code) -> dict:
        """내 대시보드 + 공유 대시보드 목록 → {my_dashboards: [...], shared_dashboards: [...]}
        my_dashboards: user_id 기반, 공유: role_code/tenant_id 기반 범위 필터"""

    def create_dashboard(self, user_id, tenant_id, data) -> dict:
        """대시보드 생성 (MAX_DASHBOARDS_PER_USER 제한)
        단일 쿼리로 COUNT/MAX(sort_order)/default_cnt 조회 (최적화)
        첫 대시보드 자동 is_default=true"""

    def update_dashboard(self, user_id, dashboard_id, data) -> dict:
        """대시보드 이름/설명 수정 (소유권 검증)"""

    def delete_dashboard(self, user_id, dashboard_id) -> dict:
        """대시보드 삭제 (기본 대시보드 불가, CASCADE로 위젯도 삭제)
        DELETE SQL에 AND user_id = %s 조건 포함 (이중 검증)"""

    def set_default_dashboard(self, user_id, dashboard_id) -> dict:
        """기본 대시보드 변경 (기존 기본 해제 → 새 기본 설정)"""

    def share_dashboard(self, user_id, dashboard_id, data) -> dict:
        """대시보드 공유 설정 (GLOBAL: all/tenant, TENANT: tenant만)"""

    # ── 위젯 CRUD ──

    def list_widgets(self, user_id, dashboard_id, tenant_id, role_code) -> dict:
        """위젯 목록 조회 → {items: [...], total: N, dashboard_id, is_read_only}
        공유 대시보드 접근 시 is_read_only=true 반환"""

    def create_widget(self, user_id, tenant_id, data) -> dict:
        """위젯 생성 (MAX_WIDGETS_PER_DASHBOARD 제한, 자동 grid_position 배치)
        dashboard_id 미지정 시 기본 대시보드에 생성
        cached_data.rows는 MAX_CACHED_ROWS로 자동 truncate"""

    def update_widget(self, user_id, widget_id, data) -> dict:
        """위젯 수정 (소유권 검증, SQL/chart_config/column_aliases 포함)"""

    def delete_widget(self, user_id, widget_id) -> dict:
        """위젯 삭제 (소유권 검증, DELETE SQL에 AND user_id = %s 이중 검증)"""

    def save_layout(self, user_id, dashboard_id, layout) -> dict:
        """레이아웃 일괄 저장 (소유권 검증, sort_order 인덱스 기반)"""

    def refresh_widget(self, user_id, widget_id) -> dict:
        """위젯 데이터 새로고침
        → sql_executor.execute_sql(stored_sql)
        → pii_service.mask_sql_rows(results)
        → cached_data (MAX_CACHED_ROWS) + last_refreshed_at 갱신"""

    def execute_sql(self, sql: str) -> dict:
        """SQL 테스트 실행 (저장 안함, 미리보기용)
        → {columns, rows, row_count, execution_time_ms} 반환"""

    # ── 내부 메서드 ──

    def _get_dashboard(self, user_id, dashboard_id) -> dict:
        """대시보드 조회 + 소유권 검증 (user_id 불일치 시 NOT_FOUND)"""

    def _get_widget(self, user_id, widget_id) -> dict:
        """위젯 조회 + 소유권 검증 (user_id 불일치 시 NOT_FOUND)"""

    def _auto_grid_position(self, dashboard_id, widget_type) -> dict:
        """기존 위젯의 max(y+h) 아래에 자동 배치 (x=0, y=maxBottom)"""

    def get_or_create_default_dashboard(self, user_id, tenant_id) -> dict:
        """기본 대시보드 조회 또는 자동 생성 (위젯 생성 시 dashboard_id 미지정 케이스)"""
```

**구현 특징**:
- `db_manager`, `sql_executor`, `pii_service`를 lazy import하여 순환 참조 방지
- `_cap_cached_data()`: cached_data 행 수를 MAX_CACHED_ROWS로 제한 + cached_at 타임스탬프 자동 부여
- 위젯 물리 삭제, 대시보드 삭제 시 CASCADE로 하위 위젯 자동 삭제
- `create_dashboard`: 단일 SQL로 COUNT/MAX(sort_order)/default_cnt 동시 조회 (DB 라운드트립 최적화)
- 삭제 쿼리에 `AND user_id = %s` 포함 (사전 소유권 검증 + SQL 레벨 이중 검증)

**참조 패턴**:
- `dashboard_service.py`: 싱글톤 인스턴스, `db_manager.get_cursor()` 패턴
- `user_service.py`: scope 필터, 소유권 검증 패턴
- `sql_executor.py`: SQL 검증/실행 재사용

### 9.6 데이터 접근 보안 (이중 검증 패턴)

대시보드/위젯 삭제 및 수정 시 **이중 검증 패턴**으로 user_id 기반 데이터 격리를 보장한다:

```
1단계: 사전 소유권 검증
  → _get_dashboard(user_id, dashboard_id) 또는 _get_widget(user_id, widget_id)
  → SELECT ... WHERE dashboard_id = %s AND user_id = %s
  → 불일치 시 NOT_FOUND 예외 (404)

2단계: SQL WHERE 절 검증
  → DELETE FROM tb_dashboard WHERE dashboard_id = %s AND user_id = %s
  → DELETE FROM tb_dashboard_widget WHERE widget_id = %s AND user_id = %s
  → 1단계를 통과해도 SQL에서 한번 더 user_id 확인
```

**적용 범위**:
| 작업 | 1단계 (사전 검증) | 2단계 (SQL 조건) |
|------|------------------|-----------------|
| 대시보드 수정 | `_get_dashboard()` | `WHERE dashboard_id=%s AND user_id=%s` |
| 대시보드 삭제 | `_get_dashboard()` | `WHERE dashboard_id=%s AND user_id=%s` |
| 위젯 수정 | `_get_widget()` | `WHERE widget_id=%s AND user_id=%s` |
| 위젯 삭제 | `_get_widget()` | `WHERE widget_id=%s AND user_id=%s` |
| 위젯 새로고침 | `_get_widget()` | 소유권 확인 후 SQL 재실행 |

### 9.7 SQL 실행 보안

모든 SQL 실행 (refresh, execute-sql)에 동일한 보안 체인 적용:

| 보안 레이어 | 적용 | 기존 코드 재사용 |
|------------|------|-----------------|
| SELECT-only 강제 | sqlparse 기반 문 타입 검증 | `sql_executor.validate_sql()` |
| DDL/DML 차단 | FORBIDDEN_KEYWORDS 블랙리스트 | `sql_executor.FORBIDDEN_KEYWORDS` |
| 복수 SQL문 차단 | 세미콜론 분리 다중 쿼리 검증 | `sql_executor.validate_sql()` |
| 테이블 화이트리스트 | 허용 테이블만 조회 가능 | `external_db_manager.get_allowed_tables()` |
| 타임아웃 | 30초 (DB 설정 가능) | `sql_executor.timeout` |
| 행 수 제한 | LIMIT 자동 추가 (DB 설정 가능) | `sql_executor.max_rows` |
| PII 필터 | 결과 데이터 PII 마스킹 | `pii_service.detect_and_mask()` |
| 인증 필수 | JWT 토큰 검증 | `Depends(get_current_active_user)` |
| 소유권 검증 | user_id 기반 위젯 접근 제어 | `_get_widget(user_id, widget_id)` |

### 9.8 Frontend API 클라이언트

```javascript
// frontend/src/api/personalDashboard.js
import api from './index'

export default {
  // 대시보드 CRUD (6개)
  getDashboards: () => api.get('/api/v1/dashboard/dashboards'),
  createDashboard: (data) => api.post('/api/v1/dashboard/dashboards', data),
  updateDashboard: (id, data) => api.put(`/api/v1/dashboard/dashboards/${id}`, data),
  deleteDashboard: (id) => api.delete(`/api/v1/dashboard/dashboards/${id}`),
  setDefaultDashboard: (id) => api.put(`/api/v1/dashboard/dashboards/${id}/default`),
  shareDashboard: (id, data) => api.put(`/api/v1/dashboard/dashboards/${id}/share`, data),

  // 위젯 CRUD (7개)
  getWidgets: (dashboardId) => api.get('/api/v1/dashboard/widgets', { params: dashboardId ? { dashboard_id: dashboardId } : {} }),
  createWidget: (data) => api.post('/api/v1/dashboard/widgets', data),
  updateWidget: (id, data) => api.put(`/api/v1/dashboard/widgets/${id}`, data),
  deleteWidget: (id) => api.delete(`/api/v1/dashboard/widgets/${id}`),
  saveLayout: (layout, dashboardId) => api.put('/api/v1/dashboard/layout', { dashboard_id: dashboardId, layout }),
  refreshWidget: (id) => api.post(`/api/v1/dashboard/widgets/${id}/refresh`),
  executeSql: (sql) => api.post('/api/v1/dashboard/execute-sql', { sql })
}
```

---

## 10. 데이터베이스 설계

### 10.1 신규 테이블

```sql
-- 대시보드 (사용자당 최대 10개)
CREATE TABLE tb_dashboard (
    dashboard_id    SERIAL PRIMARY KEY,
    user_id         INTEGER NOT NULL REFERENCES tb_user(user_id) ON DELETE CASCADE,
    tenant_id       INTEGER REFERENCES tb_tenant(tenant_id),
    name            VARCHAR(100) NOT NULL,
    description     VARCHAR(500),
    is_shared       BOOLEAN NOT NULL DEFAULT false,       -- 공유 여부
    share_scope     VARCHAR(20),                          -- 'all' | 'tenant' | NULL
    is_default      BOOLEAN NOT NULL DEFAULT false,       -- 기본 대시보드 (삭제 불가)
    sort_order      INTEGER NOT NULL DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dashboard_user_id ON tb_dashboard(user_id);
CREATE INDEX idx_dashboard_tenant_id ON tb_dashboard(tenant_id);
CREATE INDEX idx_dashboard_shared ON tb_dashboard(is_shared, share_scope) WHERE is_shared = true;
CREATE UNIQUE INDEX idx_dashboard_default_per_user ON tb_dashboard(user_id) WHERE is_default = true AND is_active = true;

-- 대시보드 위젯 (대시보드당 최대 20개)
CREATE TABLE tb_dashboard_widget (
    widget_id         SERIAL PRIMARY KEY,
    dashboard_id      INTEGER NOT NULL REFERENCES tb_dashboard(dashboard_id) ON DELETE CASCADE,
    user_id           INTEGER NOT NULL REFERENCES tb_user(user_id),
    tenant_id         INTEGER REFERENCES tb_tenant(tenant_id),
    title             VARCHAR(200) NOT NULL,
    widget_type       VARCHAR(20) NOT NULL DEFAULT 'table'
                      CHECK (widget_type IN ('table','bar','hbar','line','pie','scatter','kpi')),
    query             TEXT,                                    -- 원본 자연어 질문
    sql               TEXT,                                    -- 생성된/수정된 SQL
    chart_config      JSONB DEFAULT '{}',                      -- 차트 설정 + column_aliases
    cached_data       JSONB DEFAULT '{}',                      -- 캐시 결과 (최대 500행)
    grid_position     JSONB DEFAULT '{"x":0,"y":0,"w":6,"h":10}',
    sort_order        INTEGER DEFAULT 0,
    is_active         BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dashboard_widget_user ON tb_dashboard_widget(user_id);
CREATE INDEX idx_dashboard_widget_tenant ON tb_dashboard_widget(tenant_id);
CREATE INDEX idx_widget_dashboard_id ON tb_dashboard_widget(dashboard_id);
```

### 10.2 JSONB 필드 스키마

**chart_config**:
```json
{
  "x_column": "department_name",
  "y_columns": ["count", "avg_salary"],
  "pie_top_n": 10,
  "kpi_column": "total_count",
  "kpi_suffix": "명",
  "color_palette": "default",
  "column_aliases": {
    "department_name": "부서명",
    "count": "인원수",
    "avg_salary": "평균 급여"
  }
}
```

**cached_data**:
```json
{
  "columns": ["department_name", "count"],
  "rows": [{"department_name": "개발팀", "count": 42}],
  "row_count": 15,
  "cached_at": "2026-02-26T10:30:00"
}
```

**grid_position**:
```json
{
  "x": 0,
  "y": 0,
  "w": 6,
  "h": 10
}
```

### 10.3 제약 사항

- `cached_data.rows`: 최대 500행까지만 저장 (서비스에서 자동 truncate + `cached_at` 타임스탬프 부여)
- `widget_type`: CHECK ('table', 'bar', 'hbar', 'line', 'pie', 'scatter', 'kpi')
- **사용자당 최대 대시보드 수**: 10개 (서비스 레벨 제한)
- **대시보드당 최대 위젯 수**: 20개 (서비스 레벨 제한)
- `column_aliases`: `chart_config` JSONB 내부에 선택적 저장 (빈 값 = 원본 컬럼명 사용)
- **기본 대시보드**: 삭제 불가, `is_default=true` 유니크 제약 (사용자당 1개)
- **공유 대시보드**: GLOBAL→all/tenant, TENANT→tenant만, USER→공유 불가
- **공유 접근**: 읽기 전용 (새로고침만 허용, 수정/삭제/편집 불가)

---

## 11. 드래그앤드롭 그리드 상세

### 11.1 vue3-grid-layout-next 설정

```javascript
// DashboardGrid.vue
{
  colNum: 12,              // 12컬럼 그리드 (반응형: 8/1)
  rowHeight: 30,           // 행 높이 30px
  margin: [16, 16],        // 간격 16px
  isDraggable: editMode,   // 편집 모드에서만 드래그
  isResizable: editMode,   // 편집 모드에서만 리사이즈
  verticalCompact: true,   // 수직 자동 정렬
  useCssTransforms: true   // CSS transform 사용 (성능)
}
```

- 드래그 핸들: 위젯 헤더 전체 (`.drag-handle` 클래스)
- ResizeObserver로 초기화 타이밍 이슈 해결

### 11.2 그리드 단위 크기

| 위젯 유형 | 기본 w | 기본 h | 최소 w | 최소 h |
|----------|--------|--------|--------|--------|
| table | 6 | 10 | 4 | 6 |
| bar | 6 | 10 | 4 | 6 |
| hbar | 6 | 10 | 4 | 6 |
| line | 6 | 10 | 4 | 6 |
| pie | 5 | 10 | 4 | 6 |
| scatter | 6 | 10 | 4 | 6 |
| kpi | 3 | 5 | 2 | 3 |

### 11.3 NPM 패키지

```bash
npm install vue3-grid-layout-next
```

---

## 12. 스타일 가이드

### 12.1 CSS 변수 (대시보드 전용)

DashboardWidget 등에서 사용하는 CSS 커스텀 속성:

```scss
// 대시보드 전용 변수 (PersonalDashboardView.vue에서 정의)
--dashboard-bg                // 페이지 배경
--dashboard-card              // 위젯 카드 배경
--dashboard-border            // 위젯 테두리
--dashboard-shadow            // 기본 그림자
--dashboard-shadow-hover      // 호버 시 그림자
--dashboard-toolbar-bg        // 툴바 배경
--dashboard-toolbar-border    // 툴바 테두리
--dashboard-text-primary      // 주 텍스트
--dashboard-text-secondary    // 보조 텍스트
--dashboard-text-muted        // 연한 텍스트
--dashboard-edit-border       // 편집 모드 점선 테두리
--dashboard-edit-shadow       // 편집 모드 그림자
--dashboard-edit-bg           // 편집 모드 헤더 배경
```

### 12.2 테마 클래스

```scss
.dashboard-light { /* 라이트 모드 변수 정의 */ }
.dashboard-dark  { /* 다크 모드 변수 정의 */ }
```

테마 결정 로직:
- `auto`: 사용자 전역 설정 (`app/isUserDarkMode`)을 따름
- `light`: 강제 라이트 모드
- `dark`: 강제 다크 모드
- 테마 설정은 localStorage에 독립 저장 (`winai_dashboard_theme`)

### 12.3 ECharts 테마

`useChartOptions.js`의 `buildChartOption()`에서 `darkMode` prop 기반 색상 결정:
- `darkMode === true`: textColor=#e5e5e5, subTextColor=#8c8c8c, borderColor=#303030
- `darkMode === false`: textColor=#333333, subTextColor=#666666, borderColor=#dcdcdc
- `darkMode === null`: CSS 변수에서 동적 추출

---

## 13. 구현 순서

### Phase 1: 프론트엔드 프로토타입 ✅ 완료

| 순서 | 작업 | 산출물 | 상태 |
|------|------|--------|------|
| 1-1 | ChartBuilder에서 차트 로직 추출 | `composables/useChartOptions.js` | ✅ |
| 1-2 | Vuex 모듈 작성 (localStorage) | `store/modules/dashboard.js` | ✅ |
| 1-3 | 위젯 렌더러 컴포넌트 | `widgets/WidgetTable/Chart/Kpi.vue` | ✅ |
| 1-4 | DashboardWidget 컨테이너 | `DashboardWidget.vue` | ✅ |
| 1-5 | DashboardGrid 그리드 래퍼 | `DashboardGrid.vue` | ✅ |
| 1-6 | DashboardToolbar, EmptyState | 툴바 + 빈 상태 | ✅ |
| 1-7 | PersonalDashboardView 조립 | 메인 페이지 | ✅ |
| 1-8 | 라우터 등록 (`/dashboard`) | `router/index.js` | ✅ |
| 1-9 | SaveToDashboardModal | Chat에서 저장 모달 | ✅ |
| 1-10 | UserChatMessage 수정 | "대시보드에 추가" 버튼 | ✅ |
| 1-11 | WidgetEditModal | 위젯 수정 모달 | ✅ |
| 1-12 | AddWidgetModal | 히스토리 기반 추가 | ✅ |
| 1-13 | UserChatSidebar 수정 | "대시보드" 메뉴 | ✅ |

### Phase 2: 백엔드 API + DB 연동 ✅ 완료

| 순서 | 작업 | 산출물 | 상태 |
|------|------|--------|------|
| 2-1 | DB 테이블 생성 (`tb_dashboard_widget`) | DDL 스크립트 (`docs/sql/psql-hermes_db.sql` 추가) | ✅ |
| 2-2 | Pydantic 모델 작성 | `app/models/personal_dashboard.py` | ✅ |
| 2-3 | Service 계층 작성 (CRUD + refresh + execute-sql) | `app/api/services/personal_dashboard_service.py` | ✅ |
| 2-4 | Route 작성 (7개 엔드포인트) + main.py 등록 | `app/api/routes/personal_dashboard.py` | ✅ |
| 2-5 | API 클라이언트 작성 | `frontend/src/api/personalDashboard.js` | ✅ |
| 2-6 | Vuex 스토어 API 연동 (localStorage → API) | `store/modules/dashboard.js` 수정 | ✅ |

### Phase 3: 컬럼 별칭 + SQL 편집 ✅ 완료

| 순서 | 작업 | 산출물 | 상태 |
|------|------|--------|------|
| 3-1 | `buildChartOption()`에 columnAliases 파라미터 추가 | `useChartOptions.js` 수정 | ✅ |
| 3-2 | WidgetTable에 columnAliases prop + 헤더 매핑 | `WidgetTable.vue` 수정 | ✅ |
| 3-3 | WidgetChart에 columnAliases prop 전달 | `WidgetChart.vue` 수정 | ✅ |
| 3-4 | DashboardWidget에서 columnAliases 하위 전달 | `DashboardWidget.vue` 수정 | ✅ |
| 3-5 | SaveToDashboardModal에 컬럼 별칭 입력 UI | `SaveToDashboardModal.vue` 수정 | ✅ |
| 3-6 | WidgetEditModal에 SQL 편집 UI + 컬럼 별칭 UI | `WidgetEditModal.vue` 수정 | ✅ |
| 3-7 | AddWidgetModal에 탭 UI + 직접 질문 모드 추가 | `AddWidgetModal.vue` 수정 | ✅ |

### Phase 4: 테스트 ✅ 완료

| 순서 | 작업 | 검증 항목 | 상태 |
|------|------|----------|------|
| 4-1 | 대시보드 CRUD 테스트 | 생성/수정/삭제/기본 설정/최대 제한 (`test_12_personal_dashboard.py`) | ✅ |
| 4-2 | 대시보드 공유 테스트 | 공유 설정/해제, 읽기 전용, 권한 검증 | ✅ |
| 4-3 | 멀티 대시보드 위젯 테스트 | 대시보드별 위젯 분리, CASCADE 삭제, 접근 제어 | ✅ |
| 4-4 | 위젯 CRUD 테스트 | 생성(bar/kpi), 수정(제목/별칭), 삭제, 잘못된 타입 | ✅ |
| 4-5 | Layout + SQL 테스트 | 레이아웃 저장, 유효/금지 SQL 실행, 빈 SQL | ✅ |
| 4-6 | 인증 테스트 | 미인증 접근 시 401 응답 확인 (대시보드/위젯/SQL 5개 엔드포인트) | ✅ |

---

## 14. 리스크 및 대응

| 리스크 | 영향 | 대응 | 상태 |
|--------|------|------|------|
| vue3-grid-layout-next 호환성 | 드래그앤드롭 불가 | ResizeObserver로 초기화 타이밍 해결 | ✅ 해결 |
| cached_data JSONB 크기 | DB 성능 저하 | 최대 500행 제한, 서비스에서 자동 truncate | ✅ 해결 |
| SQL 재실행 실패 | 위젯 에러 상태 | ElMessage.error 표시, 재시도 가능 | ✅ 해결 |
| 다크/라이트 모드 전환 | 차트 색상 불일치 | darkMode prop 기반 직접 색상 결정 | ✅ 해결 |
| 차트 로직 중복 | 유지보수 부담 | useChartOptions.js composable 공유 | ✅ 해결 |
| localStorage 용량 제한 | 위젯 데이터 유실 | 백엔드 DB 연동 완료 (tb_dashboard_widget) | ✅ 해결 |
| 브라우저간 데이터 미동기화 | 다른 기기에서 접근 불가 | 백엔드 DB 연동 완료 | ✅ 해결 |
| SQL 편집 보안 (SQL Injection) | 악의적 SQL 실행 | sql_executor 보안 체인 재사용 (SELECT-only, 키워드 블랙리스트, 테이블 화이트리스트, 타임아웃) | ✅ 해결 |
| SQL 편집 후 저장 실수 | 잘못된 SQL 영구 저장 | "SQL 실행" 성공 필수 → 미실행 SQL은 저장 시 경고 | ✅ 해결 |
| 컬럼 별칭 매핑 깨짐 | SQL 변경 시 컬럼명 불일치 | SQL 편집 후 실행 시 새 columns 반환 → 기존 aliases와 자동 교차 검증 | ✅ 해결 |
| PII 노출 | SQL 결과에 개인정보 포함 | pii_service.mask_sql_rows() 적용 (refresh, execute-sql 모두) | ✅ 해결 |
| 사용자 전환 시 상태 잔존 | 이전 사용자 dashboardId로 API 호출 | `clearState` mutation + auth.js logout 시 dispatch | ✅ 해결 |
| 마지막 대시보드 삭제 | currentDashboardId 미초기화 | else 분기에서 null/[] 초기화 처리 | ✅ 해결 |
| SaveToDashboardModal dashboard_id 덮어쓰기 | 다른 대시보드에 저장 시 현재 대시보드로 변경 | saveWidget에서 `!data.dashboard_id` 조건 검사 | ✅ 해결 |
| 동시 레이아웃 저장 충돌 | 다른 탭에서 동시 수정 | 마지막 쓰기 우선 정책 (last-write-wins) | ✅ 현행 방식 |
| NL2SQL 직접 실행 장시간 대기 | 모달 내 UX 저하 | SSE 진행 상황 실시간 표시 + AbortController 기반 실행 취소 버튼 | ✅ 해결 |
| NL2SQL 직접 실행 실패 | 위젯 생성 불가 | 에러 메시지 인라인 표시 + 질문 재입력 유도 (모달 닫지 않음) | ✅ 해결 |

---

## 15. 내보내기 기능

### 15.1 개요

대시보드 위젯 데이터를 다양한 형식으로 내보내는 기능을 제공한다.
위젯 단위 내보내기와 대시보드 전체 내보내기를 지원한다.

### 15.2 구현 상태

| 기능 | 형식 | 범위 | 의존성 | 상태 |
|------|------|------|--------|------|
| 위젯 캡처 | PNG | 위젯 전체 | html2canvas | ✅ |
| 대시보드 PNG | PNG | 대시보드 전체 | html2canvas | ✅ |
| 대시보드 PDF | PDF | 대시보드 전체 | html2canvas + jsPDF | ✅ |
| 멀티시트 Excel | XLSX | 대시보드 전체 | openpyxl (백엔드) | ❌ 미구현 |
| 정형 PDF 보고서 | PDF | 대시보드 전체 | WeasyPrint (백엔드) | ❌ 미구현 |
| Word 보고서 | DOCX | 대시보드 전체 | python-docx (백엔드) | ❌ 미구현 |

### 15.3 위젯 단위 내보내기 UI

비편집 모드에서 각 위젯 헤더에 이미지 다운로드 버튼 표시:

```
[뷰전환]  [📷 이미지 다운로드]  [새로고침]
```

- **방식**: `html2canvas`로 위젯 DOM 전체 캡처 → PNG 다운로드
- **범위**: 위젯 루트 DOM 전체 (헤더 + 콘텐츠 + 푸터)

### 15.4 내보내기 상세

#### 15.4.1 위젯 캡처 (PNG)

- **방식**: `html2canvas(element)` → Canvas → `toDataURL('image/png')` → `<a>` 다운로드
- **범위**: DashboardWidget DOM 전체
- **파일명**: 동적 생성

### 15.5 대시보드 전체 내보내기

#### 15.5.1 PNG/PDF 내보내기 (스냅샷)

- **위치**: DashboardToolbar 내보내기 드롭다운 (위젯 1개 이상일 때 표시)
- **PNG**: `html2canvas`로 `.dashboard-content` DOM 캡처 → PNG 다운로드
- **PDF**: `html2canvas`로 캡처 → `jsPDF`로 PDF 생성 → 다운로드
- **형식**: A4 landscape (가로)
- **로딩**: 버튼에 `:loading="exporting"` 상태 표시

### 15.6 NPM 패키지

| 패키지 | 용도 |
|--------|------|
| `html2canvas` | DOM → Canvas 캡처 (위젯/대시보드 PNG) |
| `jspdf` | 클라이언트 사이드 PDF 생성 |

### 15.7 수정 파일 요약

| 파일 | 변경 내용 | 상태 |
|------|----------|------|
| `frontend/src/components/dashboard-personal/DashboardWidget.vue` | 이미지 다운로드 버튼 + `html2canvas` 핸들러 | ✅ |
| `frontend/src/components/dashboard-personal/DashboardToolbar.vue` | 내보내기 드롭다운 (PNG/PDF) + exporting prop | ✅ |
| `frontend/src/views/user/PersonalDashboardView.vue` | PNG/PDF 핸들러 + content ref | ✅ |
| `frontend/package.json` | html2canvas, jspdf 추가 | ✅ |

---

## 16. 컬럼 별칭(Column Aliases) 기능 ✅ 구현 완료

### 16.1 개요

NL2SQL 결과의 컬럼명은 DB 원본 그대로(영문, snake_case)이므로 사용자가 읽기 어렵다.
컬럼 별칭 기능으로 원본 컬럼명을 원하는 표시명으로 매핑하여 차트와 테이블에서 사용한다.

- **기본 동작**: 별칭 미설정 시 원본 컬럼명 표시 (기존 동작 유지)
- **매핑 방향**: 영문→한글, 영문→영문, 한글→한글 모두 가능
- **저장 위치**: `chart_config.column_aliases` (JSONB 내부, 별도 DB 컬럼 불필요)

```
예시:
  dept_nm      → "부서명"
  emp_cnt      → "Employee Count"
  avg_salary   → "평균 급여"
  department   → "Department Name"
```

### 16.2 데이터 구조

```json
// chart_config 내부
{
  "x_column": "dept_nm",
  "y_columns": ["emp_cnt", "avg_salary"],
  "column_aliases": {
    "dept_nm": "부서명",
    "emp_cnt": "인원수",
    "avg_salary": "평균 급여"
  }
}
```

- **키**: 원본 컬럼명 (DB 결과의 실제 컬럼명)
- **값**: 표시할 별칭 (빈 문자열 또는 null이면 원본 사용)
- **전체 컬럼 필수 아님**: 별칭을 설정한 컬럼만 포함

### 16.3 별칭 해석 함수

모든 위젯 컴포넌트에서 공통 사용하는 별칭 해석 헬퍼:

```javascript
// 사용 패턴 (각 컴포넌트 내부)
const getAlias = (col) => {
  return props.columnAliases?.[col] || col
}
```

또는 `useChartOptions.js` 내부에서:

```javascript
function buildChartOption({ ..., columnAliases }) {
  const getAlias = (col) => columnAliases?.[col] || col
  // ... 범례, 시리즈명, 축명에 getAlias 적용
}
```

### 16.4 적용 지점 (6곳)

| # | 위치 | 파일 | 현재 코드 | 변경 후 |
|---|------|------|----------|---------|
| 1 | 테이블 헤더 | `WidgetTable.vue:16` | `:label="col"` | `:label="getAlias(col)"` |
| 2 | 차트 범례 | `useChartOptions.js:198` | `data: yCols` | `data: yCols.map(c => getAlias(c))` |
| 3 | 차트 시리즈명 | `useChartOptions.js:243` | `name: col` | `name: getAlias(col)` |
| 4 | 산점도 축 이름 | `useChartOptions.js:168` | `name: xColumn` | `name: getAlias(xColumn)` |
| 5 | 산점도 툴팁 | `useChartOptions.js:163` | `${xColumn}` | `${getAlias(xColumn)}` |
| 6 | KPI 표시 | `WidgetKpi.vue` | 컬럼명 직접 사용 | `getAlias(kpiColumn)` |

**참고**: 모달 컴포넌트의 컬럼 선택 드롭다운(`:label="col"`)은 원본 컬럼명을 유지한다.
편집 UI에서는 원본 컬럼명을 보여야 매핑 관계가 명확하기 때문이다.

### 16.5 편집 UI

#### SaveToDashboardModal (저장 시 별칭 설정)

차트/테이블 설정 영역 하단에 "컬럼 표시명" 접이식 섹션 추가:

```
┌─────────────────────────────────────────┐
│ ▼ 컬럼 표시명 (선택)                       │
│                                         │
│  dept_nm    [부서명            ]         │
│  emp_cnt    [인원수            ]         │
│  avg_salary [                  ]  ← 빈칸 = 원본 사용 │
└─────────────────────────────────────────┘
```

- 모든 columns에 대해 입력 필드 표시
- placeholder에 원본 컬럼명 표시 (빈칸 = 원본 사용임을 시각적으로 안내)
- 테이블 유형에서도 표시 (테이블 헤더에 적용되므로)
- 접이식(Collapse) 기본 접힌 상태 → 필요할 때만 펼침

#### WidgetEditModal (수정 시 별칭 변경)

기존 "표시 설정" 섹션 내에 동일한 UI 추가:
- 기존 저장된 `column_aliases` 값을 폼에 로드
- SQL 편집 후 실행 시 새 columns 목록과 교차 검증 (아래 16.6 참조)

### 16.6 SQL 편집 시 별칭 동기화

SQL을 수정하면 결과 컬럼이 변경될 수 있으므로 별칭 매핑 동기화가 필요:

```
1. 사용자가 SQL 수정 → "SQL 실행" 클릭
2. 실행 결과에서 새 columns 목록 획득
3. 기존 column_aliases와 비교:
   - 여전히 존재하는 컬럼: 별칭 유지
   - 새로 추가된 컬럼: 빈칸으로 표시 (원본 사용)
   - 삭제된 컬럼: aliases에서 자동 제거
4. 별칭 입력 UI를 새 columns 기준으로 갱신
```

### 16.7 prop 전달 경로

```
DashboardWidget.vue
  ├─ widget.chart_config.column_aliases  (JSONB에서 추출)
  │
  ├─→ WidgetTable   :column-aliases="widget.chart_config?.column_aliases"
  ├─→ WidgetChart   :column-aliases="widget.chart_config?.column_aliases"
  └─→ WidgetKpi     :column-aliases="widget.chart_config?.column_aliases"
```

각 위젯 컴포넌트는 `columnAliases` prop을 선언하고,
내부에서 `getAlias()` 헬퍼를 통해 표시명을 결정한다.

### 16.8 제약 사항

- 별칭 최대 길이: 50자 (UI 표시 공간 제한)
- 빈 문자열/null → 원본 컬럼명 사용
- 중복 별칭 허용 (다른 컬럼에 같은 별칭 가능 — 사용자 책임)
- 별칭은 표시 전용이며, 데이터 바인딩(`prop`, `row[col]`)에는 영향 없음

---

## 17. SQL 편집 기능 ✅ 구현 완료

### 17.1 개요

저장된 위젯의 SQL을 WidgetEditModal에서 수정하고, 테스트 실행하여 결과를 미리본 뒤 저장하는 기능.
기존 NL2SQL 파이프라인의 보안 체인(`sql_executor`)을 재사용하여 안전한 SQL 실행을 보장한다.

### 17.2 UI 레이아웃 (WidgetEditModal 내)

```
┌─────────────────────────────────────────────────────┐
│ 위젯 수정                                              │
│                                                     │
│ [기본 정보]  제목 / 위젯 유형 / 차트 설정                    │
│                                                     │
│ ▼ 쿼리 정보                                            │
│ ┌─────────────────────────────────────────────────┐ │
│ │ 원본 질문: 2024년 부서별 인원수는?                      │ │
│ │                                                 │ │
│ │ SQL:                                            │ │
│ │ ┌───────────────────────────────────────────┐   │ │
│ │ │ SELECT department_name, COUNT(*) as cnt   │   │ │
│ │ │ FROM employee                             │   │ │
│ │ │ WHERE hire_date >= '2024-01-01'           │   │ │
│ │ │ GROUP BY department_name                  │   │ │
│ │ └───────────────────────────────────────────┘   │ │
│ │                         [SQL 실행]  [SQL 초기화]   │ │
│ │                                                 │ │
│ │ ┌─ 실행 결과 (15건, 0.12초) ──────────────────┐   │ │
│ │ │ department_name  │ cnt                     │   │ │
│ │ │ ─────────────────┼────                     │   │ │
│ │ │ 개발팀            │ 42                      │   │ │
│ │ │ 인사팀            │ 15                      │   │ │
│ │ │ ...              │ ...                     │   │ │
│ │ └───────────────────────────────────────────┘   │ │
│ └─────────────────────────────────────────────────┘ │
│                                                     │
│ ▼ 컬럼 표시명 (선택)                                    │
│   department_name  [부서명           ]               │
│   cnt              [인원수           ]               │
│                                                     │
│                              [취소]  [저장]           │
└─────────────────────────────────────────────────────┘
```

### 17.3 SQL 편집 컴포넌트 상세

| 요소 | 구현 | 비고 |
|------|------|------|
| SQL 입력 | `<el-input type="textarea" :rows="6">` | `font-family: monospace` |
| SQL 실행 버튼 | `<el-button>` | `POST /api/v1/dashboard/execute-sql` |
| SQL 초기화 버튼 | `<el-button>` | 원본 SQL로 복원 (`widget.sql`) |
| 실행 결과 테이블 | `<el-table :data="previewRows" size="small">` | 최대 10행 표시 |
| 실행 시간 | `execution_time_ms` | "15건, 0.12초" 형태 |
| 에러 표시 | `<el-alert type="error">` | SQL 검증/실행 오류 메시지 |
| 로딩 상태 | `<el-button :loading="executing">` | 실행 중 스피너 |

### 17.4 상태 관리

```javascript
// WidgetEditModal 내부 상태
const sqlText = ref('')          // 현재 SQL 텍스트
const originalSql = ref('')      // 원본 SQL (초기화용)
const sqlModified = ref(false)   // SQL 변경 여부
const sqlExecuted = ref(false)   // SQL 실행 완료 여부
const executing = ref(false)     // 실행 중 로딩

// SQL 실행 결과
const previewColumns = ref([])
const previewRows = ref([])
const previewRowCount = ref(0)
const executionTimeMs = ref(0)
const executeError = ref('')
```

### 17.5 SQL 편집 흐름

```
1. 모달 열기
   → sqlText = widget.sql
   → originalSql = widget.sql
   → sqlModified = false, sqlExecuted = false

2. SQL 텍스트 수정
   → watch(sqlText) → sqlModified = (sqlText !== originalSql)
   → sqlExecuted = false (수정하면 실행 결과 무효화)

3. [SQL 실행] 클릭
   → executing = true
   → POST /api/v1/dashboard/execute-sql { sql: sqlText }
   → 성공:
     - previewColumns, previewRows, previewRowCount, executionTimeMs 설정
     - sqlExecuted = true
     - executeError = ''
     - 컬럼 별칭 UI 갱신 (새 columns 기준, 16.6 참조)
   → 실패:
     - executeError = 에러 메시지
     - sqlExecuted = false
   → executing = false

4. [SQL 초기화] 클릭
   → sqlText = originalSql
   → sqlModified = false, sqlExecuted = false
   → 실행 결과 초기화

5. [저장] 클릭
   → if (sqlModified && !sqlExecuted):
       ElMessage.warning('수정한 SQL을 먼저 실행해주세요')
       return
   → if (sqlModified && sqlExecuted):
       PUT /api/v1/dashboard/widgets/{id} {
         sql: sqlText,
         cached_data: { columns: previewColumns, rows: previewRows, ... },
         chart_config: { ..., column_aliases: updatedAliases }
       }
   → else:
       PUT /api/v1/dashboard/widgets/{id} {
         title, widget_type, chart_config (별칭 포함)
       }
```

### 17.6 보안 체인

SQL 편집 기능은 기존 `sql_executor.py`의 보안 체인을 그대로 재사용:

```
사용자 입력 SQL
  → sql_executor.validate_sql(sql)
    ├── sqlparse: SELECT문만 허용
    ├── FORBIDDEN_KEYWORDS 검사 (DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE...)
    ├── 복수 SQL문 차단 (세미콜론 분리)
    └── 테이블 화이트리스트 검증 (external_db_manager.get_allowed_tables())
  → sql_executor.execute_sql(sql, timeout=30, max_rows=설정값)
    ├── LIMIT 자동 추가 (없을 경우)
    ├── 30초 타임아웃
    └── 외부 DB 연결 (external_db_manager)
  → pii_service.detect_and_mask(results)
    └── PII 감지 및 마스킹
  → 결과 반환
```

### 17.7 에러 처리

| 에러 유형 | 원인 | 사용자 메시지 |
|----------|------|-------------|
| VALIDATION | SELECT문이 아님 | "SELECT 쿼리만 실행할 수 있습니다" |
| VALIDATION | 금지 키워드 포함 | "허용되지 않는 SQL 키워드가 포함되어 있습니다" |
| VALIDATION | 허용되지 않은 테이블 | "접근 권한이 없는 테이블입니다: {table_name}" |
| TIMEOUT | 30초 초과 | "쿼리 실행 시간이 초과되었습니다 (30초)" |
| DB_ERROR | SQL 문법 오류 | "SQL 실행 오류: {db_error_message}" |
| DB_ERROR | 연결 실패 | "데이터베이스 연결에 실패했습니다" |

### 17.8 제약 사항

- SELECT문만 허용 (DML/DDL 완전 차단)
- 실행 결과는 최대 500행까지 cached_data에 저장
- 미리보기는 최대 10행까지 표시
- SQL 편집 후 반드시 실행 성공해야 저장 가능
- PII 마스킹은 서버에서 적용 (프론트엔드에서 추가 처리 불필요)
- 원본 질문(`query` 필드)은 수정 불가 (SQL만 수정 가능)

---

## 18. 테스트

### 18.1 Backend 테스트 (구현 완료 - 37 TC)

**파일**: `tests/test_12_personal_dashboard.py`

6개의 테스트 클래스, 총 37개 테스트 케이스:

| 클래스 | TC 수 | 테스트 항목 |
|--------|-------|-----------|
| `TestDashboardCRUD` | 8 | 대시보드 생성, 목록 조회(my/shared 분리), 수정(이름/설명), 기본 대시보드 변경, 기본 대시보드 삭제 불가, 일반 대시보드 삭제, 최대 10개 제한 |
| `TestDashboardShare` | 5 | 공유 설정(all/tenant), 공유 해제, 공유 대시보드 읽기 전용 확인, 권한 없는 사용자 공유 시도 실패 |
| `TestMultiDashboardWidget` | 6 | 다른 대시보드에 위젯 생성, 대시보드별 위젯 목록 분리, 대시보드 삭제 시 위젯 CASCADE 삭제, 다른 사용자 대시보드 접근 불가 |
| `TestWidgetCRUD` | 8 | 위젯 생성(bar/kpi), 잘못된 타입(422), 목록 조회, 수정(제목/별칭), 존재하지 않는 위젯 수정(에러), 삭제 |
| `TestLayoutAndSQL` | 5 | 레이아웃 저장(updated_count), 잘못된 widget_id, 유효 SQL 실행, 금지 SQL(DROP) 차단, 빈 SQL(422) |
| `TestAuth` | 5 | 미인증 접근: 대시보드 목록/생성, 위젯 목록/생성, execute-sql → 모두 401 |

**테스트 환경**:
- `admin` (admin/Win1234!) + `user01` (user01/Win1234!) 사용
- 각 테스트 클래스별 fixture로 테스트 데이터 자동 생성/정리
- `conftest.py`의 `assert_success`, `assert_error` 헬퍼 활용

### 18.2 실행 방법

```bash
# 개인 대시보드 테스트만 실행
pytest tests/test_12_personal_dashboard.py -v

# 전체 테스트 (순서 의존성 있으므로 순서대로 실행 권장)
pytest tests/ -v

# 최근 실행 결과: 37 passed in 5.26s
```
