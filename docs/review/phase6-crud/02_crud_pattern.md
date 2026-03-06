# 2. CRUD 공통 패턴 — 관리 화면은 이렇게 만든다

> **대표 파일**: `UsersView.vue` (846줄), `RolesView.vue` (432줄), `DocumentsView.vue` (478줄)

## CRUD란?

**Create**(생성), **Read**(조회), **Update**(수정), **Delete**(삭제)의 약자입니다.
관리 화면은 거의 모든 곳에서 이 4가지 작업을 반복합니다.

```
CRUD = 데이터 관리의 4가지 기본 작업

Create  → "새 사용자" 버튼 → 다이얼로그 → API POST   → 목록 새로고침
Read    → 페이지 진입      → API GET     → 테이블에 표시
Update  → "수정" 버튼      → 다이얼로그 → API PUT    → 목록 새로고침
Delete  → "삭제" 버튼      → 확인 팝업  → API DELETE → 목록 새로고침
```

---

## 공통 구조 — 모든 CRUD 화면이 따르는 패턴

### Template 구조

```html
<template>
  <div class="xxxxx-view">
    <!-- ① 페이지 헤더 -->
    <div class="page-header">
      <div>
        <h2>사용자 관리</h2>
        <p class="subtitle">설명 텍스트...</p>
      </div>
    </div>

    <div class="content-card">
      <!-- ② 툴바 (필터 + 액션 버튼) -->
      <div class="toolbar">
        <el-input ... />           <!-- 검색 -->
        <el-select ... />          <!-- 필터 -->
        <div class="flex-1" />     <!-- 빈 공간 (오른쪽 밀기) -->
        <el-button @click="openCreateDialog">새 항목</el-button>
      </div>

      <!-- ③ 데이터 테이블 -->
      <el-table :data="items" v-loading="isLoading">
        <el-table-column ... />
        <el-table-column label="동작">
          <template #default="{ row }">
            <el-button @click="openEditDialog(row)">수정</el-button>
            <el-button @click="handleDelete(row)">삭제</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- ④ 페이지네이션 -->
      <el-pagination ... />
    </div>

    <!-- ⑤ 생성/수정 다이얼로그 (숨겨져 있다가 표시) -->
    <el-dialog v-model="dialogVisible">
      <el-form ref="formRef" :model="formData" :rules="formRules">
        ...
      </el-form>
    </el-dialog>
  </div>
</template>
```

### Script 구조

```javascript
<script setup>
// ① 상태 변수
const isLoading = ref(false)
const isSaving = ref(false)
const items = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const dialogVisible = ref(false)
const dialogMode = ref('create')  // 'create' 또는 'edit'
const formRef = ref(null)

// ② 폼 데이터
const formData = reactive({ ... })

// ③ 검증 규칙
const formRules = { ... }

// ④ 데이터 로드 함수
const loadItems = async () => { ... }

// ⑤ 다이얼로그 열기/닫기
const openCreateDialog = () => { ... }
const openEditDialog = (row) => { ... }

// ⑥ 폼 제출
const handleSubmit = async () => { ... }

// ⑦ 삭제 처리
const handleDelete = async (row) => { ... }

// ⑧ 초기 로드
onMounted(() => { loadItems() })
</script>
```

---

## 패턴 1: 데이터 목록 조회 (Read)

### UsersView — 필터 + 페이지네이션

```javascript
const loadUsers = async () => {
  isLoading.value = true             // ① 로딩 시작
  try {
    const params = {
      limit: pageSize.value,                              // 페이지당 건수
      offset: (currentPage.value - 1) * pageSize.value    // 건너뛸 건수
    }
    // 필터 조건 추가 (값이 있을 때만)
    if (filterTenantId.value !== null) params.tenant_id = filterTenantId.value
    if (filterActive.value !== null) params.is_active = filterActive.value
    if (searchKeyword.value.trim()) params.keyword = searchKeyword.value.trim()

    const result = await usersApi.list(params)    // ② API 호출
    users.value = result.items || []              // ③ 데이터 반영
    total.value = result.total || 0
  } catch {
    ElMessage.error('사용자 목록 로드 실패')        // ④ 에러 처리
  } finally {
    isLoading.value = false                        // ⑤ 로딩 종료
  }
}
```

```
API 응답 구조:
{
  "items": [
    { "user_id": 1, "login_id": "admin", "display_name": "관리자", ... },
    { "user_id": 2, "login_id": "user1", "display_name": "김철수", ... }
  ],
  "total": 25      ← 전체 건수 (페이지네이션에 사용)
}

offset 계산:
  page 1: offset = (1-1) * 20 = 0    → 1~20번째 데이터
  page 2: offset = (2-1) * 20 = 20   → 21~40번째 데이터
  page 3: offset = (3-1) * 20 = 40   → 41~60번째 데이터
```

### RolesView — 단순 목록 (페이지네이션 없음)

```javascript
const loadRoles = async () => {
  isLoading.value = true
  try {
    const result = await rolesApi.list()   // 전체 목록 조회 (필터 없음)
    roles.value = result.items || []
  } catch {
    ElMessage.error('역할 목록 로드 실패')
  } finally {
    isLoading.value = false
  }
}
```

```
UsersView vs RolesView:

UsersView: 사용자 수백 명 → 필터 + 페이지네이션 필요
RolesView: 역할 3~5개    → 전체 목록 한번에 표시

→ 데이터 양에 따라 패턴을 조절!
```

### DocumentsView — Store 경유 조회

```javascript
// DocumentsView는 Store를 경유하여 데이터 관리
const documents = computed(() => store.state.document.documents)
const isLoading = computed(() => store.state.document.isLoading)
const total = computed(() => store.state.document.pagination.total)

onMounted(() => {
  store.dispatch('document/fetchDocuments')    // Store 액션으로 조회
})
```

```
3가지 조회 패턴 비교:

① UsersView:   컴포넌트 → API 직접 호출 → 로컬 ref에 저장
② RolesView:   컴포넌트 → API 직접 호출 → 로컬 ref에 저장 (필터 없음)
③ DocumentsView: 컴포넌트 → Store dispatch → Store에서 API 호출 → Store state → computed

① 언제 직접 호출?  → 단순 CRUD, 다른 컴포넌트와 상태 공유 불필요할 때
③ 언제 Store 경유?  → 여러 컴포넌트에서 같은 데이터를 사용할 때
                      (DocumentsView, DocumentDetailView, DocumentEditView)
```

---

## 패턴 2: 데이터 테이블 (el-table)

### 기본 테이블 구조

```html
<el-table
  v-loading="isLoading"                              <!-- 로딩 스피너 -->
  :data="users"                                      <!-- 데이터 배열 -->
  :default-sort="{ prop: 'user_id', order: 'ascending' }"  <!-- 기본 정렬 -->
>
```

### 열(Column) 유형별 패턴

```html
<!-- ① 단순 텍스트 -->
<el-table-column prop="login_id" label="로그인 ID" min-width="90" sortable />

<!-- ② 커스텀 표시 (슬롯 사용) -->
<el-table-column label="역할" min-width="90">
  <template #default="{ row }">           <!-- row = 해당 행의 데이터 -->
    <el-tag :type="roleTagType(row.role.role_code)" size="small">
      {{ row.role.role_name }}
    </el-tag>
  </template>
</el-table-column>

<!-- ③ 상태 표시 (조건부 색상) -->
<el-table-column prop="is_active" label="상태" width="60">
  <template #default="{ row }">
    <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
      {{ row.is_active ? '활성' : '비활성' }}
    </el-tag>
  </template>
</el-table-column>

<!-- ④ 날짜 포맷팅 -->
<el-table-column prop="last_login_at" label="최근 로그인" width="150">
  <template #default="{ row }">
    {{ formatDateTime(row.last_login_at) }}
  </template>
</el-table-column>

<!-- ⑤ 액션 버튼 (수정/삭제) -->
<el-table-column label="동작" width="120">
  <template #default="{ row }">
    <el-button link type="primary" @click="openEditDialog(row)">수정</el-button>
    <el-button link type="danger" @click="handleDelete(row)"
               :disabled="row.is_superuser">삭제</el-button>
                <!-- ↑ 슈퍼유저는 삭제 불가! -->
  </template>
</el-table-column>
```

```
#default="{ row }" 란?

el-table은 각 행을 렌더링할 때 슬롯에 데이터를 전달합니다:
  · row: 현재 행의 데이터 객체
  · $index: 현재 행의 인덱스

{ row } 는 구조 분해 할당 (destructuring):
  = scope.row 와 동일

사용 예:
  row.login_id      → "admin"
  row.is_active     → true
  row.role.role_code → "GLOBAL"
```

### 태그 색상 매핑

```javascript
// 역할 코드 → 태그 색상
const roleTagType = (roleCode) => {
  if (roleCode === 'GLOBAL') return 'danger'     // 빨간색
  if (roleCode === 'TENANT') return 'warning'    // 주황색
  return 'info'                                    // 회색
}

// RolesView: scope_level → 색상
const SCOPE_TAGS = { 0: 'danger', 1: 'warning', 2: '', 3: 'info' }
```

```
el-tag type별 색상:

'primary'  → 파란색   (기본)
'success'  → 녹색     (성공/활성)
'warning'  → 주황색   (경고/테넌트)
'danger'   → 빨간색   (위험/전체관리자)
'info'     → 회색     (정보/비활성)
''         → 기본색   (테마 기본)
```

---

## 패턴 3: 페이지네이션

```html
<el-pagination
  :current-page="currentPage"              <!-- 현재 페이지 -->
  :page-size="pageSize"                    <!-- 페이지당 건수 -->
  :page-sizes="[10, 20, 50, 100]"          <!-- 건수 선택 옵션 -->
  :total="total"                           <!-- 전체 건수 -->
  layout="total, sizes, prev, pager, next, jumper"
  @size-change="handleSizeChange"           <!-- 건수 변경 시 -->
  @current-change="handlePageChange"        <!-- 페이지 변경 시 -->
/>
```

```javascript
const handlePageChange = (page) => {
  currentPage.value = page       // 페이지 번호 갱신
  loadUsers()                    // 데이터 다시 로드
}

const handleSizeChange = (size) => {
  pageSize.value = size          // 건수 갱신
  currentPage.value = 1          // 첫 페이지로 리셋 (중요!)
  loadUsers()
}
```

```
layout 속성의 구성요소:

total  → "총 25건"
sizes  → [10 ▼] 건씩 보기
prev   → ◀ (이전 페이지)
pager  → 1 2 3 4 5
next   → ▶ (다음 페이지)
jumper → [ ] 페이지로 이동

결과:
┌─────────────────────────────────────────────────┐
│ 총 25건   20건/페이지 ▼   ◀  1  [2]  3  ▶  이동 │
└─────────────────────────────────────────────────┘
```

---

## 패턴 4: 생성/수정 다이얼로그

### 하나의 다이얼로그로 생성과 수정을 모두 처리

```javascript
const dialogMode = ref('create')        // 'create' 또는 'edit'
const dialogVisible = ref(false)
const currentUserId = ref(null)         // 수정 시 사용자 ID 저장
```

```html
<el-dialog
  v-model="dialogVisible"
  :title="dialogMode === 'create' ? '새 사용자 추가' : '사용자 수정'"
>
```

```
왜 다이얼로그를 하나만 쓰는가?

생성 폼과 수정 폼은 거의 동일 → 다이얼로그를 2개 만들면 중복!

해결: dialogMode 변수로 구분
  · 'create': 제목 = "새 사용자 추가", 비밀번호 필드 표시
  · 'edit':   제목 = "사용자 수정", 비밀번호 필드 숨김, login_id 비활성화
```

### 생성 다이얼로그 열기

```javascript
const openCreateDialog = () => {
  dialogMode.value = 'create'
  currentUserId.value = null
  activeTab.value = 'basic'
  resetForm()                          // 폼 초기화
  dialogVisible.value = true           // 다이얼로그 열기
  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()   // 검증 에러 초기화
  })
}
```

### 수정 다이얼로그 열기

```javascript
const openEditDialog = async (row) => {
  dialogMode.value = 'edit'
  currentUserId.value = row.user_id

  // 기존 데이터를 폼에 채우기
  formData.login_id = row.login_id
  formData.email = row.email
  formData.display_name = row.display_name || ''
  formData.tenant_id = row.tenant_id
  formData.role_id = row.role?.role_id || null
  formData.is_active = row.is_active
  formData.password = ''               // 비밀번호는 항상 빈 값

  dialogVisible.value = true

  // 부서 목록 로드 (테넌트가 있을 때만)
  if (row.tenant_id) {
    await loadDeptOptions(row.tenant_id)
  }

  // 사용자 메뉴 권한 로드
  initMenuPermMap()
  try {
    const result = await usersApi.getUserMenus(row.user_id)
    for (const um of (result.menus || [])) {
      if (menuPermMap[um.menu_id]) {
        menuPermMap[um.menu_id].can_create = um.can_create
        menuPermMap[um.menu_id].can_read = um.can_read
        // ...
      }
    }
  } catch { /* 실패 시 빈 상태 유지 */ }

  nextTick(() => {
    if (formRef.value) formRef.value.clearValidate()
  })
}
```

```
생성 vs 수정 다이얼로그 비교:

              생성                        수정
─────────────────────────────────────────────────────
폼 데이터    빈 값으로 초기화            row 데이터로 채우기
비밀번호     필수 입력                   표시 안 함
login_id    입력 가능                   비활성화 (변경 불가)
메뉴 권한    역할 기본값 로드            기존 권한 로드
API 호출     POST /users               PUT /users/:id
```

---

## 패턴 5: 폼 검증과 제출

### 검증 규칙 정의

```javascript
const formRules = {
  login_id: [
    { required: true, message: '로그인 ID를 입력하세요', trigger: 'blur' },
    { min: 3, message: '3자 이상 입력하세요', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '이메일을 입력하세요', trigger: 'blur' },
    { type: 'email', message: '올바른 이메일 형식이 아닙니다', trigger: 'blur' }
  ],
  role_id: [
    { required: true, message: '역할을 선택하세요', trigger: 'change' }
  ],
  tenant_id: [
    {
      // 커스텀 검증: GLOBAL이 아닌 역할이면 테넌트 필수
      validator: (_rule, value, callback) => {
        if (selectedRoleCode.value && selectedRoleCode.value !== 'GLOBAL' && !value) {
          callback(new Error('테넌트를 선택하세요'))
        } else {
          callback()
        }
      },
      trigger: 'change'
    }
  ]
}
```

```
검증 규칙 유형:

① required: true         → 필수 입력
② min: 3                 → 최소 글자 수
③ type: 'email'          → 이메일 형식 검증 (xxx@xxx.xxx)
④ pattern: /^[A-Z0-9_]+$/  → 정규식 패턴 (RolesView)
⑤ validator: (rule, value, callback) => { ... }
                          → 커스텀 검증 함수 (조건부 필수 등)

trigger 종류:
  'blur'   → 입력란에서 포커스가 떠날 때 검증
  'change' → 값이 변경될 때 검증 (주로 el-select용)
```

### 폼 제출 흐름

```javascript
const handleSubmit = async () => {
  // ① 폼 검증
  if (formRef.value) {
    const valid = await formRef.value.validate().catch(() => false)
    if (!valid) {
      activeTab.value = 'basic'    // 에러가 있는 탭으로 이동
      return
    }
  }

  isSaving.value = true            // ② 저장 중 표시
  try {
    if (dialogMode.value === 'create') {
      // ③-A 생성
      await usersApi.create({ ... })
      ElMessage.success('사용자가 생성되었습니다')
    } else {
      // ③-B 수정
      await usersApi.update(currentUserId.value, { ... })
      // 메뉴 권한 별도 업데이트
      await usersApi.assignMenus(currentUserId.value, menus)
      ElMessage.success('사용자가 수정되었습니다')
    }
    dialogVisible.value = false    // ④ 다이얼로그 닫기
    await loadUsers()              // ⑤ 목록 새로고침
  } catch (error) {
    ElMessage.error(error.message || '작업 실패')
  } finally {
    isSaving.value = false
  }
}
```

```
제출 흐름도:

[생성/수정] 버튼 클릭
    │
    ▼
validate() ──→ 실패 → 에러 표시 (빨간색 메시지)
    │
    성공 ↓
    │
    ├─ create → POST /api/v1/users
    │           └─ 성공 → "생성되었습니다" 토스트
    │
    └─ edit   → PUT /api/v1/users/:id
                ├─ 기본정보 수정
                └─ POST /api/v1/users/:id/menus (권한 별도)
                   └─ 성공 → "수정되었습니다" 토스트
    │
    ▼
다이얼로그 닫기 → 목록 새로고침
```

---

## 패턴 6: 삭제 처리

### 삭제 확인 + 보호 장치

```javascript
// UsersView
const handleDelete = async (row) => {
  // 보호 장치 ①: 슈퍼유저 삭제 방지
  if (row.is_superuser) {
    ElMessage.warning('슈퍼유저는 삭제할 수 없습니다')
    return
  }

  try {
    // 보호 장치 ②: 사용자 확인 팝업
    await ElMessageBox.confirm(
      `"${row.display_name || row.login_id}" 사용자를 삭제하시겠습니까?`,
      '사용자 삭제',
      { confirmButtonText: '삭제', cancelButtonText: '취소', type: 'warning' }
    )

    // API 호출
    await usersApi.delete(row.user_id)
    ElMessage.success('사용자가 삭제되었습니다')
    await loadUsers()    // 목록 새로고침
  } catch (error) {
    if (error === 'cancel') return   // "취소" 클릭 시 무시
    ElMessage.error(error.message || '삭제 실패')
  }
}
```

```javascript
// RolesView — 추가 보호 장치
const handleDelete = async (row) => {
  // 보호 ①: 시스템 역할 삭제 방지
  if (row.is_system) {
    ElMessage.warning('시스템 기본 역할은 삭제할 수 없습니다')
    return
  }
  // 보호 ②: 사용자가 할당된 역할 삭제 방지
  if (row.user_count > 0) {
    ElMessage.warning(`이 역할에 ${row.user_count}명의 사용자가 할당되어 있습니다`)
    return
  }
  // ... 확인 후 삭제
}
```

```
삭제 보호 장치 정리:

UsersView:
  ① is_superuser → 삭제 버튼 disabled + 경고
  ② ElMessageBox.confirm → "정말 삭제?" 확인

RolesView:
  ① is_system → 시스템 역할 보호
  ② user_count > 0 → 사용 중인 역할 보호
  ③ ElMessageBox.confirm → 확인

DocumentsView:
  ① canDeleteDoc(row) → TENANT 역할은 공용 문서 삭제 불가
  ② ElMessageBox.confirm → 확인
  ③ 일괄 삭제도 지원 (선택 후 삭제)
```

---

## 패턴 7: 필터와 검색

### UsersView — 복합 필터

```html
<div class="toolbar">
  <!-- 키워드 검색 -->
  <el-input v-model="searchKeyword" placeholder="이름 또는 로그인ID 검색"
            @keyup.enter="handleSearch" @clear="handleSearch" />

  <!-- 테넌트 필터 -->
  <el-select v-model="filterTenantId" placeholder="테넌트" clearable
             @change="handleTenantFilterChange" />

  <!-- 부서 트리 필터 (테넌트 선택 후 활성화) -->
  <el-tree-select v-model="filterDeptId" :data="filterDeptTree"
                  :disabled="!filterTenantId" />

  <!-- 상태 필터 -->
  <el-select v-model="filterActive" placeholder="상태" clearable
             @change="handleSearch" />

  <!-- 초기화 -->
  <el-button @click="resetFilters">초기화</el-button>
</div>
```

```
필터 연쇄 동작:

테넌트 선택 → 해당 테넌트의 부서 목록 로드 → 부서 필터 활성화

┌─────────────┐    ┌──────────────┐    ┌──────────┐
│ 테넌트: A사  │ →  │ 부서: [활성화] │ →  │ 검색 실행 │
│       ▼     │    │  ├ 개발팀     │    │          │
└─────────────┘    │  ├ 영업팀     │    └──────────┘
                   │  └ 기획팀     │
                   └──────────────┘

초기화: 모든 필터 값 → null, 부서 목록 → 빈 배열, 페이지 → 1
```

### DocumentsView — 코드 기반 동적 필터

```javascript
// 문서 용도(usageType)와 문서 유형(docType)의 연쇄 필터
const filteredDocTypes = computed(() => {
  if (!docTypes.value.length) return []
  const usageType = filters.value.usageType
  if (!usageType) return docTypes.value    // 전체 표시

  const isRagKnowledge = usageType === 'rag_knowledge'
  return docTypes.value.filter(dt => {
    const sortOrder = dt.sort_order || 0
    return isRagKnowledge ? sortOrder < 10 : sortOrder >= 10
  })
})
```

```
코드 테이블 기반 동적 필터:

용도(USAGE_TYPE)          유형(DOC_TYPE)
┌───────────────┐        ┌────────────────────┐
│ rag_knowledge │ ──→    │ policy (sort: 1)    │  ← RAG 전용
│ (지식)        │        │ guide (sort: 2)     │
│               │        │ faq (sort: 3)       │
├───────────────┤        ├────────────────────┤
│ rag_action    │ ──→    │ schema (sort: 10)   │  ← Action 전용
│ (Action)      │        │ query_example (11)  │
└───────────────┘        │ glossary (sort: 12) │
                         └────────────────────┘

sort_order < 10 → RAG용 문서 유형
sort_order >= 10 → Action용 문서 유형
→ 코드 테이블의 sort_order를 활용한 영리한 분류!
```

---

## 패턴 8: UsersView의 탭 다이얼로그 (고급)

UsersView는 다이얼로그에 **탭**을 사용하여 기본정보와 메뉴 권한을 분리합니다:

```html
<el-dialog v-model="dialogVisible" width="720px">
  <el-tabs v-model="activeTab">
    <!-- 탭 1: 기본정보 -->
    <el-tab-pane label="기본정보" name="basic">
      <el-form ref="formRef" :model="formData" :rules="formRules">
        <!-- 로그인ID, 이름, 이메일, 비밀번호, 역할, 테넌트, 부서 -->
      </el-form>
    </el-tab-pane>

    <!-- 탭 2: 메뉴 권한 -->
    <el-tab-pane label="메뉴 권한" name="menus">
      <el-table :data="allMenus">
        <!-- 메뉴명, 조회, 등록, 수정, 삭제, 내보내기 체크박스 -->
      </el-table>
    </el-tab-pane>
  </el-tabs>
</el-dialog>
```

### 메뉴 권한 매트릭스

```javascript
// menuPermMap: 메뉴ID → 권한 객체
const menuPermMap = reactive({})

const initMenuPermMap = () => {
  for (const m of allMenus.value) {
    menuPermMap[m.menu_id] = {
      can_create: false,
      can_read: false,
      can_update: false,
      can_delete: false,
      can_export: false
    }
  }
}
```

```
메뉴 권한 테이블:

┌────────────┬──────┬──────┬──────┬──────┬────────┐
│ 메뉴        │ 조회 │ 등록 │ 수정 │ 삭제 │ 내보내기│
├────────────┼──────┼──────┼──────┼──────┼────────┤
│ 대시보드     │  ☑  │  ☐  │  ☐  │  ☐  │  ☐    │
│ 사용자 관리  │  ☑  │  ☑  │  ☑  │  ☑  │  ☑    │
│ 역할 관리    │  ☑  │  ☐  │  ☐  │  ☐  │  ☐    │
│ 문서 관리    │  ☑  │  ☑  │  ☑  │  ☐  │  ☑    │
└────────────┴──────┴──────┴──────┴──────┴────────┘

규칙: "조회" OFF → 나머지도 모두 OFF
  → 조회할 수 없는 메뉴에 등록/수정/삭제 권한은 의미 없으니까!
```

```javascript
// 조회 OFF → 나머지도 OFF
const handleMenuPermChange = (menuId, field, val) => {
  if (field === 'can_read' && !val) {
    menuPermMap[menuId].can_create = false
    menuPermMap[menuId].can_update = false
    menuPermMap[menuId].can_delete = false
    menuPermMap[menuId].can_export = false
  }
}
```

### 역할 변경 시 자동 설정

```javascript
const handleRoleChange = async (roleId) => {
  const role = allRoles.value.find(r => r.role_id === roleId)

  // GLOBAL 역할 → 시스템 테넌트 자동 설정
  if (role.role_code === 'GLOBAL') {
    const sysTenant = allTenants.value.find(t => t.is_system)
    formData.tenant_id = sysTenant?.tenant_id || null
    formData.dept_id = null
  }

  // 역할의 기본 메뉴 권한 로드
  const response = await rolesApi.getDefaultMenus(role.role_code)
  initMenuPermMap()
  for (const dm of (response?.items || [])) {
    if (menuPermMap[dm.menu_id]) {
      menuPermMap[dm.menu_id].can_read = dm.can_read ?? true
      // ...
    }
  }
}
```

```
역할 변경 연쇄 동작:

역할을 "GLOBAL"로 변경
    │
    ├─ ① 테넌트 자동설정 → 시스템 테넌트
    ├─ ② 부서 초기화 → null
    └─ ③ 기본 메뉴 권한 로드 → API 호출 → menuPermMap 갱신

역할을 "TENANT"로 변경
    │
    ├─ ① 시스템 테넌트 선택되어 있으면 해제
    └─ ② 기본 메뉴 권한 로드
```

---

## 패턴 9: 초기 데이터 로드

### UsersView — 병렬 로드

```javascript
onMounted(async () => {
  await Promise.all([
    loadUsers(),         // 사용자 목록
    loadRoles(),         // 역할 옵션
    loadTenants(),       // 테넌트 옵션
    loadMenus(),         // 메뉴 옵션
    loadFilterTenants()  // 필터용 테넌트 목록
  ])
})
```

```
Promise.all = 여러 비동기 작업을 동시에 실행

순차 실행 (느림):
  loadUsers()    ──────▶ 500ms
  loadRoles()           ──────▶ 300ms
  loadTenants()                 ──────▶ 200ms
  총 시간: 1000ms

병렬 실행 (빠름 ✅):
  loadUsers()    ──────▶ 500ms
  loadRoles()    ────▶   300ms
  loadTenants()  ───▶    200ms
  총 시간: 500ms (가장 느린 것 기준)
```

---

## 리뷰 체크리스트

- [x] 목록 조회 시 로딩 인디케이터가 있는가? → `v-loading` ✅
- [x] 필터 변경 시 페이지가 1로 리셋되는가? → `currentPage = 1` ✅
- [x] 생성/수정 다이얼로그를 하나로 재사용하는가? → `dialogMode` ✅
- [x] 폼 검증 후 API를 호출하는가? → `validate().catch()` ✅
- [x] 삭제 전 확인 절차가 있는가? → `ElMessageBox.confirm` ✅
- [x] 삭제 보호 장치가 있는가? → `is_superuser`, `is_system`, `user_count` ✅
- [x] 성공/실패 시 사용자에게 피드백을 주는가? → `ElMessage` ✅
- [x] 초기 데이터를 병렬로 로드하는가? → `Promise.all` ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **el-table + el-table-column** | 데이터 테이블. prop으로 자동 바인딩, #default로 커스텀 |
| **el-pagination** | 페이지네이션. offset 기반으로 서버에 요청 |
| **el-dialog + v-model** | 모달 다이얼로그. true/false로 열기/닫기 |
| **dialogMode** | 'create'/'edit'로 생성/수정 다이얼로그 재사용 |
| **formRef.validate()** | 폼 전체 검증. Promise 반환 |
| **ElMessageBox.confirm** | 삭제 전 확인 팝업 |
| **ElMessage.success/error** | 토스트 알림 (화면 우측 상단) |
| **Promise.all** | 여러 비동기 작업 병렬 실행 |
| **nextTick** | DOM 업데이트 후 콜백 실행. 다이얼로그 열린 후 검증 초기화 등 |

---
> **이전**: [01_login_view.md](01_login_view.md) - 로그인 화면
> **다음**: [03_dashboard_view.md](03_dashboard_view.md) - 대시보드 화면
