# 3. 사용자 화면 (UserChatView)

> **학습 목표**: ChatGPT 스타일의 사용자 채팅 화면 구조와 관리자 화면과의 **차이점**을 이해한다.

---

## UserChatView 개요

> **파일**: `views/user/UserChatView.vue` (999줄)

일반 사용자가 사용하는 **독립 전체화면** 채팅 인터페이스입니다.
AdminLayout 없이 자체 헤더/푸터를 가집니다.

```
┌──────────────────────────────────────────┐
│  ☾  MUREUM                    사용자명   │ ← header
├──────────────────────────────────────────┤
│                                          │
│            무엇을 도와드릴까요?            │ ← main (환영 또는 메시지)
│                                          │
│   [재택근무 정책...]  [연차 휴가...]      │
│   [성과평가 제도...]  [출장비 정산...]     │
│                                          │
├──────────────────────────────────────────┤
│  [RAG▾] [궁금한 내용을 입력하세요...]  [➤] │ ← footer
│  본 AI 어시스턴트가 생성한 답변은 참고용... │
└──────────────────────────────────────────┘
```

---

## Template — 3영역 레이아웃

```
UserChatView
├── <header> — 헤더
│   ├── logo-icon + logo-text ("MUREUM")
│   ├── theme-toggle-btn (다크/라이트 전환)
│   ├── user-label (로그인 시 사용자명)
│   └── el-button (비로그인 시 "로그인" 버튼)
│
├── <main> — 메인 콘텐츠
│   ├── welcome-section (메시지 없을 때)
│   │   ├── welcome-icon
│   │   ├── welcome-title "무엇을 도와드릴까요?"
│   │   ├── welcome-subtitle
│   │   └── example-queries (예시 질문 버튼들)
│   │
│   └── messages-container (메시지 있을 때)
│       ├── UserChatMessage (v-for)
│       └── loading-indicator (로딩 + typing dots)
│
└── <footer> — 입력 영역
    └── input-container
        ├── input-wrapper
        │   ├── mode-btn (el-dropdown 모드 선택)
        │   ├── textarea (자체 구현, auto-resize)
        │   └── send-btn (전송 버튼)
        └── footer-note (면책 문구)
```

---

## 관리자 화면과의 핵심 차이

### 1. 모드 선택 — 드롭다운 vs 사이드바

```
관리자 (ChatView):                      사용자 (UserChatView):
오버레이 사이드바의 라디오 버튼           입력란 왼쪽의 드롭다운

┌─────────────────┐                     ┌──────────────────┐
│ 검색 모드        │                     │ [RAG▾] [입력...] │
│ [● RAG]          │                     └──────────────────┘
│ [○ NL2SQL]       │                         │
└─────────────────┘                         ▼ 클릭하면
                                        ┌──────────────────┐
                                        │ 📄 RAG           │
                                        │   문서 기반 검색  │
                                        │ 📊 NL2SQL        │
                                        │   데이터베이스 조회│
                                        └──────────────────┘
```

```html
<!-- 모드 선택 드롭다운 -->
<el-dropdown trigger="click" @command="handleModeChange">
  <button class="mode-btn">
    <el-icon><Operation /></el-icon>
    <span>{{ modeLabel }}</span>          ← 현재 모드명 표시
    <el-icon class="arrow"><ArrowDown /></el-icon>
  </button>
  <template #dropdown>
    <el-dropdown-menu>
      <el-dropdown-item command="rag" :class="{ active: searchMode === 'rag' }">
        <div class="mode-option">
          <span class="mode-name"><el-icon><Document /></el-icon> RAG</span>
          <span class="mode-desc">정책, 가이드, FAQ 등 문서 기반 검색</span>
        </div>
      </el-dropdown-item>
      <el-dropdown-item command="nl2sql" ...>
        ...NL2SQL...
      </el-dropdown-item>
    </el-dropdown-menu>
  </template>
</el-dropdown>
```

```
el-dropdown 동작:
1. "RAG▾" 버튼 클릭 → 드롭다운 메뉴 열림
2. 항목 클릭 → @command="handleModeChange" 실행
3. command 값 ("rag", "nl2sql") → store.dispatch('chat/setMode', mode)
4. 드롭다운 자동 닫힘
```

### 2. 입력 — 자체 textarea vs ChatInput 컴포넌트

```
관리자:                              사용자:
ChatInput 컴포넌트 사용               자체 <textarea> 구현
(el-input type="textarea")           (네이티브 HTML textarea)
(autosize: Element Plus 처리)        (autoResize: 직접 구현)
```

```html
<!-- 네이티브 textarea + auto-resize -->
<textarea
  ref="inputRef"
  v-model="inputText"
  class="chat-input"
  placeholder="궁금한 내용을 입력하세요..."
  rows="1"
  @keydown.enter.exact.prevent="handleSend"   ← Enter로 전송
  @input="autoResize"                          ← 입력마다 높이 조절
/>
```

### textarea auto-resize 원리

```javascript
const autoResize = () => {
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'       // ① 먼저 높이 초기화
    inputRef.value.style.height =
      Math.min(inputRef.value.scrollHeight, 200) + 'px'  // ② 내용에 맞게 조절 (최대 200px)
  }
}
```

```
1줄 입력:                    3줄 입력:                   많은 입력:
┌──────────────┐            ┌──────────────┐           ┌──────────────┐
│ 안녕하세요    │            │ 안녕하세요    │           │ 첫째줄       │
└──────────────┘            │ 두번째 줄     │           │ 둘째줄       │
  height: auto               │ 세번째 줄     │           │ ...          │
  → scrollHeight: 24px       └──────────────┘           │ 열번째줄     │
                              height: 72px               └──────────────┘
                                                          height: 200px (max)
                                                          overflow: scroll
```

```
왜 height = 'auto'를 먼저 설정하나?

textarea의 scrollHeight는 현재 height보다 작으면 현재 height를 반환합니다.
그래서 먼저 auto로 초기화해야 내용이 줄었을 때 높이도 줄어듭니다.

잘못된 방식:                    올바른 방식:
scrollHeight 바로 읽기           auto → scrollHeight 읽기
→ 한번 늘어나면 안 줄어듦         → 내용 줄면 높이도 줌
```

### 전송 후 높이 초기화

```javascript
const handleSend = () => {
  const text = inputText.value.trim()
  if (!text || isLoading.value) return

  store.dispatch('chat/sendMessage', text)
  inputText.value = ''

  // 전송 후 입력창 높이 초기화
  if (inputRef.value) {
    inputRef.value.style.height = 'auto'
  }
}
```

### 3. 전송 버튼 — 상태별 스타일

```html
<button
  class="send-btn"
  :class="{ active: inputText.trim() }"      ← 내용 있으면 활성 스타일
  :disabled="!inputText.trim() || isLoading"  ← 비어있거나 로딩 중이면 비활성
  @click="handleSend"
>
  <svg ...>전송 아이콘</svg>
</button>
```

```scss
.send-btn {
  background-color: var(--icon-bg);           // 기본: 어두운 배경
  color: var(--text-color-placeholder);       // 기본: 흐린 색
  cursor: not-allowed;                        // 기본: 클릭 불가

  &.active {
    background-color: var(--color-primary);   // 활성: 파란색
    color: #ffffff;                           // 활성: 흰색 아이콘
    cursor: pointer;

    &:hover {
      transform: scale(1.05);                // 호버 시 살짝 확대
    }
  }
}
```

```
비어있음:          입력 중:          로딩 중:
[⊘] (회색)        [➤] (파란색)     [⊘] (회색, disabled)
```

---

## 헤더 — 로그인 상태 + 다크모드

```javascript
const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])
const displayName = computed(() => store.getters['auth/displayName'])
const isDarkMode = computed(() => store.getters['app/isDarkMode'])
```

```html
<!-- 로그인 상태에 따른 분기 -->
<span v-if="isAuthenticated" class="user-label">{{ displayName }}</span>
<el-button v-else type="primary" size="small" @click="goToLogin">로그인</el-button>

<!-- 다크모드 토글 -->
<button class="theme-toggle-btn" @click="toggleDarkMode">
  <el-icon v-if="isDarkMode"><Sunny /></el-icon>    ← 다크모드면 ☀ 아이콘 (라이트로 전환)
  <el-icon v-else><Moon /></el-icon>                ← 라이트모드면 ☾ 아이콘 (다크로 전환)
</button>
```

```
로그인 됨:                     로그인 안 됨:
┌──────────────────────┐     ┌──────────────────────┐
│  ☾ MUREUM  홍길동    │     │  ☾ MUREUM  [로그인]  │
└──────────────────────┘     └──────────────────────┘
```

---

## Props — hideHeader

```javascript
defineProps({
  hideHeader: {
    type: Boolean,
    default: false
  }
})
```

```html
<div class="user-chat-view" :class="{ 'no-header': hideHeader }">
  <header v-if="!hideHeader" class="chat-header">...</header>
  ...
</div>
```

```
hideHeader 사용 시나리오:

1. 독립 전체화면 (/chat 라우트):
   hideHeader = false (기본값) → 헤더 표시

2. 관리자가 "새 창으로 열기" 클릭:
   window.open('/chat', '_blank', ...) → 헤더 표시

3. 다른 페이지에 임베드할 때 (가능):
   <UserChatView :hideHeader="true" /> → 헤더 숨김
```

---

## Lifecycle — 진입/이탈

```javascript
onMounted(() => {
  store.dispatch('app/setCurrentView', 'user')     // 현재 뷰를 'user'로 설정
  store.dispatch('chat/fetchChatHistory')            // 대화 이력 로드
})

onUnmounted(() => {
  store.dispatch('app/setCurrentView', 'admin')     // 'admin'으로 복원
})
```

```
사용자 화면 진입:
    │
    ├─ setCurrentView('user')   → 전역 상태에 현재 뷰 기록
    │                              (다른 컴포넌트가 "지금 사용자 뷰야" 확인 가능)
    │
    └─ fetchChatHistory()       → 과거 대화 목록 불러오기
                                   (사이드바에서 이전 대화 선택용)

사용자 화면 이탈:
    │
    └─ setCurrentView('admin')  → 관리자 뷰로 복원
```

---

## UserChatMessage — 사용자 전용 메시지 (1194줄)

> **파일**: `components/user/UserChatMessage.vue`

ChatMessage의 사용자 버전입니다. ChatGPT 스타일로 디자인되었습니다.

### 레이아웃 비교

```
ChatMessage (관리자):                    UserChatMessage (사용자):
──────────────────                      ──────────────────────
     ┌──────────┐                       ┌────────────────────────────────┐
     │ 질문 텍스트│                       │                    질문 텍스트  │
     └──────────┘                       └────────────────────────────────┘
 ← 오른쪽 정렬, 둥근 말풍선              ← 오른쪽 정렬, 둥근 말풍선 + 테두리

┌─────────────────┐                     ┌──┐ ┌──────────────────────────┐
│ 답변 텍스트       │                     │🤖│ │ 답변 텍스트                │
│ [NL2SQL] 320ms  │                     └──┘ │                          │
│ ▶ SQL 쿼리       │                          │ ▶ 조회 결과 (15건)        │ ← 토글
│ ▶ 조회 결과       │ ← el-collapse           │ [대시보드 추가] [Excel]   │
│   [Excel]        │                          │                          │
│ 📄 참고문서       │                          │ [NL2SQL] · 1/5  14:30  [📋]│
└─────────────────┘                          └──────────────────────────┘
 ← el-collapse 사용                          ← 자체 토글 버튼 + 아바타 + 복사
```

### 주요 차이점

| 기능 | ChatMessage | UserChatMessage |
|------|------------|-----------------|
| AI 아바타 | 없음 | 로봇 아이콘 (36px) |
| NL2SQL 결과 | el-collapse | 자체 토글 버튼 |
| 차트 | ChartBuilder | ChartBuilder + 대시보드 저장 |
| 복사 | 없음 | 클립보드 복사 버튼 |
| 메타 정보 | 상단 (el-tag) | 하단 (mode-badge + timestamp) |
| 행 제한 | 1000행 | 100행 |
| 모바일 대응 | 미지원 | 768px / 375px |

### NL2SQL 결과 토글 (자체 구현)

```html
<!-- el-collapse 대신 자체 토글 버튼 -->
<button class="result-toggle" @click="showResult = !showResult">
  <div class="toggle-left">
    <el-icon><TrendCharts /></el-icon>
    <span>조회 결과 ({{ message.sqlResult.row_count }}건)</span>
  </div>
  <el-icon class="toggle-icon" :class="{ expanded: showResult }">
    <ArrowDown />
  </el-icon>
</button>
<div v-show="showResult" class="result-content">
  <el-table ... />
  <ChartBuilder ... />
  <div class="export-bar">
    <el-button @click="showDashboardModal = true">대시보드에 추가</el-button>
    <el-button @click="exportToExcel">Excel 다운로드</el-button>
  </div>
</div>
```

```
접힌 상태:                    펼친 상태:
┌─────────────────────┐      ┌─────────────────────┐
│ 📊 조회 결과 (15건) ▼│      │ 📊 조회 결과 (15건) ▲│
└─────────────────────┘      │ ┌────┬────┬────┐    │
                              │ │부서│인원│비율│    │
                              │ ├────┼────┼────┤    │
                              │ │개발│ 25│ 35%│    │
                              │ ...                  │
                              │ [대시보드 추가][Excel] │
                              └─────────────────────┘
```

### 클립보드 복사 (보안 컨텍스트 체크)

```javascript
const copyContent = async () => {
  // HTTPS가 아니면 클립보드 API 사용 불가
  if (!window.isSecureContext) {
    ElMessage.warning('복사 기능은 https:// 주소에서만 지원됩니다.')
    return
  }

  try {
    await navigator.clipboard.writeText(props.message.content || '')
    ElMessage.success('답변이 클립보드에 복사되었습니다.')
  } catch {
    ElMessage.error('클립보드 복사에 실패했습니다.')
  }
}
```

```
isSecureContext 체크가 필요한 이유:

navigator.clipboard는 보안 컨텍스트에서만 동작합니다:
✅ https://example.com     → 동작
✅ http://localhost         → 동작 (개발용 예외)
❌ http://192.168.1.100    → 동작 안 함!

사내 서버가 HTTP로 배포되면 복사가 실패하므로,
미리 체크하고 친절한 안내 메시지를 보여줍니다.

SourceCard는 레거시 폴백(document.execCommand)을 사용하지만,
UserChatMessage는 경고 메시지만 표시합니다.
→ 보안 정책상 레거시 방법도 향후 제거될 예정이므로.
```

### 멀티턴 인디케이터

```javascript
const turnInfo = computed(() => {
  const { current_turn, max_turns } = props.message.metadata || {}
  if (current_turn && max_turns && props.message.queryType === 'nl2sql') {
    return `${current_turn}/${max_turns}`    // "2/5" 형태
  }
  return null
})
```

```
ChatMessage:  "턴 2/5"          UserChatMessage:  "2/5"
              ────────                             ────
              풀 텍스트                             간결한 숫자만
```

---

## 반응형 디자인 — 모바일 대응

UserChatView는 **3단계** 반응형을 지원합니다:

```scss
// 기본 (데스크탑)
.chat-content { max-width: 1200px; padding: 0 32px; }
.welcome-title { font-size: 36px; }
.mode-btn span { display: inline; }        // 모드명 텍스트 보임

// 태블릿/작은 모니터 (768px 이하)
@media (max-width: 768px) {
  .chat-content { padding: 0 16px; }       // 패딩 축소
  .welcome-title { font-size: 24px; }      // 제목 작게
  .mode-btn span { display: none; }        // 모드명 숨김 (아이콘만)
  .mode-btn .arrow { display: none; }      // 화살표도 숨김
  .example-queries { flex-direction: column; }  // 예시 세로 배치
}

// 소형 폰 (375px 이하)
@media (max-width: 375px) {
  .chat-content { padding: 0 12px; }       // 더 좁은 패딩
  .welcome-title { font-size: 22px; }
  .example-queries .example-btn { font-size: 12px; }
}
```

```
데스크탑 (>768px):              태블릿 (≤768px):          소형폰 (≤375px):
┌──────────────────┐          ┌──────────────┐         ┌──────────┐
│ [RAG▾] [입력] [➤]│          │ [⚙] [입력][➤]│         │ [⚙][입력]│
└──────────────────┘          └──────────────┘         │    [➤]   │
  모드명+화살표 표시             아이콘만 표시              더 좁은 여백
  가로 배치 예시                세로 배치 예시              작은 폰트
```

---

## 리뷰 체크리스트

- [x] 독립 전체화면으로 동작하는가? → AdminLayout 없이 자체 header/footer ✅
- [x] 다크모드 토글이 동작하는가? → `store.dispatch('app/toggleDarkMode')` ✅
- [x] 비로그인 사용자도 접근 가능한가? → 로그인 버튼 표시 ✅
- [x] textarea가 내용에 따라 높이 조절되는가? → autoResize() ✅
- [x] Enter로 전송, 전송 후 높이 초기화되는가? ✅
- [x] 전송 버튼이 입력 상태에 따라 시각적으로 변하는가? → `.active` 클래스 ✅
- [x] 모드 변경이 Store와 연동되는가? → `@command → setMode()` ✅
- [x] 모바일에서 레이아웃이 깨지지 않는가? → 768px, 375px breakpoint ✅
- [x] 클립보드 복사가 보안 컨텍스트를 체크하는가? → `isSecureContext` ✅
- [x] 대시보드 저장 기능이 있는가? → `SaveToDashboardModal` ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **el-dropdown** | Element Plus 드롭다운. `@command`로 선택값 전달 |
| **autoResize** | `height='auto'` → `scrollHeight` 읽기 → 높이 설정 |
| **hideHeader prop** | 임베드 모드 지원. true면 헤더 숨김 |
| **isSecureContext** | HTTPS/localhost 여부 확인. 클립보드 API 사전 체크 |
| **v-show vs v-if** | v-show: DOM 유지 + display 토글 (빈번한 토글에 적합) |
| **onMounted/onUnmounted** | 컴포넌트 진입/이탈 시 전역 상태 설정/복원 |
| **반응형 breakpoint** | 768px (태블릿), 375px (소형폰) 기준 스타일 분기 |

---
> **다음**: [04_how_it_works.md](04_how_it_works.md) — 시나리오별 전체 흐름
