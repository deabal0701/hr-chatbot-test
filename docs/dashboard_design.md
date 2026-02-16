# MUREUM Dashboard 전면 보완 설계서

## 1. 현황 분석

### 1.1 현재 대시보드 (DashboardView.vue)

| 영역 | 내용 | 데이터 소스 |
|------|------|-------------|
| 통계 카드 (4개) | 전체 문서, 임베딩 완료, 임베딩 대기, 오늘 대화 | documentApi.list(), store.state.chat (로컬) |
| 빠른 시작 | HR 챗봇, 문서 등록, 임베딩 실행 링크 | 정적 라우터 링크 |
| 시스템 정보 | API 상태, 서버 URL, 검색 모드, 모델 (하드코딩) | store.state.app |
| 최근 문서 | 최근 등록 문서 5건 테이블 | documentApi.list() |

**문제점**:
- "오늘 대화" 수치가 로컬 Vue store에서만 가져옴 (새로고침 시 초기화)
- 시스템 정보가 하드코딩 (실제 설정값 미반영)
- AI 검색(NL2SQL/RAG) 사용 통계 전혀 없음
- 사용자/테넌트 관리 현황 없음
- 성능 지표, 에러 추적 없음
- 시간대별 트렌드 차트 없음

### 1.2 활용 가능한 데이터 소스

| 데이터 | API 엔드포인트 | 주요 필드 |
|--------|----------------|-----------|
| **검색 통계** | `GET /api/v1/history/statistics` | total_requests, success_rate, avg_response_time_ms, nl2sql/rag_count |
| **이력 목록** | `GET /api/v1/history` | request_type, success, response_time_ms, created_at, trace_data |
| **사용자별 요약** | `GET /api/v1/history/users/{id}` | total_requests, 타입별 count, first/last_request_at |
| **세션 목록** | `GET /api/v1/history/sessions` | session_key, title, message_count, last_activity |
| **문서 관리** | `GET /api/admin/v1/documents` | total, indexed, doc_type |
| **사용자 관리** | `GET /api/admin/v1/users` | items, total, role, is_active, tenant |
| **테넌트 관리** | `GET /api/admin/v1/tenants` | items, is_active |
| **설정 조회** | `GET /api/admin/v1/settings` | LLM 모델, 프로바이더, RAG/NL2SQL 설정 |

> **참고**: 대시보드 대상은 **NL2SQL**과 **RAG** 검색이며, Agent는 대시보드 범위에서 제외한다.

---

## 2. 대시보드 레이아웃 설계

### 2.1 전체 구조 (4개 섹션)

```
┌─────────────────────────────────────────────────────────────────────┐
│  대시보드                                       기간 필터: [오늘 ▼] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ① KPI 요약 카드 (1줄 4개)                                          │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
│  │ 총 요청 수     │ │ 성공률        │ │ 활성 사용자    │ │ 전체 문서      │
│  │   1,234       │ │  98.5%       │ │    12         │ │   156         │
│  │  NL2SQL 789   │ │  에러 19건   │ │  3 테넌트     │ │ 142 임베딩완료 │
│  │  RAG    445   │ │              │ │               │ │  14 대기      │
│  └───────────────┘ └───────────────┘ └───────────────┘ └───────────────┘
│                                                                     │
│  ② 차트 영역 (2칸 분할)                                             │
│  ┌──────────────────────────────┐ ┌─────────────────────────┐      │
│  │ 일별 요청 추이 (7일)          │ │ 검색 유형 분포           │      │
│  │  ▁▂▃▅▆▇█                    │ │     ◉ NL2SQL 65%       │      │
│  │  Stacked Bar Chart           │ │     ◉ RAG    35%       │      │
│  │  NL2SQL / RAG                │ │   Donut (중앙: 총 1234) │      │
│  └──────────────────────────────┘ └─────────────────────────┘      │
│                                                                     │
│  ③ 최근 활동 + 시스템 현황 (2칸 분할)                                │
│  ┌──────────────────────────────┐ ┌─────────────────────────┐      │
│  │ 최근 검색 요청 (10건)         │ │ 시스템 현황              │      │
│  │ ──────────────────────────── │ │ API 상태:  ● 정상       │      │
│  │ 09:12 nl2sql 직원 수는?      │ │ LLM 모델:  gpt-4o      │      │
│  │ 09:10 rag    재택근무 정책..  │ │ 프로바이더: OpenAI       │      │
│  │ 09:05 nl2sql 부서별 급여...   │ │ 임베딩:    3-small      │      │
│  │ ...                          │ │ 활성 테넌트: 3           │      │
│  │             [전체보기 →]      │ │ 활성 사용자: 12          │      │
│  └──────────────────────────────┘ │ 문서 상태:  142/156     │      │
│                                    └─────────────────────────┘      │
│                                                                     │
│  ④ 빠른 액션 (1줄)                                                  │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │ 챗봇   │ │ 문서   │ │ 임베딩 │ │ 사용자 │ │ 설정   │          │
│  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 섹션별 상세 설계

---

#### ① KPI 요약 카드 (1줄 4개)

| # | 카드 | 주 값 | 보조 값 | 아이콘 | 색상 |
|---|------|-------|---------|--------|------|
| 1 | 총 요청 수 | `total_requests` | NL2SQL N건 / RAG N건 | DataAnalysis | primary (#409eff) |
| 2 | 성공률 | `success_rate` (%) | 에러 N건 | CircleCheck | success (#67c23a) |
| 3 | 활성 사용자 | 활성 사용자 수 | N개 테넌트 | User | warning (#e6a23c) |
| 4 | 전체 문서 | 문서 총 수 | 임베딩완료 N / 대기 N | Document | info (#909399) |

**데이터 소스**:
- 카드 1~2: `GET /api/v1/dashboard/summary` → kpi 필드
- 카드 3: dashboard summary → system.active_users, system.active_tenants
- 카드 4: dashboard summary → system.total_documents, indexed_documents, pending_documents

**레이아웃**: `el-row > el-col(:xs="12" :sm="12" :lg="6")` × 4 → 한 줄 배치

---

#### ② 차트 영역 (2개만)

> **성능 고려**: 차트는 렌더링 비용이 크므로 가장 중요한 2개만 표시한다.

**A. 일별 요청 추이 (Stacked Bar Chart)** — 좌측 60%

```
데이터 구조: 최근 7일
[
  { date: "02/10", nl2sql: 32, rag: 18, total: 50 },
  { date: "02/11", nl2sql: 28, rag: 22, total: 50 },
  ...
]
```

- X축: 날짜 (MM/DD)
- Y축: 요청 수
- 시리즈: NL2SQL (#67c23a), RAG (#e6a23c)
- Stacked Bar로 일별 총량과 유형별 비율을 한눈에 파악
- tooltip에 각 유형 건수 + 합계 표시
- 차트 라이브러리: **ECharts** (ChartBuilder.vue에서 이미 사용 중)

**B. 검색 유형 분포 (Donut Chart)** — 우측 40%

```
데이터: kpi.nl2sql_count, kpi.rag_count
```

- 도넛 차트 중앙: 총 요청 수
- 2개 시리즈: NL2SQL (#67c23a), RAG (#e6a23c)
- 범례: 이름 + 건수 + 비율(%)
- 심플하고 직관적인 비율 파악용

---

#### ③ 최근 활동 + 시스템 현황

**A. 최근 검색 요청 (Activity Feed)** — 좌측 60%

```
데이터: dashboard summary → recent_requests (최근 10건)
표시: 시간, 요청유형 태그, 질문 요약 (50자 truncate), 응답시간
```

- 요청 유형별 색상 태그: NL2SQL(success/green), RAG(warning/orange)
- 클릭 시 이력 상세 이동 (`/admin/history?id={request_id}`)
- "전체보기" 버튼 → `/admin/history`
- 실패 요청은 빨간색 dot으로 표시

**B. 시스템 현황 (el-descriptions)** — 우측 40%

| 항목 | 데이터 소스 |
|------|-------------|
| API 상태 | store.state.app.apiHealthy (실시간) |
| LLM 프로바이더 | settingsApi → llm.provider |
| LLM 모델 | settingsApi → llm.model |
| 임베딩 모델 | settingsApi → embedding.model |
| 활성 테넌트 | dashboard summary → system.active_tenants |
| 활성 사용자 | dashboard summary → system.active_users |
| 문서 상태 | indexed / total (프로그레스바) |
| 외부 DB 타입 | settingsApi → external_database.db_type |

---

#### ④ 빠른 액션 (Quick Actions)

| 액션 | 아이콘 | 라우트 | 설명 |
|------|--------|--------|------|
| HR 챗봇 | ChatDotRound | /admin/chat | 직원 정보 조회, 정책 검색 |
| 문서 등록 | FolderAdd | /admin/documents | 새로운 HR 문서 추가 |
| 임베딩 실행 | Upload | /admin/documents?indexed=false | 대기 중인 문서 처리 |
| 사용자 관리 | User | /admin/users | 사용자 생성/수정 |
| 설정 관리 | Setting | /admin/settings | 시스템 설정 |

---

## 3. 백엔드 API 설계

### 3.1 대시보드 전용 통합 API (신규)

개별 API 여러 번 호출 대신, **단일 엔드포인트**에서 대시보드에 필요한 모든 데이터를 반환한다.

**엔드포인트**: `GET /api/v1/dashboard/summary`

```python
# app/api/routes/dashboard.py

@router.get("/summary")
async def get_dashboard_summary(
    period: str = Query("today", description="today|week|month"),
    tenant_id: Optional[str] = Query(None),
    current_user: Optional[UserContext] = Depends(get_optional_user),
):
    """대시보드 요약 데이터 (단일 호출로 모든 KPI + 차트 데이터 제공)"""
```

**응답 구조**:

```json
{
  "success": true,
  "data": {
    "period": "today",
    "kpi": {
      "total_requests": 1234,
      "success_rate": 98.5,
      "error_count": 19,
      "nl2sql_count": 789,
      "rag_count": 445
    },
    "daily_trend": [
      { "date": "2026-02-10", "nl2sql": 32, "rag": 18, "total": 50 },
      { "date": "2026-02-11", "nl2sql": 28, "rag": 22, "total": 50 }
    ],
    "recent_requests": [
      {
        "request_id": "abc12345",
        "request_type": "nl2sql",
        "question": "2024년 입사자 수는?",
        "success": true,
        "response_time_ms": 2100,
        "created_at": "2026-02-16T09:15:00"
      }
    ],
    "system": {
      "active_users": 12,
      "active_tenants": 3,
      "total_documents": 156,
      "indexed_documents": 142,
      "pending_documents": 14
    }
  }
}
```

### 3.2 대시보드 서비스 (신규)

**파일**: `app/api/services/dashboard_service.py`

```python
class DashboardService:
    """대시보드 통합 데이터 서비스"""

    def get_summary(self, period, tenant_id, user_id) -> Dict:
        """단일 호출로 대시보드 전체 데이터 반환
        하나의 DB 커넥션으로 여러 쿼리를 순차 실행하여 성능 최적화
        """

    def _get_kpi(self, cur, from_date, to_date, tenant_id) -> Dict:
        """KPI 통계 (NL2SQL + RAG만 집계)"""

    def _get_daily_trend(self, cur, from_date, to_date, tenant_id) -> List[Dict]:
        """일별 요청 추이 (GROUP BY DATE, NL2SQL/RAG)"""

    def _get_recent_requests(self, cur, tenant_id, limit=10) -> List[Dict]:
        """최근 요청 목록 (NL2SQL/RAG만)"""

    def _get_system_info(self, cur, tenant_id) -> Dict:
        """시스템 현황 (사용자/테넌트/문서 카운트)"""
```

### 3.3 SQL 쿼리 상세

**KPI 통계 쿼리**:
```sql
SELECT
    COUNT(*) as total_requests,
    COUNT(CASE WHEN success THEN 1 END) as success_count,
    COUNT(CASE WHEN NOT success THEN 1 END) as error_count,
    COUNT(CASE WHEN request_type = 'nl2sql' THEN 1 END) as nl2sql_count,
    COUNT(CASE WHEN request_type = 'rag' THEN 1 END) as rag_count
FROM tb_api_history
WHERE request_type IN ('nl2sql', 'rag')
    AND created_at >= %s AND created_at <= %s
    {AND tenant_id = %s}
```

**일별 요청 추이 쿼리**:
```sql
SELECT
    DATE(created_at) as date,
    COUNT(CASE WHEN request_type = 'nl2sql' THEN 1 END) as nl2sql,
    COUNT(CASE WHEN request_type = 'rag' THEN 1 END) as rag,
    COUNT(*) as total
FROM tb_api_history
WHERE request_type IN ('nl2sql', 'rag')
    AND created_at >= %s AND created_at <= %s
    {AND tenant_id = %s}
GROUP BY DATE(created_at)
ORDER BY date
```

**최근 요청 쿼리**:
```sql
SELECT request_id, request_type, question, success,
       response_time_ms, created_at
FROM tb_api_history
WHERE request_type IN ('nl2sql', 'rag')
    {AND tenant_id = %s}
ORDER BY created_at DESC
LIMIT %s
```

**시스템 현황 쿼리** (사용자/테넌트):
```sql
-- 활성 사용자 수
SELECT COUNT(*) as active_users FROM tb_user_role WHERE is_active = true
    {AND tenant_id = %s};

-- 활성 테넌트 수
SELECT COUNT(*) as active_tenants FROM tb_tenant WHERE is_active = true;

-- 문서 현황
SELECT
    COUNT(*) as total_documents,
    COUNT(CASE WHEN indexed = true THEN 1 END) as indexed_documents,
    COUNT(CASE WHEN indexed = false OR indexed IS NULL THEN 1 END) as pending_documents
FROM tb_docs
    {WHERE tenant_id = %s};
```

---

## 4. 프론트엔드 구현 계획

### 4.1 파일 구조

```
frontend/src/
├── api/
│   └── dashboard.js                    # (신규) 대시보드 전용 API 클라이언트
├── views/admin/
│   └── DashboardView.vue               # (수정) 대시보드 전면 개편
├── components/dashboard/               # (신규) 대시보드 전용 컴포넌트
│   ├── KpiCards.vue                    # KPI 요약 카드 4개 (1줄)
│   ├── DailyTrendChart.vue             # 일별 요청 추이 차트 (NL2SQL/RAG)
│   ├── RequestTypeChart.vue            # 검색 유형 분포 도넛 차트 (NL2SQL/RAG)
│   ├── RecentActivity.vue              # 최근 검색 요청 피드
│   └── SystemStatus.vue                # 시스템 현황 패널
└── assets/styles/mixins/
    └── _dashboard.scss                 # (신규) 대시보드 전용 mixin
```

### 4.2 API 클라이언트 (신규)

**파일**: `frontend/src/api/dashboard.js`

```javascript
import apiClient from './index'

const dashboardApi = {
  /** 대시보드 요약 데이터 조회 */
  getSummary(params = {}) {
    return apiClient.get('/api/v1/dashboard/summary', { params })
  },
}

export default dashboardApi
```

### 4.3 DashboardView.vue 구조

```vue
<template>
  <div class="dashboard-view">
    <!-- 페이지 헤더 + 기간 필터 -->
    <div class="page-header">
      <div>
        <h2>대시보드</h2>
        <p class="subtitle">MUREUM AI 지식기반 관리 현황</p>
      </div>
      <div class="header-actions">
        <el-button-group>
          <el-button :type="period === 'today' ? 'primary' : ''"
                     @click="changePeriod('today')">오늘</el-button>
          <el-button :type="period === 'week' ? 'primary' : ''"
                     @click="changePeriod('week')">이번 주</el-button>
          <el-button :type="period === 'month' ? 'primary' : ''"
                     @click="changePeriod('month')">이번 달</el-button>
        </el-button-group>
        <el-button :icon="Refresh" circle @click="refreshDashboard" />
      </div>
    </div>

    <!-- ① KPI 카드 (1줄 4개) -->
    <KpiCards :kpi="summaryData.kpi" :system="summaryData.system"
              :loading="isLoading" />

    <!-- ② 차트 영역 (2개) -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="14">
        <DailyTrendChart :data="summaryData.daily_trend"
                         :loading="isLoading" />
      </el-col>
      <el-col :xs="24" :lg="10">
        <RequestTypeChart :kpi="summaryData.kpi"
                          :loading="isLoading" />
      </el-col>
    </el-row>

    <!-- ③ 최근 활동 + 시스템 현황 -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="14">
        <RecentActivity :data="summaryData.recent_requests"
                        :loading="isLoading" />
      </el-col>
      <el-col :xs="24" :lg="10">
        <SystemStatus :system="summaryData.system"
                      :settings="settingsData"
                      :loading="isLoading" />
      </el-col>
    </el-row>

    <!-- ④ 빠른 액션 -->
    <div class="content-card">
      <h3 class="card-title">빠른 시작</h3>
      <div class="quick-actions"> ... </div>
    </div>
  </div>
</template>
```

### 4.4 컴포넌트 상세 설계

#### KpiCards.vue

```
Props:
  - kpi: { total_requests, success_rate, error_count, nl2sql_count, rag_count }
  - system: { active_users, active_tenants, total_documents, indexed_documents, pending_documents }
  - loading: boolean

레이아웃: el-row > el-col(:xs="12" :sm="12" :lg="6") × 4 → 1줄 배치

카드 구조 (각 카드):
  ┌──────────────────────┐
  │ [아이콘]  주 값       │
  │          보조 텍스트   │
  └──────────────────────┘
```

#### DailyTrendChart.vue

```
Props:
  - data: [{ date, nl2sql, rag, total }]
  - loading: boolean

차트: ECharts Stacked Bar Chart
X축: 날짜 (MM/DD), Y축: 요청 수
시리즈: NL2SQL(#67c23a), RAG(#e6a23c)
tooltip: 날짜 + 각 유형 건수 + 합계
높이: 320px
```

#### RequestTypeChart.vue

```
Props:
  - kpi: { total_requests, nl2sql_count, rag_count }
  - loading: boolean

차트: ECharts Donut Chart
중앙 텍스트: total_requests (총 건수)
색상: NL2SQL(#67c23a), RAG(#e6a23c)
범례: 이름 + 비율(%)
높이: 320px
```

#### RecentActivity.vue

```
Props:
  - data: [{ request_id, request_type, question, success, response_time_ms, created_at }]
  - loading: boolean

구조: 커스텀 리스트 (el-timeline 대신 심플 리스트)
각 항목: 시간(HH:mm) | 유형 태그 | 질문(50자) | 응답시간
유형 태그: nl2sql=success(green), rag=warning(orange)
풋터: "전체보기" → /admin/history
```

#### SystemStatus.vue

```
Props:
  - system: { active_users, active_tenants, total_documents, indexed_documents, pending_documents }
  - settings: LLM/임베딩 설정 데이터
  - loading: boolean

구조: el-descriptions (1열, border, size=small)
항목 8개: API 상태, LLM 프로바이더, LLM 모델, 임베딩 모델,
          활성 테넌트, 활성 사용자, 문서 상태(프로그레스바), 외부 DB
```

---

## 5. SCSS 스타일 가이드

### 5.1 신규 mixin: `_dashboard.scss`

```scss
// frontend/src/assets/styles/mixins/_dashboard.scss

// 차트 컨테이너 카드
@mixin chart-card {
  @include content-card;
  min-height: 360px;
}

// Activity 리스트
@mixin activity-list {
  list-style: none;
  padding: 0;
  margin: 0;

  li {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    border-bottom: 1px solid var(--border-color-lighter);

    &:last-child {
      border-bottom: none;
    }
  }
}
```

### 5.2 _index.scss에 추가

```scss
@forward 'dashboard';
```

### 5.3 기존 mixin 활용

| 용도 | mixin | 출처 |
|------|-------|------|
| 통계 카드 | `@include mx.stat-card` | `_cards.scss` |
| 콘텐츠 카드 | `@include mx.content-card` | `_layout.scss` |
| 페이지 헤더 | `@include mx.page-header` | `_layout.scss` |
| 콘텐츠 헤더 | `@include mx.content-header` | `_layout.scss` |
| 차트 영역 | `@include mx.chart-render-area` | `_chart.scss` |
| 통계 행 | `@include mx.stats-row` | `_layout.scss` |

---

## 6. 차트 라이브러리

### 6.1 ECharts (기존 사용 중)

프로젝트에서 이미 `echarts` + `vue-echarts`를 사용 중이므로 동일 라이브러리를 사용한다.

### 6.2 반응형 처리

- `ResizeObserver`로 차트 컨테이너 크기 변경 감지 → `chart.resize()`
- 모바일: 차트 높이 축소 (320px → 250px)

---

## 7. 데이터 흐름

```
┌─────────────────────────────────────────────────────────────┐
│  DashboardView.vue (onMounted + 기간 변경 시)                │
│                                                              │
│  loadDashboardData()                                         │
│    Promise.all([                                             │
│      dashboardApi.getSummary({ period }),  ← 핵심 단일 API   │
│      settingsApi.list({ category: 'llm' }),                  │
│    ])                                                        │
│    → summaryData = response[0]  (kpi, daily_trend, ...)      │
│    → settingsData = response[1] (LLM/임베딩 설정)             │
│                                                              │
│  Props 전달:                                                  │
│  ┌─────┐  ┌──────┐  ┌──────┐  ┌──────┐  ┌─────┐           │
│  │ KPI │  │Trend │  │Donut │  │Feed  │  │ Sys │           │
│  │Cards│  │Chart │  │Chart │  │List  │  │Stat │           │
│  └─────┘  └──────┘  └──────┘  └──────┘  └─────┘           │
└─────────────────────────────────────────────────────────────┘
```

**자동 새로고침**: 60초 간격 polling (setInterval) → 화면 비활성 시 중지 (visibilitychange)

---

## 8. 권한 및 멀티테넌트 처리

| 역할 | 대시보드 범위 | 사용자/테넌트 카드 | 비고 |
|------|-------------|-------------------|------|
| GLOBAL | 전체 데이터 | 전체 사용자/테넌트 수 | 테넌트 필터 드롭다운 표시 |
| TENANT | 자기 테넌트 데이터만 | 자기 테넌트 사용자 수 | 테넌트 필터 숨김 |
| USER | 본인 데이터만 | 숨김 | 축소된 대시보드 |

- `_apply_scope_filter()` 패턴은 기존 history.py와 동일하게 적용
- GLOBAL 사용자에게는 **테넌트 선택 드롭다운** 추가 (선택 시 해당 테넌트 데이터만 표시)

---

## 9. 구현 순서 (단계별)

### Phase 1: 백엔드 API

| # | 작업 | 파일 |
|---|------|------|
| 1 | DashboardService 구현 | `app/api/services/dashboard_service.py` |
| 2 | Dashboard 라우터 등록 | `app/api/routes/dashboard.py` |
| 3 | main.py에 라우터 추가 | `app/main.py` |
| 4 | 프론트엔드 API 클라이언트 | `frontend/src/api/dashboard.js` |

### Phase 2: 프론트엔드 기본 구조

| # | 작업 | 파일 |
|---|------|------|
| 1 | 대시보드 SCSS mixin | `frontend/src/assets/styles/mixins/_dashboard.scss` |
| 2 | _index.scss에 forward 추가 | `frontend/src/assets/styles/mixins/_index.scss` |
| 3 | KpiCards 컴포넌트 | `frontend/src/components/dashboard/KpiCards.vue` |
| 4 | RecentActivity 컴포넌트 | `frontend/src/components/dashboard/RecentActivity.vue` |
| 5 | SystemStatus 컴포넌트 | `frontend/src/components/dashboard/SystemStatus.vue` |
| 6 | DashboardView 개편 | `frontend/src/views/admin/DashboardView.vue` |

### Phase 3: 차트 컴포넌트 (2개)

| # | 작업 | 파일 |
|---|------|------|
| 1 | DailyTrendChart (Stacked Bar) | `frontend/src/components/dashboard/DailyTrendChart.vue` |
| 2 | RequestTypeChart (Donut) | `frontend/src/components/dashboard/RequestTypeChart.vue` |

### Phase 4: 고도화

| # | 작업 | 내용 |
|---|------|------|
| 1 | 자동 새로고침 | 60초 polling + visibilitychange |
| 2 | 테넌트 필터 | GLOBAL 역할용 테넌트 선택 드롭다운 |
| 3 | 반응형 최적화 | 모바일/태블릿 레이아웃 조정 |
| 4 | 로딩/에러 상태 | 스켈레톤 UI + 에러 fallback |

---

## 10. 파일 변경 요약

### 신규 생성 파일 (8개)

| 파일 | 유형 | 설명 |
|------|------|------|
| `app/api/routes/dashboard.py` | Backend | 대시보드 API 라우터 |
| `app/api/services/dashboard_service.py` | Backend | 대시보드 서비스 (통합 쿼리) |
| `frontend/src/api/dashboard.js` | Frontend | 대시보드 API 클라이언트 |
| `frontend/src/components/dashboard/KpiCards.vue` | Frontend | KPI 요약 카드 (1줄 4개) |
| `frontend/src/components/dashboard/DailyTrendChart.vue` | Frontend | 일별 추이 차트 |
| `frontend/src/components/dashboard/RequestTypeChart.vue` | Frontend | 유형 분포 도넛 차트 |
| `frontend/src/components/dashboard/RecentActivity.vue` | Frontend | 최근 활동 피드 |
| `frontend/src/components/dashboard/SystemStatus.vue` | Frontend | 시스템 현황 패널 |

### 수정 파일 (3개)

| 파일 | 변경 내용 |
|------|----------|
| `frontend/src/views/admin/DashboardView.vue` | 전면 개편 (기존 코드 대체) |
| `frontend/src/assets/styles/mixins/_index.scss` | `@forward 'dashboard'` 추가 |
| `app/main.py` | dashboard 라우터 등록 |

### 신규 SCSS 파일 (1개)

| 파일 | 설명 |
|------|------|
| `frontend/src/assets/styles/mixins/_dashboard.scss` | 대시보드 전용 mixin |
