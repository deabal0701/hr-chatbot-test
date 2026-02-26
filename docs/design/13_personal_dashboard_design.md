# 개인 BI 대시보드 설계서

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
| 위젯 배치 방식 | 드래그앤드롭 그리드 | 사용자 자유도 극대화 |
| 데이터 갱신 | 수동 새로고침 | 성능 부담 최소화, 캐시 데이터 기본 표시 |
| 위젯 유형 | 테이블/Bar/Line/Pie/KPI | 일반적 BI 시각화 커버 |

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
│  │ [★ 대시보드에 추가]  ← 신규 버튼 │                             │
│  └─────────────────────────────────┘                             │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼  클릭
┌──────────────────────────────────────────────────────────────────┐
│  SaveToDashboardModal                                            │
│                                                                  │
│  위젯 제목: [부서별 직원 수 현황___________________]             │
│                                                                  │
│  위젯 유형: (●) 테이블  ( ) Bar  ( ) Line  ( ) Pie  ( ) KPI     │
│                                                                  │
│  [차트 설정 영역 - Bar/Line/Pie 선택 시 표시]                    │
│  X축: [부서명          ▼]                                        │
│  Y축: [직원수          ▼]                                        │
│                                                                  │
│  [미리보기]                                                      │
│  ┌────────────────────────────────┐                              │
│  │  (선택한 유형의 차트/테이블)    │                              │
│  └────────────────────────────────┘                              │
│                                                                  │
│                          [취소]  [저장]                           │
└──────────────────────────────────────────────────────────────────┘
         │
         ▼  저장
   POST /api/v1/dashboard/widgets
   → ElMessage.success("위젯이 대시보드에 추가되었습니다")
```

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
│ 대시보드  │ ← 신규 메뉴
│          │
└─────────┘
     │
     ▼  클릭 → /dashboard 이동
┌──────────────────────────────────────────────────────────────────┐
│  PersonalDashboardView                                           │
│                                                                  │
│  GET /api/v1/dashboard/widgets → 위젯 목록 로드                  │
│  → vue-grid-layout 그리드에 위젯 렌더링                          │
└──────────────────────────────────────────────────────────────────┘
```

### 2.3 Flow C: 대시보드 편집 (드래그앤드롭)

```
┌────────────────────────────────────────────────────────────┐
│  "편집" 클릭 → 편집 모드 진입                               │
│                                                            │
│  ● 위젯 드래그 이동 가능 (제목바가 핸들)                    │
│  ● 위젯 크기 변경 가능 (우하단 핸들)                        │
│  ● 각 위젯에 [수정] [삭제] 아이콘 표시                      │
│  ● "위젯 추가" 플로팅 버튼 표시                             │
│                                                            │
│  "레이아웃 저장" → PUT /api/v1/dashboard/layout             │
│  "취소" → 이전 레이아웃으로 복원                             │
└────────────────────────────────────────────────────────────┘
```

### 2.4 Flow D: 위젯 데이터 새로고침

```
┌────────────────────────────────────────────────────────────┐
│  위젯 새로고침 버튼 클릭                                    │
│  → POST /api/v1/dashboard/widgets/{id}/refresh              │
│  → 저장된 SQL을 External DB에서 재실행                      │
│  → 최신 데이터로 차트/테이블 갱신                           │
│  → 실패 시: 에러 오버레이 + "재시도" 버튼                   │
└────────────────────────────────────────────────────────────┘
```

### 2.5 Flow E: 대시보드에서 직접 위젯 추가

```
┌────────────────────────────────────────────────────────────┐
│  편집 모드에서 "위젯 추가" 클릭                              │
│  → AddWidgetModal 열림                                      │
│  → 자연어 질문 입력 → NL2SQL 실행                           │
│  → 결과 미리보기 + 차트 설정                                 │
│  → "추가" → 위젯 생성 + 그리드에 배치                       │
└────────────────────────────────────────────────────────────┘
```

---

## 3. 화면 레이아웃

### 3.1 대시보드 메인 화면 (View Mode)

```
┌──────────────────────────────────────────────────────────────────────┐
│  HEADER                                                              │
│  [📊] 나의 대시보드                        [전체 새로고침]  [편집]    │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  GRID AREA (vue-grid-layout, 12컬럼, 16px 간격)                      │
│                                                                      │
│  ┌────────────────────────────┐  ┌────────────────────────────┐      │
│  │ 부서별 직원 수       [🔄]  │  │ 월별 입사자 추이     [🔄]  │      │
│  │                            │  │                            │      │
│  │  ┌──┐                      │  │    ╱╲                      │      │
│  │  │  │ ┌──┐                 │  │   ╱  ╲   ╱╲               │      │
│  │  │  │ │  │ ┌──┐            │  │  ╱    ╲_╱  ╲              │      │
│  │  │  │ │  │ │  │            │  │ ╱            ╲             │      │
│  │  └──┘ └──┘ └──┘            │  │                            │      │
│  │  (Bar Chart)               │  │  (Line Chart)              │      │
│  └────────────────────────────┘  └────────────────────────────┘      │
│                                                                      │
│  ┌────────────────────────────┐  ┌─────────────┐                     │
│  │ 직급별 인원 분포     [🔄]  │  │ 전체 직원수  │                     │
│  │                            │  │             │                     │
│  │      ┌───┐                 │  │    342      │                     │
│  │   ╱──│   │──╲              │  │     명      │                     │
│  │  │   │   │   │             │  │             │                     │
│  │   ╲──│   │──╱              │  │  (KPI)     │                     │
│  │      └───┘                 │  │             │                     │
│  │  (Pie Chart)               │  └─────────────┘                     │
│  └────────────────────────────┘                                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.2 대시보드 편집 모드 (Edit Mode)

```
┌──────────────────────────────────────────────────────────────────────┐
│  HEADER                                                              │
│  [📊] 나의 대시보드                          [취소]  [레이아웃 저장]  │
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
│  [≡] = 드래그 핸들                                                   │
│  ◢◣  = 리사이즈 핸들                                                 │
│  ╌╌  = 점선 테두리 (편집 중 표시)                                    │
│                                                                      │
│                                              [+ 위젯 추가] (플로팅)  │
└──────────────────────────────────────────────────────────────────────┘
```

### 3.3 빈 상태 (Empty State)

```
┌──────────────────────────────────────────────────────────────────────┐
│  HEADER                                                              │
│  [📊] 나의 대시보드                                                  │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│                                                                      │
│                         [📊 큰 아이콘]                               │
│                                                                      │
│                     위젯이 없습니다                                   │
│           채팅에서 NL2SQL 결과를 대시보드에                           │
│                 추가해보세요                                          │
│                                                                      │
│                     [채팅으로 이동]                                   │
│                                                                      │
│                                                                      │
└──────────────────────────────────────────────────────────────────────┘
```

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
│  │ 테이블  │  Bar   │  Line  │  Pie   │  KPI   │     │
│  └────────┴────────┴────────┴────────┴────────┘     │
│                                                      │
│  ── 차트 설정 (Bar/Line/Pie 선택 시) ──              │
│                                                      │
│  X축 컬럼                                            │
│  ┌──────────────────────────────────────────┐        │
│  │ department_name                       ▼  │        │
│  └──────────────────────────────────────────┘        │
│                                                      │
│  Y축 컬럼                                            │
│  ┌──────────────────────────────────────────┐        │
│  │ employee_count                        ▼  │        │
│  └──────────────────────────────────────────┘        │
│                                                      │
│  Pie Top N (Pie 선택 시)                             │
│  ┌──────────────────────────────────────────┐        │
│  │ Top 10                                ▼  │        │
│  └──────────────────────────────────────────┘        │
│                                                      │
│  ── KPI 설정 (KPI 선택 시) ──                        │
│                                                      │
│  값 컬럼                                             │
│  ┌──────────────────────────────────────────┐        │
│  │ total_count                           ▼  │        │
│  └──────────────────────────────────────────┘        │
│                                                      │
│  단위 접미사                                         │
│  ┌──────────────────────────────────────────┐        │
│  │ 명                                       │        │
│  └──────────────────────────────────────────┘        │
│                                                      │
│  ── 미리보기 ──                                      │
│  ┌──────────────────────────────────────────┐        │
│  │                                          │        │
│  │     (선택한 유형으로 렌더링된 미리보기)   │        │
│  │                                          │        │
│  └──────────────────────────────────────────┘        │
│                                                      │
├──────────────────────────────────────────────────────┤
│                           [취소]  [저장 (Primary)]   │
└──────────────────────────────────────────────────────┘
```

### 3.5 WidgetEditModal (위젯 수정)

SaveToDashboardModal과 동일 구조에 추가 항목:

```
┌──────────────────────────────────────────────────────┐
│  위젯 수정                                    [X]    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  (SaveToDashboardModal과 동일한 필드들)               │
│                                                      │
│  ── 쿼리 정보 (접기/펼치기) ──                       │
│                                                      │
│  원본 질문: "부서별 직원 수를 알려줘"                 │
│  생성 SQL:                                           │
│  ┌──────────────────────────────────────────┐        │
│  │ SELECT department_name, COUNT(*)         │        │
│  │ FROM employee                            │        │
│  │ GROUP BY department_name                 │        │
│  └──────────────────────────────────────────┘        │
│                                                      │
├──────────────────────────────────────────────────────┤
│                           [취소]  [저장 (Primary)]   │
└──────────────────────────────────────────────────────┘
```

### 3.6 AddWidgetModal (대시보드에서 직접 추가)

```
┌──────────────────────────────────────────────────────┐
│  위젯 추가                                    [X]    │
├──────────────────────────────────────────────────────┤
│                                                      │
│  질문 입력                                           │
│  ┌──────────────────────────────────────┐ [실행]     │
│  │ 부서별 직원 수를 알려줘              │            │
│  └──────────────────────────────────────┘            │
│                                                      │
│  ── 실행 결과 (실행 후 표시) ──                      │
│                                                      │
│  ┌──────────────────────────────────────────┐        │
│  │ 부서명    │ 직원수                       │        │
│  │ 개발팀    │ 42                           │        │
│  │ 인사팀    │ 15                           │        │
│  └──────────────────────────────────────────┘        │
│                                                      │
│  (이하 SaveToDashboardModal과 동일한 설정 UI)        │
│                                                      │
├──────────────────────────────────────────────────────┤
│                           [취소]  [추가 (Primary)]   │
└──────────────────────────────────────────────────────┘
```

---

## 4. 위젯 유형 상세

### 4.1 위젯 유형별 사양

| 유형 | 기본 크기 (w x h) | 최소 크기 | 렌더링 | 설명 |
|------|-------------------|-----------|--------|------|
| table | 6 x 10 | 4 x 6 | el-table | 최대 100행, 스크롤, 컬럼 자동 생성 |
| bar | 6 x 10 | 4 x 6 | ECharts bar | 30개 이상 시 dataZoom 슬라이더 |
| line | 6 x 10 | 4 x 6 | ECharts line | 추세 분석용 |
| pie | 4 x 10 | 3 x 6 | ECharts pie | Top-N 그룹핑 + "기타" 버킷 |
| kpi | 3 x 4 | 2 x 3 | 숫자 강조 | 단일 수치 + 단위 표시 |

### 4.2 WidgetTable (테이블 위젯)

```
┌──────────────────────────────────────┐
│ 부서별 직원 현황             [🔄]    │
├──────────────────────────────────────┤
│ ┌──────────┬──────────┬──────────┐  │
│ │ 부서명    │ 직원수    │ 평균급여  │  │
│ ├──────────┼──────────┼──────────┤  │
│ │ 개발팀    │ 42       │ 5,200    │  │
│ │ 인사팀    │ 15       │ 4,800    │  │
│ │ 영업팀    │ 28       │ 5,100    │  │
│ │ ...      │          │          │  │
│ └──────────┴──────────┴──────────┘  │
│ ... 외 12건                          │
├──────────────────────────────────────┤
│ 마지막 갱신: 5분 전                   │
└──────────────────────────────────────┘
```

- el-table, size="small", border
- 위젯 높이에 맞춰 max-height 자동 계산
- 100행 초과 시 "... 외 N건" 표시
- 다크 모드 지원 (기존 el-table CSS 오버라이드 활용)

### 4.3 WidgetChart (차트 위젯 - Bar/Line/Pie)

```
┌──────────────────────────────────────┐
│ 부서별 직원 수                [🔄]   │
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
│ 마지막 갱신: 방금 전                  │
└──────────────────────────────────────┘
```

- vue-echarts (ECharts) 사용, autoresize 활성화
- ChartBuilder에서 추출한 `useChartOptions.js` composable 공유
- 다크/라이트 모드 자동 전환 (`getThemeColor` 패턴 재사용)
- Pie: Top-N 그룹핑 + "기타 (N건)" 버킷
- Bar/Line: 30개 이상 시 dataZoom 슬라이더

### 4.4 WidgetKpi (KPI 위젯)

```
┌─────────────────┐
│ 전체 직원수      │
│                  │
│      342        │
│       명         │
│                  │
│ 갱신: 1시간 전   │
└─────────────────┘
```

- sql_result.rows[0]에서 첫 번째 숫자 컬럼 값 추출
- 숫자: 48px, font-weight: 700, `var(--text-color-primary)`
- 단위: 14px, `var(--text-color-secondary)`
- 수직/수평 중앙 정렬

---

## 5. 반응형 디자인

### 5.1 화면 크기별 동작

| 화면 | 그리드 컬럼 | 드래그앤드롭 | 편집 모드 | 비고 |
|------|------------|------------|----------|------|
| Desktop (>=1024px) | 12 | 가능 | 전체 기능 | 2~3열 위젯 배치 |
| Tablet (768-1023px) | 8 | 가능 | 전체 기능 | 2열 위주 |
| Mobile (<=767px) | 1 | 비활성 | 숨김 | 세로 스택, 새로고침만 가능 |

### 5.2 모바일 대응

- 위젯: 전체 폭 (1컬럼) 세로 스택
- 차트 최소 높이: 250px, 테이블 최소 높이: 300px, KPI 최소 높이: 150px
- "편집" 버튼 숨김 (모바일에서는 레이아웃 변경 불가)
- 모달: 전체 화면 (`el-dialog :fullscreen="isMobile"`)
- 사이드바: 기존 UserChatSidebar 패턴 유지 (햄버거 메뉴)

---

## 6. 컴포넌트 구조

### 6.1 컴포넌트 트리

```
PersonalDashboardView.vue
├── DashboardToolbar.vue
│   ├── 편집 모드 전환 버튼
│   ├── 전체 새로고침 버튼
│   └── 제목 + 서브타이틀
├── DashboardGrid.vue (vue-grid-layout 래퍼)
│   └── DashboardWidget.vue (v-for 각 위젯)
│       ├── 위젯 제목바 (제목, 새로고침, 편집, 삭제 버튼)
│       └── 위젯 콘텐츠 (동적):
│           ├── WidgetTable.vue    (widget.type === 'table')
│           ├── WidgetChart.vue    (widget.type in ['bar','line','pie'])
│           └── WidgetKpi.vue      (widget.type === 'kpi')
├── DashboardEmptyState.vue (위젯 0개일 때)
├── WidgetEditModal.vue (위젯 수정)
└── AddWidgetModal.vue (위젯 직접 추가)

UserChatMessage.vue (기존 파일 수정)
└── SaveToDashboardModal.vue (신규 자식 컴포넌트)
```

### 6.2 파일 구조

```
frontend/src/
├── views/user/
│   └── PersonalDashboardView.vue          # 신규: 메인 대시보드 페이지
├── components/dashboard-personal/         # 신규 디렉토리
│   ├── DashboardGrid.vue                  # vue-grid-layout 래퍼
│   ├── DashboardWidget.vue                # 위젯 컨테이너
│   ├── DashboardEmptyState.vue            # 빈 상태
│   ├── DashboardToolbar.vue               # 상단 툴바
│   ├── SaveToDashboardModal.vue           # Chat에서 저장 모달
│   ├── WidgetEditModal.vue                # 위젯 수정 모달
│   ├── AddWidgetModal.vue                 # 대시보드에서 추가 모달
│   └── widgets/
│       ├── WidgetTable.vue                # 테이블 렌더러
│       ├── WidgetChart.vue                # 차트 렌더러 (Bar/Line/Pie)
│       └── WidgetKpi.vue                  # KPI 렌더러
├── composables/
│   └── useChartOptions.js                 # ChartBuilder에서 추출한 공유 로직
├── store/modules/
│   └── dashboard.js                       # Vuex 대시보드 모듈
└── api/
    └── personalDashboard.js               # API 클라이언트
```

### 6.3 수정 대상 파일

| 파일 | 변경 내용 |
|------|----------|
| `frontend/src/router/index.js` | `/dashboard` 라우트 추가 |
| `frontend/src/store/index.js` | dashboard 모듈 등록 |
| `frontend/src/components/user/UserChatMessage.vue` | "대시보드에 추가" 버튼 추가 |
| `frontend/src/components/user/UserChatSidebar.vue` | "대시보드" 네비게이션 메뉴 추가 |
| `frontend/src/components/chart/ChartBuilder.vue` | 차트 옵션 로직을 composable로 추출 |
| `app/main.py` | personal_dashboard 라우터 등록 |

---

## 7. 상태 관리 (Vuex)

### 7.1 Dashboard Store 모듈

```javascript
// store/modules/dashboard.js

state: () => ({
  widgets: [],             // 위젯 목록 (API에서 로드)
  layout: [],              // [{i, x, y, w, h}] vue-grid-layout용
  isLoading: false,        // 초기 로딩 상태
  editMode: false,         // 편집 모드 여부
  pendingLayout: null,     // 편집 모드 진입 시 백업 (취소용)
  refreshingWidgets: {},   // { widgetId: true/false } 개별 위젯 로딩
})

// Actions
fetchWidgets()         // GET /api/v1/dashboard/widgets → 위젯 + 레이아웃 로드
saveWidget(config)     // POST /api/v1/dashboard/widgets → 위젯 생성
updateWidget(id, cfg)  // PUT /api/v1/dashboard/widgets/{id} → 위젯 수정
deleteWidget(id)       // DELETE /api/v1/dashboard/widgets/{id} → 위젯 삭제
saveLayout(layout)     // PUT /api/v1/dashboard/layout → 레이아웃 일괄 저장
refreshWidget(id)      // POST /api/v1/dashboard/widgets/{id}/refresh → 데이터 갱신
refreshAllWidgets()    // 모든 위젯 순차 새로고침
enterEditMode()        // 현재 레이아웃 백업 + 편집 모드 진입
cancelEditMode()       // 백업 레이아웃 복원 + 편집 모드 종료
saveEditMode()         // 레이아웃 저장 + 편집 모드 종료
```

### 7.2 위젯 데이터 구조

```javascript
{
  widget_id: 1,
  title: "부서별 직원 수",
  widget_type: "bar",              // table | bar | line | pie | kpi
  query: "부서별 직원 수를 알려줘", // 원본 자연어 질문
  sql: "SELECT department_name, COUNT(*) ...",  // 생성된 SQL
  chart_config: {
    x_column: "department_name",   // X축 컬럼
    y_columns: ["count"],          // Y축 컬럼 (배열)
    pie_top_n: null,               // Pie Top N (null=전체)
    kpi_column: null,              // KPI 값 컬럼
    kpi_suffix: null               // KPI 단위 ("명", "%", "원")
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

### 7.3 데이터 흐름

```
[Chat → 저장]
UserChatMessage.vue
  → message.sqlResult (columns, rows), message.sql, message.content
  → SaveToDashboardModal (props로 전달)
  → 사용자가 제목/유형/차트설정 입력
  → store.dispatch('dashboard/saveWidget', config)
  → POST /api/v1/dashboard/widgets

[대시보드 로드]
PersonalDashboardView.onMounted
  → store.dispatch('dashboard/fetchWidgets')
  → GET /api/v1/dashboard/widgets
  → commit SET_WIDGETS + SET_LAYOUT
  → DashboardGrid ← Vuex 바인딩
  → DashboardWidget ← v-for 개별 위젯

[위젯 새로고침]
DashboardWidget 새로고침 버튼
  → store.dispatch('dashboard/refreshWidget', widgetId)
  → POST /api/v1/dashboard/widgets/{id}/refresh
  → SQL 재실행 → commit UPDATE_WIDGET_DATA
  → 위젯 리렌더링
```

---

## 8. Backend API 설계

### 8.1 엔드포인트

| Method | Path | 설명 | Status | 응답 data |
|--------|------|------|--------|-----------|
| GET | `/api/v1/dashboard/widgets` | 위젯 목록 | 200 | `{items: [...], total: N}` |
| POST | `/api/v1/dashboard/widgets` | 위젯 생성 | 201 | 생성된 위젯 객체 |
| PUT | `/api/v1/dashboard/widgets/{id}` | 위젯 수정 | 200 | 수정된 위젯 객체 |
| DELETE | `/api/v1/dashboard/widgets/{id}` | 위젯 삭제 | 200 | `{message, deleted_count}` |
| PUT | `/api/v1/dashboard/layout` | 레이아웃 저장 | 200 | `{message, updated_count}` |
| POST | `/api/v1/dashboard/widgets/{id}/refresh` | 데이터 갱신 | 200 | `{widget_id, cached_data, last_refreshed_at}` |

### 8.2 요청/응답 예시

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
    "y_columns": ["cnt"]
  },
  "cached_data": {
    "columns": ["department_name", "cnt"],
    "rows": [{"department_name": "개발팀", "cnt": 42}, ...],
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
    {"widget_id": 3, "x": 0, "y": 10, "w": 4, "h": 10}
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

### 8.3 Backend 파일 구조

```
app/
├── api/
│   ├── routes/
│   │   └── personal_dashboard.py      # 신규: API 엔드포인트
│   └── services/
│       └── personal_dashboard_service.py  # 신규: 비즈니스 로직
└── models/
    └── personal_dashboard.py          # 신규: Pydantic 모델
```

### 8.4 새로고침 시 보안

- 저장된 SQL을 `sql_executor.py` 통해 실행 (기존 보안 체크 적용)
  - SELECT-only 검증
  - 키워드 블랙리스트 (DROP, DELETE, UPDATE 등)
  - 테이블 화이트리스트
  - 30초 타임아웃
  - 행 수 제한
- PII 필터는 기존 `pii_service.py` 적용

---

## 9. 데이터베이스 설계

### 9.1 신규 테이블

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

### 9.2 JSONB 필드 스키마

**chart_config**:
```json
{
  "x_column": "department_name",
  "y_columns": ["count", "avg_salary"],
  "pie_top_n": 10,
  "kpi_column": "total_count",
  "kpi_suffix": "명"
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

### 9.3 제약 사항

- `cached_data.rows`: 최대 500행까지만 저장 (Backend에서 truncate)
- `widget_type`: CHECK ('table', 'bar', 'line', 'pie', 'kpi')
- 사용자당 최대 위젯 수: 20개 (서비스 레벨 제한)

---

## 10. 드래그앤드롭 그리드 상세

### 10.1 vue-grid-layout 설정

```javascript
// DashboardGrid.vue
{
  colNum: 12,              // 12컬럼 그리드
  rowHeight: 30,           // 행 높이 30px
  margin: [16, 16],        // 간격 16px
  isDraggable: editMode,   // 편집 모드에서만 드래그
  isResizable: editMode,   // 편집 모드에서만 리사이즈
  verticalCompact: true,   // 수직 자동 정렬
  useCssTransforms: true   // CSS transform 사용 (성능)
}
```

### 10.2 기본 위젯 크기 (그리드 단위)

| 위젯 유형 | 기본 w | 기본 h | 최소 w | 최소 h | 화면 비율 |
|----------|--------|--------|--------|--------|----------|
| table | 6 | 10 | 4 | 6 | 50% 폭 x 300px |
| bar | 6 | 10 | 4 | 6 | 50% 폭 x 300px |
| line | 6 | 10 | 4 | 6 | 50% 폭 x 300px |
| pie | 4 | 10 | 3 | 6 | 33% 폭 x 300px |
| kpi | 3 | 4 | 2 | 3 | 25% 폭 x 120px |

### 10.3 NPM 패키지

```bash
npm install vue3-grid-layout-next
```

---

## 11. 스타일 가이드

### 11.1 사용할 SCSS 믹스인

| 믹스인 | 파일 | 용도 |
|--------|------|------|
| `@include mx.content-card` | `_layout.scss` | 위젯 카드 배경/테두리/그림자 |
| `@include mx.content-header` | `_layout.scss` | 위젯 제목바 레이아웃 |
| `@include mx.page-header` | `_layout.scss` | 대시보드 페이지 헤더 |
| `@include mx.stat-card` | `_cards.scss` | KPI 위젯 스타일 |
| `@include mx.chart-render-area` | `_chart.scss` | 차트 컨테이너 |
| `@include mx.chart-config-panel` | `_chart.scss` | 모달 차트 설정 영역 |
| `@include mx.chart-config-item` | `_chart.scss` | 설정 항목 (라벨 + 컨트롤) |

### 11.2 테마 변수

기존 UserChatView 다크 모드 스타일과 일관성 유지:

```scss
// 위젯 카드
background: var(--bg-color-card);
border: 1px solid var(--border-color-lighter);
border-radius: 8px;
box-shadow: var(--box-shadow);

// 텍스트
color: var(--text-color-primary);      // 제목, 데이터
color: var(--text-color-secondary);    // 서브텍스트, 타임스탬프

// 편집 모드
border: 2px dashed var(--el-color-primary);  // 점선 테두리
cursor: grab;                                 // 드래그 커서
```

### 11.3 ECharts 테마

ChartBuilder.vue의 기존 `getThemeColor` 패턴 재사용:
- 다크 모드: 밝은 계열 색상, 어두운 배경
- 라이트 모드: 표준 색상, 밝은 배경
- 테마 변경 시 `watch(isDarkMode)` → 차트 재렌더링

---

## 12. 구현 순서

### Phase 1: 인프라 (Backend)

| 순서 | 작업 | 산출물 |
|------|------|--------|
| 1-1 | DB 테이블 생성 (`tb_dashboard_widget`) | DDL 스크립트 |
| 1-2 | Pydantic 모델 작성 | `app/models/personal_dashboard.py` |
| 1-3 | Service 계층 작성 | `app/api/services/personal_dashboard_service.py` |
| 1-4 | Route 작성 + main.py 등록 | `app/api/routes/personal_dashboard.py` |

### Phase 2: 프론트엔드 기반

| 순서 | 작업 | 산출물 |
|------|------|--------|
| 2-1 | `npm install vue3-grid-layout-next` | package.json 업데이트 |
| 2-2 | ChartBuilder에서 차트 로직 추출 | `composables/useChartOptions.js` |
| 2-3 | API 클라이언트 작성 | `api/personalDashboard.js` |
| 2-4 | Vuex 모듈 작성 | `store/modules/dashboard.js` |

### Phase 3: 위젯 컴포넌트

| 순서 | 작업 | 산출물 |
|------|------|--------|
| 3-1 | WidgetTable, WidgetChart, WidgetKpi | `components/dashboard-personal/widgets/` |
| 3-2 | DashboardWidget (컨테이너) | 위젯 래퍼 + 제목바 |
| 3-3 | DashboardGrid (그리드 래퍼) | vue-grid-layout 통합 |

### Phase 4: 페이지 조립

| 순서 | 작업 | 산출물 |
|------|------|--------|
| 4-1 | DashboardToolbar, DashboardEmptyState | 툴바 + 빈 상태 |
| 4-2 | PersonalDashboardView | 메인 페이지 |
| 4-3 | 라우터 등록 (`/dashboard`) | `router/index.js` 수정 |

### Phase 5: 모달 + 연동

| 순서 | 작업 | 산출물 |
|------|------|--------|
| 5-1 | SaveToDashboardModal | Chat에서 저장 모달 |
| 5-2 | UserChatMessage 수정 | "대시보드에 추가" 버튼 |
| 5-3 | WidgetEditModal | 위젯 수정 모달 |
| 5-4 | AddWidgetModal | 대시보드에서 직접 추가 |
| 5-5 | UserChatSidebar 수정 | "대시보드" 메뉴 추가 |

### Phase 6: 테스트

| 순서 | 작업 | 검증 항목 |
|------|------|----------|
| 6-1 | Backend API 테스트 | CRUD + refresh 엔드포인트 |
| 6-2 | Chat 저장 기능 테스트 | 모달 → 저장 → 대시보드 반영 |
| 6-3 | 드래그앤드롭 테스트 | 이동/리사이즈 → 저장 → 새로고침 유지 |
| 6-4 | 데이터 갱신 테스트 | SQL 재실행 → 최신 데이터 반영 |
| 6-5 | 반응형 테스트 | 모바일/태블릿 레이아웃 확인 |

---

## 13. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| vue3-grid-layout-next 호환성 | 드래그앤드롭 불가 | Fallback: CSS Grid + interact.js |
| cached_data JSONB 크기 | DB 성능 저하 | 최대 500행 제한, 저장 시 truncate |
| SQL 재실행 실패 | 위젯 에러 상태 | 에러 오버레이 + 재시도/삭제 옵션 |
| 다크/라이트 모드 전환 | 차트 색상 불일치 | watch(isDarkMode) → 차트 재렌더링 |
| 차트 로직 중복 | 유지보수 부담 | useChartOptions.js composable 공유 |
