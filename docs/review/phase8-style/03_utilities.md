# Phase 8-3: 유틸리티 — CSS 클래스 & JS 함수

## 이 문서의 목적

자주 사용되는 **CSS 유틸리티 클래스**(`_utilities.scss`, `_chat-global.scss`)와
**JS 유틸리티 함수**(markdownParser, format, exportUtils)를 설명합니다.

---

## 비유: 공구함

```
유틸리티 = 공구함의 도구들

  CSS 유틸리티 = 기본 공구 (드라이버, 망치, 자)
    → .flex, .mt-10, .text-center

  JS 유틸리티 = 전동 공구 (전동 드릴, 그라인더)
    → formatMarkdownToHtml(), downloadCsv()

  둘 다 "어떤 프로젝트든" 필요할 때 꺼내 쓰는 범용 도구입니다.
```

---

## Part 1: CSS 유틸리티 클래스

### 1-1. _utilities.scss (60줄)

HTML에 클래스명만 붙이면 즉시 스타일이 적용되는 **원자적 클래스**들입니다.

#### 레이아웃 유틸리티

```scss
.flex         { display: flex; }
.flex-center  { display: flex; align-items: center; justify-content: center; }
.flex-between { display: flex; align-items: center; justify-content: space-between; }
.flex-1       { flex: 1; }
```

```html
<!-- 사용 예 -->
<div class="flex-between">
  <span>왼쪽 텍스트</span>
  <span>오른쪽 텍스트</span>
</div>
```

```
.flex-between 결과:

  ┌──────────────────────────────────────┐
  │  왼쪽 텍스트            오른쪽 텍스트  │
  └──────────────────────────────────────┘
```

#### 텍스트 유틸리티

```scss
.text-center  { text-align: center; }
.text-primary { color: var(--color-primary); }    // 파란색
.text-success { color: var(--color-success); }    // 초록색
.text-warning { color: var(--color-warning); }    // 주황색
.text-danger  { color: var(--color-danger); }     // 빨간색
.text-muted   { color: var(--text-color-secondary); }  // 연한 회색
```

#### 간격 유틸리티

```scss
.mt-10 { margin-top: 10px; }      .mt-20 { margin-top: 20px; }
.mb-10 { margin-bottom: 10px; }   .mb-20 { margin-bottom: 20px; }
.ml-10 { margin-left: 10px; }     .mr-10 { margin-right: 10px; }
.p-10  { padding: 10px; }         .p-20  { padding: 20px; }
```

```
네이밍 규칙:
  m = margin,  p = padding
  t = top,  b = bottom,  l = left,  r = right
  숫자 = px 값

  .mt-20 = margin-top: 20px
```

---

### 1-2. _chat-global.scss (179줄) — 공통 레이아웃 클래스

전역으로 사용되는 **구조적 스타일 클래스**들입니다.

#### 채팅 레이아웃

```scss
.chat-container   { height: 100%; display: flex; flex-direction: column; }
.chat-messages    { flex: 1; overflow-y: auto; padding: 20px; }
.chat-input-area  { padding: 20px; border-top: 1px solid var(--chat-input-border); }
```

```
채팅 레이아웃 구조:

  ┌─── .chat-container ────────────┐
  │                                │
  │  ┌── .chat-messages ────────┐  │
  │  │                          │  │  flex: 1 (남은 공간 모두 차지)
  │  │  메시지1                  │  │  overflow-y: auto (스크롤)
  │  │  메시지2                  │  │
  │  │  메시지3                  │  │
  │  └──────────────────────────┘  │
  │  ────────────────────────────  │  border-top
  │  ┌── .chat-input-area ──────┐  │
  │  │  [질문을 입력하세요... ]   │  │  고정 높이
  │  └──────────────────────────┘  │
  └────────────────────────────────┘
```

#### 메시지 버블

```scss
.message-bubble {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: 8px;
  margin-bottom: 16px;

  &.user {
    background-color: var(--chat-bubble-user-bg);
    margin-left: auto;                          // 오른쪽 정렬
    border-bottom-right-radius: 2px;            // 꼬리 효과
  }

  &.assistant {
    background-color: var(--chat-bubble-assistant-bg);
    border: 1px solid var(--chat-bubble-assistant-border);
    border-bottom-left-radius: 2px;             // 꼬리 효과
  }
}
```

```
메시지 버블 레이아웃:

              ┌──────────────────────┐
              │  2024년 입사자 수는?  ├┐  ← user (오른쪽, 꼬리 우하단)
              └──────────────────────┘│
                                     ┘

  ┌┬──────────────────────────────┐
  │├  2024년 입사자는 총 15명이며, │  ← assistant (왼쪽, 꼬리 좌하단)
  ┘│  부서별 분포는 다음과 같습니다 │
   └──────────────────────────────┘
```

#### 카드 & 페이지 헤더

```scss
.content-card {
  background-color: var(--bg-color-card);
  border-radius: 6px;
  padding: 12px;
  box-shadow: var(--box-shadow);
}

.page-header {
  display: flex;
  justify-content: space-between;
  h2 { font-size: 20px; font-weight: 500; }
  .header-right { display: flex; gap: 8px; }
}
```

```
page-header 레이아웃:

  ┌──────────────────────────────────────────┐
  │  사용자 관리                   [+ 추가]   │
  │  사용자를 관리합니다                       │
  │  ←── h2 + subtitle     header-right ──→  │
  └──────────────────────────────────────────┘
```

#### 기타 공통 클래스

```scss
.filter-row          // 검색/필터 도구 모음 (flex-wrap)
.pagination-wrapper  // 페이지네이션 감싸기
.title-link          // 클릭 가능한 제목 (말줄임 + 포인터)
.section-title       // 섹션 제목
.empty-state         // 빈 상태 메시지 (중앙 정렬)
.form-help           // 폼 도움말 텍스트
.loading-overlay     // 로딩 오버레이 (absolute 전체 커버)
```

---

## Part 2: JS 유틸리티 — markdownParser.js (308줄)

### 2-1. formatMarkdownToHtml() — 11단계 파이프라인

AI가 응답한 마크다운 텍스트를 HTML로 변환하는 핵심 함수입니다.

```
입력: "## 결과\n\n**총원**: 15명\n\n| 부서 | 인원 |\n|---|---|\n| 개발 | 8 |"
                    │
         11단계 변환 파이프라인
                    │
                    ▼
출력: "<span class='md-h2'>결과</span><br>
       <strong>총원</strong>: 15명<br>
       <div class='md-table-wrapper'>...</div>"
```

### 변환 순서 (순서가 중요!)

```
┌─────┬──────────────────┬──────────────────────────────────┐
│ 단계 │ 처리 대상         │ 왜 이 순서?                       │
├─────┼──────────────────┼──────────────────────────────────┤
│  1  │ 코드 블록 (```)   │ 코드 안의 마크다운이 변환되면 안 됨 │
│  2  │ 인라인 코드 (`)   │ 같은 이유                         │
│  3  │ 테이블 (| ... |)  │ 테이블 파이프가 다른 규칙과 충돌    │
│  4  │ 헤더 (## ###)     │ 블록 요소 먼저                    │
│  5  │ 수평선 (---)      │ 블록 요소                        │
│  6  │ 볼드 (**text**)   │ * 하나와 구분 필요 (볼드 먼저)     │
│  7  │ 기울임 (*text*)   │ 볼드 처리 후 남은 * 만 대상       │
│  8  │ 리스트 (-, *, 1.) │ 인라인 요소                      │
│  9  │ 줄바꿈 (\n)       │ 마지막에 처리                     │
│ 10  │ <br> 정리         │ 블록 요소 사이 중복 <br> 제거      │
│ 11  │ placeholder 복원  │ 보호했던 코드 블록 되돌리기         │
└─────┴──────────────────┴──────────────────────────────────┘
```

### Placeholder 보호 패턴

```javascript
const placeholders = []

const hold = (html) => {
  const idx = placeholders.length
  placeholders.push(html)
  return `\x00${idx}\x00`        // 특수문자로 치환
}

// 1단계: 코드 블록을 placeholder로 교체
text = text.replace(/```(\w*)\n?([\s\S]*?)```/g, (_, lang, code) => {
  return hold(`<pre><code>${escapeHtml(code)}</code></pre>`)
  //     ^^^^^^ 실제 HTML을 배열에 저장, 텍스트에는 \x00인덱스\x00만 남김
})

// 2~10단계: 다른 마크다운 처리
// → \x00인덱스\x00은 마크다운 규칙에 걸리지 않음!

// 11단계: placeholder 복원
placeholders.forEach((html, i) => {
  text = text.replace(`\x00${i}\x00`, html)
})
```

```
비유: 소중한 물건을 금고에 넣기

  ① 코드 블록을 금고에 넣고 (placeholder), 영수증만 남김 (\x00번호\x00)
  ② 나머지 텍스트에 대해 마음껏 변환 작업
  ③ 작업 끝나면 영수증을 금고의 물건으로 교환
```

### XSS 방지 — escapeHtml()

```javascript
function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')     // & → &amp;
    .replace(/</g, '&lt;')     // < → &lt;
    .replace(/>/g, '&gt;')     // > → &gt;
    .replace(/"/g, '&quot;')   // " → &quot;
}
```

> 사용자 또는 AI의 응답에 `<script>alert('XSS')</script>` 같은
> 악의적 HTML이 있어도 `&lt;script&gt;`로 변환되어 **실행되지 않습니다**.

### 테이블 파서 (parseMarkdownTable)

```javascript
// 입력:
// | 이름 | 부서 |
// |------|------|
// | 김철수 | 개발 |

// 출력 HTML:
// <div class="md-table-wrapper">
//   <button class="copy-table-btn">...</button>
//   <div class="md-table-scroll">
//     <table class="md-table">
//       <thead><tr><th>이름</th><th>부서</th></tr></thead>
//       <tbody><tr><td>김철수</td><td>개발</td></tr></tbody>
//     </table>
//   </div>
// </div>
```

```
변환 과정:

  | 이름 | 부서 |      ← 첫 번째 줄 → thead (헤더)
  |------|------|      ← 구분선 → skip
  | 김철수 | 개발 |    ← 나머지 줄 → tbody (본문)
```

### 2-2. registerTableCopyFunction() — 전역 복사

```javascript
export function registerTableCopyFunction() {
  window.copyTable = (btn) => {
    // 1. 버튼의 부모에서 테이블 찾기
    const table = btn.closest('.md-table-wrapper').querySelector('table')

    // 2. 테이블 → 탭 구분 텍스트로 변환
    let text = ''
    table.querySelectorAll('tr').forEach(row => {
      const cells = row.querySelectorAll('th, td')
      text += Array.from(cells).map(c => c.textContent.trim()).join('\t') + '\n'
    })

    // 3. 클립보드 복사 (HTTPS 우선, HTTP fallback)
    if (window.isSecureContext && navigator.clipboard) {
      navigator.clipboard.writeText(text)
    } else {
      fallbackCopy(text)     // execCommand('copy') 사용
    }
  }
}
```

```
왜 window.copyTable인가?

  v-html로 렌더링된 HTML의 onclick은 Vue 바인딩이 아닌 순수 DOM 이벤트.
  따라서 전역 함수(window.copyTable)로 등록해야 동작합니다.

  <button onclick="window.copyTable(this)">  ← v-html 내부
```

### 복사 fallback 전략

```
① navigator.clipboard (HTTPS 전용)
     │
     └─ 실패 시
         │
         ▼
② document.execCommand('copy') (HTTP에서도 동작)
     │
     └─ 실패 시
         │
         ▼
③ 경고 토스트: "복사 기능은 HTTPS 환경에서만 지원됩니다."
```

---

## Part 3: JS 유틸리티 — format.js (69줄)

날짜, 숫자, 시간을 한국어 형식으로 포맷하는 함수 5개입니다.

```javascript
formatDateTime("2026-02-12T16:38:47")  → "2026.02.12 16:38:47"
formatDate("2026-02-12")                → "2026.02.12"
formatNumber(1234567)                   → "1,234,567"
formatResponseTime(850)                 → "850ms"
formatResponseTime(2500)                → "2.5s"
truncateText("아주 긴 텍스트...", 10)    → "아주 긴 텍스트..."
```

### null 안전 처리

```javascript
export function formatDateTime(dateStr) {
  if (!dateStr) return '-'              // null/undefined → "-"
  const d = new Date(dateStr)
  if (isNaN(d.getTime())) return '-'    // 잘못된 날짜 → "-"
  // ...
}
```

> 모든 포맷 함수에 **null/undefined 방어**가 있어,
> API에서 빈 값이 와도 에러 없이 `"-"`를 표시합니다.

---

## Part 4: JS 유틸리티 — exportUtils.js (188줄)

### 4-1. 파일 다운로드 기본 함수

```javascript
// Blob → 파일 다운로드
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob)    // Blob → 임시 URL 생성
  const link = document.createElement('a') // 가상 링크 생성
  link.href = url
  link.download = filename
  link.click()                             // 클릭 → 다운로드 시작
  URL.revokeObjectURL(url)                 // 메모리 해제
}
```

```
동작 흐름:

  Blob(데이터) → createObjectURL → <a> 클릭 → 다운로드 → 메모리 해제
```

### 4-2. CSV 다운로드

```javascript
export function downloadCsv(columns, rows, filename) {
  const csvContent = '\uFEFF' + header + '\n' + body
  //                  ^^^^^^ BOM (Byte Order Mark)

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  downloadBlob(blob, filename)
}
```

```
왜 BOM(\uFEFF)이 필요한가?

  Excel은 CSV 파일을 열 때 인코딩을 자동 감지합니다.
  BOM이 없으면 한글이 깨질 수 있습니다.

  \uFEFF = "이 파일은 UTF-8입니다!"라는 표시
```

### CSV 값 이스케이프

```javascript
const escapeCsv = (val) => {
  const str = String(val)
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    return `"${str.replace(/"/g, '""')}"`    // 쌍따옴표 이스케이프
  }
  return str
}
```

```
이스케이프 예시:
  "개발, 기획"  → ""개발, 기획""    (쉼표가 있으면 따옴표로 감싸기)
  '그는 "팀장"' → '"그는 ""팀장"""'  (따옴표 안의 따옴표는 2개로)
```

### 4-3. DOM → PNG 캡처

```javascript
export async function captureElementPng(element, filename) {
  const { toPng } = await import('html-to-image')  // 동적 import
  const restore = expandForCapture(element)         // 스크롤 영역 확장

  try {
    const dataUrl = await toPng(element, {
      pixelRatio: 2,                 // 레티나 대응 (2배 해상도)
      backgroundColor: '#ffffff',
      filter: exportFilter           // export-exclude 클래스 제외
    })
    downloadDataUrl(dataUrl, filename)
  } finally {
    restore()                        // 스크롤 영역 복원
  }
}
```

### expandForCapture — 스크롤 영역 확장

```javascript
function expandForCapture(element) {
  const saved = {
    overflow: element.style.overflow,
    height: element.style.height,
    maxHeight: element.style.maxHeight
  }
  element.style.overflow = 'visible'
  element.style.height = 'auto'
  element.style.maxHeight = 'none'

  return () => {                    // 복원 함수 반환
    element.style.overflow = saved.overflow
    element.style.height = saved.height
    element.style.maxHeight = saved.maxHeight
  }
}
```

```
왜 확장하나?

  화면에서 스크롤해야 보이는 내용도 캡처에 포함시키기 위해.
  overflow: hidden → visible로 바꾸면
  모든 콘텐츠가 한 번에 보이게 됩니다.

  ┌────────┐              ┌────────┐
  │ 보이는  │              │ 보이는  │
  │ 영역   │   →  확장 →  │ 영역   │
  │........│              │ 숨겨진  │
  │(스크롤) │              │ 영역   │
  └────────┘              │ 전부   │
                          │ 보임   │
                          └────────┘
```

### 4-4. DOM → PDF (멀티페이지)

```javascript
export async function exportElementPdf(element, title, filename) {
  const { toPng } = await import('html-to-image')
  const { default: jsPDF } = await import('jspdf')

  // 1. 임시 헤더 DOM 삽입 (한글 깨짐 방지)
  const headerDiv = document.createElement('div')
  headerDiv.innerHTML = `<span>${title}</span><span>${new Date().toLocaleString('ko-KR')}</span>`
  element.insertBefore(headerDiv, element.firstChild)

  // 2. 스크롤 확장
  const restore = expandForCapture(element)

  // 3. DOM → 이미지 캡처
  const dataUrl = await toPng(element, { pixelRatio: 2 })

  // 4. 이미지 → PDF (멀티페이지)
  const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' })
  // ... 페이지 분할 로직 ...
  pdf.save(filename)

  // 5. 정리
  element.removeChild(headerDiv)
  restore()
}
```

### 멀티페이지 분할 원리

```
하나의 긴 이미지를:

  ┌─────────────────┐
  │   페이지 1       │  ← A4 높이만큼 잘라서
  ├─────────────────┤
  │   페이지 2       │  ← 다음 페이지에 넣고
  ├─────────────────┤
  │   페이지 3       │  ← 또 다음 페이지에
  └─────────────────┘

  totalPages = Math.ceil(scaledH / availH)

  각 페이지마다:
    Canvas에서 해당 영역을 잘라 → PDF 페이지에 addImage
```

### 한글 깨짐 방지 전략

```
문제: jsPDF의 text() 메서드는 한글 폰트를 내장하지 않음
해결: text() 대신 DOM에 직접 헤더를 삽입 → 브라우저가 렌더링 → 이미지로 캡처

  jsPDF.text("제목")           → 한글 깨짐 ❌
  DOM.insertBefore(headerDiv)  → 브라우저 렌더링 → 캡처 → 한글 정상 ✅
```

### exportFilter — 제외 필터

```javascript
function exportFilter(domNode) {
  return !domNode.classList?.contains('export-exclude')
}
```

> `export-exclude` 클래스가 있는 요소(예: 내보내기 버튼 자체)는
> 캡처에서 제외됩니다. 캡처 결과에 버튼이 나오면 이상하니까요.

---

## 리뷰 체크리스트

- [ ] CSS 유틸리티 클래스명이 직관적인가? (`.mt-10` = margin-top: 10px)
- [ ] `formatMarkdownToHtml()`의 변환 순서가 올바른가? (코드 블록 → placeholder 보호 먼저)
- [ ] `escapeHtml()`로 XSS가 방지되는가?
- [ ] CSV 다운로드에 BOM(`\uFEFF`)이 포함되어 한글이 깨지지 않는가?
- [ ] PNG/PDF 캡처 시 스크롤 영역이 확장되어 전체 내용이 포함되는가?
- [ ] `expandForCapture()`의 복원 함수가 finally 블록에서 호출되는가? (에러 시에도 복원)
- [ ] PDF 멀티페이지가 올바르게 분할되는가?
- [ ] `window.copyTable`이 중복 등록되지 않는가? (`_copyTableRegistered` 플래그 확인)
