# 4. UserChatLayout + UserChatSidebar - 사용자 채팅 레이아웃

> **파일 위치**:
> - `frontend/src/components/user/UserChatLayout.vue` (450줄)
> - `frontend/src/components/user/UserChatSidebar.vue` (820줄)

## 이 컴포넌트들이 하는 일

사용자 채팅 화면(`/chat`)의 레이아웃입니다. **ChatGPT와 유사한 디자인**으로, 왼쪽에 대화 이력 사이드바, 오른쪽에 채팅 화면이 배치됩니다.

```
[데스크탑 화면]                      [모바일 화면]
┌──────────┬─────────────────┐     ┌─────────────────────┐
│UserChat  │   Desktop       │     │☰ MUREUM    📤 💾 👤 │ ← 모바일 헤더
│Sidebar   │   Header        │     │─────────────────────│
│          │─────────────────│     │                     │
│ 새 채팅   │                 │     │   UserChatView      │
│ 이력 검색 │  UserChatView   │     │   (채팅 화면)        │
│ 오늘      │  (채팅 화면)    │     │                     │
│  대화1    │                 │     │                     │
│  대화2    │                 │     └─────────────────────┘
│ 어제      │                 │
│  대화3    │                 │     ☰ 클릭 시:
│          │                 │     ┌──────────┬──────────┐
│ [사용자]  │                 │     │ 사이드바  │ 오버레이  │
└──────────┴─────────────────┘     │ (280px)  │ (반투명)  │
                                    └──────────┴──────────┘
```

---

## 관리자 레이아웃과의 차이

```
┌──────────────────┬────────────────────────────────┐
│     항목          │  관리자 (AdminLayout)  │  사용자 (UserChatLayout)   │
├──────────────────┼────────────────────────────────┤
│ 사이드바 내용     │  메뉴 네비게이션       │  채팅 이력 + 검색          │
│ 사이드바 접기     │  아이콘만 표시 (64px)  │  완전히 숨김               │
│ 콘텐츠 영역       │  다양한 CRUD 페이지    │  채팅 화면 고정            │
│ 모바일 대응       │  없음                  │  반응형 (768px 기준)       │
│ 추가 기능         │  없음                  │  공유하기, 저장하기        │
│ 하단 영역         │  버전 표시             │  사용자 정보 + 로그아웃    │
└──────────────────┴────────────────────────────────┘
```

---

## UserChatLayout — 반응형 설계 ⭐

### 데스크탑 vs 모바일 감지

```javascript
const windowWidth = ref(window.innerWidth)
const MOBILE_BREAKPOINT = 768

const isMobile = computed(() => windowWidth.value <= MOBILE_BREAKPOINT)

const handleResize = () => {
  windowWidth.value = window.innerWidth
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
  if (isMobile.value) {
    store.dispatch('app/setUserSidebarVisible', false)  // 모바일은 기본 숨김
  }
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)    // 메모리 누수 방지!
})
```

```
브라우저 너비 1200px → isMobile = false → 데스크탑 모드
                                         → 사이드바 표시
                                         → desktop-header 표시

브라우저 너비 600px  → isMobile = true  → 모바일 모드
                                        → 사이드바 숨김
                                        → mobile-header 표시

브라우저 크기 조절 → resize 이벤트 → windowWidth 갱신
                                   → isMobile 재계산
                                   → 화면 자동 전환!
```

### 조건부 헤더 렌더링

```html
<!-- 데스크탑 헤더: 공유/저장 버튼 -->
<header v-if="!isMobile" class="desktop-header">
  <button class="action-btn" @click="handleShare">공유하기</button>
  <button class="action-btn" @click="handleSave">저장하기</button>
</header>

<!-- 모바일 헤더: 햄버거 메뉴 + 로고 + 아이콘 버튼 -->
<header v-if="isMobile" class="mobile-header">
  <button @click="toggleSidebar"><Menu /></button>
  <h1>MUREUM</h1>
  <button @click="handleShare"><Share /></button>
  <button @click="handleSave"><Download /></button>
</header>
```

### 모바일 사이드바 오버레이

```html
<!-- 모바일에서 사이드바 열렸을 때 배경 어둡게 -->
<div
  v-if="sidebarVisible && isMobile"
  class="sidebar-overlay"
  @click="closeSidebar"     ← 오버레이 클릭 시 사이드바 닫기
/>
```

```
모바일에서 ☰ 클릭:
┌──────────┬──────────────────┐
│ 사이드바  │   ■■■■■■■■■■■■  │ ← 반투명 오버레이
│          │   ■■■■■■■■■■■■  │
│ 새 채팅   │   ■■■■■■■■■■■■  │   (클릭하면 사이드바 닫힘)
│ 이력...   │   ■■■■■■■■■■■■  │
│          │   ■■■■■■■■■■■■  │
└──────────┴──────────────────┘

→ 사이드바가 화면 위에 떠서 표시 (position: fixed)
→ 배경을 클릭하면 자동으로 닫힘
```

### 사이드바 트랜지션 애니메이션

```html
<transition name="sidebar-slide">
  <UserChatSidebar v-show="sidebarVisible" />
</transition>
```

```scss
// _animations.scss mixin 사용
@include mx.sidebar-slide-transition;

// 모바일에서의 슬라이드 애니메이션
@media (max-width: 768px) {
  :deep(.user-chat-sidebar) {
    position: fixed;
    transform: translateX(-100%);   // 기본: 화면 밖에 숨김
    transition: transform 0.3s ease;

    &.mobile-visible {
      transform: translateX(0);      // 열림: 화면 안으로 슬라이드
    }
  }
}
```

---

## 공유하기 / 저장하기 기능

### 공유하기 (클립보드 복사)

```javascript
const handleShare = async () => {
  // HTTPS가 아니면 클립보드 API 사용 불가
  if (!window.isSecureContext) {
    ElMessage.warning('공유 기능은 https:// 주소에서만 지원됩니다.')
    return
  }

  const messages = store.state.chat.messages
  if (messages.length === 0) {
    ElMessage.warning('공유할 대화 내용이 없습니다.')
    return
  }

  // 대화를 텍스트로 변환
  const chatText = messages.map(msg => {
    const role = msg.role === 'user' ? '사용자' : 'AI'
    return `[${role}]\n${msg.content}`
  }).join('\n\n---\n\n')

  await navigator.clipboard.writeText(chatText)
  ElMessage.success('대화 내용이 클립보드에 복사되었습니다.')
}
```

### 저장하기 (마크다운 파일 다운로드)

```javascript
const handleSave = () => {
  const messages = store.state.chat.messages

  // 마크다운 포맷으로 변환
  let markdown = `# MUREUM 대화 기록\n\n`
  markdown += `- 저장 일시: ${dateStr} ${timeStr}\n`
  markdown += `- 메시지 수: ${messages.length}개\n\n---\n\n`

  messages.forEach(msg => {
    const role = msg.role === 'user' ? '👤 사용자' : '🤖 AI'
    markdown += `## ${role}\n\n${msg.content}\n\n`

    // RAG 소스가 있으면 추가
    if (msg.ragResult?.sources?.length > 0) {
      markdown += `<details>\n<summary>📚 참조 문서</summary>\n...\n</details>\n`
    }

    // SQL 결과가 있으면 추가
    if (msg.nl2sqlResult?.sql) {
      markdown += `<details>\n<summary>🔍 SQL 쿼리</summary>\n...\n</details>\n`
    }
  })

  // Blob → 파일 다운로드 (Phase 4 search.js의 exportExcel과 같은 패턴)
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `mureum-chat-${date}.md`
  link.click()
}
```

---

## UserChatSidebar — ChatGPT 스타일 사이드바

### 구조

```
UserChatSidebar (aside)
├── sidebar-header
│   ├── 로고 (MUREUM)
│   ├── 접기 버튼 (데스크탑)
│   └── 닫기 버튼 (모바일)
│
├── new-chat-section
│   ├── [새 채팅] 버튼
│   └── [나의 대시보드] 버튼
│
├── search-section
│   └── 이력 검색 입력창 (디바운스 300ms)
│
├── chat-history-section (스크롤 가능)
│   ├── 오늘
│   │   ├── 대화1  [🗑]
│   │   └── 대화2  [🗑]
│   ├── 어제
│   │   └── 대화3  [🗑]
│   ├── 지난 7일
│   ├── 지난 30일
│   └── 이전
│
└── sidebar-footer
    ├── 사용자 정보 (인증됨: 드롭다운)
    └── 로그인 버튼 (미인증)
```

### 날짜 그룹핑 (ChatGPT 스타일)

```javascript
const groupedHistory = computed(() => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const yesterday = new Date(today); yesterday.setDate(today.getDate() - 1)
  const weekAgo = new Date(today); weekAgo.setDate(today.getDate() - 7)
  const monthAgo = new Date(today); monthAgo.setDate(today.getDate() - 30)

  const buckets = {
    today: { label: '오늘', items: [] },
    yesterday: { label: '어제', items: [] },
    week: { label: '지난 7일', items: [] },
    month: { label: '지난 30일', items: [] },
    older: { label: '이전', items: [] }
  }

  for (const chat of chatHistory.value) {
    const date = new Date(chat.last_activity)
    if (date >= today) buckets.today.items.push(chat)
    else if (date >= yesterday) buckets.yesterday.items.push(chat)
    else if (date >= weekAgo) buckets.week.items.push(chat)
    else if (date >= monthAgo) buckets.month.items.push(chat)
    else buckets.older.items.push(chat)
  }

  // 비어있지 않은 그룹만 반환
  return Object.values(buckets).filter(b => b.items.length > 0)
})
```

### 검색 디바운스

```javascript
const searchQuery = ref('')
let searchTimer = null

const handleSearchInput = () => {
  if (searchTimer) clearTimeout(searchTimer)    // 이전 타이머 취소
  searchTimer = setTimeout(() => {              // 300ms 후 실행
    store.dispatch('chat/fetchChatHistory', searchQuery.value || null)
  }, 300)
}
```

```
디바운스 = "타이핑이 끝날 때까지 기다렸다가 검색"

"입" 타이핑 → 300ms 타이머 시작
"입사" 타이핑 → 이전 타이머 취소 → 새 타이머 시작
"입사자" 타이핑 → 이전 타이머 취소 → 새 타이머 시작
(300ms 대기...)
→ API 호출! (fetchChatHistory("입사자"))

→ 글자마다 API를 호출하지 않고, 타이핑 멈추면 1번만 호출
→ 서버 부하 감소!
```

### 로딩 스켈레톤

```html
<div v-if="historyLoading" class="history-loading">
  <div v-for="i in 5" :key="i" class="skeleton-item">
    <div class="skeleton-line"></div>
  </div>
</div>
```

```
실제 데이터 로딩 전:         로딩 후:
┌──────────────────┐       ┌──────────────────┐
│ ████████████████ │       │ 오늘              │
│ ████████████     │       │  2024년 입사자 수?│
│ ██████████████   │       │  재택근무 정책    │
│ ██████████       │       │ 어제              │
│ ████████████     │       │  부서별 인원 현황 │
└──────────────────┘       └──────────────────┘
  (반짝이는 애니메이션)       (실제 대화 목록)

→ 빈 화면 대신 "무언가 로딩되고 있다"는 시각적 피드백
```

---

## 부모-자식 통신 (emit 패턴)

```javascript
// UserChatSidebar.vue
const emit = defineEmits(['new-chat', 'select-chat', 'close', 'toggle'])

// 새 채팅 버튼 클릭
const handleNewChat = () => {
  store.dispatch('chat/newChat')
  emit('new-chat')                    // 부모에게 알림
  if (props.isMobile) emit('close')   // 모바일이면 사이드바 닫기
}

// 대화 선택
const handleSelectChat = (sessionKey) => {
  store.dispatch('chat/selectChat', sessionKey)
  emit('select-chat', sessionKey)
  if (props.isMobile) emit('close')   // 모바일이면 사이드바 닫기
}
```

```
UserChatLayout (부모)                UserChatSidebar (자식)
─────────────────                    ──────────────────

<UserChatSidebar                     defineProps({ isMobile })
  :is-mobile="isMobile"              defineEmits(['close', 'toggle'])
  @close="closeSidebar"
  @toggle="toggleSidebar"            [X 버튼 클릭]
/>                                    emit('close')
       │                                  │
       ◄──────────────────────────────────┘
       │
closeSidebar()
  → store.dispatch('app/setUserSidebarVisible', false)
```

---

## 리뷰 체크리스트

- [x] 반응형 디자인이 적용되어 있는가? → 768px 기준 데스크탑/모바일 ✅
- [x] 모바일에서 사이드바가 오버레이로 표시되는가? → position: fixed + overlay ✅
- [x] 사이드바 트랜지션 애니메이션이 있는가? → sidebar-slide-transition ✅
- [x] 대화 이력이 날짜별로 그룹핑되는가? → 오늘/어제/7일/30일/이전 ✅
- [x] 검색 디바운스가 적용되는가? → 300ms setTimeout ✅
- [x] 공유 기능이 HTTPS 체크를 하는가? → `window.isSecureContext` ✅
- [x] 저장 시 RAG/SQL 결과도 포함하는가? → details 태그 ✅
- [x] resize 리스너가 정리되는가? → `onUnmounted` ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **반응형 디자인** | `window.innerWidth`로 데스크탑/모바일 자동 전환 |
| **모바일 오버레이** | 사이드바가 콘텐츠 위에 떠서 표시, 배경 클릭으로 닫기 |
| **날짜 그룹핑** | 채팅 이력을 오늘/어제/7일/30일/이전으로 분류 |
| **디바운스** | 타이핑 후 대기 시간이 지나야 검색 실행 (서버 부하 감소) |
| **스켈레톤 로딩** | 데이터 로딩 중 빈 화면 대신 반짝이는 플레이스홀더 표시 |
| **emit 패턴** | 자식 → 부모 이벤트 전달. `defineEmits` + `$emit` |
| **Blob 다운로드** | 마크다운 텍스트 → Blob → 파일 다운로드 |

---
> **이전**: [03_app_sidebar.md](03_app_sidebar.md) - 관리자 사이드바
> **다음**: [05_how_it_works.md](05_how_it_works.md) - 동작 원리 종합
