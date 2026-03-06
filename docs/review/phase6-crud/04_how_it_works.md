# 4. 동작 원리 종합 — 화면은 이렇게 동작한다

## 이 문서에서 다루는 것

Phase 6에서 배운 로그인, CRUD, 대시보드 화면이 **실제로 어떻게 동작하는지** 시나리오별로 따라갑니다.

---

## 시나리오 1: 로그인부터 대시보드까지

```
① 사용자가 브라우저에서 /admin 접속
    │
    ▼
② 라우터 가드 실행 (Phase 2)
    ├─ 토큰 없음 → /login?redirect=/admin 으로 리다이렉트
    │
    ▼
③ LoginView 표시
    ├─ onMounted: isAuthenticated 확인 → false → 로그인 폼 표시
    │
    ▼
④ 사용자: admin / Win1234! 입력 → [로그인] 클릭
    │
    ▼
⑤ handleLogin()
    ├─ formRef.validate() → 검증 통과 ✅
    ├─ store.dispatch('auth/login', { loginId, password })
    │     │
    │     ▼
    │   auth Store:
    │     ├─ loginLoading = true        → 버튼 스피너 표시
    │     ├─ POST /api/v1/auth/login
    │     │     ├─ 200 OK → token, user 저장
    │     │     └─ 401 → loginError = "인증 실패"
    │     └─ loginLoading = false       → 스피너 해제
    │
    ▼ (로그인 성공)
⑥ redirect 쿼리 확인
    ├─ redirect = '/admin' → router.push('/admin')
    │
    ▼
⑦ /admin → AdminLayout 렌더링
    ├─ AppSidebar + AppHeader 표시
    ├─ router-view → children[0] = DashboardView
    │
    ▼
⑧ DashboardView.onMounted()
    ├─ loadDashboardData() → 4개 API 병렬 호출
    ├─ startAutoRefresh()  → 60초 타이머 시작
    └─ visibilitychange 리스너 등록
    │
    ▼
⑨ 대시보드 화면 표시 완료!
    ├─ KPI 카드 4개
    ├─ 차트 2개
    ├─ 최근 활동 + 시스템 현황
    └─ 빠른 시작 바로가기
```

---

## 시나리오 2: 사용자 목록 조회 + 필터링

```
① 사이드바에서 "사용자 관리" 클릭
    │
    ▼
② router-view → UsersView로 교체
    │
    ▼
③ onMounted() 실행
    ├─ Promise.all([
    │     loadUsers(),           ← GET /users?limit=20&offset=0
    │     loadRoles(),           ← GET /users/options/roles
    │     loadTenants(),         ← GET /users/options/tenants
    │     loadMenus(),           ← GET /users/options/menus
    │     loadFilterTenants()    ← GET /users/options/tenants
    │  ])
    │
    ▼
④ 테이블 렌더링
    ├─ v-loading: isLoading = true → 스피너 표시
    ├─ API 응답: { items: [...], total: 25 }
    ├─ users = items, total = 25
    └─ isLoading = false → 스피너 해제, 데이터 표시

⑤ 관리자가 테넌트 필터를 "A사"로 변경
    │
    ├─ handleTenantFilterChange('A사')
    │     ├─ filterDeptId = null        ← 부서 필터 초기화
    │     ├─ loadDeptOptions('A사')     ← A사의 부서 목록 로드
    │     ├─ currentPage = 1           ← 1페이지로 리셋
    │     └─ loadUsers()               ← 필터 적용하여 다시 조회
    │           └─ GET /users?tenant_id=2&limit=20&offset=0
    │
    ▼
⑥ 테이블에 A사 사용자만 표시
    ├─ 부서 트리 필터 활성화 (disabled → enabled)
    └─ 페이지네이션 갱신 (total 변경)
```

---

## 시나리오 3: 새 사용자 생성

```
① [새 사용자] 버튼 클릭
    │
    ▼
② openCreateDialog()
    ├─ dialogMode = 'create'
    ├─ resetForm()          ← 폼 초기화 (빈 값)
    ├─ dialogVisible = true ← 다이얼로그 열림
    └─ clearValidate()      ← 이전 에러 메시지 제거
    │
    ▼
③ 다이얼로그 표시
    ┌──────────────────────────────────────┐
    │  새 사용자 추가                   [X] │
    │  [기본정보] [메뉴 권한]               │
    │  ┌──────────────────────────────┐   │
    │  │ 로그인ID: [________]         │   │
    │  │ 이름:     [________]         │   │
    │  │ 이메일:   [________]         │   │
    │  │ 비밀번호: [________]  ← 생성 시만 │
    │  │ 역할:     [▼ 선택  ]         │   │
    │  │ 테넌트:   [▼ 선택  ]         │   │
    │  │ 부서:     [▼ 선택  ]         │   │
    │  └──────────────────────────────┘   │
    │                    [취소] [생성]      │
    └──────────────────────────────────────┘

④ 역할을 "TENANT"로 선택
    │
    ├─ handleRoleChange(roleId)
    │     ├─ 시스템 테넌트 선택되어 있으면 해제
    │     └─ TENANT의 기본 메뉴 권한 로드 → menuPermMap 갱신
    │
    ▼
⑤ 테넌트를 "A사"로 선택
    │
    ├─ handleTenantChange('A사')
    │     ├─ formData.dept_id = null  ← 부서 초기화
    │     └─ loadDeptOptions('A사')   ← A사 부서 목록 로드
    │
    ▼
⑥ [메뉴 권한] 탭으로 이동 → 기본 메뉴 확인/수정
    │
    ▼
⑦ [생성] 버튼 클릭
    │
    ├─ handleSubmit()
    │     ├─ formRef.validate()     ← 폼 검증
    │     │     ├─ 실패: activeTab = 'basic' → 기본정보 탭으로 이동
    │     │     └─ 성공 ↓
    │     │
    │     ├─ buildMenusPayload()    ← menuPermMap → 배열 변환
    │     ├─ usersApi.create({ ..., menus })  ← POST /users
    │     │     └─ 201 Created
    │     │
    │     ├─ ElMessage.success('사용자가 생성되었습니다')
    │     ├─ dialogVisible = false  ← 다이얼로그 닫힘
    │     └─ loadUsers()            ← 목록 새로고침
    │
    ▼
⑧ 테이블에 새 사용자 표시됨!
```

---

## 시나리오 4: 사용자 수정

```
① 테이블에서 "김철수" 행의 [수정] 클릭
    │
    ▼
② openEditDialog(row)
    ├─ dialogMode = 'edit'
    ├─ currentUserId = row.user_id
    ├─ 폼에 기존 데이터 채우기:
    │     formData.login_id = 'user1'          ← disabled (변경 불가)
    │     formData.display_name = '김철수'
    │     formData.email = 'kim@a.com'
    │     formData.role_id = 3
    │     formData.tenant_id = 2
    │
    ├─ loadDeptOptions(2)                ← 해당 테넌트의 부서 목록 로드
    │
    ├─ getUserMenus(userId)              ← 기존 메뉴 권한 로드
    │     └─ menuPermMap에 기존 권한 반영
    │
    └─ dialogVisible = true
    │
    ▼
③ 관리자가 이메일 수정 + 메뉴 권한 변경
    │
    ▼
④ [수정] 버튼 클릭 → handleSubmit()
    │
    ├─ validate() → 통과
    ├─ usersApi.update(userId, { email, ... })     ← PUT /users/:id
    ├─ usersApi.assignMenus(userId, menus)          ← POST /users/:id/menus
    │     ↑ 기본정보와 메뉴 권한을 별도 API로 처리!
    │
    ├─ ElMessage.success('사용자가 수정되었습니다')
    └─ loadUsers() → 목록 갱신
```

```
생성 vs 수정의 API 호출 차이:

생성: usersApi.create({ ..., menus })
      → 한 번의 API 호출로 기본정보 + 메뉴 권한 함께 전송

수정: usersApi.update(id, { ... })      ← 기본정보
    + usersApi.assignMenus(id, menus)    ← 메뉴 권한 (별도)
      → 두 번의 API 호출

왜 다른가?
  → 생성 시: 사용자가 아직 없으므로 한번에 전송
  → 수정 시: 사용자가 이미 존재, 기본정보와 권한은 독립적 리소스
```

---

## 시나리오 5: 삭제 보호 장치 동작

```
[Case A: 슈퍼유저 삭제 시도]

① 테이블에서 admin 행의 [삭제] 클릭
    │
    ▼
② 버튼이 이미 :disabled="row.is_superuser" → 클릭 불가!
   (추가로 handleDelete에서도 체크)

결과: "슈퍼유저는 삭제할 수 없습니다" 경고


[Case B: 사용자가 할당된 역할 삭제 시도]

① RolesView에서 TENANT 역할의 [삭제] 클릭
    │
    ▼
② handleDelete(row)
    ├─ row.is_system? → false (시스템 역할이 아님)
    ├─ row.user_count > 0? → true (3명 할당!)
    │     └─ ElMessage.warning('3명의 사용자가 할당되어 있습니다')
    │
    ▼
③ 삭제 중단! 먼저 사용자의 역할을 변경해야 함.


[Case C: 정상 삭제]

① 테넌트 관리 화면에서 "테스트 테넌트" [삭제] 클릭
    │
    ▼
② ElMessageBox.confirm 표시:
    ┌─────────────────────────────────┐
    │  ⚠ 테넌트 삭제                  │
    │                                 │
    │  "테스트 테넌트"를              │
    │  삭제하시겠습니까?              │
    │                                 │
    │           [취소]  [삭제]         │
    └─────────────────────────────────┘
    │
    ├─ [취소] 클릭 → catch(error === 'cancel') → 아무 일도 안 함
    └─ [삭제] 클릭 ↓

③ API 호출: DELETE /tenants/:id
    ├─ 성공 → ElMessage.success('삭제되었습니다')
    │          → loadItems() 목록 갱신
    └─ 실패 → ElMessage.error('삭제 실패')
             (서버에서도 is_system 체크 등 추가 보호)
```

---

## 시나리오 6: 문서 일괄 작업

```
① DocumentsView에서 체크박스로 문서 3개 선택
    │
    ├─ @selection-change → store.commit('document/SET_SELECTED', [1, 3, 7])
    │
    ▼
② 상단에 "3개 선택됨" + [임베딩 실행] [삭제] 버튼 표시
    │
    ├─ [임베딩 실행] 클릭
    │     │
    │     ▼
    │   store.dispatch('document/executeEmbedding', { docIds: [1, 3, 7] })
    │     ├─ API 호출
    │     ├─ 성공 → ElMessage.success('임베딩이 완료되었습니다')
    │     └─ 선택 해제: CLEAR_SELECTED
    │
    └─ [삭제] 클릭
          │
          ▼
        ElMessageBox.confirm('3개 문서를 삭제하시겠습니까?')
          ├─ [삭제] → store.dispatch('document/deleteSelected')
          │            → 성공 → ElMessage.success
          └─ [취소] → 무시
```

```
DocumentsView의 특징: Store 경유 패턴

UsersView:  컴포넌트 → API → 로컬 state
DocumentsView: 컴포넌트 → Store → API → Store state → computed

┌─────────────────┐    dispatch     ┌──────────────┐    API     ┌────────┐
│  DocumentsView  │ ──────────── → │ document     │ ─────── → │ Server │
│  (컴포넌트)      │                │ Store        │           │        │
│                 │ ← computed ─── │ state.docs   │ ← ─────── │        │
└─────────────────┘                └──────────────┘           └────────┘

이유: Detail, Edit 페이지에서도 같은 문서 데이터 공유
```

---

## 시나리오 7: 권한 기반 UI 변화

```
[GLOBAL 역할 (전체 관리자)로 문서 관리 접근]

┌──────────────────────────────────────────────┐
│ [테넌트 필터 ▼]  [용도 ▼]  [유형 ▼]  [상태 ▼]│  ← 테넌트 필터 표시!
├──────────────────────────────────────────────┤
│ ID │ 제목    │ 테넌트 │ 작업              │
│  1 │ 정책... │ 공용   │ [수정] [삭제]     │  ← 공용 문서도 수정/삭제 가능
│  2 │ FAQ..  │ A사    │ [수정] [삭제]     │
└──────────────────────────────────────────────┘


[TENANT 역할 (테넌트 관리자)로 문서 관리 접근]

┌──────────────────────────────────────────────┐
│ [용도 ▼]  [유형 ▼]  [상태 ▼]                 │  ← 테넌트 필터 없음!
├──────────────────────────────────────────────┤
│ ID │ 제목    │ 테넌트 │ 작업              │
│  1 │ 정책... │ 공용   │ (버튼 없음)       │  ← 공용 문서 수정/삭제 불가!
│  2 │ FAQ..  │ A사    │ [수정] [삭제]     │  ← 자기 테넌트만 가능
└──────────────────────────────────────────────┘
```

```javascript
// DocumentsView의 권한 체크
const isGlobal = computed(() => roleCode.value === 'GLOBAL')

// 테넌트 필터: GLOBAL만 표시
<el-select v-if="isGlobal" ... />

// 수정/삭제 버튼: 공용 문서는 GLOBAL만 가능
const canEditDoc = (row) => {
  if (isGlobal.value) return true      // GLOBAL → 전부 가능
  return row.tenant_id !== '1'          // TENANT → 공용(1) 제외
}
```

```
권한 기반 UI 패턴 정리:

┌──────────────┬─────────────────────────────────────────┐
│ 패턴          │ 구현 방법                                │
├──────────────┼─────────────────────────────────────────┤
│ 요소 숨기기    │ v-if="isGlobal"                         │
│ 버튼 비활성화  │ :disabled="row.is_superuser"            │
│ 조건부 표시    │ v-if="canEditDoc(row)"                  │
│ 테넌트 자동설정│ handleRoleChange → sysTenant 자동 할당   │
│ 데이터 범위    │ 서버에서 role_code 기반 필터링             │
└──────────────┴─────────────────────────────────────────┘

중요: UI 숨기기는 "편의 기능"일 뿐!
      진짜 보안은 서버 API의 권한 체크 (Depends(require_menu_permission))
      → 프론트에서 버튼을 숨겨도, API를 직접 호출하면 서버에서 차단
```

---

## 전체 흐름 요약

```
┌─────────────────────────────────────────────────────────────────┐
│                    화면 컴포넌트 동작 전체도                       │
│                                                                 │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│  │ LoginView │ ──→ │ Router   │ ──→ │ Layout   │               │
│  │ (인증)    │     │ Guard    │     │ (골조)   │               │
│  └──────────┘     └──────────┘     └──┬───────┘               │
│                                       │                        │
│                        ┌──────────────┼──────────────┐         │
│                        ▼              ▼              ▼         │
│                  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│                  │Dashboard │  │ CRUD View│  │ Chat View│     │
│                  │ View     │  │ (CRUD)   │  │ (Phase 7)│     │
│                  └──┬───────┘  └──┬───────┘  └──────────┘     │
│                     │             │                            │
│           ┌─────────┤       ┌─────┤                            │
│           ▼         ▼       ▼     ▼                            │
│      ┌────────┐ ┌──────┐ ┌─────┐ ┌────────┐                  │
│      │ 자식   │ │ 자식  │ │ API │ │ Store  │                  │
│      │컴포넌트│ │컴포넌트│ │직접 │ │ 경유   │                  │
│      │ (5개)  │ │ (차트)│ │호출 │ │        │                  │
│      └────────┘ └──────┘ └──┬──┘ └──┬─────┘                  │
│                              │       │                        │
│                              ▼       ▼                        │
│                         ┌──────────────┐                      │
│                         │   백엔드 API  │                      │
│                         │  (FastAPI)    │                      │
│                         └──────────────┘                      │
│                                                                │
│  데이터 흐름:                                                   │
│  API → 로컬 ref (직접) 또는 API → Store → computed (간접)       │
│                                                                │
│  UI 피드백:                                                     │
│  v-loading (테이블), :loading (버튼), ElMessage (토스트)        │
│                                                                │
│  보호 장치:                                                     │
│  폼 검증 → 확인 팝업 → UI 비활성화 → 서버 권한 체크              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 6 총정리

### 3가지 화면 유형

| 유형 | 대표 | 특징 |
|------|------|------|
| **인증 화면** | LoginView | 독립 레이아웃, 폼 검증, Store dispatch, 리다이렉트 |
| **CRUD 관리** | UsersView, RolesView, DocumentsView | 테이블+필터+페이징+다이얼로그, API/Store 연동 |
| **대시보드** | DashboardView | 자식 컴포넌트 조합, 자동 새로고침, 반응형 그리드 |

### CRUD 공통 패턴 요약

```
1. 목록 조회:  onMounted → loadItems() → el-table에 바인딩
2. 필터링:     el-select/el-input → 필터 값 변경 → loadItems()
3. 페이지네이션: el-pagination → handlePageChange → loadItems()
4. 생성/수정:  dialogMode + el-dialog → validate → API → loadItems()
5. 삭제:       confirm → API → loadItems()
6. 보호:       is_superuser, is_system, user_count 체크
7. 피드백:     v-loading, ElMessage.success/error
```

### 데이터 관리 2가지 패턴

```
패턴 A (직접): 컴포넌트 → API → 로컬 ref
  → UsersView, RolesView, TenantsView 등
  → 단순 CRUD, 한 화면에서만 사용하는 데이터

패턴 B (Store): 컴포넌트 → Store → API → Store state → computed
  → DocumentsView, DashboardView
  → 여러 화면에서 공유, 복잡한 상태 관리
```

---
> **이전**: [03_dashboard_view.md](03_dashboard_view.md) - 대시보드 화면
> **돌아가기**: [00_phase6_overview.md](00_phase6_overview.md) - Phase 6 개요
