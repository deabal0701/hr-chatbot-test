# 1. 입력과 메시지 표시 컴포넌트

> **학습 목표**: 채팅의 **입력 → 전송 → 표시** 흐름을 컴포넌트 단위로 이해한다.

---

## ChatInput — 입력 컴포넌트 (66줄)

> **파일**: `components/chat/ChatInput.vue`

관리자 화면(ChatView)에서 사용하는 **재사용 가능한** 입력 컴포넌트입니다.

```
┌──────────────────────────────────────────┐
│  [textarea (auto-resize)]   [전송 버튼]  │
└──────────────────────────────────────────┘
```

### 전체 코드 (66줄 — 짧아서 전부 살펴봅니다)

```html
<template>
  <div class="chat-input">
    <el-input
      v-model="inputText"
      type="textarea"
      :rows="2"
      :autosize="{ minRows: 2, maxRows: 6 }"    ← Element Plus가 높이 자동 조절
      :placeholder="placeholder"
      :disabled="disabled"
      @keydown.enter.exact.prevent="handleSend"  ← Enter만 누르면 전송 (Shift+Enter는 줄바꿈)
    />
    <el-button
      type="primary"
      :icon="Promotion"
      :disabled="disabled || !inputText.trim()"  ← 빈 내용이면 비활성
      @click="handleSend"
    >
      전송
    </el-button>
  </div>
</template>
```

**핵심 포인트:**

```
Props (부모 → 자식)          Events (자식 → 부모)
──────────────────          ─────────────────────
disabled: Boolean           emit('send', text)
placeholder: String
```

```javascript
const handleSend = () => {
  const text = inputText.value.trim()
  if (text && !props.disabled) {
    emit('send', text)       // 부모에게 텍스트 전달
    inputText.value = ''     // 입력란 비우기
  }
}
```

**비유**: ChatInput은 "마이크"입니다.
마이크는 소리(텍스트)를 받아서 스피커(부모)에게 전달만 합니다.
마이크가 직접 처리하지 않습니다.

```
ChatView (부모)                   ChatInput (자식)
─────────────                   ────────────────
                                사용자 입력: "재택근무 정책?"
                                    │
                         emit('send', text) ──→
handleSend(query) ←──────────────┘
    │
store.dispatch('chat/sendMessage', query)
```

---

## ChatMessage — 관리자 메시지 표시 (639줄)

> **파일**: `components/chat/ChatMessage.vue`

관리자 화면의 **메시지 말풍선**입니다. 하나의 컴포넌트가 사용자/AI 양쪽 역할을 모두 처리합니다.

### 레이아웃 구조

```
message.role === 'user'                message.role === 'assistant'
─────────────────────                  ──────────────────────────
          ┌────────────┐              ┌─────────────────────────┐
          │ 재택근무    │              │  답변 내용 (마크다운)     │
          │ 정책이 뭐야?│              │  ─────────────────       │
          └────────────┘              │  메타: [RAG] 턴 1/5 320ms│
                                      │  ─────────────────       │
                          14:30       │  [실행된 SQL 쿼리]  ← NL2SQL│
                                      │  [참고 문서 (3개)]  ← RAG   │
                                      │  [실행 단계 보기]   ← Agent │
                                      └─────────────────────────┘
                                                          14:30
```

### 역할별 분기

```html
<!-- 사용자 메시지: 단순 텍스트 -->
<div v-if="message.role === 'user'" class="message-bubble user">
  <div class="message-content">{{ message.content }}</div>
</div>

<!-- AI 응답: 복잡한 구조 -->
<div v-else class="message-bubble assistant">
  <!-- ① 스트리밍 진행 중 -->
  <template v-if="message.isStreaming">
    <div class="streaming-indicator">...</div>
  </template>
  <!-- ② 최종 응답 -->
  <template v-else>
    <div class="message-content" v-html="formattedContent"></div>
  </template>
  <!-- ③ 메타 정보 -->
  <!-- ④ NL2SQL 결과 (SQL + 테이블 + 차트 + Excel) -->
  <!-- ⑤ RAG 출처 (SourceCard 목록) -->
  <!-- ⑥ Agent 결과 (실행 단계) -->
</div>
```

### AI 응답의 6가지 섹션

```
┌─────────────────────────────────────────────┐
│ ① 스트리밍 진행 (isStreaming === true일 때)   │
│    ✓ 의도 분석 완료                          │
│    ✓ SQL 생성 완료                           │
│    ● ● ● 쿼리 실행 중...                     │
├─────────────────────────────────────────────┤
│ ② 답변 텍스트 (마크다운 → HTML)              │
│    formatMarkdownToHtml(message.content)     │
│    → v-html로 렌더링                         │
├─────────────────────────────────────────────┤
│ ③ 메타 정보                                  │
│    [RAG 태그]  턴 1/5  320ms                 │
├─────────────────────────────────────────────┤
│ ④ NL2SQL 결과 (message.sql 존재 시)          │
│    ├─ [실행된 SQL 쿼리] ← el-collapse        │
│    └─ [조회 결과]       ← el-table + 차트    │
│        └─ [Excel 다운로드] 버튼               │
├─────────────────────────────────────────────┤
│ ⑤ RAG 출처 (message.sources 존재 시)         │
│    📄 참고 문서 (3개)                        │
│    ├─ SourceCard                             │
│    ├─ SourceCard                             │
│    └─ SourceCard                             │
├─────────────────────────────────────────────┤
│ ⑥ Agent 결과 (message.agentResult 존재 시)   │
│    [실행 단계 보기] ← el-collapse             │
│    ├─ Step 1: query_database [SQL+테이블]    │
│    ├─ Step 2: search_documents               │
│    └─ 총 3번 반복 | 도구: sql, rag | 성공    │
└─────────────────────────────────────────────┘
```

### 마크다운 렌더링

```javascript
import { formatMarkdownToHtml, registerTableCopyFunction } from '@/utils/markdownParser'

// AI 답변을 HTML로 변환
const formattedContent = computed(() => {
  return formatMarkdownToHtml(props.message.content)
})
```

```
AI 응답 원문 (마크다운):          렌더링 결과 (HTML):
──────────────────────          ─────────────────────
# 재택근무 정책                 <h1>재택근무 정책</h1>

**조건**: 입사 1년 이상         <strong>조건</strong>: 입사 1년 이상

| 항목 | 기준 |                 <table>
|------|------|                   <tr><th>항목</th><th>기준</th></tr>
| 대상 | 정규직 |                  <tr><td>대상</td><td>정규직</td></tr>
                                </table>
```

CSS에서 마크다운 요소 스타일링에 **SCSS mixin**을 사용합니다:

```scss
.message-content {
  @include mx.md-table-styles;     // 테이블 스타일
  @include mx.copy-table-btn;      // 테이블 복사 버튼
  @include mx.md-header-styles;    // 제목 스타일
  @include mx.md-list-styles;      // 목록 스타일
  @include mx.inline-code-styles;  // 인라인 코드
  @include mx.code-block-styles;   // 코드 블록
  @include mx.strong-styles;       // 볼드
  @include mx.md-hr-styles;        // 수평선
  @include mx.md-em-styles;        // 기울임
}
```

### 메타 정보 — 모드 태그 + 멀티턴 + 응답시간

```javascript
// 모드별 태그 색상
const queryTypeTag = computed(() => {
  switch (props.message.queryType) {
    case 'rag':    return { label: 'RAG',    type: 'success' }  // 초록
    case 'nl2sql': return { label: 'NL2SQL', type: 'warning' }  // 주황
    case 'agent':  return { label: 'Agent',  type: 'primary' }  // 파랑
    default:       return { label: 'Auto',   type: 'info' }     // 회색
  }
})

// NL2SQL 멀티턴 표시 (예: "턴 2/5")
const turnInfo = computed(() => {
  const { current_turn, max_turns } = props.message.metadata || {}
  if (current_turn && max_turns && props.message.queryType === 'nl2sql') {
    return `턴 ${current_turn}/${max_turns}`
  }
  return null
})
```

```
[NL2SQL]  턴 2/5  320ms
  │        │       │
  │        │       └─ 서버 응답 시간 (message.responseTimeMs)
  │        └─ 현재 턴 / 최대 턴 (멀티턴 대화)
  └─ 검색 모드 태그 (색상으로 구분)
```

### NL2SQL 결과 — SQL + 테이블 + 차트 + Excel

```html
<div v-if="message.sql" class="nl2sql-result">
  <el-collapse>
    <!-- SQL 코드 보기 -->
    <el-collapse-item title="실행된 SQL 쿼리" name="sql">
      <pre class="sql-code">{{ message.sql }}</pre>
    </el-collapse-item>

    <!-- 조회 결과 테이블 + 차트 -->
    <el-collapse-item v-if="message.sqlResult" title="조회 결과" name="result">
      <el-table :data="message.sqlResult.rows.slice(0, 1000)" ...>
        <el-table-column v-for="col in message.sqlResult.columns" .../>
      </el-table>
      <ChartBuilder :columns="..." :rows="..." />
      <el-button @click="exportToExcel">Excel 다운로드</el-button>
    </el-collapse-item>
  </el-collapse>
</div>
```

**el-collapse 동작:**

```
초기 상태:                        클릭 후:
┌──────────────────────┐         ┌──────────────────────┐
│ ▶ 실행된 SQL 쿼리     │         │ ▼ 실행된 SQL 쿼리     │
├──────────────────────┤         │  SELECT department,   │
│ ▶ 조회 결과           │         │    COUNT(*) as cnt    │
└──────────────────────┘         │  FROM employee        │
                                  │  GROUP BY department  │
  접혀 있음 → 화면 절약           ├──────────────────────┤
                                  │ ▶ 조회 결과           │
                                  └──────────────────────┘
                                    SQL만 펼침
```

### Excel 내보내기

```javascript
const exportToExcel = async () => {
  exporting.value = true
  try {
    const msg = props.message
    const cb = chartBuilderRef.value              // ChartBuilder 인스턴스 참조
    const includeChart = cb?.chartGenerated || false

    await searchApi.exportExcel({
      columns: msg.sqlResult.columns,             // 컬럼 목록
      rows: msg.sqlResult.rows,                   // 데이터 행
      question: msg.content || '',                // 원래 질문
      sql: msg.sql || '',                         // 실행된 SQL
      include_chart: includeChart,                // 차트 포함 여부
      chart_config: includeChart ? {              // 차트 설정
        chart_type: cb.chartType,
        x_column: cb.xAxisColumn,
        y_columns: cb.yAxisColumns
      } : null
    })
    ElMessage.success('Excel 파일이 다운로드되었습니다.')
  } catch {
    ElMessage.error('Excel 다운로드에 실패했습니다.')
  } finally {
    exporting.value = false
  }
}
```

```
사용자가 [Excel 다운로드] 클릭
    │
    ├─ exporting = true (버튼에 로딩 스피너)
    │
    ├─ searchApi.exportExcel({columns, rows, chart_config})
    │   → 서버가 Excel(.xlsx) 파일 생성
    │   → Blob으로 다운로드
    │
    ├─ 성공 → ElMessage.success("Excel 파일이 다운로드되었습니다.")
    └─ 실패 → ElMessage.error("Excel 다운로드에 실패했습니다.")
```

---

## SourceCard — RAG 출처 카드 (337줄)

> **파일**: `components/chat/SourceCard.vue`

RAG 검색 결과의 **출처 문서**를 보여주는 카드입니다.

### 카드 구조

```
┌──────────────────────────────────────────┐
│ [정책] 재택근무 가이드라인     V 85.3%   │ ← 문서타입 + 제목 + 점수
│ 재택근무는 입사 1년 이상 정규직 직원이... │ ← 내용 미리보기 (150자)
└──────────────────────────────────────────┘
  ↑ 클릭하면 상세 다이얼로그 열림
```

### 점수 표시 — 3가지 검색 점수

```
하이브리드 검색 (벡터 + 키워드):
┌──────────────────────────────────────┐
│  V 85.3%  K 72.1%  (RRF 1.23%)      │
│  │         │        │                │
│  │         │        └─ RRF 점수      │
│  │         └─ 키워드 점수 (BM25)     │
│  └─ 벡터 점수 (코사인 유사도)        │
└──────────────────────────────────────┘

단일 검색 (벡터만):
┌──────────────────────────────────────┐
│  85.3%                               │ ← similarity_score 표시
└──────────────────────────────────────┘
```

```html
<!-- 점수 표시 로직 -->
<span v-if="source.vector_score" class="score-vector">
  V {{ (source.vector_score * 100).toFixed(1) }}%
</span>
<span v-if="source.keyword_score" class="score-keyword">
  K {{ (source.keyword_score * 100).toFixed(1) }}%
</span>
<!-- 하이브리드가 아닌 단일 검색일 때만 표시 -->
<span v-if="source.similarity_score && !source.vector_score && !source.keyword_score">
  {{ (source.similarity_score * 100).toFixed(1) }}%
</span>
<span v-if="source.rrf_score">
  (RRF {{ (source.rrf_score * 100).toFixed(2) }}%)
</span>
```

### 상세 다이얼로그

```
┌──────────────────────────────────────────┐
│  재택근무 가이드라인                  [X] │
├──────────────────────────────────────────┤
│  [정책] 벡터: 85.3% 키워드: 72.1%       │
│                                          │
│  ┌────────────────────────────────[📋]┐  │ ← 복사 버튼
│  │ 재택근무는 입사 1년 이상 정규직      │  │
│  │ 직원이 부서장 승인 하에 주 2회까지   │  │
│  │ 시행할 수 있다. ...                 │  │
│  └────────────────────────────────────┘  │
│                                          │
│  메타데이터                               │
│  ┌─────────┬──────────────────────────┐  │
│  │ source  │ HR_정책_2024.pdf         │  │
│  │ page    │ 15                       │  │
│  └─────────┴──────────────────────────┘  │
└──────────────────────────────────────────┘
```

### 클립보드 복사 (폴백 패턴)

```javascript
const copyContent = async () => {
  try {
    // ① 최신 Clipboard API 시도
    await navigator.clipboard.writeText(props.source.content || '')
  } catch {
    // ② 실패 시 레거시 방법 (HTTP 환경 등)
    const textarea = document.createElement('textarea')
    textarea.value = props.source.content || ''
    document.body.appendChild(textarea)
    textarea.select()
    document.execCommand('copy')            // 구식이지만 HTTP에서 동작
    document.body.removeChild(textarea)
  }
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)  // 2초 후 "복사됨!" 해제
}
```

```
Clipboard API 가능?  ──→  navigator.clipboard.writeText()  ✅
   (HTTPS 필요)
        │
        ▼ 실패
document.execCommand('copy')  ← 레거시 폴백 (HTTP에서도 동작)
```

---

## 관리자 ChatView — 오버레이 사이드바

> **파일**: `views/admin/ChatView.vue` (524줄)

### 사이드바 슬라이딩 메커니즘

```
평소 (숨겨진 상태):                    호버 후 (보이는 상태):
┌────────────────────── «│            ┌──────────── «│검색 모드      │
│                        │            │              │[● RAG]        │
│  채팅 영역              │            │  채팅 영역    │[○ NL2SQL]     │
│                        │            │              │───────────    │
│                        │            │              │대화관리│사용자 │
└────────────────────────┘            └──────────────┘화면         │
                                                     └─────────────┘
```

### 호버 타이머 로직

```javascript
// 마우스 진입 → 500ms 후 표시
const showSidebar = () => {
  if (sidebarHideTimer) {             // 숨기기 타이머가 있으면 취소
    clearTimeout(sidebarHideTimer)
    sidebarHideTimer = null
  }
  if (!isSidebarVisible.value && !sidebarShowTimer) {
    sidebarShowTimer = setTimeout(() => {
      isSidebarVisible.value = true   // 500ms 후 표시
      sidebarShowTimer = null
    }, 500)
  }
}

// 마우스 이탈 → 500ms 후 숨김
const hideSidebar = () => {
  if (sidebarShowTimer) {             // 표시 타이머가 있으면 취소
    clearTimeout(sidebarShowTimer)
    sidebarShowTimer = null
  }
  if (isSidebarVisible.value) {
    sidebarHideTimer = setTimeout(() => {
      isSidebarVisible.value = false  // 500ms 후 숨김
      sidebarHideTimer = null
    }, 500)
  }
}

// 클릭 → 즉시 토글 (타이머 무시)
const toggleSidebar = () => {
  clearTimeout(sidebarShowTimer)
  clearTimeout(sidebarHideTimer)
  isSidebarVisible.value = !isSidebarVisible.value
}
```

```
마우스 시나리오:

1. 호버 진입 → 0.5초 기다림 → 사이드바 나타남
2. 호버 이탈 → 0.5초 기다림 → 사이드바 숨겨짐
3. 빠른 진입→이탈 (0.5초 미만) → 아무 일 없음 (타이머 취소됨)
4. 클릭 → 즉시 토글 (기다림 없음)

왜 500ms 딜레이?
→ 실수로 마우스가 스쳤을 때 사이드바가 깜빡이지 않도록
→ 의도적 호버와 실수 호버를 구분하는 UX 패턴
```

### CSS 슬라이딩 트랜지션

```scss
.sidebar-overlay-wrapper {
  position: absolute;
  right: 0;
  transform: translateX(280px);         // 오른쪽 바깥에 숨김
  transition: transform 0.5s cubic-bezier(0.4, 0, 0.2, 1);

  &.visible {
    transform: translateX(0);           // 제자리로 슬라이딩
  }
}
```

```
transform 방식의 장점:
──────────────────────
width 변경 → 레이아웃 재계산 (리플로우) → 느림 ❌
transform 변경 → GPU 처리 (컴포지팅) → 빠름 ✅

cubic-bezier(0.4, 0, 0.2, 1) = "ease-out" 느낌
→ 시작은 빠르고, 끝은 천천히 = 자연스러운 감속
```

### 모드별 예시 질문

```javascript
const ragExampleQueries = [
  '재택근무 정책의 적용 조건과 제한 사항은?',
  '연차 휴가 신청 절차와 승인 기준은?', ...
]

const nl2sqlExampleQueries = [
  '2017년 입사자 현황을 상세하게 알려줘!',
  '우리회사의 부서별 직원 수는?', ...
]

// 현재 모드에 맞는 예시 반환
const exampleQueries = computed(() => {
  if (searchMode.value === 'nl2sql') return nl2sqlExampleQueries
  if (searchMode.value === 'agent')  return agentExampleQueries
  return ragExampleQueries
})
```

```
모드 변경 시 환영 메시지도 변경:

RAG 모드:     "문서 기반 질문을 자유롭게 해주세요."
NL2SQL 모드:  "데이터베이스 기반 질문을 자유롭게 해주세요."
Agent 모드:   "AI Agent에게 복합 질문을 자유롭게 해주세요."
```

### 자동 스크롤

```javascript
// 새 메시지 추가 시 맨 아래로 스크롤
watch(messages, async () => {
  await nextTick()                    // DOM 업데이트 완료 대기
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}, { deep: true })                    // 메시지 내용 변경도 감지
```

```
nextTick()이 필요한 이유:

messages 배열 변경 → Vue 반응형 시스템 감지
  → 아직 DOM은 업데이트 안 됨!
  → 이 시점에 scrollHeight를 읽으면 이전 값

await nextTick()
  → DOM 업데이트 완료!
  → 이제 scrollHeight에 새 메시지 높이 포함
  → scrollTop = scrollHeight → 맨 아래로 이동
```

---

## 리뷰 체크리스트

- [x] ChatInput이 부모-자식 통신 패턴(props/emit)을 따르는가? ✅
- [x] Enter키로 전송, Shift+Enter로 줄바꿈이 동작하는가? → `@keydown.enter.exact.prevent` ✅
- [x] ChatMessage가 사용자/AI 메시지를 구분하는가? → `message.role` 분기 ✅
- [x] 마크다운이 안전하게 렌더링되는가? → `formatMarkdownToHtml` + `v-html` ✅
- [x] NL2SQL 결과가 접이식으로 표시되는가? → `el-collapse` ✅
- [x] Excel 내보내기가 차트 포함을 지원하는가? → `chartBuilderRef` 참조 ✅
- [x] SourceCard가 점수를 정확히 표시하는가? → 벡터/키워드/RRF 분기 ✅
- [x] 사이드바가 의도치 않게 깜빡이지 않는가? → 500ms 딜레이 타이머 ✅
- [x] 새 메시지 시 자동 스크롤이 동작하는가? → `watch` + `nextTick` ✅

## 핵심 정리

| 개념 | 설명 |
|------|------|
| **emit('send', text)** | 자식→부모 이벤트 전달. ChatInput의 유일한 출력 |
| **v-html** | HTML 문자열을 DOM으로 렌더링. XSS 주의 (sanitize 필요) |
| **formatMarkdownToHtml** | 마크다운→HTML 변환 유틸리티 |
| **el-collapse** | Element Plus 접이식 패널. 펼침/접힘으로 정보량 조절 |
| **SCSS mixin** | `@include mx.md-table-styles` 등으로 마크다운 스타일 일괄 적용 |
| **setTimeout + clearTimeout** | 디바운싱 패턴. 빠른 반복 동작에서 마지막 것만 실행 |
| **transform: translateX** | GPU 가속 애니메이션. width 변경보다 성능 우수 |
| **nextTick()** | Vue DOM 업데이트 완료 후 코드 실행 보장 |

---
> **다음**: [02_sse_streaming_ui.md](02_sse_streaming_ui.md) — SSE 스트리밍과 chat Store
