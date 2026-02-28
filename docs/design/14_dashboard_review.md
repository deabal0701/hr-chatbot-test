# 관리자 대시보드 코드 리뷰 및 개선 계획

> 작성일: 2026-02-28
> 대상: 관리자 대시보드 (Admin Dashboard) 전체
> 분석 파일: 12개 (Backend 5 + Frontend 7)

---

## 1. 관련 파일 목록

### Backend
| 파일 | 역할 |
|------|------|
| `app/api/routes/dashboard.py` | 대시보드 라우트 (GET /summary) |
| `app/api/services/dashboard_service.py` | 대시보드 서비스 (KPI, 추이, 최근활동, 시스템) |
| `app/models/` | **대시보드 응답 모델 없음** (Dict 반환) |

### Frontend
| 파일 | 역할 |
|------|------|
| `frontend/src/views/admin/DashboardView.vue` | 메인 대시보드 뷰 |
| `frontend/src/components/dashboard/KpiCards.vue` | KPI 카드 4개 |
| `frontend/src/components/dashboard/DailyTrendChart.vue` | 일별 추이 차트 (Stacked Bar) |
| `frontend/src/components/dashboard/RequestTypeChart.vue` | 요청 유형 차트 (Donut) |
| `frontend/src/components/dashboard/RecentActivity.vue` | 최근 검색 활동 리스트 |
| `frontend/src/components/dashboard/SystemStatus.vue` | 시스템 현황 패널 |
| `frontend/src/api/dashboard.js` | API 클라이언트 |
| `frontend/src/assets/styles/mixins/_dashboard.scss` | 대시보드 스타일 mixin |

---

## 2. 보안/결함 수정 (Critical ~ High)

### 2-1. [Critical] 데이터 누출 - 시스템 메트릭 스코프 미적용

**파일**: `app/api/services/dashboard_service.py` → `_get_system_info()`

**문제**: `avg_response_ms`, `last_request_at` 쿼리에 tenant/user 스코프 필터가 없어 TENANT 관리자가 전체 시스템 성능 메트릭을 볼 수 있음

**수정**: `_add_scope_filter()`를 해당 쿼리에도 적용

### 2-2. [Critical] 다크모드 ECharts 차트 깨짐

**파일**: `DailyTrendChart.vue`, `RequestTypeChart.vue`

**문제**:
- ECharts는 Canvas 렌더링이므로 CSS 변수 `var(--text-color-primary)` 미동작
- 축 라벨, 범례, 텍스트 모두 라이트모드 색상 고정
- 기존 `useChartOptions.js` 컴포저블에 다크모드 처리 로직이 있으나 **미사용**

**수정**: `useChartOptions.js` 활용하여 테마 인식 차트 옵션 적용

### 2-3. [High] 관리자 대시보드 API 메뉴 권한 체크 누락

**파일**: `app/api/routes/dashboard.py`

**문제**: `get_current_user`만 사용, `require_menu_permission("DASHBOARD", "read")` 미적용.
프론트엔드 라우터 가드(`menuCode: 'DASHBOARD'`)로 화면 접근은 차단되지만, **API 엔드포인트가 열려있어** 인증만 되면 누구나 `GET /api/v1/dashboard/summary` 호출 가능.

**수정**: 다른 관리자 라우트와 동일하게 `require_menu_permission("DASHBOARD", "read")` 적용

**참고 - 개인 대시보드(`/dashboard`)는 권한 불필요**:
- 개인 대시보드는 모든 인증된 사용자의 개인 BI 위젯이므로 `get_current_user`만으로 적절
- 역할별 기본 메뉴 템플릿: GLOBAL/TENANT만 `DASHBOARD: can_read` 보유, USER 역할은 미포함
- USER 역할은 프론트엔드 라우터 가드에서 `/admin/dashboard` 접근 차단 → 개인 대시보드만 사용

### 2-4. [High] 이중 에러 핸들링으로 에러 소실

**파일**: `dashboard_service.py` + `dashboard.py` (라우트)

**문제**: 서비스에서 모든 예외를 catch하여 빈 데이터 반환 → 라우트의 try/except가 사실상 dead code

**수정**: 서비스의 catch-all 제거, 라우트에서 통일 처리

### 2-5. [High] 사용자 전환 시 개인 대시보드 상태 미초기화

**파일**: `frontend/src/store/modules/auth.js` (로그아웃), `frontend/src/store/modules/dashboard.js` (상태 관리)

**문제**: 로그아웃 시 `dashboard` Vuex store의 `currentDashboardId`가 초기화되지 않음.
다른 사용자로 재로그인하면 이전 사용자의 `dashboard_id`로 API 호출 → "대시보드를 찾을 수 없습니다" 에러 발생.

**수정**:
1. `auth.js:logout`에 `dispatch('dashboard/clearState', null, { root: true })` 추가
2. `dashboard.js`에 `clearState` mutation/action 추가 (`currentDashboardId = null`, `widgets = []`)
3. `fetchDashboards`에서 `currentDashboardId`가 `my_dashboards`에 없으면 강제 리셋

**완료**: 데모 위젯(getMockWidgets/resetToMock) 전체 삭제 완료.
- `dashboard.js`: `getMockWidgets()` 함수 (~130줄 목업 데이터) + `resetToMock` action 제거
- `DashboardEmptyState.vue`: "데모 위젯 불러오기" 버튼 → "위젯 추가" 버튼으로 교체 (편집모드 진입 + AddWidgetModal 열기)
- `PersonalDashboardView.vue`: `loadDemo` 핸들러 제거 → `handleAddWidgetFromEmpty` 추가
- `deleteDashboard` 버그 수정: 마지막 대시보드 삭제 시 `currentDashboardId=null`, `widgets=[]` 초기화
- `saveWidget` 버그 수정: `widgetConfig.dashboard_id`가 명시된 경우 `currentDashboardId`로 덮어쓰지 않도록 수정
- `create_dashboard` 최적화: 3개 커서 → 단일 SQL (COUNT/MAX/SUM 동시 조회)
- `_shared_dashboard_row_to_dict` 중복 제거: `_dashboard_row_to_dict` 위임으로 단순화

### 2-6. [Medium] recent_requests 쿼리에 날짜 필터 없음

**파일**: `dashboard_service.py` → `_get_recent_requests()`

**문제**: `ORDER BY created_at DESC LIMIT N` 만 있고 WHERE 날짜 조건 없음 → 대량 데이터 시 성능 저하

**수정**: `created_at >= NOW() - INTERVAL '30 days'` 조건 추가

---

## 3. 불필요/중복 코드 정리

| # | 위치 | 내용 | 조치 |
|---|------|------|------|
| 1 | `DashboardView.vue` | `goTo()` 함수 1회만 사용 | `<router-link :to>` 로 대체 |
| 2 | `RecentActivity.vue` | `formatTime()` 로컬 정의 | `utils/format.js` 통합 |
| 3 | `SystemStatus.vue` | `formatLastRequest()` 로컬 정의 | `utils/format.js` 통합 |
| 4 | `_dashboard.scss` | `chart-card` mixin 정의 후 미사용 | 삭제 또는 차트 컴포넌트에서 활용 |
| 5 | `SystemStatus.vue` | `avg_response_ms` 백엔드 반환 → 프론트 미표시 | 표시 추가 또는 백엔드 제거 |
| 6 | `DailyTrendChart` + `RequestTypeChart` | ECharts `use()` 등록 코드 완전 동일 중복 | 공통 setup 파일로 추출 |
| 7 | `DashboardView.vue` | Settings API 3회 호출이 60초마다 반복 | 최초 1회 로드 + 긴 TTL 캐시 |

---

## 4. 모듈화 개선

### 4-1. Pydantic 응답 모델 생성

**생성 파일**: `app/models/dashboard.py`

대시보드 서비스가 `Dict[str, Any]`를 반환하여 타입 검증이 없고 API 문서에 응답 구조가 표시되지 않음. `DashboardKPI`, `DailyTrendItem`, `RecentRequest`, `SystemInfo`, `DashboardSummary` 모델 생성 필요.

### 4-2. ECharts 설정 통합

어드민 대시보드 차트 2개가 인라인으로 옵션을 구성하고 색상을 하드코딩(`#67c23a`, `#e6a23c`). 기존 `useChartOptions.js` 컴포저블을 활용하면 다크모드/테마/팔레트가 자동 적용됨.

### 4-3. 날짜 포맷 유틸 통합

3곳에서 각각 다른 날짜 포맷터를 사용 중. `utils/format.js`에 `formatTime()`, `formatKoreanDateTime()` 추가 후 통합.

### 4-4. Quick Actions 컴포넌트 분리

`DashboardView.vue` 내 인라인 Quick Actions → `QuickActions.vue` 분리 + 메뉴 권한 기반 필터링 적용.

### 4-5. Settings 추출 로직 통합

`SystemStatus.vue`에서 4개의 computed가 동일 패턴으로 설정값 추출 → `useSettingsValue()` 컴포저블 생성.

---

## 5. 차트 Empty State 추가

| 컴포넌트 | 현재 | 개선 |
|----------|------|------|
| `DailyTrendChart.vue` | 빈 그리드만 표시 | "데이터가 없습니다" 메시지 |
| `RequestTypeChart.vue` | 0이 표시된 빈 도넛 | "데이터가 없습니다" 메시지 |
| `RecentActivity.vue` | 로딩과 빈 상태 구분 미흡 | 로딩/빈 상태 분리 |

---

## 6. 테스트 추가

관리자 대시보드 테스트가 **전혀 없음** (개인 대시보드 테스트 `test_12_personal_dashboard.py` — 37 TC PASSED).

**생성 파일**: `tests/test_12_dashboard.py`

필요한 테스트 케이스:
- KPI 계산 정확성 (기간별: today/week/month)
- 스코프 필터링 (GLOBAL: 전체, TENANT: 소속, USER: 본인)
- 빈 데이터 처리 (이력 없는 경우)
- 잘못된 기간 값 → 기본값 fallback 확인

---

## 7. 엔터프라이즈 기능 제안

### Phase 2 - KPI 고도화

| # | 항목 | 설명 |
|---|------|------|
| 1 | 전기간 대비 지표 | "+12% vs 어제" 트렌드 화살표 (이전 기간 비교 API 추가) |
| 2 | P50/P95/P99 응답시간 | AVG 외 퍼센타일 지표로 이상값 파악 |
| 3 | 에러 유형 분석 | 에러 코드별 분포 (AUTH, VALIDATION, LLM_ERROR 등) |
| 4 | KPI 드릴다운 | 카드 클릭 시 해당 기간 History 페이지로 이동 |
| 5 | Agent 포함 토글 | Agent 요청도 대시보드에 포함 가능한 옵션 |

### Phase 3 - 운영 모니터링

| # | 항목 | 설명 |
|---|------|------|
| 6 | 실시간 헬스체크 | `/health` 폴링 → DB/LLM/Vector 상태 개별 표시 |
| 7 | 커넥션 풀 모니터링 | DB Pool 사용률, 대기 시간 표시 |
| 8 | LLM 사용량/비용 추적 | 토큰 사용량, 예상 비용 KPI 카드 |
| 9 | 임계값 알림 | 성공률 < 95%, 응답시간 > 5초 시 경고 표시 |
| 10 | 사용자 활동 랭킹 | Top-N 사용자별 요청 수, 활성 시간대 히트맵 |

### Phase 4 - 고급 기능

| # | 항목 | 설명 |
|---|------|------|
| 11 | 커스텀 기간 선택 | DateRangePicker로 임의 기간 설정 |
| 12 | 대시보드 Export | PDF/Excel 내보내기 (차트 이미지 포함) |
| 13 | 응답 캐싱 | Redis 또는 인메모리 캐시 (30~60초 TTL) |
| 14 | WebSocket 실시간 | HTTP 폴링 → WebSocket push 전환 |
| 15 | 레이아웃 커스터마이징 | 위젯 드래그 앤 드롭 배치 |
| 16 | 감사 추적 | 대시보드 접근/조회 이력 기록 |

---

## 8. 작업 우선순위 요약

```
[내일 작업] Phase 1: 즉시 적용 (6건)
  ├─ 2-1. 시스템 메트릭 스코프 수정 (Critical)
  ├─ 2-2. 다크모드 차트 수정 (Critical)
  ├─ 2-3. 메뉴 권한 추가 (High)
  ├─ 2-4. 에러 핸들링 정리 (High)
  ├─ 2-5. recent_requests 날짜 필터 (Medium)
  └─ 5. 차트 Empty State (Medium)

[후속] 코드 정리 (7건)
  ├─ 3. 불필요/중복 코드 정리
  └─ 4. 모듈화 개선

[추가 개발] 엔터프라이즈 기능 (16건)
  ├─ Phase 2: KPI 고도화
  ├─ Phase 3: 운영 모니터링
  └─ Phase 4: 고급 기능
```
