# Phase 8-4: 어떻게 동작하나 — 스타일 시스템 시나리오

## 이 문서의 목적

CSS 변수, SCSS Mixin, JS 유틸리티가 **실제 사용자 동작**에서
어떻게 협력하는지 6가지 시나리오로 설명합니다.

---

## 시나리오 1: 다크모드 토글

**상황**: 사용자가 헤더의 테마 토글 버튼을 클릭합니다.

### 전체 흐름

```
사용자: 🌙 버튼 클릭
     │
     ▼
[1] JavaScript (AppHeader.vue)
     │  store.commit('app/SET_THEME', 'dark')
     │  document.documentElement.setAttribute('data-theme', 'dark')
     │  localStorage.setItem('theme', 'dark')
     │
     ▼
[2] CSS 변수 전환 (_variables.scss)
     │  :root 변수 → [data-theme="dark"] 변수로 전환
     │  --bg-color: #f5f7fa → #1a1a1a
     │  --text-color-primary: #303133 → #e5e5e5
     │  --border-color: #dcdfe6 → #4a4a4a
     │
     ▼
[3] transition 애니메이션 (_reset.scss)
     │  body { transition: var(--theme-transition); }
     │  → 0.3초에 걸쳐 배경/텍스트/테두리 색상 부드럽게 변경
     │
     ▼
[4] Element Plus 오버라이드 (_element-dark.scss)
     │  [data-theme="dark"] .el-card { ... }
     │  [data-theme="dark"] .el-table { ... }
     │  → 20+ 컴포넌트가 다크 스타일로 전환
     │
     ▼
[5] 화면 전체가 0.3초 만에 다크모드로 전환 완료
```

### 영향 범위

```
전환되는 것:
  ✅ 페이지 배경색
  ✅ 카드/입력창/테이블 배경
  ✅ 텍스트 색상 (주/보조/placeholder)
  ✅ 테두리/그림자
  ✅ 스크롤바 색상
  ✅ 채팅 버블 색상
  ✅ Element Plus 컴포넌트 21종

전환되지 않는 것:
  ❌ 레이아웃 (위치, 크기는 변하지 않음)
  ❌ 아이콘 위치
  ❌ 주요 색상 (primary #409eff는 라이트/다크 동일)
```

### 시간순 분석

```
t=0ms    사용자 클릭
t=1ms    setAttribute('data-theme', 'dark') 실행
t=2ms    CSS 변수 즉시 전환 → transition 시작
t=150ms  전환 50% 진행 (중간 색상)
t=300ms  전환 완료 (다크 모드 색상)
t=301ms  localStorage에 'dark' 저장 (다음 방문 시 유지)
```

---

## 시나리오 2: 마크다운 렌더링 파이프라인

**상황**: AI가 테이블과 코드 블록이 포함된 답변을 보냅니다.

### 입력 텍스트

```
## 부서별 현황

| 부서 | 인원 | 평균연봉 |
|------|------|----------|
| 개발 | 15   | 5,200만원 |
| 기획 | 8    | 4,800만원 |

**합계**: 23명

```sql
SELECT department, COUNT(*) FROM employees GROUP BY department
```
```

### 변환 과정

```
[1단계] 코드 블록 보호
     │  ```sql ... ``` → \x000\x00 (placeholder 저장)
     │  placeholders[0] = "<pre><code class='language-sql'>...</code></pre>"
     │
[2단계] 인라인 코드 보호
     │  (이 예제에는 없음)
     │
[3단계] 테이블 변환 (parseMarkdownTable)
     │  | 부서 | 인원 | → <table class="md-table">...</table>
     │  구분선(|---|---| ) → skip
     │
[4단계] 헤더 변환
     │  ## 부서별 현황 → <span class="md-h2">부서별 현황</span>
     │
[5~6단계] 볼드/기울임
     │  **합계** → <strong>합계</strong>
     │
[7단계] 리스트
     │  (이 예제에는 없음)
     │
[8단계] 줄바꿈 → <br>
     │
[9단계] 블록 요소 사이 <br> 정리
     │
[10단계] placeholder 복원
     │  \x000\x00 → <pre><code class="language-sql">...</code></pre>
```

### 렌더링 결과와 스타일 적용

```
┌─ ChatMessage.vue ──────────────────────────────────────┐
│                                                        │
│  부서별 현황                    ← md-h2 mixin 적용       │
│                                                        │
│  ┌─ md-table-wrapper ─────────────────────────────┐   │
│  │  [📋] ← copy-table-btn mixin                   │   │
│  │  ┌─ md-table ──────────────────────────────┐   │   │
│  │  │  부서  │  인원  │  평균연봉              │   │   │
│  │  │───────┼────────┼──────────────────────│   │   │
│  │  │  개발  │   15   │  5,200만원            │   │   │
│  │  │  기획  │    8   │  4,800만원            │   │   │
│  │  └────────────────────────────────────────┘   │   │
│  └────────────────────────────────────────────────┘   │
│                                                        │
│  합계: 23명               ← strong mixin 적용           │
│                                                        │
│  ┌─ pre (code-block) ─────────────────────────────┐   │
│  │  SELECT department, COUNT(*)                    │   │
│  │  FROM employees                                 │   │
│  │  GROUP BY department                            │   │
│  └─────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────┘
```

### 스타일 적용 체인

```
ChatMessage.vue의 <style scoped>
  │
  @use '@/assets/styles/mixins' as mixins;
  │
  .message-content {
  │  @include mixins.md-table-styles;     ← :deep(.md-table) 스타일
  │  @include mixins.copy-table-btn;      ← :deep(.copy-table-btn) 스타일
  │  @include mixins.md-header-styles;    ← :deep(.md-h2) 스타일
  │  @include mixins.code-block-styles;   ← :deep(pre) 스타일
  │  @include mixins.strong-styles;       ← :deep(strong) 스타일
  │  @include mixins.inline-code-styles;  ← :deep(code) 스타일
  └─ ...
```

---

## 시나리오 3: 테이블 복사

**상황**: 사용자가 마크다운 테이블의 복사 버튼(📋)을 클릭합니다.

### 전체 흐름

```
사용자: [📋] 버튼 클릭
     │
     ▼
[1] onclick="window.copyTable(this)"  (v-html 내의 순수 DOM 이벤트)
     │
     ▼
[2] window.copyTable(btn)  (registerTableCopyFunction에서 등록)
     │
     ├─ btn.closest('.md-table-wrapper')    테이블 감싸개 찾기
     ├─ wrapper.querySelector('table')      테이블 요소 찾기
     │
     ▼
[3] 테이블 → 탭 구분 텍스트 변환
     │  "부서\t인원\t평균연봉\n개발\t15\t5,200만원\n기획\t8\t4,800만원\n"
     │
     ▼
[4] 클립보드 복사 시도
     │
     ├─ HTTPS? → navigator.clipboard.writeText(text)
     │    │
     │    └─ 실패 → fallbackCopy(text)  (execCommand)
     │
     └─ HTTP?  → fallbackCopy(text)  (execCommand)
          │
          └─ 실패 → 경고 토스트
     │
     ▼
[5] 성공 시
     │  ├─ 버튼 테두리 → 초록색 (1.5초간)
     │  └─ 토스트: "표가 클립보드에 복사되었습니다."
     │
     ▼
[6] 복사된 텍스트를 Excel에 붙여넣기
     │
     ┌──────┬──────┬───────────┐
     │ 부서 │ 인원 │ 평균연봉   │  ← 탭 구분이라 셀에 정확히 배치
     │ 개발 │  15  │ 5,200만원  │
     │ 기획 │   8  │ 4,800만원  │
     └──────┴──────┴───────────┘
```

### 성공 피드백 시각화

```
클릭 전:                     클릭 직후 (0~1.5초):
┌────┐                      ┌────┐
│ 📋 │  회색 테두리          │ 📋 │  초록색 테두리 + 토스트
└────┘                      └────┘

1.5초 후:
┌────┐
│ 📋 │  회색 테두리 (원복)
└────┘
```

---

## 시나리오 4: 대시보드 PDF 내보내기

**상황**: 관리자가 대시보드를 PDF로 내보냅니다.

### 전체 흐름

```
관리자: [PDF 내보내기] 버튼 클릭
     │
     ▼
[1] exportElementPdf(element, "대시보드 리포트", filename)
     │
     ▼
[2] 동적 import (최초 1회만 다운로드)
     │  const { toPng } = await import('html-to-image')    ~50KB
     │  const { default: jsPDF } = await import('jspdf')   ~300KB
     │
     ▼
[3] 임시 헤더 DOM 삽입 (한글 깨짐 방지)
     │  ┌──────────────────────────────────────────────┐
     │  │ 대시보드 리포트              2026. 3. 4. 오후 │
     │  │ ─────────────────────────────────────────── │
     │  │ (기존 대시보드 내용)                          │
     │  └──────────────────────────────────────────────┘
     │
     ▼
[4] 스크롤 영역 확장
     │  overflow: hidden → visible
     │  height: 600px → auto
     │
     ▼
[5] DOM → PNG 이미지 캡처 (pixelRatio: 2)
     │  → 고해상도 이미지 (레티나 대응)
     │  → export-exclude 클래스 요소 제외
     │
     ▼
[6] 이미지 → PDF 멀티페이지 변환
     │
     │  이미지 높이가 A4 1페이지를 초과하면:
     │
     │  ┌─ Page 1 ─────────┐  ┌─ Page 2 ─────────┐
     │  │ 헤더              │  │ 차트 계속          │
     │  │ KPI 카드          │  │ 시스템 현황        │
     │  │ 차트 시작부분      │  │                   │
     │  └──────────────────┘  └──────────────────┘
     │
     ▼
[7] pdf.save("대시보드_20260304_163847.pdf")
     │
     ▼
[8] 정리
     │  ├─ 임시 헤더 DOM 제거
     │  └─ 스크롤 영역 복원 (overflow, height 원복)
```

### 핵심 포인트

```
Q: 왜 jsPDF.text()를 안 쓰고 DOM 헤더를 삽입하나?
A: jsPDF는 한글 폰트를 내장하지 않음.
   DOM에 직접 넣으면 브라우저가 렌더링 → 이미지로 캡처 → 한글 정상

Q: 왜 동적 import를 쓰나?
A: html-to-image(~50KB) + jsPDF(~300KB)는 큰 라이브러리.
   PDF 내보내기를 안 쓰는 사용자는 다운로드할 필요 없음.
   버튼 클릭 시에만 로드 → 초기 로딩 시간 절약.

Q: pixelRatio: 2는 왜?
A: 레티나 디스플레이(고해상도)에서도 선명하게 보이려면
   2배 크기로 캡처해야 합니다.
```

---

## 시나리오 5: NL2SQL 결과 → CSV 다운로드

**상황**: NL2SQL 결과 테이블을 CSV로 내보냅니다.

### 전체 흐름

```
사용자: [📥 CSV] 버튼 클릭
     │
     ▼
[1] downloadCsv(columns, rows, filename)
     │
     │  columns = ["부서", "인원", "평균연봉"]
     │  rows = [
     │    { "부서": "개발", "인원": 15, "평균연봉": "5,200만원" },
     │    { "부서": "기획", "인원": 8,  "평균연봉": "4,800만원" }
     │  ]
     │
     ▼
[2] CSV 문자열 생성
     │  BOM + 헤더 + 본문
     │
     │  "\uFEFF부서,인원,평균연봉\n개발,15,\"5,200만원\"\n기획,8,\"4,800만원\""
     │         ↑                              ↑
     │        BOM                     쉼표 포함 → 따옴표 감싸기
     │
     ▼
[3] Blob 생성 + 다운로드
     │  Blob(text/csv;charset=utf-8)
     │  → createObjectURL → <a>.click() → 다운로드
     │
     ▼
[4] 결과: "부서별인원_20260304_163847.csv" 파일 저장
     │
     Excel에서 열면:
     ┌──────┬──────┬───────────┐
     │ 부서 │ 인원 │ 평균연봉   │  ← 한글 정상 표시 (BOM 덕분)
     │ 개발 │  15  │ 5,200만원  │
     │ 기획 │   8  │ 4,800만원  │
     └──────┴──────┴───────────┘
```

---

## 시나리오 6: 새 컴포넌트에 스타일 적용하기

**상황**: 개발자가 새 Vue 컴포넌트를 만들고 MUREUM 스타일을 적용합니다.

### 단계별 가이드

```
[1] 전역 클래스 활용 (HTML에 클래스명만 추가)
     │
     │  <template>
     │    <div class="content-card">          ← _chat-global.scss
     │      <div class="page-header">         ← _chat-global.scss
     │        <h2>새 페이지</h2>
     │        <div class="header-right">
     │          <el-button>추가</el-button>
     │        </div>
     │      </div>
     │      <div class="flex-between mt-20">  ← _utilities.scss
     │        <span class="text-muted">설명</span>
     │      </div>
     │    </div>
     │  </template>
     │
     ▼
[2] Mixin 활용 (scoped 스타일에서 @include)
     │
     │  <style lang="scss" scoped>
     │  @use '@/assets/styles/mixins' as mixins;
     │
     │  .stats-row {
     │    @include mixins.stats-row;
     │  }
     │
     │  .stat-item {
     │    @include mixins.stat-card;
     │  }
     │
     │  .message-content {
     │    @include mixins.md-table-styles;     // 마크다운 테이블
     │    @include mixins.md-header-styles;    // 마크다운 헤더
     │    @include mixins.strong-styles;       // 볼드
     │    @include mixins.code-block-styles;   // 코드 블록
     │  }
     │  </style>
     │
     ▼
[3] CSS 변수 직접 사용 (커스텀 스타일)
     │
     │  .custom-panel {
     │    background-color: var(--bg-color-card);     // 테마 자동 전환
     │    color: var(--text-color-primary);
     │    border: 1px solid var(--border-color);
     │    transition: var(--theme-transition);         // 부드러운 전환
     │  }
```

### 요약: 어떤 방식을 언제 쓰나?

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│   필요한 것            → 사용할 방식                           │
│   ─────────────────────────────────────────────              │
│   단순 정렬/여백        → 전역 클래스 (.flex, .mt-10)          │
│   공통 레이아웃 구조    → 전역 클래스 (.content-card, .page-header)│
│   마크다운 렌더링       → Mixin (@include mixins.md-table-styles) │
│   크기 커스텀 가능 스타일 → 파라미터 Mixin (font-size, padding)    │
│   색상/테마 적응         → CSS 변수 (var(--bg-color-card))       │
│   다크모드 Element Plus  → 자동 (_element-dark.scss가 처리)      │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 전체 아키텍처 시각화

```
┌─── 앱 시작 ──────────────────────────────────────────────────┐
│                                                              │
│  main.js                                                     │
│    │                                                         │
│    ├─ import 'main.scss'                                     │
│    │    ├─ _variables.scss    → :root + [data-theme="dark"]  │
│    │    ├─ _reset.scss        → *, body + scrollbar          │
│    │    ├─ _utilities.scss    → .flex, .mt-10, ...           │
│    │    ├─ _chat-global.scss  → .content-card, .message-bubble│
│    │    ├─ _element-dark.scss → 21개 컴포넌트 다크 오버라이드  │
│    │    └─ _dropdown.scss     → 드롭다운 팝업 다크            │
│    │                                                         │
│    └─ createApp(App)                                         │
│         │                                                    │
│         └─ 컴포넌트 렌더링                                    │
│              │                                               │
│              ├─ <style scoped>                                │
│              │    @use 'mixins' as m;                         │
│              │    @include m.stat-card;    ← mixin 포함       │
│              │    color: var(--text-color-primary); ← CSS변수  │
│              │                                               │
│              ├─ v-html="formatMarkdownToHtml(content)"       │
│              │    → markdownParser.js → HTML 생성             │
│              │    → :deep() mixin으로 스타일 적용              │
│              │                                               │
│              └─ 내보내기 클릭                                  │
│                   → exportUtils.js → CSV/PNG/PDF 다운로드     │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 리뷰 체크리스트 (Phase 8 종합)

### CSS 변수 & 테마
- [ ] 모든 색상이 CSS 변수를 통해 사용되는가?
- [ ] 라이트/다크 변수가 쌍으로 정의되어 있는가?
- [ ] transition으로 부드러운 테마 전환이 적용되는가?
- [ ] 대시보드 테마 격리가 Element Plus `--el-*` 변수까지 포함하는가?

### SCSS Mixin
- [ ] 파라미터에 합리적인 기본값이 있는가?
- [ ] `:deep()` 선택자가 올바르게 사용되는가?
- [ ] 동일 스타일이 중복 없이 mixin으로 통합되어 있는가?

### JS 유틸리티
- [ ] `escapeHtml()`로 XSS가 방지되는가?
- [ ] 마크다운 파서의 변환 순서가 올바른가?
- [ ] CSV에 BOM이 포함되어 한글이 깨지지 않는가?
- [ ] PDF 캡처 후 DOM이 원래 상태로 복원되는가?
- [ ] `window.copyTable` 중복 등록이 방지되는가?

### 전역 스타일
- [ ] `_reset.scss`가 `box-sizing: border-box`를 전역 적용하는가?
- [ ] `_element-dark.scss`가 텔레포트 컴포넌트를 처리하는가?
- [ ] 전역 클래스와 mixin의 역할이 명확히 구분되는가?
