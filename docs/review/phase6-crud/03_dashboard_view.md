# 3. DashboardView — 대시보드 화면

> **파일 위치**: `frontend/src/views/admin/DashboardView.vue` (288줄)

## 이 화면이 하는 일

관리자가 로그인 후 처음 보는 **대시보드** 화면입니다.
CRUD와 달리, **여러 자식 컴포넌트를 조합**하여 전체 현황을 한눈에 보여줍니다.

```
┌──────────────────────────────────────────────────────────────┐
│  대시보드                                                     │
│  MUREUM AI 지식기반 관리 현황        [오늘][7일][1달] [🔄]     │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 총 요청   │ │ 성공률   │ │ NL2SQL   │ │ RAG      │       │
│  │   127    │ │  98.4%   │ │   45     │ │   82     │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ← ① KpiCards                                               │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ 일별 요청 추이         │  │ 검색 유형 분포         │        │
│  │ ▉▉▊▊▋▋▌▌▍▍           │  │    ┌───┐              │        │
│  │ ▉▉▊▊▋▋▌▌▍▍           │  │   / NL2 \             │        │
│  │ ▉▉▊▊▋▋▌▌▍▍           │  │  │ SQL   │ RAG        │        │
│  └──────────────────────┘  │   \ 35% /  65%        │        │
│  ← ② DailyTrendChart       │    └───┘              │        │
│                             └──────────────────────┘        │
│                             ← ③ RequestTypeChart            │
├──────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ 최근 검색 요청         │  │ 시스템 현황            │        │
│  │ · "2024년 입사자..."   │  │ LLM: gpt-4o          │        │
│  │ · "재택근무 정책..."   │  │ 사용자: 12명           │        │
│  │ · "부서별 인원..."     │  │ 문서: 45개 (임베딩 40) │        │
│  └──────────────────────┘  └──────────────────────┘        │
│  ← ④ RecentActivity         ← ⑤ SystemStatus               │
├──────────────────────────────────────────────────────────────┤
│  빠른 시작                                                   │
│  [💬 자연어 검색] [📁 문서 등록] [⬆ 임베딩] [👤 사용자] [⚙ 설정]│
│  ← ⑥ 빠른 액션 (router-link)                                │
└──────────────────────────────────────────────────────────────┘
```

---

## Template 구조 — 자식 컴포넌트 조합

```html
<template>
  <div class="dashboard-view">
    <!-- 헤더 + 기간 필터 -->
    <div class="page-header">
      <div>
        <h2>대시보드</h2>
        <p class="subtitle">MUREUM AI 지식기반 관리 현황</p>
      </div>
      <div class="header-actions">
        <el-button-group>
          <el-button :type="period === 'today' ? 'primary' : ''" @click="changePeriod('today')">
            오늘
          </el-button>
          <!-- ... 7일, 1달 -->
        </el-button-group>
        <el-button :icon="Refresh" circle @click="loadDashboardData" :loading="isLoading" />
      </div>
    </div>

    <!-- ① KPI 카드 -->
    <KpiCards :kpi="summaryData.kpi" :system="summaryData.system" :loading="isLoading" />

    <!-- ② + ③ 차트 2개 -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <DailyTrendChart :data="summaryData.daily_trend" :loading="isLoading" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <RequestTypeChart :kpi="summaryData.kpi" :loading="isLoading" />
      </el-col>
    </el-row>

    <!-- ④ + ⑤ 최근활동 + 시스템 현황 -->
    <el-row :gutter="20">
      <el-col :xs="24" :lg="12">
        <RecentActivity :data="summaryData.recent_requests" :loading="isLoading" />
      </el-col>
      <el-col :xs="24" :lg="12">
        <SystemStatus :system="summaryData.system" :settings="settingsData" :loading="isLoading" />
      </el-col>
    </el-row>

    <!-- ⑥ 빠른 액션 -->
    <div class="content-card">
      <h3 class="card-title">빠른 시작</h3>
      <div class="quick-actions">
        <router-link to="/admin/chat" class="action-item"> ... </router-link>
        <!-- ... -->
      </div>
    </div>
  </div>
</template>
```

**CRUD 화면과의 차이:**

```
CRUD 화면 (UsersView):              대시보드 (DashboardView):
─────────────────────────           ─────────────────────────
· 단일 데이터 소스 (users)           · 복수 데이터 소스 (kpi, trend, recent...)
· 하나의 큰 컴포넌트                 · 5개 자식 컴포넌트 조합
· 필터 + 테이블 + 페이지네이션        · 카드 + 차트 + 리스트 + 상태 패널
· 사용자 액션 (CRUD) 중심            · 정보 표시(읽기) 중심
· 수동 새로고침                      · 자동 새로고침 (60초)
```

---

## 자식 컴포넌트 목록

```
frontend/src/components/dashboard/
├── KpiCards.vue          ← KPI 요약 카드 (총요청, 성공률, NL2SQL, RAG)
├── DailyTrendChart.vue   ← 일별 요청 추이 (Stacked Bar Chart)
├── RequestTypeChart.vue  ← 검색 유형 분포 (Donut Chart)
├── RecentActivity.vue    ← 최근 검색 요청 피드
└── SystemStatus.vue      ← 시스템 현황 패널
```

```
DashboardView의 역할 = "오케스트라 지휘자"

DashboardView (지휘자)
    │
    ├─ loadDashboardData()로 API 호출 (악보 준비)
    │
    ├─ summaryData를 자식들에게 props로 전달 (파트 분배)
    │   ├─ KpiCards       ← :kpi, :system
    │   ├─ DailyTrendChart ← :data (daily_trend)
    │   ├─ RequestTypeChart ← :kpi
    │   ├─ RecentActivity  ← :data (recent_requests)
    │   └─ SystemStatus    ← :system, :settings
    │
    └─ 기간 변경, 자동 새로고침 관리 (템포 조절)
```

---

## 데이터 로드 — 병렬 API 호출

```javascript
const loadDashboardData = async () => {
  isLoading.value = true
  try {
    const [summary, llmSettings, embeddingSettings, nl2sqlSettings] = await Promise.all([
      dashboardApi.getSummary({ period: period.value }),           // ① 대시보드 요약
      settingsApi.getCategory('llm').catch(() => ({})),            // ② LLM 설정
      settingsApi.getCategory('embedding').catch(() => ({})),      // ③ 임베딩 설정
      settingsApi.getCategory('nl2sql').catch(() => ({})),         // ④ NL2SQL 설정
    ])

    summaryData.value = summary || summaryData.value
    settingsData.value = {
      llm: llmSettings?.settings || llmSettings?.items || [],
      embedding: embeddingSettings?.settings || embeddingSettings?.items || [],
      nl2sql: nl2sqlSettings?.settings || nl2sqlSettings?.items || [],
    }
  } catch (error) {
    console.error('Dashboard data load error:', error)
  } finally {
    isLoading.value = false
  }
}
```

```
4개 API를 병렬 호출:

┌─ dashboardApi.getSummary ──────▶ summaryData (KPI, 추이, 최근활동, 시스템)
│
├─ settingsApi('llm')     ────▶ settingsData.llm
│
├─ settingsApi('embedding') ──▶ settingsData.embedding
│
└─ settingsApi('nl2sql')  ────▶ settingsData.nl2sql

.catch(() => ({})) 의 의미:
  → 설정 API가 실패해도 빈 객체를 반환 → 대시보드 전체가 깨지지 않음!
  → "하나가 실패해도 나머지는 보여주자" 전략
```

### summaryData 구조

```javascript
const summaryData = ref({
  kpi: {
    total_requests: 0,    // 총 요청 수
    success_rate: 0,       // 성공률
    error_count: 0,        // 에러 수
    nl2sql_count: 0,       // NL2SQL 요청 수
    rag_count: 0           // RAG 요청 수
  },
  daily_trend: [],          // 일별 추이 데이터 (차트용)
  recent_requests: [],      // 최근 요청 목록
  system: {
    active_users: 0,        // 활성 사용자 수
    active_tenants: 0,      // 활성 테넌트 수
    total_documents: 0,     // 전체 문서 수
    indexed_documents: 0,   // 임베딩 완료 문서 수
    pending_documents: 0    // 임베딩 대기 문서 수
  }
})
```

---

## 기간 필터 — 버튼 그룹

```javascript
const period = ref('today')    // 'today', 'week', 'month'

const changePeriod = (newPeriod) => {
  period.value = newPeriod     // 기간 변경
  loadDashboardData()          // 데이터 다시 로드
}
```

```html
<el-button-group>
  <el-button :type="period === 'today' ? 'primary' : ''" @click="changePeriod('today')">
    오늘
  </el-button>
  <el-button :type="period === 'week' ? 'primary' : ''" @click="changePeriod('week')">
    최근 7일
  </el-button>
  <el-button :type="period === 'month' ? 'primary' : ''" @click="changePeriod('month')">
    최근 1달
  </el-button>
</el-button-group>
```

```
버튼 동작:

[오늘]  [최근 7일]  [최근 1달]      ← period = 'today' (기본)
 ▀▀▀▀

[오늘]  [최근 7일]  [최근 1달]      ← "최근 7일" 클릭
         ▀▀▀▀▀▀▀

:type="period === 'week' ? 'primary' : ''"
  → 선택된 버튼만 파란색(primary), 나머지는 기본색

changePeriod('week')
  → period = 'week'
  → loadDashboardData() → API에 period='week' 전달
  → 서버에서 최근 7일 데이터 반환
```

---

## 자동 새로고침 — 60초 간격

```javascript
let refreshTimer = null
const REFRESH_INTERVAL = 60000        // 60초 = 1분

const startAutoRefresh = () => {
  stopAutoRefresh()                    // 기존 타이머 제거 (중복 방지)
  refreshTimer = setInterval(() => {
    if (!document.hidden) {            // 화면이 보이는 상태일 때만!
      loadDashboardData()
    }
  }, REFRESH_INTERVAL)
}

const stopAutoRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
}
```

```
자동 새로고침 흐름:

onMounted()
    │
    ├─ loadDashboardData()    ← 최초 1회 로드
    ├─ startAutoRefresh()     ← 60초 타이머 시작
    └─ visibilitychange 리스너 등록
    │
    ▼ 60초 후...
    │
    ├─ document.hidden === false? (화면 보이는 중?)
    │   ├─ Yes → loadDashboardData() 실행
    │   └─ No  → 건너뜀 (다른 탭 보는 중이면 API 호출 안 함)
    │
    ▼ 60초 후... (반복)
    │
onBeforeUnmount()
    └─ stopAutoRefresh()      ← 타이머 제거 (메모리 누수 방지!)
```

### 탭 전환 시 즉시 갱신

```javascript
const handleVisibilityChange = () => {
  if (!document.hidden) {
    loadDashboardData()    // 탭이 다시 보이면 즉시 새로고침
  }
}

onMounted(() => {
  document.addEventListener('visibilitychange', handleVisibilityChange)
})

onBeforeUnmount(() => {
  document.removeEventListener('visibilitychange', handleVisibilityChange)
})
```

```
시나리오: 관리자가 다른 탭에서 작업 후 대시보드로 돌아옴

1. 대시보드 열림 → 데이터 로드 + 60초 타이머
2. 다른 탭으로 전환 → document.hidden = true → 타이머는 돌지만 API 호출 안 함
3. 5분 후 대시보드 탭 클릭 → document.hidden = false
   → visibilitychange 이벤트 발생 → 즉시 데이터 갱신!

이게 없으면:
  → 5분 전 데이터를 보다가 최대 60초를 기다려야 갱신
  → 사용자 경험 나쁨 😣

이게 있으면:
  → 탭 전환 즉시 최신 데이터! ✅
```

---

## 반응형 그리드 — el-row + el-col

```html
<el-row :gutter="20">
  <el-col :xs="24" :lg="12">
    <DailyTrendChart />
  </el-col>
  <el-col :xs="24" :lg="12">
    <RequestTypeChart />
  </el-col>
</el-row>
```

```
el-col의 반응형 props:

:xs="24"  → 모바일 (< 768px):  24/24 = 전체 너비 (세로 배치)
:lg="12"  → 데스크탑 (≥ 1200px): 12/24 = 절반 너비 (가로 배치)

Element Plus 그리드: 24등분 시스템 (12 = 50%, 8 = 33%, 6 = 25%)

데스크탑:
┌─────────────────┐ ┌─────────────────┐
│ DailyTrendChart │ │ RequestTypeChart│
│   (12/24=50%)   │ │   (12/24=50%)  │
└─────────────────┘ └─────────────────┘

모바일:
┌───────────────────────────────────┐
│ DailyTrendChart (24/24=100%)      │
└───────────────────────────────────┘
┌───────────────────────────────────┐
│ RequestTypeChart (24/24=100%)     │
└───────────────────────────────────┘

:gutter="20" → 컬럼 사이 20px 간격
```

---

## 빠른 액션 — router-link

```html
<div class="quick-actions">
  <router-link to="/admin/chat" class="action-item">
    <el-icon :size="32" class="icon-primary"><ChatDotRound /></el-icon>
    <span>자연어 검색</span>
    <p>AI 기반 문서 검색, 데이터 조회</p>
  </router-link>

  <div class="action-item" @click="goTo('/admin/documents?indexed=false')">
    <el-icon :size="32" class="icon-warning"><Upload /></el-icon>
    <span>임베딩 실행</span>
    <p>대기 중인 문서 처리</p>
  </div>
</div>
```

```
router-link vs @click:

① router-link to="/admin/chat"
   → <a> 태그로 렌더링 → SEO 친화적, 마우스 오른쪽 클릭 메뉴 지원
   → 단순 경로일 때 사용

② @click="goTo('/admin/documents?indexed=false')"
   → 자바스크립트로 이동 → 쿼리 파라미터가 복잡할 때
   → router.push(path) 호출
```

---

## 리소스 정리 — onBeforeUnmount

```javascript
onBeforeUnmount(() => {
  stopAutoRefresh()                                           // 타이머 제거
  document.removeEventListener('visibilitychange', handleVisibilityChange)  // 리스너 제거
})
```

```
왜 정리해야 하는가?

onMounted에서 등록한 것:
  ① setInterval (60초 타이머)
  ② addEventListener (탭 전환 감지)

다른 페이지로 이동하면 DashboardView는 파괴됨
하지만 타이머와 리스너는 자동으로 사라지지 않음!

정리 안 하면:
  · 타이머: 대시보드 안 보는데도 60초마다 API 호출 → 서버 부하 😣
  · 리스너: 메모리에 남아있음 → 메모리 누수 😣

→ onBeforeUnmount에서 반드시 정리! ✅
```

---

## 리뷰 체크리스트

- [x] 5개 자식 컴포넌트를 조합하는가? → KPI, Trend, Type, Recent, System ✅
- [x] 데이터를 병렬로 로드하는가? → `Promise.all` 4개 API ✅
- [x] 설정 API 실패 시 전체가 깨지지 않는가? → `.catch(() => ({}))` ✅
- [x] 기간 필터가 동작하는가? → `period` + API 파라미터 ✅
- [x] 자동 새로고침이 있는가? → 60초 `setInterval` ✅
- [x] 화면 비활성 시 불필요한 호출을 방지하는가? → `document.hidden` 체크 ✅
- [x] 탭 복귀 시 즉시 갱신하는가? → `visibilitychange` 리스너 ✅
- [x] 페이지 떠날 때 리소스를 정리하는가? → `onBeforeUnmount` ✅
- [x] 반응형 레이아웃인가? → `el-row/el-col` + `xs/lg` ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **자식 컴포넌트 조합** | 부모가 데이터를 로드하고, props로 자식에게 분배 |
| **Promise.all** | 여러 API를 동시에 호출 → 로딩 시간 단축 |
| **.catch(() => ({}))** | 개별 API 실패를 격리 → 부분 실패 허용 |
| **setInterval** | 주기적 함수 실행 (자동 새로고침) |
| **document.hidden** | 페이지 가시성 API. 탭이 보이는지 확인 |
| **visibilitychange** | 탭 전환 감지 이벤트 |
| **onBeforeUnmount** | 컴포넌트 파괴 직전 실행. 리소스 정리 |
| **el-row + el-col** | Element Plus 그리드. 24등분, 반응형 breakpoint |
| **el-button-group** | 연결된 버튼 그룹. 라디오 버튼처럼 사용 |

---
> **이전**: [02_crud_pattern.md](02_crud_pattern.md) - CRUD 공통 패턴
> **다음**: [04_how_it_works.md](04_how_it_works.md) - 동작 원리 종합
