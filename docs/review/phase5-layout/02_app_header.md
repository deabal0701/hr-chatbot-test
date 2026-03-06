# 2. AppHeader - 관리자 헤더

> **파일 위치**: `frontend/src/components/layout/AppHeader.vue` (312줄)

## 이 컴포넌트가 하는 일

관리자 화면 상단의 **헤더 바**입니다. 현재 페이지 제목, API 상태, 사용자 메뉴를 표시합니다.

```
┌──────────────────────────────────────────────────────┐
│  ☰  사용자 관리          🟢 Online  [👤 관리자 ▼]    │
│                                     ├ 권한: 전체 관리자│
│  왼쪽: 페이지 제목        오른쪽:    ├ 비밀번호 변경   │
│                          API 상태   └ 로그아웃        │
└──────────────────────────────────────────────────────┘
```

---

## Template 구조

```
header-container (flex, space-between)
├── header-left
│   ├── Menu 아이콘
│   └── pageTitle (라우트 meta.title)
│
└── header-right
    ├── API 상태 태그 (Online/Offline)
    ├── 사용자 드롭다운 메뉴
    │   ├── 권한 표시 (비활성 항목)
    │   ├── 비밀번호 변경
    │   └── 로그아웃
    └── 비밀번호 변경 다이얼로그 (숨겨져 있다가 표시)
```

---

## 페이지 제목 — 라우트에서 자동 추출

```javascript
const pageTitle = computed(() => {
  return route.meta.title || 'MUREUM'
})
```

**라우트 meta와 연결:**
```javascript
// router/index.js (Phase 2)
{ path: 'users', component: UsersView, meta: { title: '사용자 관리' } }
{ path: 'documents', component: DocumentsView, meta: { title: '문서 관리' } }
{ path: 'settings', component: SettingsView, meta: { title: '시스템 설정' } }
```

```
/admin/users 접속 → route.meta.title = '사용자 관리'
                   → 헤더에 "☰ 사용자 관리" 표시

/admin/documents → route.meta.title = '문서 관리'
                 → 헤더가 "☰ 문서 관리"로 자동 변경!

→ 코드 수정 없이 라우트 meta만 추가하면 제목 자동 반영
```

---

## API 상태 표시 — 30초마다 헬스 체크

```javascript
const apiHealthy = computed(() => store.state.app.apiHealthy)

const checkApiHealth = async () => {
  try {
    await apiClient.get('/health')       // GET /health 호출
    store.commit('app/SET_API_HEALTH', true)   // 성공 → Online
  } catch {
    store.commit('app/SET_API_HEALTH', false)  // 실패 → Offline
  }
}

onMounted(() => {
  checkApiHealth()                       // 최초 1회 체크
  setInterval(checkApiHealth, 30000)     // 이후 30초마다 반복
})
```

```html
<!-- 템플릿에서 -->
<el-tag :type="apiHealthy ? 'success' : 'danger'" size="small" effect="plain">
  <el-icon><Connection /></el-icon>
  {{ apiHealthy ? 'Online' : 'Offline' }}
</el-tag>
```

```
[API 서버 정상]              [API 서버 다운]
┌────────────┐              ┌────────────┐
│ 🟢 Online  │              │ 🔴 Offline │
└────────────┘              └────────────┘
  el-tag type="success"       el-tag type="danger"

30초마다 /health → 성공? Online : Offline
→ 관리자가 서버 상태를 실시간으로 확인 가능
```

---

## 사용자 드롭다운 메뉴

```html
<el-dropdown v-if="currentUser" @command="handleUserCommand" trigger="click">
  <div class="user-info">
    <el-avatar :size="24"><el-icon><UserFilled /></el-icon></el-avatar>
    <span class="user-name">{{ displayName }}</span>
    <el-icon class="user-arrow"><ArrowDown /></el-icon>
  </div>
  <template #dropdown>
    <el-dropdown-menu>
      <el-dropdown-item disabled>
        권한 : {{ roleName }}          <!-- 역할 표시 (클릭 불가) -->
      </el-dropdown-item>
      <el-dropdown-item command="password" divided>
        비밀번호 변경                  <!-- 클릭 → 다이얼로그 열기 -->
      </el-dropdown-item>
      <el-dropdown-item command="logout">
        로그아웃                       <!-- 클릭 → 로그아웃 처리 -->
      </el-dropdown-item>
    </el-dropdown-menu>
  </template>
</el-dropdown>
```

**command 처리:**
```javascript
const handleUserCommand = async (command) => {
  if (command === 'logout') {
    await store.dispatch('auth/logout')    // Store에서 로그아웃 처리
    router.push('/login')                   // 로그인 페이지로 이동
  } else if (command === 'password') {
    passwordDialogVisible.value = true      // 비밀번호 변경 다이얼로그 열기
  }
}
```

```
사용자가 [👤 관리자 ▼] 클릭
    │
    ▼
드롭다운 메뉴 표시
    │
    ├─ "로그아웃" 클릭 → command = 'logout'
    │   ├─ dispatch('auth/logout')  → 토큰 삭제 + 상태 초기화
    │   └─ router.push('/login')    → 로그인 페이지로
    │
    └─ "비밀번호 변경" 클릭 → command = 'password'
        └─ passwordDialogVisible = true → 다이얼로그 열림
```

---

## 비밀번호 변경 다이얼로그

```javascript
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const passwordRules = {
  currentPassword: [
    { required: true, message: '현재 비밀번호를 입력해주세요' }
  ],
  newPassword: [
    { required: true, message: '새 비밀번호를 입력해주세요' },
    { min: 8, message: '8자 이상 입력해주세요' },
    {
      validator: (rule, value, callback) => {
        const hasUpper = /[A-Z]/.test(value)    // 대문자 포함?
        const hasLower = /[a-z]/.test(value)    // 소문자 포함?
        const hasDigit = /[0-9]/.test(value)    // 숫자 포함?
        if (!(hasUpper && hasLower && hasDigit)) {
          callback(new Error('대문자, 소문자, 숫자를 포함해야 합니다'))
        } else {
          callback()
        }
      }
    }
  ],
  confirmPassword: [
    { required: true, message: '비밀번호를 다시 입력해주세요' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error('비밀번호가 일치하지 않습니다'))
        } else {
          callback()
        }
      }
    }
  ]
}
```

**Element Plus 폼 검증 패턴:**

```
el-form의 검증 흐름:

① :rules에 검증 규칙 정의
② 사용자가 입력 → trigger: 'blur' (포커스 떠날 때 검증)
③ "변경" 버튼 클릭 → passwordFormRef.validate() 전체 검증
④ 검증 통과 → API 호출
⑤ 검증 실패 → 에러 메시지 표시 (자동!)
```

**비밀번호 변경 흐름:**

```javascript
const handleChangePassword = async () => {
  // ① 폼 전체 검증
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) return   // 검증 실패 → 중단

  passwordLoading.value = true
  try {
    // ② Store를 통해 API 호출
    await store.dispatch('auth/changePassword', {
      currentPassword: passwordForm.currentPassword,
      newPassword: passwordForm.newPassword
    })
    // ③ 성공
    ElMessage.success('비밀번호가 변경되었습니다')
    passwordDialogVisible.value = false     // 다이얼로그 닫기
    // 폼 초기화
    passwordForm.currentPassword = ''
    passwordForm.newPassword = ''
    passwordForm.confirmPassword = ''
  } catch (err) {
    // ④ 실패
    ElMessage.error(err.detail || err.message || '비밀번호 변경에 실패했습니다')
  } finally {
    passwordLoading.value = false
  }
}
```

---

## Store와의 데이터 연결

```javascript
// auth Store에서 읽기
const currentUser = computed(() => store.getters['auth/currentUser'])
const displayName = computed(() => store.getters['auth/displayName'])
const roleName = computed(() => {
  return store.getters['auth/roleName'] || store.getters['auth/roleCode'] || '-'
})

// app Store에서 읽기
const apiHealthy = computed(() => store.state.app.apiHealthy)
const isDarkMode = computed(() => store.getters['app/isDarkMode'])
```

```
┌─── auth Store ────────────┐     ┌─── AppHeader ────────────┐
│ user.display_name = '관리자' │ ──→ │ displayName = '관리자'    │
│ user.role_name = '전체관리자'│ ──→ │ roleName = '전체 관리자'  │
│ accessToken = 'eyJ...'    │ ──→ │ currentUser ≠ null       │
└───────────────────────────┘     │ → 드롭다운 메뉴 표시       │
                                   └───────────────────────────┘
┌─── app Store ─────────────┐
│ apiHealthy = true         │ ──→ │ 🟢 Online 태그 표시       │
└───────────────────────────┘
```

---

## 리뷰 체크리스트

- [x] 페이지 제목이 라우트에서 자동 추출되는가? → `route.meta.title` ✅
- [x] API 상태가 주기적으로 체크되는가? → 30초 `setInterval` ✅
- [x] 로그인 사용자만 드롭다운이 보이는가? → `v-if="currentUser"` ✅
- [x] 비밀번호 규칙이 적절한가? → 8자, 대소문자+숫자 ✅
- [x] 비밀번호 확인이 일치하는지 검증하는가? → `confirmPassword` validator ✅
- [x] CSS 변수로 다크모드를 지원하는가? → `var(--text-color-primary)` 등 ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **route.meta.title** | 라우트 정의에서 페이지 제목을 가져오는 방법 |
| **el-dropdown** | Element Plus 드롭다운 메뉴. command로 클릭 이벤트 처리 |
| **el-dialog** | 모달 다이얼로그. v-model로 열기/닫기 제어 |
| **el-form + rules** | 폼 검증. 규칙 정의 → validate()로 전체 검증 |
| **setInterval** | 주기적 함수 실행. 여기서는 30초마다 API 헬스 체크 |
| **ElMessage** | Element Plus 토스트 메시지 (success/error/warning) |

---
> **이전**: [01_admin_layout.md](01_admin_layout.md) - AdminLayout
> **다음**: [03_app_sidebar.md](03_app_sidebar.md) - 관리자 사이드바
