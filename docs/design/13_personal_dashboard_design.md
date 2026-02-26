# 개인 BI 대시보드 설계서

> **현행화 일자**: 2026-02-26
> **구현 상태**: 프론트엔드 프로토타입 완료 (localStorage 기반), 백엔드 미구현

---

## 1. 개요

### 1.1 목적

사용자 화면(Chat)에서 NL2SQL 쿼리 결과를 개인화하여 **경량 BI 도구** 역할을 하는 "개인 대시보드" 기능을 제공한다.
자연어로 질문하고, 결과를 저장하고, 드래그앤드롭으로 자신만의 대시보드를 구성할 수 있다.

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
| 데이터 갱신 | 수동 새로고침 | 성능 부담 최소화, 캐시 데이터 기본 표시 |
| 위젯 유형 | 테이블/Bar/H-Bar/Line/Pie/Scatter/KPI | 다양한 BI 시각화 커버 |
| 테마 | auto/light/dark 3단계 토글 | 사용자 기본 다크모드와 독립 제어 가능 |
| 컬러 팔레트 | 6종 프리셋 (기본/비비드/파스텔/따뜻한/시원한/어스톤) | 위젯별 차트 색상 개인화 |
| 저장소 (현재) | localStorage | 프로토타입 단계, 백엔드 연동 전 |

### 1.4 구현 상태 요약

| 영역 | 상태 | 비고 |
|------|------|------|
| 프론트엔드 컴포넌트 | ✅ 완료 | 12개 컴포넌트 + composable |
| Vuex 스토어 | ✅ 완료 | localStorage 기반 CRUD |
| 라우터 | ✅ 완료 | `/dashboard` 등록 |
| Chat 연동 | ✅ 완료 | UserChatMessage "대시보드에 추가" 버튼 |
| 사이드바 메뉴 | ✅ 완료 | UserChatSidebar "대시보드" 항목 |
| 백엔드 API | ❌ 미구현 | 설계만 완료 |
| 데이터베이스 | ❌ 미구현 | DDL 설계만 완료 |

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
│                          [취소]  [저장]                           │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼  저장
   store.dispatch('dashboard/saveWidget', config)
   → localStorage 저장 (프로토타입)
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
│  → localStorage 로드 (없으면 빈 배열)                            │
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
│  "레이아웃 저장" → localStorage 저장                        │
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
│  → [프로토타입] 1초 딜레이 시뮬레이션 (실제 SQL 재실행 없음) │
│  → last_refreshed_at 타임스탬프 갱신                        │
│                                                            │
│  [향후 백엔드 연동 시]                                      │
│  → POST /api/v1/dashboard/widgets/{id}/refresh              │
│  → 저장된 SQL을 External DB에서 재실행                      │
│  → 최신 데이터로 차트/테이블 갱신                           │
│  → 실패 시: 에러 오버레이 + "재시도" 버튼                   │
└────────────────────────────────────────────────────────────┘
```

### 2.5 Flow E: 대시보드에서 직접 위젯 추가

```
┌────────────────────────────────────────────────────────────┐
│  편집 모드에서 "+" 플로팅 버튼 클릭                          │
│  → AddWidgetModal 열림                                      │
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
│    → 위젯 생성 + localStorage에 저장                        │
└────────────────────────────────────────────────────────────┘
```

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

```
┌──────────────────────────────────────────────────────────────────────┐
│  TOOLBAR                                                             │
│  [←] [📊] BI 대시보드                                                │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                                                                      │
│                         [📊 큰 아이콘]                               │
│                                                                      │
│                     위젯이 없습니다                                   │
│           채팅에서 NL2SQL 결과를 대시보드에                           │
│                 추가해보세요                                          │
│                                                                      │
│               [채팅으로 이동]  [데모 위젯 로드]                        │
│                                                                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

- "데모 위젯 로드": 6개의 목업 위젯을 로드하여 기능 체험 가능

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

### 3.5 WidgetEditModal (위젯 수정)

SaveToDashboardModal과 동일 구조에 기존 위젯 설정을 초기값으로 로드:
- 제목, 위젯 유형, 차트 설정(X/Y축, 컬러 팔레트), KPI 설정 변경 가능
- 쿼리/SQL은 읽기 전용 표시

### 3.6 AddWidgetModal (대시보드에서 직접 추가)

```
┌──────────────────────────────────────────────────────┐
│  위젯 추가                                    [X]    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  대화 히스토리                                       │
│  ┌──────────────────────────────────────────┐        │
│  │ 대화를 선택하세요                     ▼  │        │
│  └──────────────────────────────────────────┘        │
│  (최근 100개 세션, nl2sql/agent 필터, 검색 가능)     │
│                                                      │
│  쿼리 결과 선택 (세션 선택 후 표시)                  │
│  ┌──────────────────────────────────────────┐        │
│  │ 쿼리 결과를 선택하세요                ▼  │        │
│  └──────────────────────────────────────────┘        │
│  (trace_data.sql_result가 있는 레코드만 표시)        │
│  (결과 1개 시 자동 선택)                             │
│                                                      │
│  ── 실행 결과 (선택 후 표시) ──                      │
│  ┌──────────────────────────────────────────┐        │
│  │ 부서명    │ 직원수                       │        │
│  │ 개발팀    │ 42                           │        │
│  │ 인사팀    │ 15                           │        │
│  └──────────────────────────────────────────┘        │
│  ... 외 N건                                          │
│                                                      │
│  (이하 SaveToDashboardModal과 동일한 위젯 설정 UI)   │
│                                                      │
├──────────────────────────────────────────────────────┤
│                           [취소]  [추가 (Primary)]   │
└──────────────────────────────────────────────────────┘
```

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
│   ├── 채팅으로 이동 버튼 (ArrowLeft)
│   ├── 테마 토글 버튼 (Monitor/Sunny/Moon)
│   ├── 전체 새로고침 버튼
│   ├── 편집 모드 전환 버튼
│   └── 편집 모드: 취소 / 레이아웃 저장 버튼
├── DashboardEmptyState.vue (위젯 0개일 때)
│   ├── 채팅으로 이동 버튼
│   └── 데모 위젯 로드 버튼
├── DashboardGrid.vue (vue3-grid-layout-next 래퍼)
│   └── DashboardWidget.vue (v-for 각 위젯)
│       ├── 위젯 헤더 (타입 아이콘, 제목, 뷰전환, 새로고침/수정/삭제)
│       ├── 위젯 콘텐츠 (동적):
│       │   ├── WidgetTable.vue    (table 또는 뷰전환 시)
│       │   ├── WidgetChart.vue    (bar/hbar/line/pie/scatter 또는 뷰전환 시)
│       │   └── WidgetKpi.vue      (kpi)
│       └── 위젯 푸터 (마지막 갱신 타임스탬프)
├── WidgetEditModal.vue (위젯 수정)
├── AddWidgetModal.vue (히스토리 기반 위젯 추가)
└── [+] FAB 플로팅 버튼 (편집 모드 시)

UserChatMessage.vue (기존 파일 수정)
└── SaveToDashboardModal.vue (NL2SQL 결과 → 대시보드 저장)
```

### 6.2 파일 구조 (✅ = 구현 완료, ❌ = 미구현)

```
frontend/src/
├── views/user/
│   └── PersonalDashboardView.vue          ✅ 메인 대시보드 페이지
├── components/dashboard-personal/
│   ├── DashboardGrid.vue                  ✅ vue3-grid-layout-next 래퍼
│   ├── DashboardWidget.vue                ✅ 위젯 컨테이너 + 뷰전환
│   ├── DashboardEmptyState.vue            ✅ 빈 상태 + 데모 로드
│   ├── DashboardToolbar.vue               ✅ 상단 툴바 + 테마 토글
│   ├── SaveToDashboardModal.vue           ✅ Chat에서 저장 모달
│   ├── WidgetEditModal.vue                ✅ 위젯 수정 모달
│   ├── AddWidgetModal.vue                 ✅ 히스토리 기반 추가 모달
│   └── widgets/
│       ├── WidgetTable.vue                ✅ 테이블 렌더러
│       ├── WidgetChart.vue                ✅ 차트 렌더러 (Bar/H-Bar/Line/Pie/Scatter)
│       └── WidgetKpi.vue                  ✅ KPI 렌더러
├── composables/
│   └── useChartOptions.js                 ✅ 차트 옵션 공유 로직
├── store/modules/
│   └── dashboard.js                       ✅ Vuex 대시보드 모듈 (localStorage)
├── api/
│   └── (personalDashboard.js)             ❌ 미생성 (localStorage 직접 사용)
└── router/index.js                        ✅ /dashboard 라우트 등록

app/
├── api/
│   ├── routes/
│   │   └── (personal_dashboard.py)        ❌ 미구현
│   └── services/
│       └── (personal_dashboard_service.py) ❌ 미구현
├── models/
│   └── (personal_dashboard.py)            ❌ 미구현
└── main.py                                ❌ 라우터 미등록
```

### 6.3 수정된 기존 파일

| 파일 | 변경 내용 | 상태 |
|------|----------|------|
| `frontend/src/router/index.js` | `/dashboard` 라우트 추가 | ✅ |
| `frontend/src/store/index.js` | dashboard 모듈 등록 | ✅ |
| `frontend/src/components/user/UserChatMessage.vue` | "대시보드에 추가" 버튼 추가 | ✅ |
| `frontend/src/components/user/UserChatSidebar.vue` | "대시보드" 네비게이션 메뉴 추가 | ✅ |
| `frontend/src/components/chart/ChartBuilder.vue` | 차트 옵션 로직을 composable로 추출 | ✅ |
| `app/main.py` | personal_dashboard 라우터 등록 | ❌ |

---

## 7. 상태 관리 (Vuex)

### 7.1 Dashboard Store 모듈

**파일**: `store/modules/dashboard.js`
**저장소**: localStorage (키: `mureum_dashboard_widgets`, `mureum_dashboard_theme`)

```javascript
state: () => ({
  widgets: [],             // 위젯 목록 (localStorage에서 로드)
  isLoading: false,        // 초기 로딩 상태
  editMode: false,         // 편집 모드 여부
  pendingLayout: null,     // 편집 모드 진입 시 백업 (취소용)
  refreshingWidgets: {},   // { widgetId: true/false } 개별 위젯 로딩
  dashboardTheme: 'auto'   // 'auto' | 'light' | 'dark'
})

// Getters
widgetCount               // widgets.length
isEditMode                // editMode
widgetById(id)            // 위젯 검색
isWidgetRefreshing(id)    // 새로고침 중 여부
dashboardTheme            // 현재 테마
gridLayout                // vue-grid-layout용 [{i, x, y, w, h, minW, minH}] 변환

// Actions
fetchWidgets()            // localStorage 로드 (빈 경우 빈 배열)
saveWidget(config)        // 위젯 생성 → localStorage 저장
updateWidget(id, updates) // 위젯 수정 → localStorage 저장
deleteWidget(id)          // 위젯 삭제 → localStorage 저장
saveLayout(layout)        // 레이아웃 일괄 저장
refreshWidget(id)         // [프로토타입] 1초 딜레이 시뮬레이션
refreshAllWidgets()       // 모든 위젯 순차 새로고침
enterEditMode()           // 현재 레이아웃 백업 + 편집 모드 진입
cancelEditMode()          // 백업 레이아웃 복원 + 편집 모드 종료
saveEditMode()            // 레이아웃 저장 + 편집 모드 종료
setDashboardTheme(theme)  // 테마 변경 → localStorage 저장
resetToMock()             // 6개 데모 위젯으로 리셋
```

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
    color_palette: "default"       // 컬러 팔레트 (default|vivid|pastel|warm|cool|earth)
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
  → 사용자가 제목/유형/차트설정/컬러팔레트 입력
  → store.dispatch('dashboard/saveWidget', config)
  → localStorage 저장

[대시보드 로드]
PersonalDashboardView.onMounted
  → store.dispatch('dashboard/fetchWidgets')
  → localStorage 로드
  → commit SET_WIDGETS
  → DashboardGrid ← Vuex gridLayout getter 바인딩
  → DashboardWidget ← v-for 개별 위젯

[대시보드에서 추가]
AddWidgetModal
  → historyApi.listSessions() → 세션 목록 로드 (nl2sql/agent 필터)
  → historyApi.getSessionHistory() → NL2SQL 결과 있는 레코드 필터
  → 결과 선택 → 위젯 설정 → store.dispatch('dashboard/saveWidget')
  → localStorage 저장

[위젯 새로고침 - 프로토타입]
DashboardWidget 새로고침 버튼
  → store.dispatch('dashboard/refreshWidget', widgetId)
  → 1초 딜레이 → last_refreshed_at 갱신 (실제 SQL 미실행)
```

### 7.5 데모 위젯 목록

빈 상태에서 "데모 위젯 로드" 시 생성되는 6개 위젯:

| # | 제목 | 유형 | 크기 (w x h) | 설명 |
|---|------|------|-------------|------|
| 1 | 부서별 직원 수 | bar | 6 x 10 | 7개 부서 데이터 |
| 2 | 월별 입사자 추이 (2024) | line | 6 x 10 | 12개월 추이 |
| 3 | 직급별 인원 분포 | pie | 5 x 10 | 6개 직급 |
| 4 | 전체 직원 수 | kpi | 3 x 5 | 342명 |
| 5 | 평균 연봉 | kpi | 3 x 5 | 5,280만원 |
| 6 | 부서별 평균 근속년수 | table | 6 x 8 | 7개 부서 |

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
  colorPalette     // 팔레트 키 (기본 'default')
})
```

---

## 9. Backend API 설계 (미구현)

> 아래는 향후 백엔드 연동 시 구현할 API 설계입니다. 현재는 프로토타입으로 localStorage만 사용합니다.

### 9.1 엔드포인트

| Method | Path | 설명 | Status | 응답 data |
|--------|------|------|--------|-----------|
| GET | `/api/v1/dashboard/widgets` | 위젯 목록 | 200 | `{items: [...], total: N}` |
| POST | `/api/v1/dashboard/widgets` | 위젯 생성 | 201 | 생성된 위젯 객체 |
| PUT | `/api/v1/dashboard/widgets/{id}` | 위젯 수정 | 200 | 수정된 위젯 객체 |
| DELETE | `/api/v1/dashboard/widgets/{id}` | 위젯 삭제 | 200 | `{message, deleted_count}` |
| PUT | `/api/v1/dashboard/layout` | 레이아웃 저장 | 200 | `{message, updated_count}` |
| POST | `/api/v1/dashboard/widgets/{id}/refresh` | 데이터 갱신 | 200 | `{widget_id, cached_data, last_refreshed_at}` |

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
    "color_palette": "default"
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
    "title": "부서별 직원 수",
    "widget_type": "bar",
    "grid_position": {"x": 0, "y": 0, "w": 6, "h": 10},
    ...
  }
}
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
// Response (200)
{
  "success": true,
  "data": {
    "widget_id": 1,
    "cached_data": {
      "columns": ["department_name", "cnt"],
      "rows": [...],
      "row_count": 15,
      "cached_at": "2026-02-26T10:30:00"
    },
    "last_refreshed_at": "2026-02-26T10:30:00"
  }
}
```

### 9.3 Backend 파일 구조 (미구현)

```
app/
├── api/
│   ├── routes/
│   │   └── personal_dashboard.py      # API 엔드포인트
│   └── services/
│       └── personal_dashboard_service.py  # 비즈니스 로직
└── models/
    └── personal_dashboard.py          # Pydantic 모델
```

### 9.4 새로고침 시 보안 (구현 예정)

- 저장된 SQL을 `sql_executor.py` 통해 실행 (기존 보안 체크 적용)
  - SELECT-only 검증
  - 키워드 블랙리스트 (DROP, DELETE, UPDATE 등)
  - 테이블 화이트리스트
  - 30초 타임아웃
  - 행 수 제한
- PII 필터는 기존 `pii_service.py` 적용

---

## 10. 데이터베이스 설계 (미구현)

### 10.1 신규 테이블

```sql
-- 개인 대시보드 위젯
CREATE TABLE tb_dashboard_widget (
    widget_id         SERIAL PRIMARY KEY,
    user_id           INTEGER NOT NULL,
    title             VARCHAR(200) NOT NULL,
    widget_type       VARCHAR(20) NOT NULL DEFAULT 'table',
    query             TEXT,                                    -- 원본 자연어 질문
    sql               TEXT,                                    -- 생성된 SQL
    chart_config      JSONB DEFAULT '{}',                      -- 차트 설정
    cached_data       JSONB DEFAULT '{}',                      -- 캐시 결과
    grid_position     JSONB DEFAULT '{"x":0,"y":0,"w":6,"h":10}',
    sort_order        INTEGER DEFAULT 0,
    is_active         BOOLEAN DEFAULT TRUE,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dashboard_widget_user ON tb_dashboard_widget(user_id);
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
  "color_palette": "default"
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

- `cached_data.rows`: 최대 500행까지만 저장 (SaveToDashboardModal에서 truncate)
- `widget_type`: CHECK ('table', 'bar', 'hbar', 'line', 'pie', 'scatter', 'kpi')
- 사용자당 최대 위젯 수: 20개 (서비스 레벨 제한)

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
- 테마 설정은 localStorage에 독립 저장 (`mureum_dashboard_theme`)

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

### Phase 2: 백엔드 구현 (예정)

| 순서 | 작업 | 산출물 | 상태 |
|------|------|--------|------|
| 2-1 | DB 테이블 생성 (`tb_dashboard_widget`) | DDL 스크립트 | ❌ |
| 2-2 | Pydantic 모델 작성 | `app/models/personal_dashboard.py` | ❌ |
| 2-3 | Service 계층 작성 | `app/api/services/personal_dashboard_service.py` | ❌ |
| 2-4 | Route 작성 + main.py 등록 | `app/api/routes/personal_dashboard.py` | ❌ |
| 2-5 | API 클라이언트 작성 | `frontend/src/api/personalDashboard.js` | ❌ |
| 2-6 | Vuex 스토어 API 연동 | `store/modules/dashboard.js` 수정 | ❌ |

### Phase 3: 테스트 (예정)

| 순서 | 작업 | 검증 항목 | 상태 |
|------|------|----------|------|
| 3-1 | Backend API 테스트 | CRUD + refresh 엔드포인트 | ❌ |
| 3-2 | Chat 저장 기능 테스트 | 모달 → 저장 → 대시보드 반영 | ❌ |
| 3-3 | 드래그앤드롭 테스트 | 이동/리사이즈 → 저장 → 새로고침 유지 | ❌ |
| 3-4 | 데이터 갱신 테스트 | SQL 재실행 → 최신 데이터 반영 | ❌ |
| 3-5 | 반응형 테스트 | 모바일/태블릿 레이아웃 확인 | ❌ |

---

## 14. 리스크 및 대응

| 리스크 | 영향 | 대응 | 상태 |
|--------|------|------|------|
| vue3-grid-layout-next 호환성 | 드래그앤드롭 불가 | ResizeObserver로 초기화 타이밍 해결 | ✅ 해결 |
| cached_data JSONB 크기 | DB 성능 저하 | 최대 500행 제한, 저장 시 truncate | ✅ 적용 |
| SQL 재실행 실패 | 위젯 에러 상태 | 에러 오버레이 + 재시도/삭제 옵션 (설계) | ❌ 미구현 |
| 다크/라이트 모드 전환 | 차트 색상 불일치 | darkMode prop 기반 직접 색상 결정 | ✅ 해결 |
| 차트 로직 중복 | 유지보수 부담 | useChartOptions.js composable 공유 | ✅ 해결 |
| localStorage 용량 제한 | 위젯 데이터 유실 | 백엔드 DB 연동으로 해결 예정 | ❌ 미해결 |
| 브라우저간 데이터 미동기화 | 다른 기기에서 접근 불가 | 백엔드 DB 연동으로 해결 예정 | ❌ 미해결 |

---

## 15. 내보내기 기능

### 15.1 개요

대시보드 위젯 데이터를 다양한 형식으로 내보내는 기능을 제공한다.
위젯 단위 내보내기와 대시보드 전체 내보내기를 지원한다.

### 15.2 구현 상태

| 기능 | 형식 | 범위 | 의존성 | 상태 |
|------|------|------|--------|------|
| 차트 이미지 | PNG | 위젯 (차트 뷰) | ECharts 내장 `getDataURL()` | ✅ |
| 위젯 캡처 | PNG | 위젯 전체 | html-to-image | ✅ |
| CSV 다운로드 | CSV | 위젯 | 없음 (순수 프론트엔드) | ✅ |
| Excel 다운로드 | XLSX | 위젯 | 기존 백엔드 API (`/api/v1/export/excel`) | ✅ |
| 대시보드 PDF | PDF | 대시보드 전체 | html-to-image + jsPDF | ✅ |
| 멀티시트 Excel | XLSX | 대시보드 전체 | openpyxl (백엔드) | ❌ 미구현 |
| 정형 PDF 보고서 | PDF | 대시보드 전체 | WeasyPrint (백엔드) | ❌ 미구현 |
| Word 보고서 | DOCX | 대시보드 전체 | python-docx (백엔드) | ❌ 미구현 |

### 15.3 위젯 단위 내보내기 UI

비편집 모드에서 각 위젯 헤더에 내보내기 드롭다운 표시:

```
[뷰전환]  [▼ 내보내기]  [새로고침]
               ├── 차트 이미지 (PNG)   — 차트 뷰일 때만 활성
               ├── 위젯 캡처 (PNG)     — DOM 전체 캡처
               ├─────────────────────
               ├── CSV 다운로드
               └── Excel 다운로드
```

### 15.4 내보내기 상세

#### 15.4.1 차트 이미지 (PNG)

- **방식**: ECharts 인스턴스의 `getDataURL({ type: 'png', pixelRatio: 2 })` 호출
- **조건**: 차트 뷰 모드일 때만 활성 (테이블/KPI 뷰에서는 비활성)
- **해상도**: 2x pixel ratio
- **파일명**: `{위젯제목}_{yyyyMMdd_HHmmss}.png`

#### 15.4.2 위젯 캡처 (PNG)

- **방식**: `html-to-image`의 `toPng(element, { pixelRatio: 2, backgroundColor: '#ffffff' })`
- **범위**: 위젯 루트 DOM 전체 (헤더 + 콘텐츠 + 푸터)
- **파일명**: `{위젯제목}_{yyyyMMdd_HHmmss}_capture.png`

#### 15.4.3 CSV 다운로드

- **방식**: 프론트엔드 순수 구현 (서버 호출 없음)
- **인코딩**: BOM 포함 UTF-8 (`\uFEFF` prefix → Excel 한글 깨짐 방지)
- **이스케이프**: 쉼표/따옴표/줄바꿈 포함 시 `"..."` 래핑, `"` → `""` 치환
- **데이터**: `widget.cached_data`의 columns + rows 사용
- **파일명**: `{위젯제목}_{yyyyMMdd_HHmmss}.csv`

#### 15.4.4 Excel 다운로드

- **방식**: 기존 백엔드 API (`POST /api/v1/export/excel`) 재사용
- **기능**: openpyxl 기반 보고서 형태 (질문, SQL, 데이터 테이블 + 차트 삽입)
- **차트 포함**: 차트 유형 위젯일 경우 `include_chart: true` + `chart_config` 전달
- **유형 매핑**: hbar → bar (openpyxl 미지원)
- **파일명**: 서버에서 생성 (기존 export API 패턴)

### 15.5 대시보드 전체 내보내기

#### 15.5.1 PDF 내보내기 (스냅샷)

- **위치**: DashboardToolbar에 PDF 아이콘 버튼 (위젯 1개 이상일 때 표시)
- **방식**: `.dashboard-content` DOM을 html-to-image로 캡처 → jsPDF로 PDF 생성
- **형식**: A4 landscape (가로), 10mm 마진
- **헤더**: 좌측에 "BI 대시보드" 제목, 우측에 현재 시각 (ko-KR locale)
- **이미지**: 비율 유지하여 페이지에 맞춤
- **파일명**: `BI_대시보드_{yyyyMMdd_HHmmss}.pdf`
- **로딩**: 버튼에 `:loading="exporting"` 상태 표시

### 15.6 유틸리티 함수

**파일**: `frontend/src/utils/exportUtils.js`

| 함수 | 용도 |
|------|------|
| `sanitizeFilename(name)` | 파일명 특수문자 제거 (`\/:*?"<>\|` → `_`), 공백 → `_`, 최대 100자 |
| `formatTimestamp(date)` | `yyyyMMdd_HHmmss` 형식 타임스탬프 |
| `downloadBlob(blob, filename)` | Blob → Object URL → `<a>` 다운로드 → URL 해제 |
| `downloadCsv(columns, rows, filename)` | columns + rows → BOM UTF-8 CSV 파일 다운로드 |
| `downloadDataUrl(dataUrl, filename)` | base64 data URL → 파일 다운로드 |
| `captureElementPng(element, filename)` | DOM → PNG 캡처 (html-to-image, 2x) → 파일 다운로드 |
| `exportElementPdf(element, title, filename)` | DOM → PNG → jsPDF A4 landscape PDF 저장 |

### 15.7 NPM 패키지

| 패키지 | 버전 | 크기 | 용도 |
|--------|------|------|------|
| `html-to-image` | ^1.x | ~27KB | DOM → PNG 변환 (SVG foreignObject 기반) |
| `jspdf` | ^2.x | ~300KB | 클라이언트 사이드 PDF 생성 |

두 패키지 모두 동적 import (`await import(...)`)로 사용하여 초기 번들 크기 영향 최소화.

### 15.8 수정 파일 요약

| 파일 | 변경 내용 | 상태 |
|------|----------|------|
| `frontend/src/utils/exportUtils.js` | **신규**: 7개 유틸 함수 | ✅ |
| `frontend/src/components/dashboard-personal/DashboardWidget.vue` | 내보내기 드롭다운 (4종) + 핸들러 | ✅ |
| `frontend/src/components/dashboard-personal/DashboardToolbar.vue` | PDF 내보내기 버튼 + exporting prop | ✅ |
| `frontend/src/views/user/PersonalDashboardView.vue` | PDF 핸들러 + content ref | ✅ |
| `frontend/src/components/dashboard-personal/widgets/WidgetChart.vue` | `getChartImage` expose (기존) | ✅ |
| `frontend/package.json` | html-to-image, jspdf 추가 | ✅ |
