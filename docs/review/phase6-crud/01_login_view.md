# 1. LoginView — 로그인 화면

> **파일 위치**: `frontend/src/views/LoginView.vue` (259줄)

## 이 화면이 하는 일

사용자가 아이디와 비밀번호를 입력하여 **로그인**하는 화면입니다.
관리자 레이아웃(`AdminLayout`) 없이 **독립적으로** 표시됩니다.

```
┌──────────────────────────────────────────────────┐
│                                                  │
│           ⬡ (그리드 배경 + 글로우 효과)            │
│                                                  │
│              ┌──────────────────┐                │
│              │    💬 MUREUM     │                │
│              │  AI 지식 도우미    │                │
│              │                  │                │
│              │  [👤 아이디    ]  │                │
│              │  [🔒 비밀번호  ]  │                │
│              │                  │                │
│              │  [  로그인  ]     │                │
│              └──────────────────┘                │
│                                                  │
│              MUREUM v2.0.0                       │
└──────────────────────────────────────────────────┘
```

---

## Template 구조

```
login-container (전체 화면, 배경 효과)
├── ::before (대각선 블루/틸 글로우 배경)
├── ::after (그리드 라인 패턴)
│
├── login-card (흰색 카드)
│   ├── login-header (로고 + 타이틀)
│   │   ├── ChatDotRound 아이콘 (48px)
│   │   ├── h1 "MUREUM"
│   │   └── p "AI 지식 도우미"
│   │
│   └── el-form (로그인 폼)
│       ├── el-form-item (아이디 입력)
│       ├── el-form-item (비밀번호 입력)
│       ├── el-alert (에러 메시지, 조건부)
│       └── el-button (로그인 버튼)
│
└── login-footer ("MUREUM v2.0.0")
```

---

## 폼 데이터와 검증 규칙

```javascript
// 폼 데이터: 아이디와 비밀번호 2개 필드
const form = reactive({
  loginId: '',
  password: ''
})

// 검증 규칙: 빈 값 확인만
const rules = {
  loginId: [
    { required: true, message: '아이디를 입력해주세요', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '비밀번호를 입력해주세요', trigger: 'blur' }
  ]
}
```

**Element Plus 폼 검증이 동작하는 방식:**

```
사용자가 아이디 입력란에서 포커스를 떠남 (blur)
    │
    ▼
rules.loginId 실행:
    └─ required: true → 빈 값이면 "아이디를 입력해주세요" 표시
                       → 입력되어 있으면 통과 ✅

"로그인" 버튼 클릭:
    │
    ▼
formRef.value.validate() → 모든 필드의 규칙을 한번에 검증
    ├─ 전부 통과 → true 반환 → API 호출 진행
    └─ 하나라도 실패 → false 반환 → 에러 메시지 자동 표시
```

---

## 로그인 처리 흐름

```javascript
const handleLogin = async () => {
  // ① 폼 검증
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return   // 검증 실패 → 중단

  try {
    // ② Store를 통해 로그인 API 호출
    await store.dispatch('auth/login', {
      loginId: form.loginId,
      password: form.password
    })

    // ③ 로그인 성공 → 리다이렉트
    const redirect = route.query.redirect
    if (redirect) {
      router.push(redirect)                          // 원래 가려던 페이지로
    } else {
      router.push(store.getters['auth/landingPage']) // 역할별 기본 페이지로
    }
  } catch {
    // ④ 실패 → loginError가 Store에 자동 설정됨
  }
}
```

**이 흐름을 그림으로:**

```
사용자: [아이디 입력] → [비밀번호 입력] → [로그인 클릭]
    │
    ▼
① formRef.validate()
    ├─ 실패: 빈 칸 에러 표시 → 중단
    └─ 성공 ↓

② store.dispatch('auth/login', { loginId, password })
    │
    ▼
   auth Store의 login 액션 실행 (Phase 3에서 학습)
    ├─ API 호출: POST /api/v1/auth/login
    ├─ 성공: token 저장, user 정보 저장
    └─ 실패: loginError에 에러 메시지 저장
    │
    ▼
③ 성공 시 리다이렉트:
    ├─ redirect 쿼리 있음? → 해당 페이지로
    │   예) /login?redirect=/admin/users → /admin/users로 이동
    │
    └─ redirect 없음? → 역할별 기본 페이지로
        ├─ GLOBAL → /admin/dashboard
        ├─ TENANT → /admin/dashboard
        └─ USER   → /chat

④ 실패 시:
    └─ loginError 표시 (el-alert)
       "아이디 또는 비밀번호가 일치하지 않습니다"
       "계정이 잠겨있습니다 (30분 후 재시도)"
       "비활성화된 계정입니다"
```

---

## Store와의 연결

```javascript
// Store에서 읽기 (computed → 실시간 반영)
const loginLoading = computed(() => store.state.auth.loginLoading)
const loginError = computed(() => store.state.auth.loginError)
```

```
LoginView                    auth Store
─────────                    ──────────
loginLoading ← ──────── ── loginLoading
loginError   ← ──────── ── loginError

"로그인" 클릭
    │
    ▼
dispatch('auth/login')  ──→  loginLoading = true
                              ├─ API 호출 중...
                              ├─ 성공: loginLoading = false, user 설정
                              └─ 실패: loginLoading = false, loginError 설정

LoginView에서:
  · loginLoading = true → 버튼에 스피너 표시 + 입력란 비활성화
  · loginError 있음 → el-alert에 에러 메시지 표시
```

**코드와 화면의 연결:**

```html
<!-- 로그인 버튼: loading 상태 연동 -->
<el-button
  type="primary"
  :loading="loginLoading"         ← Store의 loginLoading 반영
  @click="handleLogin"
>
  {{ loginLoading ? '로그인 중...' : '로그인' }}
</el-button>

<!-- 에러 메시지: loginError가 있을 때만 표시 -->
<el-alert
  v-if="loginError"              ← loginError 있으면 표시
  :title="loginError"            ← 에러 메시지 내용
  type="error"
  show-icon
  :closable="false"
/>
```

---

## 이미 로그인된 상태 처리

```javascript
// 이미 로그인 되어 있으면 → 바로 랜딩 페이지로 이동
onMounted(() => {
  if (store.getters['auth/isAuthenticated']) {
    router.replace(store.getters['auth/landingPage'])
  }
})
```

```
사용자가 /login에 접속
    │
    ▼
onMounted() 실행
    │
    ├─ 이미 로그인됨 (토큰 존재)
    │   └─ router.replace(landingPage) → 로그인 화면 건너뜀!
    │
    └─ 로그인 안 됨
        └─ 로그인 폼 표시 (정상 동작)

* router.push vs router.replace:
  · push: 히스토리에 추가 → 뒤로가기 가능
  · replace: 히스토리 교체 → 뒤로가기 불가 (로그인 화면으로 돌아가면 안 되니까!)
```

---

## 키보드 이벤트 처리

```html
<!-- 아이디 입력란에서 엔터 → 로그인 실행 -->
<el-input
  v-model="form.loginId"
  @keyup.enter="handleLogin"    ← 엔터키로 바로 로그인
/>

<!-- 비밀번호 입력란에서도 엔터 → 로그인 실행 -->
<el-input
  v-model="form.password"
  type="password"
  @keyup.enter="handleLogin"    ← 엔터키로 바로 로그인
/>
```

```
사용자 입력 시나리오:

1. 아이디 입력 → Tab → 비밀번호 입력 → Enter → 로그인!
2. 아이디 입력 → Enter → 비밀번호 비어있으므로 검증 실패
3. 아이디 + 비밀번호 입력 → [로그인] 버튼 클릭 → 로그인!

→ Enter와 버튼 클릭 모두 같은 handleLogin() 함수를 호출
```

---

## CSS — 배경 효과

로그인 화면의 시각적 특징은 **배경 효과**입니다:

```scss
.login-container {
  min-height: 100vh;                    // 전체 화면 높이
  display: flex;
  align-items: center;                  // 세로 중앙
  justify-content: center;             // 가로 중앙

  // ① 대각선 블루/틸 글로우 (::before)
  &::before {
    background:
      radial-gradient(... at 20% 30%, rgba(99,102,241, 0.18) ...),   // 왼쪽 위 보라
      radial-gradient(... at 80% 70%, rgba(6,182,212, 0.14) ...),    // 오른쪽 아래 틸
      radial-gradient(... at 50% 50%, rgba(64,158,255, 0.08) ...);   // 중앙 블루
    pointer-events: none;              // 클릭 통과 (배경이니까)
    z-index: 0;
  }

  // ② 그리드 라인 (::after)
  &::after {
    background-image:
      linear-gradient(rgba(64,158,255, 0.08) 1px, transparent 1px),
      linear-gradient(90deg, rgba(64,158,255, 0.08) 1px, transparent 1px);
    background-size: 48px 48px;         // 48px 간격 격자
    mask-image: radial-gradient(ellipse 80% 70% at center, black, transparent);
                                        // 중앙에서 점점 사라지는 마스크
  }
}
```

```
화면 레이어 구조:

z-index 1  →  로그인 카드 (최상위, 클릭 가능)
z-index 0  →  ::before (글로우 효과)
z-index 0  →  ::after (그리드 라인)
              └─ 배경색: var(--bg-color-page)

결과:
┌──────────────────────────────────┐
│ · · · · · · · · · · · · · · · · │  ← 그리드 라인 (중앙에서 fade)
│ · ╔════════════╗ · · · · · · · │
│ ·░║  MUREUM    ║░· · · · · · · │  ← 글로우 효과
│ ·░║  [로그인]   ║░· · · · · · · │
│ · ╚════════════╝ · · · · · · · │
│ · · · · · · · · · · · · · · · · │
└──────────────────────────────────┘
```

---

## 자동완성 방지 (브라우저 호환)

```scss
// 크롬의 자동완성 배경색을 카드 배경과 일치시킴
:deep(.el-input__inner) {
  &:-webkit-autofill,
  &:-webkit-autofill:hover,
  &:-webkit-autofill:focus {
    -webkit-box-shadow: 0 0 0 1000px var(--bg-color-card) inset !important;
    -webkit-text-fill-color: var(--text-color-primary) !important;
    transition: background-color 5000s ease-in-out 0s;  // 배경 전환을 5000초로 → 사실상 안 바뀜
  }
}
```

```
문제: 크롬이 자동완성 시 입력란을 노란색으로 바꿈 😣
      → 다크모드에서 특히 눈에 거슬림

해결: -webkit-box-shadow로 배경을 "덮어씀"
      → 자동완성되어도 카드 배경색과 동일하게 보임 ✅
```

---

## 리뷰 체크리스트

- [x] 폼 검증이 작동하는가? → `rules` + `formRef.validate()` ✅
- [x] 로그인 중 UI 피드백이 있는가? → `loginLoading` 스피너 + disabled ✅
- [x] 에러 메시지가 표시되는가? → `loginError` + `el-alert` ✅
- [x] 이미 로그인된 상태를 처리하는가? → `onMounted` + `replace` ✅
- [x] 엔터키로 로그인 가능한가? → `@keyup.enter` ✅
- [x] 역할별 랜딩 페이지가 다른가? → `auth/landingPage` getter ✅
- [x] CSS 변수로 다크모드를 지원하는가? → `var(--bg-color-card)` 등 ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **reactive()** | 객체를 반응형으로 만듦. 값이 바뀌면 화면 자동 갱신 |
| **el-form + rules** | Element Plus 폼 검증. required, min, type 등 규칙 정의 |
| **formRef.validate()** | 폼 전체를 한번에 검증. Promise 반환 (async/await 사용) |
| **store.dispatch** | Vuex Store의 액션 호출. 여기서는 로그인 처리 |
| **computed** | Store 상태를 실시간 반영하는 반응형 변수 |
| **router.replace** | 히스토리를 교체하며 이동 (뒤로가기 방지) |
| **@keyup.enter** | 엔터키 이벤트 바인딩 (Vue 이벤트 수식어) |
| **:deep()** | scoped CSS에서 자식 컴포넌트 스타일 접근 |

---
> **다음**: [02_crud_pattern.md](02_crud_pattern.md) - CRUD 공통 패턴
